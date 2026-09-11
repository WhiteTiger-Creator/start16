"""Verifier tests for this task.

Every test below corresponds to something instruction.md states is graded.
Shared machinery lives in harness.py.
"""

import harness
from harness import *  # noqa: F401,F403


# The policy, the incident record and the shard catalogue as the image ships
# them, captured once at import. The crafted probes below rewrite those three
# files and restore them in a finally, so a graded run reads the shipped state
# -- but only because the session fixtures happen to be instantiated by a test
# that precedes the probes in file order. Under `-k`, a reordering or a partial
# run, a fixture could be built while a probe's crafted world was still on disk
# and grade the run against inputs the task never ships. Restoring these bytes
# first makes the two graded runs independent of when they are asked for.
SHIPPED_INPUTS = {p: p.read_bytes() for p in (
    DATA / "resume_policy.json", DATA / "data_incident.json",
    DATA / "shard_catalog.json")}


def _restore_shipped_inputs():
    for path, blob in SHIPPED_INPUTS.items():
        if path.read_bytes() != blob:
            path.write_bytes(blob)


@pytest.fixture(scope="session")
def primary_outputs():
    _restore_shipped_inputs()
    return _run_pipeline()


@pytest.fixture(scope="session")
def alternate_outputs():
    _restore_shipped_inputs()
    return _run_pipeline(input_path=ALT_INPUT)





# --------------------------------------------------------------------------
# Step one: the truncated registry must be rebuilt before anything is planned
# --------------------------------------------------------------------------
def test_recovery_sources_are_intact():
    """The snapshot, journal, catalogue, incident record and run log are read, not rewritten."""
    live = {n: hashlib.sha256(Path(p).read_bytes()).hexdigest() for n, p in (
        ("snapshot", SNAPSHOT_PATH), ("journal", JOURNAL_PATH),
        ("catalog", DATA / "shard_catalog.json"), ("incident", DATA / "data_incident.json"),
        ("policy", DATA / "resume_policy.json"), ("log", LOG_PATH))}
    assert _digest(live) == FIXTURE["rule_sources_digest"]


def test_recovery_sources_are_still_intact_after_the_graded_run(primary_outputs):
    """Checked again once the planner has run, not only before it.

    The digest above is taken at collection, before the verifier drives the
    submitted planner. A planner that rewrote one of its own inputs mid-run --
    repairing data it had misread, say -- would pass that check and be caught
    only sideways. Depending on primary_outputs orders this one after the run.
    """
    live = {n: hashlib.sha256(Path(p).read_bytes()).hexdigest() for n, p in (
        ("snapshot", SNAPSHOT_PATH), ("journal", JOURNAL_PATH),
        ("catalog", DATA / "shard_catalog.json"), ("incident", DATA / "data_incident.json"),
        ("policy", DATA / "resume_policy.json"), ("log", LOG_PATH))}
    assert _digest(live) == FIXTURE["rule_sources_digest"], (
        "an input was rewritten while the graded run was in flight")


def test_registry_was_recovered():
    """The rebuilt registry matches the governed replay exactly."""
    recovered = _load_json(REGISTRY_PATH)
    assert len(recovered) == FIXTURE["recovered_entry_count"]
    assert _digest(recovered) == FIXTURE["recovered_registry_digest"]


def test_recovered_entries_carry_only_the_declared_fields():
    """Migrator bookkeeping never survives the replay."""
    for row in _load_json(REGISTRY_PATH):
        assert set(row) == ENTRY_KEYS


def test_recovered_registry_is_sorted():
    """The registry ascends by step, rank, kind, then entry id."""
    rows = _load_json(REGISTRY_PATH)
    keys = [(r["step"], r["rank"], r["kind"], r["entry_id"]) for r in rows]
    assert keys == sorted(keys)


def test_wrong_replays_differ_from_the_governed_registry():
    """Three plausible misreadings of the replay each give a different registry."""
    expected = FIXTURE["recovered_registry_digest"]
    assert FIXTURE["shipped_truncated_digest"] != expected
    snapshot = {r["entry_id"]: r for r in _load_json(SNAPSHOT_PATH)}
    journal = _load_json(JOURNAL_PATH)

    def replay(by_seq: bool, reinstate_from_snapshot: bool):
        live = {k: dict(v) for k, v in snapshot.items()}
        held = {}
        for c in (sorted(journal, key=lambda x: x["seq"]) if by_seq else journal):
            eid, kind = c["entry_id"], c["kind"]
            if kind == "amend" and eid in live:
                live[eid][c["field"]] = c["value"]
            elif kind == "invalidate" and eid in live:
                held[eid] = dict(live.pop(eid))
            elif kind == "reinstate":
                if reinstate_from_snapshot:
                    if eid in snapshot and eid not in live:
                        live[eid] = dict(snapshot[eid])
                elif eid in held:
                    live[eid] = held.pop(eid)
        rows = sorted(live.values(),
                      key=lambda r: (r["step"], r["rank"], r["kind"], r["entry_id"]))
        return _digest(rows)

    assert replay(False, False) != expected
    assert replay(True, True) != expected


# --------------------------------------------------------------------------
# Step two: the resume plan
# --------------------------------------------------------------------------
def test_primary_summary_matches_fixture(primary_outputs):
    """Every summary field matches the sealed reference run."""
    _, summary, _, _ = primary_outputs
    assert summary == FIXTURE["primary"]["summary"]


def test_primary_artifacts_match_fixture(primary_outputs):
    """The plan and the deferred queue match the sealed digests."""
    _, _, plan, queue = primary_outputs
    assert _digest(plan) == FIXTURE["primary"]["plan_digest"]
    assert _digest(queue) == FIXTURE["primary"]["queue_digest"]


def test_alternate_registry_matches_fixture(alternate_outputs):
    """A held-out registry the agent never sees produces the sealed result."""
    _, summary, plan, queue = alternate_outputs
    assert summary == FIXTURE["alternate"]["summary"]
    assert _digest(plan) == FIXTURE["alternate"]["plan_digest"]
    assert _digest(queue) == FIXTURE["alternate"]["queue_digest"]


