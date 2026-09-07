# Planning governance log

How the resume planner is *meant* to behave -- the recovery of the truncated checkpoint registry, what makes a checkpoint complete, which checkpoint the run may resume from after the data incident, and which shards come back and in what order -- was settled incrementally by the training governance board, and those decisions live in the review entries below, not in any single summary. Several stages deliberately depart from the intuitive reading, and which ones they are is settled in the entries below rather than here. The February draft proposals were revisited during the 2026-05 run review and several were reversed; where a draft or interim conflicts with a later decision, the later dated decision governs. `/app/docs/resume_contract.json` is the output contract only.

- 2026-02-04: The checkpoint service owner filed a routine observation. Gradient-norm logging was noisier than usual and attributed to the logging cadence. A second reviewer concurred.

> **Recovery draft proposal (2026-02-05 - #ML-6020)** Rosa: rebuild the truncated registry by concatenating the pre-migration snapshot with the migrator journal and keeping the last row seen for each entry; a reinstated entry is re-read from the snapshot *(Superseded -- reversed in the 2026-05 run review.)*

> **Recovery draft proposal (2026-02-12 - #ML-6026)** Anders: a checkpoint counts as complete once every rank has written its model shard; the optimizer shards are a convenience and need not all be present *(Superseded -- reversed in the 2026-05 run review.)*

> **Recovery draft proposal (2026-02-18 - #ML-6032)** Marek: restart from the newest complete checkpoint, since that is the furthest the run got *(Superseded -- reversed in the 2026-05 run review.)*

- 2026-02-09: The on-call trainer filed a routine observation. Checkpoint write latency spiked on one rank; traced to a slow object-store PUT, not the writer. Nothing here bears on planner behaviour.

- 2026-02-19: A shift handover raised and closed a routine observation. A tensorboard scalar was mislabelled in the dashboard and corrected at source. Noted and closed.

- 2026-02-27: The cluster operator logged a routine observation. Checkpoint write latency spiked on one rank; traced to a slow object-store PUT, not the writer. Nothing here bears on planner behaviour.

- 2026-02-21: The data-integrity owner recorded a routine observation. The dataloader's shard assignment was confirmed stable across the restart. Nothing here bears on planner behaviour.

- 2026-02-20: A platform engineer raised and closed a routine observation. A rank restarted after an NCCL timeout and rejoined at the next barrier. Referred to the dated decisions and closed.

- 2026-02-08: The checkpoint service owner carried forward a routine observation. Disk pressure on a staging host cleared after the retention sweep ran. Closed with no parameter change.

- 2026-02-17: The storage team carried forward a routine observation. One shard upload retried once and succeeded on the second attempt.

- 2026-02-12: The observability team noted a routine observation. One rank's optimizer shard landed a few seconds after its model shard, as expected. Recorded without further action.

- 2026-02-27: The data-integrity owner recorded a routine observation. One node reported an ECC-corrected memory event with no run impact. A second reviewer concurred.

- 2026-02-27: A shift handover raised and closed a routine observation. The dataloader's shard assignment was confirmed stable across the restart. Closed with no parameter change.

- 2026-02-15: The checkpoint service owner spot-checked a routine observation. One shard upload retried once and succeeded on the second attempt. The desk confirmed no run impact.

- 2026-02-04: The observability team signed off a routine observation. Gradient-norm logging was noisier than usual and attributed to the logging cadence. Filed for the record.

- 2026-02-21: The checkpoint service owner filed a routine observation. An alert fired on checkpoint age and cleared once the write completed. Recorded without further action.

- 2026-02-23: A weekly training review filed a routine observation. The registry export matched the object store's listing on the first pass. No follow-up was requested.

- 2026-02-23: A weekly training review raised and closed a routine observation. A run was paused briefly while the scheduler rebalanced across the pool.

- 2026-02-25: The data-integrity owner signed off a routine observation. The loss curve showed a brief plateau that recovered without intervention.

- 2026-02-11: The cluster operator raised and closed a routine observation. The registry export matched the object store's listing on the first pass. Filed for the record.

- 2026-02-23: A platform engineer carried forward a routine observation. One shard upload retried once and succeeded on the second attempt. A second reviewer concurred.

- 2026-02-16: An SRE on shift signed off a routine observation. An alert fired on checkpoint age and cleared once the write completed. Referred to the dated decisions and closed.

- 2026-02-12: A platform engineer logged a routine observation. The nightly integrity scan over the shard catalogue completed clean. A second reviewer concurred.

- 2026-02-17: A weekly training review signed off a routine observation. Checkpoint write latency spiked on one rank; traced to a slow object-store PUT, not the writer. Recorded without further action.

- 2026-02-08: The checkpoint service owner opened a query on a routine observation. The nightly integrity scan over the shard catalogue completed clean.

- 2026-02-03: The scheduling desk minuted a routine observation. An operator asked whether an epoch boundary had been crossed; it had, at the prior step. No dissent was recorded.

- 2026-03-04: The data-integrity owner spot-checked a routine observation. GPU memory headroom was reported comfortable at the current micro-batch size. Logged for trend purposes only.

> **Interim decision (2026-03-04 - #ML-6044)** Priya: the re-fetch queue is taken largest shard first, so the biggest gaps close soonest *(Revised -- see the 2026-05 run review.)*

- 2026-03-23: A run reviewer logged a routine observation. The dataloader's shard assignment was confirmed stable across the restart. Recorded without further action.

- 2026-03-03: The on-call trainer carried forward a routine observation. Two nodes were drained for a driver update and returned before the next epoch. Filed for the record.

- 2026-03-09: The storage team noted a routine observation. Two nodes were drained for a driver update and returned before the next epoch. Recorded without further action.

- 2026-03-01: The observability team signed off a routine observation. GPU memory headroom was reported comfortable at the current micro-batch size. No dissent was recorded.

- 2026-03-01: A platform engineer carried forward a routine observation. The loss curve showed a brief plateau that recovered without intervention.

- 2026-03-20: The on-call trainer filed a routine observation. The registry export matched the object store's listing on the first pass. Noted and closed.

- 2026-03-15: A run reviewer carried forward a routine observation. A stale mount on one node was remounted before the next checkpoint window. The thread was archived after review.

- 2026-03-08: The scheduling desk recorded a routine observation. Disk pressure on a staging host cleared after the retention sweep ran. Recorded without further action.

- 2026-03-20: The data-integrity owner signed off a routine observation. Disk pressure on a staging host cleared after the retention sweep ran. Referred to the dated decisions and closed.

- 2026-03-05: The scheduling desk filed a routine observation. The epoch counter and the step counter were reconciled after the resume. The desk confirmed no run impact.

- 2026-03-03: The scheduling desk reviewed a routine observation. An alert fired on checkpoint age and cleared once the write completed.

- 2026-03-14: The scheduling desk reviewed a routine observation. One shard upload retried once and succeeded on the second attempt. No dissent was recorded.

- 2026-03-17: An SRE on shift carried forward a routine observation. A stale mount on one node was remounted before the next checkpoint window. Filed for the record.

- 2026-03-10: A platform engineer recorded a routine observation. A tensorboard scalar was mislabelled in the dashboard and corrected at source. The desk confirmed no run impact.

- 2026-03-18: The checkpoint service owner minuted a routine observation. An operator asked whether an epoch boundary had been crossed; it had, at the prior step. No action was carried forward.

- 2026-03-21: A run reviewer raised and closed a routine observation. An operator asked whether an epoch boundary had been crossed; it had, at the prior step.

- 2026-03-12: The checkpoint service owner logged a routine observation. GPU memory headroom was reported comfortable at the current micro-batch size. Nothing here bears on planner behaviour.

- 2026-03-01: The data-integrity owner reviewed a routine observation. Disk pressure on a staging host cleared after the retention sweep ran. The desk confirmed no run impact.

- 2026-03-13: The checkpoint service owner minuted a routine observation. Two nodes were drained for a driver update and returned before the next epoch. Recorded without further action.

- 2026-03-14: A platform engineer logged a routine observation. Disk pressure on a staging host cleared after the retention sweep ran. No action was carried forward.

- 2026-03-22: A platform engineer minuted a routine observation. A stale mount on one node was remounted before the next checkpoint window.

- 2026-03-13: A weekly training review logged a routine observation. The nightly integrity scan over the shard catalogue completed clean.

- 2026-03-16: The data-integrity owner recorded a routine observation. One node reported an ECC-corrected memory event with no run impact. Noted and closed.

- 2026-03-16: An SRE on shift noted a routine observation. The epoch counter and the step counter were reconciled after the resume. The thread was archived after review.

- 2026-04-02: A run reviewer filed a routine observation. Throughput dipped for a step while the dataloader refilled its prefetch buffer. Referred to the dated decisions and closed.

- 2026-04-10: The checkpoint service owner carried forward a routine observation. Throughput dipped for a step while the dataloader refilled its prefetch buffer. The desk confirmed no run impact.

- 2026-04-16: A run reviewer noted a routine observation. The registry export matched the object store's listing on the first pass. Nothing here bears on planner behaviour.

- 2026-04-19: A platform engineer opened a query on a routine observation. Two nodes were drained for a driver update and returned before the next epoch.

- 2026-04-06: The storage team opened a query on a routine observation. The dataloader's shard assignment was confirmed stable across the restart.

- 2026-04-10: A shift handover carried forward a routine observation. One shard upload retried once and succeeded on the second attempt. Recorded without further action.

- 2026-04-06: The observability team spot-checked a routine observation. The nightly integrity scan over the shard catalogue completed clean.

- 2026-04-27: The scheduling desk filed a routine observation. One shard upload retried once and succeeded on the second attempt. Referred to the dated decisions and closed.

- 2026-04-13: The observability team logged a routine observation. The epoch counter and the step counter were reconciled after the resume. No action was carried forward.

- 2026-04-07: The scheduling desk logged a routine observation. An operator asked whether an epoch boundary had been crossed; it had, at the prior step. Closed with no parameter change.

- 2026-04-03: A platform engineer minuted a routine observation. The loss curve showed a brief plateau that recovered without intervention. Logged for trend purposes only.

- 2026-04-01: The scheduling desk signed off a routine observation. Checkpoint write latency spiked on one rank; traced to a slow object-store PUT, not the writer. Filed for the record.

- 2026-04-11: A run reviewer filed a routine observation. A stale mount on one node was remounted before the next checkpoint window.

- 2026-04-09: A run reviewer filed a routine observation. Gradient-norm logging was noisier than usual and attributed to the logging cadence. Filed for the record.

- 2026-04-25: A run reviewer minuted a routine observation. An alert fired on checkpoint age and cleared once the write completed.

- 2026-04-01: The checkpoint service owner signed off a routine observation. The epoch counter and the step counter were reconciled after the resume.

- 2026-04-02: The observability team logged a routine observation. The dataloader's shard assignment was confirmed stable across the restart.

- 2026-04-10: An SRE on shift filed a routine observation. The nightly integrity scan over the shard catalogue completed clean. The desk confirmed no run impact.

- 2026-04-23: The storage team opened a query on a routine observation. The registry export matched the object store's listing on the first pass.

- 2026-04-12: The storage team noted a routine observation. A tensorboard scalar was mislabelled in the dashboard and corrected at source. The thread was archived after review.

- 2026-04-01: A shift handover opened a query on a routine observation. Disk pressure on a staging host cleared after the retention sweep ran. No follow-up was requested.

- 2026-04-19: A shift handover recorded a routine observation. A rank restarted after an NCCL timeout and rejoined at the next barrier. Closed with no parameter change.

- 2026-04-07: A shift handover recorded a routine observation. Gradient-norm logging was noisier than usual and attributed to the logging cadence. A second reviewer concurred.

- 2026-05-18: The cluster operator recorded a routine observation. The nightly integrity scan over the shard catalogue completed clean.

> **Governance decision (2026-05-06 - #ML-6150)** Priya: Input paths, final. The shard catalogue, the data incident record and the resume policy are always read from their fixed absolute paths under /app/data; `--input` selects the checkpoint registry only. Both `--input` and `--output-dir` keep their documented defaults.

> **Governance decision (2026-05-08 - #ML-6170)** Yusuf: Registry recovery, final (supersedes #ML-6020). Start from the pre-migration snapshot and replay the migrator journal in ascending `seq`, never in file order. An `amend` overwrites the named field in place. An `invalidate` takes the entry out of the registry, but the migrator keeps it as it stood at that moment. A `reinstate` returns an invalidated entry EXACTLY as it then stood: an amendment posted before the invalidation survives, and one posted while the entry was out is lost. A change naming an entry the snapshot never carried is ignored, and a reinstatement of an entry that was never invalidated does nothing.

> **Governance decision (2026-05-09 - #ML-6174)** Yusuf: Recovered shape, final. The rebuilt registry is a JSON array ascending by step, then rank, then kind, then entry id. Each row carries the eight declared fields -- the migrator's bookkeeping (`seq`, `kind`, `posted_by`) never survives the replay.

> **Governance decision (2026-05-13 - #ML-6182)** Lena: Checkpoint completeness, final (supersedes #ML-6026; deviates from the model-only reading). A checkpoint is complete only where every rank of the configured world holds BOTH its model shard and its optimizer shard. A rank missing either one leaves the whole checkpoint unusable, however many other shards landed for that step.

> **Governance decision (2026-05-16 - #ML-6186)** Marek: Resume point, final (supersedes #ML-6032; deviates from the newest-complete reading). The run trained through the poisoned epochs, so a checkpoint written at or after the first step of the earliest poisoned epoch has already learned from the corrupt shards and cannot be resumed from, complete or not. The resume point is the HIGHEST complete checkpoint whose step falls strictly before that first poisoned step. An epoch's first step is its epoch number multiplied by the incident record's steps_per_epoch. Where the incident record names NO poisoned epoch there is no such step and nothing to fall before: every complete checkpoint is admissible, the resume point is simply the highest of them, and first_poisoned_step is reported as -1. The same -1 stands for the resume point where no checkpoint is complete at all.

> **Governance decision (2026-05-20 - #ML-6190)** Marek: Re-fetch set, final. A data shard is re-fetched where its stored checksum disagrees with the catalogue's expected checksum. Every shard belonging to a poisoned epoch is re-fetched as well, whatever its checksum says, because the adapter that wrote them is not trusted. A shard to which both apply carries `poisoned_epoch` as its reason: the epoch is the stronger finding, and the checksum tells us nothing further once the writer itself is in doubt.

> **Governance decision (2026-05-24 - #ML-6194)** Priya: Re-fetch order, final (revises #ML-6044; deviates from the largest-first interim). The re-fetch set is taken in ascending epoch, then ascending shard id, so the oldest data the run will read again comes back first. Shards are admitted to the plan in that order until either the policy's refetch_budget_bytes would be exceeded or its max_refetch_shards is reached. The admitted set is a PREFIX of that order and nothing else: admission stops at the first shard that does not fit, and the plan does not step over it to pick up a smaller one further down. That shard and every shard behind it are deferred to the queue, keeping the same order. The board is explicit because the two readings differ on any run where a large shard sits ahead of a small one: filling the remaining room out of the tail would reorder the queue against this minute and admit a set the board never described.

> **Governance decision (2026-05-28 - #ML-6196)** Lena: Emission order, final. The plan lists every checkpoint ascending by step, whether complete or not, and its re-fetch list in the admitted order. The deferred queue keeps the same ascending epoch and shard id order.

- 2026-05-02: The checkpoint service owner minuted a routine observation. A stale mount on one node was remounted before the next checkpoint window. Recorded without further action.

- 2026-05-17: The checkpoint service owner minuted a routine observation. A run was paused briefly while the scheduler rebalanced across the pool. No dissent was recorded.

- 2026-05-13: The checkpoint service owner filed a routine observation. An operator asked whether an epoch boundary had been crossed; it had, at the prior step. Filed for the record.

- 2026-05-03: The cluster operator reviewed a routine observation. Throughput dipped for a step while the dataloader refilled its prefetch buffer. A second reviewer concurred.

- 2026-05-16: The scheduling desk spot-checked a routine observation. A stale mount on one node was remounted before the next checkpoint window.

- 2026-05-23: A weekly training review noted a routine observation. Checkpoint write latency spiked on one rank; traced to a slow object-store PUT, not the writer. No dissent was recorded.

- 2026-05-05: The checkpoint service owner minuted a routine observation. One rank's optimizer shard landed a few seconds after its model shard, as expected.

- 2026-05-05: A run reviewer spot-checked a routine observation. The registry export matched the object store's listing on the first pass. No dissent was recorded.

- 2026-05-19: The data-integrity owner reviewed a routine observation. One node reported an ECC-corrected memory event with no run impact. A second reviewer concurred.

- 2026-05-23: An SRE on shift filed a routine observation. The registry export matched the object store's listing on the first pass.

- 2026-05-03: The data-integrity owner minuted a routine observation. A run was paused briefly while the scheduler rebalanced across the pool. A second reviewer concurred.

- 2026-05-12: The scheduling desk filed a routine observation. An alert fired on checkpoint age and cleared once the write completed. Nothing here bears on planner behaviour.

- 2026-05-19: The cluster operator logged a routine observation. One shard upload retried once and succeeded on the second attempt. Referred to the dated decisions and closed.

- 2026-05-10: An SRE on shift logged a routine observation. Two nodes were drained for a driver update and returned before the next epoch. Referred to the dated decisions and closed.

- 2026-05-07: A platform engineer carried forward a routine observation. Gradient-norm logging was noisier than usual and attributed to the logging cadence. A second reviewer concurred.

- 2026-05-02: A shift handover spot-checked a routine observation. A tensorboard scalar was mislabelled in the dashboard and corrected at source.

- 2026-05-22: A platform engineer recorded a routine observation. A stale mount on one node was remounted before the next checkpoint window. No dissent was recorded.

- 2026-05-23: The observability team recorded a routine observation. The dataloader's shard assignment was confirmed stable across the restart. Closed with no parameter change.

- 2026-05-09: An SRE on shift filed a routine observation. Gradient-norm logging was noisier than usual and attributed to the logging cadence.

- 2026-05-16: A platform engineer carried forward a routine observation. Two nodes were drained for a driver update and returned before the next epoch.

- 2026-06-03: The checkpoint service owner opened a query on a routine observation. Checkpoint write latency spiked on one rank; traced to a slow object-store PUT, not the writer. Closed with no parameter change.

> **Governance decision (2026-06-02 - #ML-6210)** Priya: Resume policy baseline, read from /app/data/resume_policy.json at that fixed absolute path. Any field the policy file omits keeps its baseline: world_size = 16; refetch_budget_bytes = 35000000000; max_refetch_shards = 120.

- 2026-06-14: A platform engineer raised and closed a routine observation. Gradient-norm logging was noisier than usual and attributed to the logging cadence. Recorded without further action.

- 2026-06-02: A platform engineer filed a routine observation. One shard upload retried once and succeeded on the second attempt.

- 2026-06-19: The storage team recorded a routine observation. A rank restarted after an NCCL timeout and rejoined at the next barrier. Referred to the dated decisions and closed.

- 2026-06-16: A shift handover reviewed a routine observation. Two nodes were drained for a driver update and returned before the next epoch. No action was carried forward.

- 2026-06-13: The storage team noted a routine observation. GPU memory headroom was reported comfortable at the current micro-batch size.

- 2026-06-14: The checkpoint service owner filed a routine observation. Gradient-norm logging was noisier than usual and attributed to the logging cadence. The thread was archived after review.

- 2026-06-11: A shift handover reviewed a routine observation. The epoch counter and the step counter were reconciled after the resume.

- 2026-06-02: The scheduling desk opened a query on a routine observation. The epoch counter and the step counter were reconciled after the resume. Filed for the record.

- 2026-06-16: The cluster operator logged a routine observation. A rank restarted after an NCCL timeout and rejoined at the next barrier. A second reviewer concurred.

- 2026-06-05: The on-call trainer minuted a routine observation. One node reported an ECC-corrected memory event with no run impact. No action was carried forward.

- 2026-06-22: The storage team spot-checked a routine observation. The nightly integrity scan over the shard catalogue completed clean.

- 2026-06-07: A weekly training review signed off a routine observation. The nightly integrity scan over the shard catalogue completed clean.

- 2026-06-05: The observability team recorded a routine observation. One node reported an ECC-corrected memory event with no run impact. A second reviewer concurred.

- 2026-06-26: The observability team spot-checked a routine observation. An alert fired on checkpoint age and cleared once the write completed. The desk confirmed no run impact.

- 2026-06-25: A weekly training review minuted a routine observation. Two nodes were drained for a driver update and returned before the next epoch. Recorded without further action.

- 2026-06-26: The data-integrity owner recorded a routine observation. The loss curve showed a brief plateau that recovered without intervention.

- 2026-06-23: The storage team noted a routine observation. Checkpoint write latency spiked on one rank; traced to a slow object-store PUT, not the writer. The desk confirmed no run impact.

- 2026-06-17: The scheduling desk spot-checked a routine observation. Disk pressure on a staging host cleared after the retention sweep ran. Noted and closed.

- 2026-06-24: The on-call trainer opened a query on a routine observation. Disk pressure on a staging host cleared after the retention sweep ran. Recorded without further action.

- 2026-06-10: A weekly training review minuted a routine observation. The registry export matched the object store's listing on the first pass.

- 2026-06-02: The on-call trainer minuted a routine observation. An alert fired on checkpoint age and cleared once the write completed. Referred to the dated decisions and closed.
