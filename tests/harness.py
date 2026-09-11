"""Shared machinery for this task's verifier.

Paths, fixture loading, the unprivileged runner and the crafted-world
helpers live here so test_outputs.py carries assertions and nothing else.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

APP = Path("/app")
DATA = APP / "data"
WORKFLOW_PATH = APP / "workflow" / "plan_resume.go"
ORIGINAL_WORKFLOW_PATH = APP / "workflow" / ".plan_resume.original.go"
SNAPSHOT_PATH = DATA / "registry_snapshot_pre_migration.json"
JOURNAL_PATH = DATA / "registry_journal.json"
REGISTRY_PATH = DATA / "checkpoint_registry.json"
SPEC_PATH = APP / "docs" / "resume_contract.json"
# The contract is golden metadata: the verifier reads it from its own image,
# never from the agent-writable copy under /app.
GOLDEN_CONTRACT_PATH = Path("/tests/fixtures/contract_golden.json")
LOG_PATH = APP / "incident" / "training_governance_log.md"
EXPECTED_FIXTURE = Path("/tests/fixtures/expected_report.json")
ALT_INPUT = Path("/tests/fixtures/alt_registry.json")

FIXTURE = json.loads(EXPECTED_FIXTURE.read_text())
SPEC = json.loads(GOLDEN_CONTRACT_PATH.read_text())

ENTRY_KEYS = set(SPEC["reconciled_inputs"]["checkpoint_registry"]["record_fields"])
SUMMARY_KEYS = set(SPEC["outputs"]["summary"]["required_fields"])
PLAN_KEYS = set(SPEC["outputs"]["resume_plan"]["required_fields"])
CHECKPOINT_KEYS = set(SPEC["outputs"]["resume_plan"]["checkpoint_fields"])
REFETCH_KEYS = set(SPEC["outputs"]["refetch_queue"]["element_fields"])
REFETCH_REASONS = set(SPEC["outputs"]["refetch_queue"]["reasons"])

# Budget published by the contract and stated in instruction.md. Held as a literal
# so it cannot be relaxed by editing the environment, and cross-checked below.
RUNTIME_BUDGET_SEC = 90.0
# The contract's published budget IS the candidate timeout: an overrunning
# run is killed and the suite fails. No measured elapsed time is graded, so
# the verdict does not depend on how fast the grading host happens to be.
HARD_TIMEOUT_SEC = int(RUNTIME_BUDGET_SEC)

CANDIDATE_UID = 65534
_CWORK = Path("/candidate-work")
def _setpriv_prefix(base: list) -> list:
    """The strictest setpriv invocation this image actually supports.

    Dropping the uid is not the whole of it: a candidate that kept inheritable
    or bounding-set capabilities could regain privilege across an exec. The two
    flags are probed rather than assumed, because a util-linux without them
    would make every run fail on the flag rather than on the task.
    """
    strict = base + ["--inh-caps=-all", "--bounding-set=-all"]
    try:
        probe = subprocess.run(strict + ["/bin/true"], capture_output=True, timeout=30)
        if probe.returncode == 0:
            return strict
    except (OSError, subprocess.SubprocessError):
        pass
    return base


# Resource ceilings for anything run as the candidate. Deliberately not
# RLIMIT_AS or RLIMIT_DATA: a language runtime that reserves a large virtual
# arena at start-up dies under those, so they would kill a correct program
# rather than a runaway one. These bound the failure modes that actually escape
# a process group -- forking without end, filling the disk, dumping core.
_CANDIDATE_NPROC = 512
_CANDIDATE_FSIZE = 512 * 1024 * 1024
_CANDIDATE_NOFILE = 1024


def _apply_rlimits() -> None:
    """Run in the child between fork and exec: own session, plus ceilings."""
    import resource

    for what, limit in (
        (resource.RLIMIT_NPROC, _CANDIDATE_NPROC),
        (resource.RLIMIT_FSIZE, _CANDIDATE_FSIZE),
        (resource.RLIMIT_NOFILE, _CANDIDATE_NOFILE),
        (resource.RLIMIT_CORE, 0),
    ):
        try:
            _soft, hard = resource.getrlimit(what)
            ceiling = limit if hard == resource.RLIM_INFINITY else min(limit, hard)
            resource.setrlimit(what, (ceiling, ceiling))
        except (ValueError, OSError):
            continue
    os.setsid()


def _pids_owned_by(uid: int) -> list:
    """Every live pid whose owner is `uid`, read from /proc."""
    pids = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            if os.stat("/proc/" + entry).st_uid == uid:
                pids.append(int(entry))
        except OSError:
            continue
    return pids


def reap_candidate_uid(uid: int = CANDIDATE_UID) -> None:
    """Kill everything still running as the candidate, whatever group it is in.

    Killing the process group is not enough on its own: a submitted program can
    call setsid and leave its own group, and would then survive into later tests
    -- holding the staged inputs of the next run, or still writing into an
    output directory being read. Ownership is the property that cannot be
    escaped, so the sweep is by owner.
    """
    import signal as _signal
    import time as _time

    for _ in range(50):
        pids = _pids_owned_by(uid)
        if not pids:
            return
        for pid in pids:
            try:
                os.kill(pid, _signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                continue
        for pid in pids:
            try:
                os.waitpid(pid, os.WNOHANG)
            except (ChildProcessError, OSError):
                continue
        _time.sleep(0.02)


_SETPRIV = _setpriv_prefix(["setpriv", f"--reuid={CANDIDATE_UID}", f"--regid={CANDIDATE_UID}",
            "--clear-groups", "--no-new-privs"])
CHILD_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/candidate-work",
             "LANG": "C.UTF-8", "GOCACHE": "/candidate-work/gocache",
             "GO111MODULE": "off", "GOPATH": "/candidate-work/gopath"}
_BIN_CACHE: dict[str, str] = {}
_run_ctr = iter(range(1, 10_000))


def _digest(value) -> str:
    """Content digest of a decoded artifact, insensitive to free whitespace."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_jsonl(path):
    """Read a contracted JSONL artifact, taking every line as written.

    Skipping blank lines here softened a contract that says one compact object
    per line: a run that padded its output with empty lines read back the same
    as a clean one and scored full marks. A blank line is a malformed line and
    is read as one.
    """
    text = Path(path).read_text(encoding="utf-8")
    if not text:
        return []
    assert text.endswith("\n"), f"{Path(path).name} has no trailing newline"
    lines = text.split("\n")[:-1]
    for number, line in enumerate(lines, start=1):
        assert line.strip(), f"{Path(path).name} line {number} is blank"
    return [json.loads(line) for line in lines]


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build(script_path: Path) -> str:
    """Compile the submitted single-file planner, cached per source path.

    Compilation runs as root: it is the trusted verifier's own action. The source
    is copied to a temp dir as main.go first so the frozen snapshot and any
    sibling files in /app/workflow never join the build.
    """
    key = str(script_path)
    if key in _BIN_CACHE:
        return _BIN_CACHE[key]
    build_dir = tempfile.mkdtemp(prefix="gobuild_")
    os.chmod(build_dir, 0o755)
    src = Path(build_dir) / "main.go"
    shutil.copyfile(script_path, src)
    binary = Path(build_dir) / "planner"
    result = subprocess.run(
        ["go", "build", "-o", str(binary), str(src)],
        capture_output=True, text=True,
        # The build environment is written out rather than inherited. Copying
        # os.environ carried whatever the surrounding run happened to hold: a
        # GOOS or GOARCH left in the environment cross-compiles the submission
        # into a binary this container cannot execute, and a correct submission
        # then fails for a reason that has nothing to do with it. The target is
        # this machine, named outright.
        env={"PATH": os.environ.get("PATH", "/usr/local/go/bin:/usr/bin:/bin"),
             "HOME": "/tmp", "LANG": "C.UTF-8",
             "GOCACHE": "/tmp/gocache", "GO111MODULE": "off",
             "GOPATH": "/tmp/gopath", "GOFLAGS": "", "GOOS": "linux",
             "GOARCH": "arm64" if platform.machine() in ("aarch64", "arm64") else "amd64",
             "CGO_ENABLED": "0", "GOTOOLCHAIN": "local"},
        preexec_fn=_apply_rlimits,
    )
    reap_candidate_uid()
    assert result.returncode == 0, f"go build failed:\n{result.stderr}"
    os.chmod(binary, 0o755)
    _BIN_CACHE[key] = str(binary)
    return str(binary)