def test_a_stale_file_in_the_given_output_dir_is_cleared(tmp_path: Path):
    """The contract's "exactly the three named files" holds for --output-dir too.

    The default-path run above plants a stale artifact; this does the same for an
    explicitly supplied directory, which is the case the reference missed -- it
    created the directory if absent but never removed what was already there.
    """
    binary = _build(WORKFLOW_PATH)
    _publish_inputs()
    work = _candidate_dir()
    out_dir = work / "given"
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(out_dir, 0o777)
    (out_dir / "stale.txt").write_text("left over\n", encoding="utf-8")
    os.chmod(out_dir / "stale.txt", 0o666)
    # A symlink is content too, and every probe here planted only ordinary files
    # and directories. A cleanup that skipped links -- an unremarkable safety
    # rule, since removing one blind can look like following it -- cleared the
    # file, wrote the three artifacts, exited nought and left a fourth entry
    # standing, which is not the end state the contract names. The two here point
    # at a file and at a directory; neither target may be touched either, since
    # what the contract asks to be cleared is the entry, not what it refers to.
    outside = work / "link-target"
    outside.mkdir()
    (outside / "keep.txt").write_text("not the run's to remove\n", encoding="utf-8")
    os.chmod(outside, 0o777)
    os.chmod(outside / "keep.txt", 0o666)
    (out_dir / "stale-file-link").symlink_to(outside / "keep.txt")
    (out_dir / "stale-dir-link").symlink_to(outside)
    # A directory with something in it, and removable. Every probe here planted
    # files, links and at most an EMPTY directory, so a clearing loop that
    # unlinked each entry one by one rather than removing it recursively cleared
    # everything the suite staged and passed -- and would have reported failure
    # over an ordinary directory the contract says to clear.
    (out_dir / "nested").mkdir()
    (out_dir / "nested" / "old.json").write_text("{}\n", encoding="utf-8")
    os.chmod(out_dir / "nested", 0o777)
    os.chmod(out_dir / "nested" / "old.json", 0o666)
    before = out_dir.stat()
    result = _run_agent([binary, "--output-dir", str(out_dir)], cwd=work)
    assert result.returncode == 0, (
        f"the run exited {result.returncode}\n"
        f"stdout: {result.stdout[-2000:]}\nstderr: {result.stderr[-2000:]}")
    assert sorted(q.name for q in out_dir.iterdir()) == [
        "refetch_queue.jsonl", "resume_plan.json", "summary.json"], (
        "a stale entry survived into the output directory: "
        f"{sorted(q.name for q in out_dir.iterdir())}")
    assert (outside / "keep.txt").exists() and outside.is_dir(), (
        "the run cleared through a link rather than removing the link itself")
    after = out_dir.stat()
    assert (after.st_ino, after.st_dev) == (before.st_ino, before.st_dev), (
        "the directory was replaced rather than cleared")
    # names and an exit code are not enough: a planner that emitted three empty
    # documents whenever --output-dir was given satisfied every line above while
    # staying correct on every other run here. This run reads the same default
    # input as the graded one, so it has to produce the same three artifacts.
    assert _load_json(out_dir / "summary.json") == FIXTURE["primary"]["summary"], (
        "the run cleared the directory but did not produce the graded result")
    assert _digest(_load_json(out_dir / "resume_plan.json")) == \
        FIXTURE["primary"]["plan_digest"]
    assert _digest(_load_jsonl(out_dir / "refetch_queue.jsonl")) == \
        FIXTURE["primary"]["queue_digest"]


def test_an_output_directory_that_does_not_exist_is_created():
    """instruction.md says an absent --output-dir is created, not a failure.

    Every other run here hands the planner a directory that already exists --
    _run_pipeline makes one, and the two clearing probes make theirs before the
    run -- so the branch the instruction states outright was never reached, and a
    planner that refused a path it could not stat would have passed the whole
    suite. The parent is missing as well, so nothing short of creating the chain
    gets the run through.
    """
    binary = _build(WORKFLOW_PATH)
    _publish_inputs()
    work = _candidate_dir()
    out_dir = work / "absent-parent" / "absent-output"
    assert not out_dir.exists() and not out_dir.parent.exists(), (
        "the probe's output directory is already there, so it proves nothing")

    result = _run_agent([binary, "--output-dir", str(out_dir)], cwd=work)
    assert result.returncode == 0, (
        f"the run exited {result.returncode} over an output directory that does "
        f"not yet exist, though the instruction has it created rather than "
        f"treated as a failure\n"
        f"stdout: {result.stdout[-2000:]}\nstderr: {result.stderr[-2000:]}")
    assert out_dir.is_dir(), "the run exited nought but created no output directory"
    assert sorted(q.name for q in out_dir.iterdir()) == [
        "refetch_queue.jsonl", "resume_plan.json", "summary.json"]
    # and it is the graded run that was written there, not three empty documents
    assert _load_json(out_dir / "summary.json") == FIXTURE["primary"]["summary"]
    assert _digest(_load_json(out_dir / "resume_plan.json")) == \
        FIXTURE["primary"]["plan_digest"]
    assert _digest(_load_jsonl(out_dir / "refetch_queue.jsonl")) == \
        FIXTURE["primary"]["queue_digest"]


def test_output_dir_contains_exactly_three_files(primary_outputs):
    """A run writes the three contracted artifacts and nothing else."""
    out_dir, _, _, _ = primary_outputs
    assert sorted(p.name for p in out_dir.iterdir()) == [
        "refetch_queue.jsonl", "resume_plan.json", "summary.json"]


def test_summary_schema_and_types(primary_outputs):
    """The summary carries exactly the contracted fields at the contracted types."""
    _, summary, _, _ = primary_outputs
    assert set(summary) == SUMMARY_KEYS
    for field, kind in SPEC["outputs"]["summary"]["field_types"].items():
        value = summary[field]
        if kind == "integer":
            assert isinstance(value, int) and not isinstance(value, bool), field
        else:
            assert isinstance(value, str), field


def test_plan_schema_and_ordering(primary_outputs):
    """The plan carries the contracted shape and its checkpoints ascend by step."""
    _, _, plan, _ = primary_outputs
    assert set(plan) == PLAN_KEYS
    steps = [c["step"] for c in plan["checkpoints"]]
    assert steps == sorted(steps)
    for c in plan["checkpoints"]:
        assert set(c) == CHECKPOINT_KEYS
        assert isinstance(c["complete"], bool) and isinstance(c["admissible"], bool)
    for r in plan["refetch"]:
        assert set(r) == REFETCH_KEYS
        assert r["reason"] in REFETCH_REASONS


def test_queue_schema_and_ordering(primary_outputs):
    """Deferred rows carry the contracted fields and ascend by epoch then shard id."""
    _, _, _, queue = primary_outputs
    keys = [(r["epoch"], r["shard_id"]) for r in queue]
    assert keys == sorted(keys)
    for r in queue:
        assert set(r) == REFETCH_KEYS
        assert r["reason"] in REFETCH_REASONS


def test_resume_point_lies_before_the_first_poisoned_step(primary_outputs):
    """The chosen restart predates the incident and is itself complete."""
    _, summary, plan, _ = primary_outputs
    assert summary["resume_step"] == plan["resume_step"]
    assert summary["resume_step"] < summary["first_poisoned_step"]
    chosen = [c for c in plan["checkpoints"] if c["step"] == summary["resume_step"]]
    assert chosen and chosen[0]["complete"] and chosen[0]["admissible"]


def test_resume_point_is_the_highest_admissible_one(primary_outputs):
    """No admissible checkpoint sits above the one selected."""
    _, summary, plan, _ = primary_outputs
    admissible = [c["step"] for c in plan["checkpoints"] if c["admissible"]]
    assert admissible and max(admissible) == summary["resume_step"]


def test_a_newer_complete_checkpoint_was_available_and_rejected(primary_outputs):
    """The shipped run really does hold a later complete checkpoint.

    Without one the rollback rule would be untested on the graded data: the
    newest complete step must lie past the incident and still be refused.
    """
    _, summary, plan, _ = primary_outputs
    newest_complete = max(c["step"] for c in plan["checkpoints"] if c["complete"])
    assert newest_complete >= summary["first_poisoned_step"]
    assert newest_complete > summary["resume_step"]


def test_the_artifacts_are_serialised_exactly_as_the_contract_states(primary_outputs):
    """Read off the raw bytes, which _digest normalises away by parsing first.

    The contract fixes a two-space indent and a trailing newline for the summary,
    the resume plan and the rebuilt registry, and every check here decoded them
    before comparing -- so a run emitting the same values compactly matched every
    sealed digest while breaking the stated form.
    """
    out_dir = primary_outputs[0]
    spec = SPEC["outputs"]
    for name, section in (("summary.json", "summary"),
                          ("resume_plan.json", "resume_plan")):
        raw = (out_dir / name).read_text(encoding="utf-8")
        stated = spec[section]["serialisation"]
        assert "two-space indent" in stated and "trailing newline" in stated, stated
        assert raw.endswith("\n") and not raw.endswith("\n\n"), name
        assert raw == json.dumps(json.loads(raw), indent=2) + "\n", (
            f"{name} is not the contract's two-space indent")

    raw = (out_dir / "refetch_queue.jsonl").read_text(encoding="utf-8")
    assert "compact JSON object per line" in spec["refetch_queue"]["serialisation"]
    assert raw == "" or raw.endswith("\n")
    for line in raw.splitlines():
        assert line.strip(), "the queue carries a blank line"
        assert line == json.dumps(json.loads(line), separators=(",", ":")), (
            "a queue line is not compact JSON")

    # the rebuilt registry is a graded artifact too, and carries its own rule
    raw = REGISTRY_PATH.read_text(encoding="utf-8")
    stated = SPEC["reconciled_inputs"]["checkpoint_registry"]["serialisation"]
    assert "two-space indent" in stated and "trailing newline" in stated, stated
    assert raw.endswith("\n") and not raw.endswith("\n\n")
    assert raw == json.dumps(json.loads(raw), indent=2) + "\n", (
        "the rebuilt registry is not the contract's two-space indent")


