"""Verifier tests for this task.

Every test below corresponds to something instruction.md states is graded.
Shared machinery lives in harness.py.
"""

import harness
from harness import *  # noqa: F401,F403

@pytest.fixture(scope="session")
def primary_outputs():
    return _run_pipeline()


@pytest.fixture(scope="session")
def alternate_outputs():
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
    default_out = Path("/app/output")
    shutil.rmtree(default_out, ignore_errors=True)
    default_out.mkdir(parents=True, exist_ok=True)
    os.chmod(default_out, 0o777)
    result = _run_agent([binary], cwd=_candidate_dir())
    assert result.returncode == 0, result.stderr
    assert sorted(q.name for q in default_out.iterdir()) == ['refetch_queue.jsonl', 'resume_plan.json', 'summary.json']
    _, summary, doc, queue = primary_outputs
    assert _load_json(default_out / "summary.json") == summary
    assert _digest(_load_json(default_out / "resume_plan.json")) == _digest(doc)
    assert _digest(_load_jsonl(default_out / "refetch_queue.jsonl")) == _digest(queue)


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
    shipped = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert shipped == json.loads(GOLDEN_CONTRACT_PATH.read_text(encoding="utf-8"))