def _candidate_dir() -> Path:
    """A fresh work area for one run, created where nothing can pre-empt it.

    /candidate-work is world-writable, so a predictable name here was an opening:
    a submission could plant the next `run-N` as a symlink to the sealed fixtures
    and wait. The root-side mkdir(exist_ok=True) would succeed through the link
    and the chmod would follow it, since os.chmod resolves symlinks and Linux has
    no lchmod. mkdtemp closes both halves -- the name is unpredictable and the
    directory is created fresh or not at all.
    """
    d = Path(tempfile.mkdtemp(prefix=f"run-{next(_run_ctr)}-", dir=str(_CWORK)))
    assert not d.is_symlink(), d
    os.chmod(d, 0o777)
    return d


def _publish_inputs() -> None:
    """Open read access on the agent-produced inputs before privileges drop.

    Never follows a link out of the agent-owned tree: os.chmod resolves symlinks,
    so a link planted at /app/... -> /tests would otherwise open the sealed
    fixtures to the unprivileged candidate.
    """
    app_root = APP.resolve()
    for path in sorted(APP.rglob("*")):
        if path.is_symlink():
            continue
        try:
            if not path.resolve().is_relative_to(app_root):
                continue
        except OSError:
            continue
        try:
            os.chmod(path, 0o755 if path.is_dir() else 0o644)
        except OSError:
            pass