def test_a_shard_that_is_both_poisoned_and_mismatched_reads_poisoned(primary_outputs):
    """#ML-6190: the epoch is the stronger finding, and it decides the label.

    Twenty-seven shards on the graded run are in a poisoned epoch AND carry a
    checksum that disagrees with the catalogue, so the precedence is not a corner
    case -- it settles the reason on every one of them. The rule was only implied
    by the order the reference happened to test in, so a solution labelling them
    checksum_mismatch failed the sealed digests with nothing to explain why.
    """
    _, _, plan, queue = primary_outputs
    catalog = _load_json(DATA / "shard_catalog.json")
    rows = catalog if isinstance(catalog, list) else catalog["shards"]
    poisoned = set(_load_json(DATA / "data_incident.json")["poisoned_epochs"])
    both = {s["shard_id"] for s in rows
            if s["epoch"] in poisoned
            and s["stored_checksum"] != s["expected_checksum"]}
    assert both, "no shard is both poisoned and mismatched, so this rule is unreachable"
    seen = {row["shard_id"]: row["reason"] for row in list(plan["refetch"]) + list(queue)}
    assert both <= set(seen), (
        "a shard that is both poisoned and mismatched appears in neither the plan "
        "nor the queue, so the rule it pins is not reachable here")
    for shard_id in sorted(both):
        assert seen[shard_id] == "poisoned_epoch", (
            f"{shard_id} is in a poisoned epoch and mismatched, so #ML-6190 "
            f"gives it poisoned_epoch, not {seen[shard_id]!r}")


def test_a_budget_near_the_int64_ceiling_still_defers_what_it_cannot_hold():
    """The byte budget is a mathematical bound, not a wrapping one.

    Admission was decided by `spent + bytes <= budget`, which overflows int64
    once the running total plus the next shard passes the type's ceiling: the sum
    wraps negative, the comparison passes, and a shard the budget cannot hold is
    planned. Comparing against `budget - spent` cannot wrap, since spent never
    exceeds budget. Two shards of five exabytes each sum past max-int64, so
    the second has to defer however large the budget looks.
    """
    huge = 5 * 10**18                       # 10^19 > max int64, so two cannot both fit
    catalog = [
        {"shard_id": "data-e01-p00", "epoch": 1, "bytes": huge,
         "expected_checksum": "a", "stored_checksum": "b"},
        {"shard_id": "data-e01-p01", "epoch": 1, "bytes": huge,
         "expected_checksum": "a", "stored_checksum": "b"},
    ]
    _, summary, plan, queue = _probe(
        _full(1000), poisoned=(), catalog=catalog, budget=2**63 - 1)
    assert [r["shard_id"] for r in plan["refetch"]] == ["data-e01-p00"], (
        "both shards were planned against a budget that cannot mathematically "
        "hold them, so the admission test wrapped")
    assert [r["shard_id"] for r in queue] == ["data-e01-p01"]
    assert summary["refetch_planned_bytes"] == huge



def test_the_refetch_counts_partition_what_was_needed(primary_outputs):
    """needed is planned plus deferred, and the planned bytes are the planned ones.

    The three counters are the only place the budget's effect is reported, and
    the contract now states that needed splits into exactly those two. Without
    this, a run could report a needed count that had nothing to do with the two
    it split into and still satisfy every other check.
    """
    _, summary, plan, queue = primary_outputs
    assert summary["refetch_needed_count"] == (
        summary["refetch_planned_count"] + summary["refetch_deferred_count"])
    # the plan carries what was admitted, the queue what was deferred
    assert summary["refetch_planned_count"] == len(plan["refetch"])
    assert summary["refetch_deferred_count"] == len(queue)
    assert summary["refetch_planned_bytes"] == sum(row["bytes"] for row in plan["refetch"])
    assert summary["refetch_planned_bytes"] <= summary["effective_refetch_budget"], (
        "the plan spent more than the resolved budget allows")
    # and the two sets are disjoint, so nothing is both planned and deferred
    assert not ({row["shard_id"] for row in plan["refetch"]}
                & {row["shard_id"] for row in queue})


def test_summary_counts_track_the_artifacts(primary_outputs):
    """The summary's own totals agree with the artifacts beside it."""
    _, summary, plan, queue = primary_outputs
    assert summary["entry_count"] == len(_load_json(REGISTRY_PATH))
    assert summary["checkpoint_count"] == len(plan["checkpoints"])
    assert summary["complete_checkpoint_count"] == sum(1 for c in plan["checkpoints"] if c["complete"])
    assert summary["admissible_checkpoint_count"] == sum(1 for c in plan["checkpoints"] if c["admissible"])
    assert summary["refetch_planned_count"] == len(plan["refetch"])
    assert summary["refetch_deferred_count"] == len(queue)
    assert summary["refetch_needed_count"] == len(plan["refetch"]) + len(queue)
    assert summary["refetch_planned_bytes"] == sum(r["bytes"] for r in plan["refetch"])


def test_plan_respects_the_budget_and_the_cap(primary_outputs):
    """The admitted set stays inside both policy limits."""
    _, summary, plan, _ = primary_outputs
    assert summary["refetch_planned_bytes"] <= summary["effective_refetch_budget"]
    assert len(plan["refetch"]) <= summary["effective_max_refetch"]


def test_both_refetch_reasons_occur(primary_outputs):
    """The graded run exercises every documented re-fetch reason."""
    _, _, plan, queue = primary_outputs
    assert {r["reason"] for r in plan["refetch"]} | {r["reason"] for r in queue} == REFETCH_REASONS


# --------------------------------------------------------------------------
# Each reversed rule, pinned on an instance where the drafts disagree
# --------------------------------------------------------------------------
def _entry(step, rank, kind, bytes_=1_000_000):
    return {"entry_id": f"CK-{step}-{rank}-{kind[0]}", "step": step, "rank": rank,
            "kind": kind, "shard_id": f"s{step}-r{rank}-{kind[0]}", "bytes": bytes_,
            "checksum": f"c{step}{rank}{kind[0]}", "written_seq": step * 10 + rank}


def _full(step, world=2):
    return [_entry(step, r, k) for r in range(world) for k in ("model", "optimizer")]


def _probe(entries, *, world=2, poisoned=(5,), steps_per_epoch=1000,
           catalog=None, budget=10**15, max_refetch=1000, policy=None):
    """Run the submitted planner over a crafted world and return its artifacts.

    `policy` overrides the staged policy outright, which is how the baseline
    fallback is exercised: every other caller writes all three fields, so an
    omitted one was never tested.
    """
    names = ("resume_policy.json", "data_incident.json", "shard_catalog.json")
    saved = {n: (DATA / n).read_text(encoding="utf-8") for n in names}
    staged = _CWORK / f"probe-{next(_run_ctr)}.json"
    try:
        _write_json(DATA / "resume_policy.json", policy if policy is not None else {"default": {
            "world_size": world, "refetch_budget_bytes": budget,
            "max_refetch_shards": max_refetch}})
        _write_json(DATA / "data_incident.json", {
            "poisoned_epochs": list(poisoned), "steps_per_epoch": steps_per_epoch})
        _write_json(DATA / "shard_catalog.json", catalog if catalog is not None else [])
        _write_json(staged, entries)
        os.chmod(staged, 0o644)
        return _run_pipeline(input_path=staged)
    finally:
        for n, text in saved.items():
            (DATA / n).write_text(text, encoding="utf-8")