def _reap_group(pgid: int) -> None:
    """Kill and reap everything left in the candidate's process group.

    start_new_session makes the candidate a session and group leader, so its pgid
    equals its pid and every process it spawns shares that group. The id is
    captured before the run: once the direct child has been waited on its pgid can
    no longer be looked up, and a leaked grandchild would survive to keep writing
    while the outputs are graded.
    """
    try:
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        return
    for _ in range(50):
        try:
            os.killpg(pgid, 0)
        except (ProcessLookupError, PermissionError, OSError):
            return
        time.sleep(0.02)


def _run_agent(argv, cwd: Path):
    """Run the submitted program unprivileged and in its own process group.

    Output goes to temporary files rather than pipes. A program that forks a
    child into its own session leaves that child holding the inherited pipe, and
    communicate() then waits for an EOF that never comes -- stalling the run for
    the whole budget and timing out a submission that had already finished. A
    file has no reader to wait on, so the parent's exit ends the wait and the
    reaps below clear whatever is left.
    """
    with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as out, \
            tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as err:
        proc = subprocess.Popen(
            _SETPRIV + argv, cwd=str(cwd), env=dict(CHILD_ENV),
            stdout=out, stderr=err,
            preexec_fn=_apply_rlimits,
        )
        pgid = proc.pid      # session leader: pgid == pid, captured before the wait
        try:
            proc.wait(timeout=HARD_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            _reap_group(pgid)
            reap_candidate_uid()
            proc.wait()
            raise
        finally:
            # even on a clean exit, anything the program left running is stopped
            # before its outputs are read
            _reap_group(pgid)
            reap_candidate_uid()
        out.seek(0)
        err.seek(0)
        return subprocess.CompletedProcess(argv, proc.returncode, out.read(), err.read())


# --------------------------------------------------------------------------
# What the submission is entitled to find under /app
# --------------------------------------------------------------------------
DECLARED_DATA = (
    DATA / "checkpoint_registry.json",
    DATA / "data_incident.json",
    DATA / "registry_journal.json",
    DATA / "registry_snapshot_pre_migration.json",
    DATA / "resume_policy.json",
    DATA / "shard_catalog.json",
)
DECLARED_INPUTS = DECLARED_DATA + (SPEC_PATH, LOG_PATH, WORKFLOW_PATH,
                                   ORIGINAL_WORKFLOW_PATH)


def _hide_everything_else_under_app() -> tuple:
    """Move aside every file under /app the submission was not given.

    The planner is compiled one file at a time, so a helper split into a sibling
    SOURCE never reaches the build -- but nothing stopped a wrapper reading or
    running that sibling at RUN time and letting it do the planning. Whatever
    else is under /app goes into a root-owned stash for the duration of one
    graded run and comes back afterwards. The recovery tool is swept up with it,
    which is the point: the instruction says only the registry it leaves behind
    is read.
    """
    allowed = {path.resolve() for path in DECLARED_INPUTS}
    stash = Path(tempfile.mkdtemp(prefix="app-stash-"))
    moved = []
    for path in sorted(APP.rglob("*"), key=lambda q: len(str(q)), reverse=True):
        if path.is_dir() and not path.is_symlink():
            continue
        try:
            if path.resolve() in allowed:
                continue
        except OSError:
            pass
        target = stash / path.relative_to(APP)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(target))
        moved.append(path.relative_to(APP))
    return stash, moved