def test_a_repeated_registry_row_counts_again_toward_shard_count():
    """The contract counts shard_count in REGISTRY ENTRIES, not distinct shards.

    Every registry the suite stages lists each (rank, kind) once, so counting the
    distinct pairs and counting the rows gave the same number and nothing could
    tell them apart. total_bytes has always summed the rows, so a registry that
    lists one shard twice is where the two readings part company: four rows over
    three distinct pairs, and the bytes of both copies.
    """
    registry = [
        {"entry_id": "e-1", "step": 1000, "rank": 0, "kind": "model",
         "shard_id": "sh-0", "bytes": 10, "checksum": "c0", "written_seq": 1},
        {"entry_id": "e-2", "step": 1000, "rank": 0, "kind": "optimizer",
         "shard_id": "sh-1", "bytes": 20, "checksum": "c1", "written_seq": 2},
        {"entry_id": "e-3", "step": 1000, "rank": 1, "kind": "model",
         "shard_id": "sh-2", "bytes": 30, "checksum": "c2", "written_seq": 3},
        # the same shard listed a second time: another row, another entry_id
        {"entry_id": "e-4", "step": 1000, "rank": 1, "kind": "model",
         "shard_id": "sh-2", "bytes": 30, "checksum": "c2", "written_seq": 4},
    ]
    _, summary, plan, _ = _probe(registry, world=2, poisoned=())
    row = next(c for c in plan["checkpoints"] if c["step"] == 1000)
    assert row["shard_count"] == 4, (
        "shard_count collapsed the repeated row to three, though the contract "
        "counts the registry entries the step carries and total_bytes already "
        "counts both copies")
    assert row["total_bytes"] == 90, row["total_bytes"]
    assert row["rank_count"] == 2, row["rank_count"]
    # the repeat adds nothing to completeness: rank 1 still holds no optimizer
    assert row["complete"] is False
    assert summary["entry_count"] == 4


def _four_rank_pair():
    """Two ranks, both kinds, at one step -- complete under a world size of two."""
    return [
        {"entry_id": "e-1", "step": 1000, "rank": 0, "kind": "model",
         "shard_id": "sh-0", "bytes": 10, "checksum": "c0", "written_seq": 1},
        {"entry_id": "e-2", "step": 1000, "rank": 0, "kind": "optimizer",
         "shard_id": "sh-1", "bytes": 10, "checksum": "c1", "written_seq": 2},
        {"entry_id": "e-3", "step": 1000, "rank": 1, "kind": "model",
         "shard_id": "sh-2", "bytes": 10, "checksum": "c2", "written_seq": 3},
        {"entry_id": "e-4", "step": 1000, "rank": 1, "kind": "optimizer",
         "shard_id": "sh-3", "bytes": 10, "checksum": "c3", "written_seq": 4},
    ]


def test_each_policy_field_falls_back_on_its_own():
    """#ML-6210 names a baseline per field, and each is exercised alone.

    Dropping world_size was the only case here, and every other run supplied
    both limits, so a planner that fell back for world_size and read a missing
    refetch_budget_bytes or max_refetch_shards as Go's zero passed everything:
    nothing ever handed it a policy without them. Each field is left out in turn
    below, and each case checks the effective value AND the plan that value
    produced, since an echoed number proves nothing on its own.
    """
    catalog = [{"shard_id": f"data-e01-p{i:02d}", "epoch": 1, "bytes": 1000,
                "expected_checksum": "a", "stored_checksum": "b"} for i in range(3)]
    full = {"world_size": 2, "refetch_budget_bytes": 35_000_000_000,
            "max_refetch_shards": 120}

    # refetch_budget_bytes omitted: the baseline of 35 GB admits all three
    # shards, where a zero budget would admit none of them
    sparse = {"default": {k: v for k, v in full.items()
                          if k != "refetch_budget_bytes"}}
    _, summary, plan, queue = _probe(_four_rank_pair(), policy=sparse,
                                     poisoned=(), catalog=catalog)
    assert summary["effective_refetch_budget"] == 35_000_000_000, summary
    assert summary["effective_world_size"] == 2
    assert summary["effective_max_refetch"] == 120
    assert [r["shard_id"] for r in plan["refetch"]] == [
        c["shard_id"] for c in catalog], (
        "an omitted refetch_budget_bytes admitted no shard, so it fell back to "
        "nought rather than to the governed 35000000000")
    assert queue == []
    assert summary["refetch_planned_count"] == 3

    # max_refetch_shards omitted: the baseline of 120 admits all three, where a
    # zero cap would admit none
    sparse = {"default": {k: v for k, v in full.items()
                          if k != "max_refetch_shards"}}
    _, summary, plan, queue = _probe(_four_rank_pair(), policy=sparse,
                                     poisoned=(), catalog=catalog)
    assert summary["effective_max_refetch"] == 120, summary
    assert summary["effective_world_size"] == 2
    assert summary["effective_refetch_budget"] == 35_000_000_000
    assert [r["shard_id"] for r in plan["refetch"]] == [
        c["shard_id"] for c in catalog], (
        "an omitted max_refetch_shards admitted no shard, so it fell back to "
        "nought rather than to the governed 120")
    assert queue == []
    assert summary["refetch_planned_count"] == 3

    # and the whole policy omitted: all three baselines at once. A world size of
    # 16 is not met by two ranks, so nothing is complete and the resume point
    # stays at -1 while the shards are still admitted under the other two.
    _, summary, plan, queue = _probe(_four_rank_pair(), policy={"default": {}},
                                     poisoned=(), catalog=catalog)
    assert summary["effective_world_size"] == 16
    assert summary["effective_refetch_budget"] == 35_000_000_000
    assert summary["effective_max_refetch"] == 120
    assert summary["complete_checkpoint_count"] == 0
    assert summary["resume_step"] == -1
    assert len(plan["refetch"]) == 3 and queue == []


def test_a_policy_that_omits_a_field_keeps_the_governed_baseline():
    """#ML-6210 states the baselines a field the policy file omits falls back to.

    Every policy the suite stages writes all three fields, so the fallback was
    never exercised and a planner that ignored it passed. Dropping world_size
    leaves the baseline of 16, which a two-rank checkpoint does not satisfy, so
    nothing is complete and the resume point stays at -1.
    """
    sparse = {"default": {"refetch_budget_bytes": 35000000000, "max_refetch_shards": 120}}
    registry = [
        {"entry_id": "e-1", "step": 1000, "rank": 0, "kind": "model",
         "shard_id": "sh-0", "bytes": 10, "checksum": "c0", "written_seq": 1},
        {"entry_id": "e-2", "step": 1000, "rank": 0, "kind": "optimizer",
         "shard_id": "sh-1", "bytes": 10, "checksum": "c1", "written_seq": 2},
        {"entry_id": "e-3", "step": 1000, "rank": 1, "kind": "model",
         "shard_id": "sh-2", "bytes": 10, "checksum": "c2", "written_seq": 3},
        {"entry_id": "e-4", "step": 1000, "rank": 1, "kind": "optimizer",
         "shard_id": "sh-3", "bytes": 10, "checksum": "c3", "written_seq": 4},
    ]
    _, summary, _plan, _queue = _probe(registry, policy=sparse, poisoned=())
    assert summary["effective_world_size"] == 16, (
        "the omitted world_size did not fall back to the governed baseline")
    assert summary["complete_checkpoint_count"] == 0
    assert summary["resume_step"] == -1


def test_every_complete_checkpoint_past_the_incident_leaves_no_resume_point():
    """-1 is not only the no-complete-checkpoint case.

    The contract has resume_step read -1 whenever nothing is admissible, and
    complete checkpoints that all sit at or after the first poisoned step are
    exactly that: they exist, they are complete, and none of them may be resumed
    from, so the run starts over. A planner patched in two passes -- take the
    highest complete step, then walk back below the first poisoned step when an
    incident names one -- keeps the first pass's answer here, because the
    walk-back finds nothing and leaves what was already set. Every other world
    in this suite has a clean checkpoint underneath to fall back to, so that
    mistake survived them all.
    """
    entries = _full(5000) + _full(6000)
    _, summary, plan, _ = _probe(entries, poisoned=(5,), steps_per_epoch=1000)
    assert summary["first_poisoned_step"] == 5000
    assert summary["complete_checkpoint_count"] == 2, (
        "the probe has no complete checkpoint, so it cannot separate the two "
        "readings of -1")
    assert summary["admissible_checkpoint_count"] == 0
    assert summary["resume_step"] == -1, (
        f"resume_step is {summary['resume_step']}; both complete checkpoints sit "
        "at or after the first poisoned step, so none is admissible and the run "
        "has no resume point to return")
    assert plan["resume_step"] == -1
    assert [c["step"] for c in plan["checkpoints"]] == [5000, 6000]
    assert all(c["complete"] is True for c in plan["checkpoints"])
    assert all(c["admissible"] is False for c in plan["checkpoints"])

    # and the same world with the incident moved later does have a resume point,
    # so the -1 above is the rule biting rather than the probe being empty
    _, later, _, _ = _probe(entries, poisoned=(7,), steps_per_epoch=1000)
    assert later["resume_step"] == 6000


def test_a_rank_missing_its_optimizer_shard_leaves_the_checkpoint_incomplete():
    """Every rank needs both shards, not the model alone.

    Rank 1 wrote its model but never its optimizer state, so step 2000 is
    incomplete and the run falls back to step 1000.
    """
    entries = _full(1000) + [_entry(2000, 0, "model"), _entry(2000, 0, "optimizer"),
                             _entry(2000, 1, "model")]
    _, summary, plan, _ = _probe(entries)
    by_step = {c["step"]: c for c in plan["checkpoints"]}
    assert by_step[1000]["complete"] is True
    assert by_step[2000]["complete"] is False
    assert summary["resume_step"] == 1000


def test_resume_rolls_back_behind_the_first_poisoned_step():
    """A newer complete checkpoint past the incident is refused.

    Epoch 5 at a thousand steps an epoch puts the first poisoned step at 5000,
    so the complete checkpoint at 6000 cannot be resumed from and the run falls
    back to the complete one at 4000.
    """
    entries = _full(4000) + _full(6000)
    _, summary, plan, _ = _probe(entries, poisoned=(5,), steps_per_epoch=1000)
    by_step = {c["step"]: c for c in plan["checkpoints"]}
    assert by_step[6000]["complete"] is True and by_step[6000]["admissible"] is False
    assert summary["first_poisoned_step"] == 5000
    assert summary["resume_step"] == 4000


def test_a_poisoned_shard_is_refetched_even_when_its_checksum_agrees():
    """The adapter is not trusted, so a matching checksum does not excuse a shard."""
    catalog = [
        {"shard_id": "data-e05-p00", "epoch": 5, "bytes": 10,
         "expected_checksum": "same", "stored_checksum": "same"},
        {"shard_id": "data-e01-p00", "epoch": 1, "bytes": 10,
         "expected_checksum": "same", "stored_checksum": "same"},
    ]
    _, summary, plan, _ = _probe(_full(1000), poisoned=(5,), catalog=catalog)
    assert summary["refetch_needed_count"] == 1
    assert [(r["shard_id"], r["reason"]) for r in plan["refetch"]] == [
        ("data-e05-p00", "poisoned_epoch")]


def test_refetch_order_is_by_epoch_not_by_size():
    """The oldest data comes back first, however small the shard.

    The epoch-1 shard is a tenth the size of the epoch-9 one; ordering by size
    would put the larger first.
    """
    catalog = [
        {"shard_id": "data-e09-p00", "epoch": 9, "bytes": 900,
         "expected_checksum": "a", "stored_checksum": "b"},
        {"shard_id": "data-e01-p00", "epoch": 1, "bytes": 90,
         "expected_checksum": "a", "stored_checksum": "b"},
    ]
    _, _, plan, _ = _probe(_full(1000), poisoned=(), catalog=catalog)
    assert [r["shard_id"] for r in plan["refetch"]] == ["data-e01-p00", "data-e09-p00"]


def test_the_order_inside_one_epoch_follows_the_shard_id():
    """The second key of the order, which nothing here used to separate.

    Every other crafted catalogue lists its shards already ascending by id
    inside an epoch, so a run that sorted on the epoch alone -- a stable sort on
    one key, which keeps the file's own order underneath it -- came out looking
    right on all of them. This catalogue puts one epoch's shards in the file
    backwards, where the two readings disagree: taking the file order under a
    stable epoch sort gives p03, p01, p02, p00, and the order the contract names
    gives p00 through p03.
    """
    catalog = [
        {"shard_id": "data-e04-p03", "epoch": 4, "bytes": 10,
         "expected_checksum": "a", "stored_checksum": "b"},
        {"shard_id": "data-e04-p01", "epoch": 4, "bytes": 10,
         "expected_checksum": "a", "stored_checksum": "b"},
        {"shard_id": "data-e04-p02", "epoch": 4, "bytes": 10,
         "expected_checksum": "a", "stored_checksum": "b"},
        {"shard_id": "data-e04-p00", "epoch": 4, "bytes": 10,
         "expected_checksum": "a", "stored_checksum": "b"},
    ]
    expected = ["data-e04-p00", "data-e04-p01", "data-e04-p02", "data-e04-p03"]
    _, _, plan, _ = _probe(_full(1000), poisoned=(), catalog=catalog)
    assert [r["shard_id"] for r in plan["refetch"]] == expected, (
        "the plan takes the shards in the catalogue's own order rather than by "
        f"shard id: {[r['shard_id'] for r in plan['refetch']]}")
    # Again with room for two, so the split falls between p01 and p02 and the
    # deferred queue carries the other half in the same order. Taking the file
    # order instead would admit p03 and p01 and defer p02 and p00.
    _, _, capped, queue = _probe(
        _full(1000), poisoned=(), catalog=catalog, max_refetch=2)
    assert [r["shard_id"] for r in capped["refetch"]] == expected[:2], (
        f"the cap admitted {[r['shard_id'] for r in capped['refetch']]}, not the "
        f"{expected[:2]} that come first by shard id")
    assert [r["shard_id"] for r in queue] == expected[2:], (
        "the deferred queue carries the shards in the catalogue's own order "
        f"rather than by shard id: {[r['shard_id'] for r in queue]}")


def test_the_budget_defers_the_tail_in_the_same_order():
    """Shards past the byte budget are deferred, keeping the epoch order."""
    catalog = [
        {"shard_id": f"data-e0{e}-p00", "epoch": e, "bytes": 100,
         "expected_checksum": "a", "stored_checksum": "b"} for e in (1, 2, 3)
    ]
    _, summary, plan, queue = _probe(_full(1000), poisoned=(), catalog=catalog, budget=250)
    assert [r["shard_id"] for r in plan["refetch"]] == ["data-e01-p00", "data-e02-p00"]
    assert [r["shard_id"] for r in queue] == ["data-e03-p00"]
    assert summary["refetch_planned_bytes"] == 200