def _restore_everything_under_app(stash: Path, moved: list) -> None:
    for relative in moved:
        destination = APP / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(stash / relative), str(destination))
    shutil.rmtree(stash, ignore_errors=True)


# --------------------------------------------------------------------------
# Reading the submitted Go source.
#
# The import list and the token stream are read by Go itself rather than by a
# lexer written here. A hand-written one is only as good as its author's model
# of the language -- a rune holding a double quote, a raw literal holding a
# backtick -- and a scan a submission can step out of is not a check at all. A
# small program built from go/scanner and go/parser hands back the token stream
# and the import declarations of a file, and nothing the source does can put
# Go's scanner out of step with Go.
# --------------------------------------------------------------------------
_GO_SCANNER_SOURCE = r"""package main

import (
	"encoding/json"
	"go/parser"
	"go/scanner"
	"go/token"
	"os"
	"strconv"
	"strings"
)

type reading struct {
	Imports    []string `json:"imports"`
	Strings    []string `json:"strings"`
	Payload    string   `json:"payload"`
	ParseError string   `json:"parse_error"`
}

func main() {
	src, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Stderr.WriteString(err.Error())
		os.Exit(1)
	}
	out := reading{Imports: []string{}, Strings: []string{}}

	fset := token.NewFileSet()
	file := fset.AddFile(os.Args[1], fset.Base(), len(src))
	var sc scanner.Scanner
	sc.Init(file, src, nil, 0) // no comment tokens, errors counted and ignored
	var payload strings.Builder
	for {
		_, tok, lit := sc.Scan()
		if tok == token.EOF {
			break
		}
		switch tok {
		case token.STRING, token.CHAR:
			value, err := strconv.Unquote(lit)
			if err != nil {
				value = lit
			}
			out.Strings = append(out.Strings, value)
			payload.WriteString(value)
		case token.ADD:
			// the seam of a concatenation contributes nothing, so a path split
			// across "/te" + "sts" closes back up into the token it spells
		case token.SEMICOLON:
			payload.WriteString(";")
		default:
			if lit != "" {
				payload.WriteString(lit)
			} else {
				payload.WriteString(tok.String())
			}
		}
	}
	out.Payload = payload.String()

	parsed, err := parser.ParseFile(token.NewFileSet(), os.Args[1], src, parser.ImportsOnly)
	if err != nil {
		out.ParseError = err.Error()
	} else {
		for _, spec := range parsed.Imports {
			value, err := strconv.Unquote(spec.Path.Value)
			if err != nil {
				value = spec.Path.Value
			}
			out.Imports = append(out.Imports, value)
		}
	}
	json.NewEncoder(os.Stdout).Encode(out)
}
"""

_GO_SCANNER_BIN: list = []
_GO_READINGS: dict = {}


def _go_scanner() -> str:
    """Build the lexing helper once per session."""
    if not _GO_SCANNER_BIN:
        d = tempfile.mkdtemp(prefix="goscan_")
        source = Path(d) / "main.go"
        source.write_text(_GO_SCANNER_SOURCE, encoding="utf-8")
        binary = Path(d) / "goscan"
        built = subprocess.run(
            ["go", "build", "-o", str(binary), str(source)],
            capture_output=True, text=True,
            env={**os.environ, "GOCACHE": "/tmp/gocache", "GO111MODULE": "off",
                 "GOPATH": "/tmp/gopath"})
        assert built.returncode == 0, f"the source reader failed to build:\n{built.stderr}"
        _GO_SCANNER_BIN.append(str(binary))
    return _GO_SCANNER_BIN[0]