def test_the_shard_cap_defers_the_tail_as_well():
    """The shard cap bites independently of the byte budget."""
    catalog = [
        {"shard_id": f"data-e0{e}-p00", "epoch": e, "bytes": 1,
         "expected_checksum": "a", "stored_checksum": "b"} for e in (1, 2, 3)
    ]
    _, _, plan, queue = _probe(_full(1000), poisoned=(), catalog=catalog, max_refetch=1)
    assert [r["shard_id"] for r in plan["refetch"]] == ["data-e01-p00"]
    assert [r["shard_id"] for r in queue] == ["data-e02-p00", "data-e03-p00"]


# --------------------------------------------------------------------------
# Contract, budget, determinism and isolation
# --------------------------------------------------------------------------
def test_policy_path_actually_influences_the_output():
    """The policy is resolved from its fixed path, not inlined as constants."""
    saved = (DATA / "resume_policy.json").read_text(encoding="utf-8")
    try:
        _write_json(DATA / "resume_policy.json", {"default": {
            "world_size": 4, "refetch_budget_bytes": 1_000_000, "max_refetch_shards": 7}})
        _, summary, _, _ = _run_pipeline()
        assert summary["effective_world_size"] == 4
        assert summary["effective_refetch_budget"] == 1_000_000
        assert summary["effective_max_refetch"] == 7
        assert summary != FIXTURE["primary"]["summary"]
    finally:
        (DATA / "resume_policy.json").write_text(saved, encoding="utf-8")


def test_incident_record_actually_influences_the_output():
    """The incident record is resolved from its fixed path too."""
    saved = (DATA / "data_incident.json").read_text(encoding="utf-8")
    try:
        _write_json(DATA / "data_incident.json",
                    {"poisoned_epochs": [2], "steps_per_epoch": 1500})
        _, summary, _, _ = _run_pipeline()
        assert summary["first_poisoned_step"] == 3000
        assert summary != FIXTURE["primary"]["summary"]
    finally:
        (DATA / "data_incident.json").write_text(saved, encoding="utf-8")


def test_run_is_idempotent(primary_outputs):
    """Re-running over the same registry reproduces the same artifacts."""
    _, summary, plan, queue = primary_outputs
    _, s2, p2, q2 = _run_pipeline()
    assert s2 == summary and _digest(p2) == _digest(plan) and _digest(q2) == _digest(queue)


def test_no_argument_run_writes_to_the_documented_defaults(primary_outputs):
    """With no flags at all the program reads and writes its documented defaults.

    The previous form still passed --output-dir, so it only exercised the --input
    default; a changed default output directory went unnoticed.
    """
    binary = _build(WORKFLOW_PATH)
    _publish_inputs()
    # /app is root-owned, so the run cannot replace this directory -- only empty
    # it. The directory is shared state, so it is restored in the finally below.
    default_out = Path("/app/output")
    default_out.mkdir(parents=True, exist_ok=True)
    before_mode = default_out.stat().st_mode & 0o777
    for stale in sorted(default_out.iterdir()):
        stale.unlink() if stale.is_file() or stale.is_symlink() else shutil.rmtree(stale)
    os.chmod(default_out, 0o777)
    # something for the run to clear. resume_contract.json states that the output
    # directory carries exactly the three named files, so a stale artifact left
    # by an earlier run must not survive into this one.
    (default_out / "left_behind.json").write_text("{}\n", encoding="utf-8")
    os.chmod(default_out / "left_behind.json", 0o666)
    (default_out / "scratch").mkdir()
    os.chmod(default_out / "scratch", 0o777)
    try:
        result = _run_agent([binary], cwd=_candidate_dir())
        assert result.returncode == 0, (
            f"the no-argument run exited {result.returncode}\n"
            f"stdout: {result.stdout[-2000:]}\nstderr: {result.stderr[-2000:]}")
        assert sorted(q.name for q in default_out.iterdir()) == [
            "refetch_queue.jsonl", "resume_plan.json", "summary.json"], (
            "the run did not clear what an earlier run left in the output "
            "directory, which the contract requires to carry exactly three files")
        _, summary, doc, queue = primary_outputs
        assert _load_json(default_out / "summary.json") == summary
        assert _digest(_load_json(default_out / "resume_plan.json")) == _digest(doc)
        assert _digest(_load_jsonl(default_out / "refetch_queue.jsonl")) == _digest(queue)
    finally:
        for stale in sorted(default_out.iterdir()):
            stale.unlink() if stale.is_file() or stale.is_symlink() else shutil.rmtree(stale)
        os.chmod(default_out, before_mode)



def test_the_budget_is_enforced_by_killing_an_overrunning_run(primary_outputs):
    """The budget is enforced, and not by timing the grading machine.

    Every candidate run is executed with the contract's published budget as its
    hard timeout, so a run that overruns is killed and the suite fails. Nothing
    compares a measured elapsed time against a threshold.
    """
    assert HARD_TIMEOUT_SEC == int(RUNTIME_BUDGET_SEC)
    assert primary_outputs[1]["checkpoint_count"] > 0, "the graded run did not complete"



def test_runtime_budget_is_stated_in_the_contract():
    """The budget enforced above is the one the contract publishes."""
    assert int(SPEC["runtime_budget_seconds"]) == int(RUNTIME_BUDGET_SEC)


def test_submitted_program_runs_unprivileged_and_cannot_write_reward(tmp_path):
    """The graded program runs as nobody and cannot touch the reward path."""
    probe = tmp_path / "main.go"
    probe.write_text(
        'package main\n\nimport ("fmt"; "os")\n\n'
        'func main() {\n\tfmt.Println(os.Getuid())\n'
        '\terr := os.WriteFile("/logs/verifier/reward.txt", []byte("1"), 0o644)\n'
        '\tfmt.Println(err != nil)\n}\n', encoding="utf-8")
    binary = _build(probe)
    result = _run_agent([binary], cwd=_candidate_dir())
    assert result.returncode == 0, result.stderr
    parts = result.stdout.split()
    assert parts[0] == str(CANDIDATE_UID) and parts[1] == "true"


def test_a_candidate_that_leaves_the_process_group_does_not_survive_the_run():
    """A setsid escape is reaped, because the sweep is by owner and not by group.

    The probe forks a child, puts it in a session of its own and leaves it
    sleeping well past the run. Killing the process group alone would let it
    live into the next test, holding staged inputs or still writing where a
    later run reads.
    """
    probe_dir = Path("/probe-work")
    probe_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(probe_dir, 0o755)
    probe = probe_dir / "escape.py"
    probe.write_text(
        "import os, sys, time\n"
        "if os.fork() == 0:\n"
        "    os.setsid()\n"
        "    time.sleep(600)\n"
        "    sys.exit(0)\n"
        "print('spawned')\n",
        encoding="utf-8")
    os.chmod(probe, 0o644)
    _run_agent([sys.executable, str(probe)], cwd=probe_dir)
    assert not harness._pids_owned_by(harness.CANDIDATE_UID), (
        "a candidate process outlived its run by leaving its process group")


def test_the_strictest_setpriv_this_image_supports_is_the_one_in_use():
    """Capabilities are dropped as well as the uid, where setpriv allows it."""
    assert "--no-new-privs" in harness._SETPRIV
    assert f"--reuid={harness.CANDIDATE_UID}" in harness._SETPRIV
    probe = subprocess.run(
        ["setpriv", f"--reuid={harness.CANDIDATE_UID}", f"--regid={harness.CANDIDATE_UID}",
         "--clear-groups", "--no-new-privs", "--inh-caps=-all", "--bounding-set=-all",
         "/bin/true"],
        capture_output=True)
    if probe.returncode == 0:
        assert "--inh-caps=-all" in harness._SETPRIV, (
            "setpriv accepts the strict capability flags but the harness is not using them")
        assert "--bounding-set=-all" in harness._SETPRIV


def test_app_data_holds_exactly_the_files_it_held_before():
    """instruction.md: the registry is the one file under /app/data replaced.

    The six declared files were each pinned by their own digest, so the rule the
    digests enforced was "these six are unchanged" rather than the one the
    instruction states. A recovery step that copied the truncated registry to a
    .bak beside it, or left a staging file or a transcript behind, satisfied
    every digest here while leaving /app/data holding something the contract
    does not name.
    """
    present = sorted(q.name for q in DATA.iterdir())
    declared = sorted(q.name for q in DECLARED_DATA)
    assert present == declared, (
        "/app/data holds something other than the files it was given: "
        f"{sorted(set(present) ^ set(declared))}")
    for path in DATA.iterdir():
        assert path.is_file() and not path.is_symlink(), (
            f"{path} is not the ordinary file it was")


def test_the_planner_declares_no_option_beyond_the_two_it_documents():
    """instruction.md: the three fixed inputs are not selectable by a flag.

    The fixed-path rule was graded only in the positive direction -- change the
    catalogue in place and the plan moves -- which an implementation offering a
    --catalog of its own passes without difficulty, since no run here ever
    supplies one. A planner that declares only the two documented options
    refuses an unknown one instead, which is what the flag package does for it.
    """
    binary = _build(WORKFLOW_PATH)
    _publish_inputs()

    # The declared set itself, rather than four guesses at what it might be
    # called. Probing --catalog/--incident/--policy caught those three
    # spellings and nothing else, so a planner offering --catalog-path, or any
    # third option at all, cleared the rule it was meant to be held to. The
    # flag package prints every option it declares when it refuses -h, so the
    # set is read off the program rather than guessed at.
    work = _candidate_dir()
    usage = _run_agent([binary, "-h"], cwd=work)
    text = usage.stdout + usage.stderr
    declared = set(re.findall(r"^\s*-([A-Za-z0-9_.-]+)", text, re.MULTILINE))
    assert declared, (
        "the planner printed no usage for -h, so the options it declares "
        f"cannot be read off it: {text[-2000:]}")
    assert declared == {"input", "output-dir"}, (
        f"the planner declares {sorted(declared)}; the contract names "
        "--input and --output-dir and no other option")

    for option in ("--catalog", "--incident", "--policy", "--registry"):
        work = _candidate_dir()
        out_dir = work / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(out_dir, 0o777)
        elsewhere = work / "elsewhere.json"
        elsewhere.write_text("[]\n", encoding="utf-8")
        os.chmod(elsewhere, 0o644)
        result = _run_agent(
            [binary, option, str(elsewhere), "--output-dir", str(out_dir)], cwd=work)
        assert result.returncode != 0, (
            f"the planner accepted {option}, so an input the contract fixes at "
            "an absolute path can be pointed somewhere else after all")


def test_the_planner_hands_the_work_to_no_other_program():
    """instruction.md: the planner does its own work.

    Compiling one file at a time keeps a sibling SOURCE out of the build, and
    that was taken for the whole of the single-file constraint. It is not: a
    wrapper of a few lines can shell out to an interpreter and let a script
    beside it -- or one it carries as a string -- do the planning, and every
    behavioural assertion in this file would still pass. There is no way to
    start a process in Go that does not go through one of these, and the run
    with /app stripped below closes the same route from the other side.
    """
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    banned_imports = {"os/exec", "plugin", "C"}
    declared = set(_go_imports(source))
    assert not declared & banned_imports, (
        f"plan_resume.go imports {sorted(declared & banned_imports)}: the "
        "planner is meant to do the work itself rather than start another "
        "program, and cgo is not the standard library the build allows")
    payload = _go_source_payload(source)
    # Spelled against the name the FILE binds, not against the package name.
    # `import sc "syscall"` followed by `sc.Exec(...)` replaces the process with
    # an interpreter and writes the string "syscall.Exec" nowhere, so a scan for
    # that literal passed it straight through. The entry points are listed per
    # package and the local name is asked of Go's own parser.
    banned_entries = {
        "os": ("StartProcess",),
        "syscall": ("Exec", "ForkExec", "StartProcess", "Syscall", "RawSyscall",
                    "Syscall6", "RawSyscall6", "Syscall9", "Syscall12",
                    "Syscall15", "RawSyscall9", "SYS_EXECVE", "SYS_EXECVEAT",
                    "SYS_FORK", "SYS_VFORK", "SYS_CLONE"),
    }
    local = _go_import_names(source)
    for path, entries in banned_entries.items():
        name = local.get(path)
        if name is None:
            continue
        assert name != ".", (
            f"plan_resume.go dot-imports {path}, which puts its process-starting "
            "entry points in scope under bare names")
        for entry in entries:
            assert f"{name}.{entry}" not in payload, (
                f"plan_resume.go reaches {path}.{entry} (written {name}.{entry}), "
                "which starts another program or replaces this one")
    # a linker directive lives in a comment, where neither scan above looks
    assert "go:linkname" not in source, (
        "plan_resume.go links to an unexported entry point")
    third_party = sorted({path for path in declared if "." in path.split("/")[0]})
    assert not third_party, f"third-party import(s): {third_party}"


def test_the_graded_run_needs_nothing_under_app_but_the_inputs_and_its_own_source(
        primary_outputs):
    """The single-file rule graded as behaviour rather than as build shape.

    Everything under /app that is neither a declared input nor the planner is
    moved aside, and the plan has to come out the same without it. A submission
    whose Go file is a wrapper over a helper it left beside itself passes every
    other test in this file and fails here.
    """
    stash, moved = _hide_everything_else_under_app()
    try:
        _, summary, plan, queue = _run_pipeline()
        assert summary == FIXTURE["primary"]["summary"], (
            "the plan changed once everything the submission left under /app "
            f"was taken away: {sorted(str(q) for q in moved)}")
        assert _digest(plan) == FIXTURE["primary"]["plan_digest"]
        assert _digest(queue) == FIXTURE["primary"]["queue_digest"]
    finally:
        _restore_everything_under_app(stash, moved)


def test_frozen_snapshot_preserved():
    """The migration's planner must still be on disk, unmodified."""
    assert ORIGINAL_WORKFLOW_PATH.exists()
    assert hashlib.sha256(ORIGINAL_WORKFLOW_PATH.read_bytes()).hexdigest() == \
        FIXTURE["broken_planner_sha256"]


def test_frozen_snapshot_is_wrong(primary_outputs):
    """The shipped planner does not already produce the governed plan."""
    _, summary, _, _ = primary_outputs
    _, broken, _, _ = _run_pipeline(script_path=ORIGINAL_WORKFLOW_PATH)
    assert broken != summary


def test_governance_log_present():
    """The run log the rules are reconstructed from is in the environment."""
    assert LOG_PATH.exists() and LOG_PATH.stat().st_size > 0


def test_shard_catalog_actually_influences_the_output():
    """The shard catalogue is resolved from its fixed path, not inlined."""
    path = DATA / "shard_catalog.json"
    saved = path.read_text(encoding="utf-8")
    try:
        catalog = _load_json(path)
        for shard in catalog:
            shard["stored_checksum"] = shard["expected_checksum"]
        _write_json(path, catalog)
        _, summary, _, _ = _run_pipeline()
        assert summary["refetch_needed_count"] < FIXTURE["primary"]["summary"]["refetch_needed_count"]
        assert summary != FIXTURE["primary"]["summary"]
    finally:
        path.write_text(saved, encoding="utf-8")


def test_shipped_contract_matches_the_golden_copy():
    """The output contract in the environment is unmodified.

    Field lists, container shapes and sort orders are golden metadata and are read
    from the verifier's own image; this proves the agent's copy still agrees with
    it, so the contract cannot be trimmed to weaken a schema check.
    """
    # bytes first: instruction.md names the contract among the files that come
    # back byte for byte unchanged, and a re-dump at a different indent or key
    # order satisfied the parsed comparison while breaking that promise
    assert hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest() == \
        hashlib.sha256(GOLDEN_CONTRACT_PATH.read_bytes()).hexdigest(), (
        "the shipped contract differs from the golden copy in its bytes")
    shipped = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert shipped == json.loads(GOLDEN_CONTRACT_PATH.read_text(encoding="utf-8"))