def _go_reading(source: str) -> dict:
    """Lex a Go source with Go's own scanner, cached per source text."""
    key = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if key in _GO_READINGS:
        return _GO_READINGS[key]
    d = tempfile.mkdtemp(prefix="goread_")
    path = Path(d) / "subject.go"
    path.write_text(source, encoding="utf-8")
    try:
        done = subprocess.run([_go_scanner(), str(path)],
                              capture_output=True, text=True, timeout=120)
        assert done.returncode == 0, f"the source reader failed:\n{done.stderr}"
        reading = json.loads(done.stdout)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    _GO_READINGS[key] = reading
    return reading


def _go_strings(source: str) -> list:
    """Every string and rune literal in a Go file, as Go's scanner reads them.

    Raw backtick literals included: they hold a path just as well as an
    interpreted one does, and a raw-literal path handed to os.ReadFile was invisible to an
    earlier scan that skipped them.
    """
    return list(_go_reading(source)["strings"])


def _go_source_payload(source: str) -> str:
    """The token stream with its comments gone and its literal seams closed up.

    Scanning whole literals catches a path written as one. It does not catch a
    path assembled out of pieces -- "/te" + "sts/fixtures" is two literals,
    neither of which contains the token -- so the concatenating plus contributes
    nothing here and the pieces close back up. The punctuation between unrelated
    calls survives, so f("/te"); g("sts") does not become a match.
    """
    return _go_reading(source)["payload"]


def _go_imports(source: str) -> list:
    """Import paths declared by a Go file, read from its import declarations."""
    reading = _go_reading(source)
    assert not reading["parse_error"], (
        f"the submitted source does not parse as Go: {reading['parse_error']}")
    return list(reading["imports"])



def _run_pipeline(script_path: Path = WORKFLOW_PATH, input_path: Path = REGISTRY_PATH):
    """Build and run the submitted planner as an unprivileged subprocess."""
    binary = _build(script_path)
    _publish_inputs()
    work = _candidate_dir()
    out_dir = work / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(out_dir, 0o777)
    staged = work / "registry.json"
    shutil.copyfile(str(input_path), str(staged))
    os.chmod(staged, 0o644)
    result = _run_agent([binary, "--input", str(staged), "--output-dir", str(out_dir)], cwd=work)
    assert result.returncode == 0, f"planner failed:\n{result.stdout}\n{result.stderr}"
    return (out_dir,
            _load_json(out_dir / "summary.json"),
            _load_json(out_dir / "resume_plan.json"),
            _load_jsonl(out_dir / "refetch_queue.jsonl"))


__all__ = [
    "GOLDEN_CONTRACT_PATH",
    "annotations",
    "hashlib",
    "json",
    "os",
    "re",
    "shutil",
    "signal",
    "subprocess",
    "sys",
    "tempfile",
    "time",
    "Path",
    "pytest",
    "APP",
    "DATA",
    "WORKFLOW_PATH",
    "ORIGINAL_WORKFLOW_PATH",
    "SNAPSHOT_PATH",
    "JOURNAL_PATH",
    "REGISTRY_PATH",
    "SPEC_PATH",
    "LOG_PATH",
    "EXPECTED_FIXTURE",
    "ALT_INPUT",
    "FIXTURE",
    "SPEC",
    "ENTRY_KEYS",
    "SUMMARY_KEYS",
    "PLAN_KEYS",
    "CHECKPOINT_KEYS",
    "REFETCH_KEYS",
    "REFETCH_REASONS",
    "RUNTIME_BUDGET_SEC",
    "HARD_TIMEOUT_SEC",
    "CANDIDATE_UID",
    "_CWORK",
    "_SETPRIV",
    "CHILD_ENV",
    "_BIN_CACHE",
    "_run_ctr",
    "_digest",
    "_load_json",
    "_load_jsonl",
    "_write_json",
    "_build",
    "_candidate_dir",
    "_publish_inputs",
    "_run_agent",
    "_run_pipeline",
    "DECLARED_DATA",
    "DECLARED_INPUTS",
    "_hide_everything_else_under_app",
    "_restore_everything_under_app",
    "_go_reading",
    "_go_strings",
    "_go_source_payload",
    "_go_imports",
]