def test_an_amendment_past_two_to_the_fifty_third_keeps_every_digit():
    """A byte figure the contract admits, decoded through the wrong number type.

    resume_contract.json puts every byte figure anywhere in the signed 64-bit
    range. A journal value decoded into an untyped Go `any` arrives as float64,
    and a float64 carries 53 bits of mantissa, so 9007199254740993 comes back
    9007199254740992 -- off by one, silently, on a value the contract allows.
    The journal now carries such an amendment against CK-000002, and the
    recovered registry has to hold it digit for digit.
    """
    journal = _load_json(JOURNAL_PATH)
    big = [c for c in journal if c.get("value") == 9007199254740993]
    assert big, "the journal carries no amendment past 2^53, so this proves nothing"
    assert len(big) == 1, big
    change = big[0]
    assert change["kind"] == "amend" and change["field"] == "bytes"
    # the file itself holds the digits, not a rounded neighbour
    assert "9007199254740993" in JOURNAL_PATH.read_text(encoding="utf-8")

    recovered = {row["entry_id"]: row for row in _load_json(REGISTRY_PATH)}
    row = recovered.get(change["entry_id"])
    assert row is not None, f"{change['entry_id']} is not in the recovered registry"
    assert row["bytes"] == 9007199254740993, (
        f"{change['entry_id']} carries {row['bytes']}, not the 9007199254740993 the "
        "journal amended it to; the value went through a float on the way in")
    assert row["bytes"] != 9007199254740992, "the value was rounded to the nearest float64"


def test_the_admitted_refetch_set_is_a_prefix_of_the_order():
    """#ML-6194 admits a prefix and never steps over a shard to reach a smaller one.

    Every crafted world here used shards of one size, where the two readings of
    the rule agree. With sizes that vary, they part company: under a budget of
    2500 the first two shards fit, the third does not, and the fourth would.
    Skipping the third to pick up the fourth fills the budget better and is the
    reading the minute now rules out; the admitted set stops at the first shard
    that does not fit.
    """
    catalog = [
        {"shard_id": "data-e01-p00", "epoch": 1, "bytes": 1000,
         "expected_checksum": "a", "stored_checksum": "b"},
        {"shard_id": "data-e01-p01", "epoch": 1, "bytes": 1000,
         "expected_checksum": "a", "stored_checksum": "b"},
        {"shard_id": "data-e01-p02", "epoch": 1, "bytes": 900,
         "expected_checksum": "a", "stored_checksum": "b"},
        {"shard_id": "data-e01-p03", "epoch": 1, "bytes": 400,
         "expected_checksum": "a", "stored_checksum": "b"},
    ]
    _, summary, plan, queue = _probe(_four_rank_pair(), poisoned=(),
                                     catalog=catalog, budget=2500)
    assert [r["shard_id"] for r in plan["refetch"]] == [
        "data-e01-p00", "data-e01-p01"], (
        "the plan stepped over the shard that did not fit to admit a smaller one "
        "further down, which #ML-6194 rules out")
    assert [r["shard_id"] for r in queue] == ["data-e01-p02", "data-e01-p03"], (
        "the deferred queue is not the rest of the order, in order")
    assert summary["refetch_planned_bytes"] == 2000
    assert summary["refetch_planned_count"] == 2
    assert summary["refetch_deferred_count"] == 2
    # and the better-filling set really was available, so the case discriminates
    assert 1000 + 1000 + 400 <= 2500


def test_an_incident_naming_no_poisoned_epoch_admits_every_complete_checkpoint():
    """#ML-6186's edge: with nothing poisoned there is no step to fall before.

    Every world here named a poisoned epoch, so what an empty list means was
    settled only by the reference's own arithmetic. The minute now says it: no
    poisoned epoch leaves every complete checkpoint admissible, the resume point
    is the highest of them, and first_poisoned_step is reported as -1.
    """
    entries = _four_rank_pair() + [
        {"entry_id": "e-5", "step": 9000, "rank": 0, "kind": "model",
         "shard_id": "sh-4", "bytes": 10, "checksum": "c4", "written_seq": 5},
        {"entry_id": "e-6", "step": 9000, "rank": 0, "kind": "optimizer",
         "shard_id": "sh-5", "bytes": 10, "checksum": "c5", "written_seq": 6},
        {"entry_id": "e-7", "step": 9000, "rank": 1, "kind": "model",
         "shard_id": "sh-6", "bytes": 10, "checksum": "c6", "written_seq": 7},
        {"entry_id": "e-8", "step": 9000, "rank": 1, "kind": "optimizer",
         "shard_id": "sh-7", "bytes": 10, "checksum": "c7", "written_seq": 8},
    ]
    _, summary, plan, _ = _probe(entries, poisoned=())
    assert summary["first_poisoned_step"] == -1, summary
    assert summary["complete_checkpoint_count"] == 2
    assert summary["admissible_checkpoint_count"] == 2, (
        "a checkpoint was ruled inadmissible though no epoch is poisoned")
    assert summary["resume_step"] == 9000, (
        "the resume point is not the highest complete checkpoint")
    assert [row["admissible"] for row in plan["checkpoints"]] == [True, True]


def test_a_stale_entry_the_run_cannot_clear_is_reported_rather_than_ignored():
    """The contract's three-file output is not met, so the run must not claim it.

    Both the directory read and the removals had their errors dropped, so a
    stale subdirectory the run could not remove left the output carrying more
    than the three named files while the run still exited nought. Here the
    output directory is left writable but the stale subdirectory inside it is
    not, so its contents cannot be unlinked.
    """
    binary = _build(WORKFLOW_PATH)
    _publish_inputs()
    work = _candidate_dir()
    out_dir = work / "given-output"
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(out_dir, 0o777)
    stuck = out_dir / "stuck"
    stuck.mkdir()
    (stuck / "inner.json").write_text("{}\n", encoding="utf-8")
    # the directory holding it is read and executable but not writable, so the
    # entry inside it cannot be removed by the unprivileged run
    os.chmod(stuck / "inner.json", 0o444)
    os.chmod(stuck, 0o555)
    try:
        result = _run_agent([binary, "--output-dir", str(out_dir)], cwd=work)
        assert result.returncode != 0, (
            "the run could not clear the output directory and reported success "
            "anyway; the contract's three-file output was not met")
        assert (stuck / "inner.json").exists(), "the probe removed its own obstacle"
        # All three, not summary.json alone. Checking one name graded the write
        # ORDER rather than the rule: a run that wrote the plan and the queue
        # first and only then discovered it could not clear the directory left
        # two artifacts beside content it could not remove and still passed.
        left = sorted(q.name for q in out_dir.iterdir()
                      if q.name in ("summary.json", "resume_plan.json",
                                    "refetch_queue.jsonl"))
        assert not left, (
            f"the run wrote {left} beside content it could not clear, though a "
            "failed clearing writes no artifacts at all")
        # instruction.md has the run NAME the offending path on standard error.
        # Graded on the diagnostic as well as the status, because an exit code
        # alone leaves an operator with a failed run and nothing to act on, and
        # a run that exits non-zero silently is indistinguishable here from one
        # that crashed for some other reason entirely.
        assert str(stuck) in result.stderr or str(stuck / "inner.json") in result.stderr, (
            "the run exited non-zero but did not say what it could not clear; "
            f"stderr was {result.stderr[-2000:]!r}")
    finally:
        os.chmod(stuck, 0o777)
