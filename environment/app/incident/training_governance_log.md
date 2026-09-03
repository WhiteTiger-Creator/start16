# Planning governance log

How the resume planner is *meant* to behave -- the recovery of the truncated checkpoint registry, what makes a checkpoint complete, which checkpoint the run may resume from after the data incident, and which shards come back and in what order -- was settled incrementally by the training governance board, and those decisions live in the review entries below, not in any single summary. Several stages deliberately depart from the intuitive reading, and which ones they are is settled in the entries below rather than here. The February draft proposals were revisited during the 2026-05 run review and several were reversed; where a draft or interim conflicts with a later decision, the later dated decision governs. `/app/docs/resume_contract.json` is the output contract only.

- 2026-02-04: The exceptions queue owner carried forward a routine observation. A query about a prior-period entry was answered from the published schedule. Referred to the dated decisions and closed.

> **Recovery draft proposal (2026-02-05 - #ML-6020)** Rosa: rebuild the truncated registry by concatenating the pre-migration snapshot with the migrator journal and keeping the last row seen for each entry; a reinstated entry is re-read from the snapshot *(Superseded -- reversed in the 2026-05 run review.)*

> **Recovery draft proposal (2026-02-12 - #ML-6026)** Anders: a checkpoint counts as complete once every rank has written its model shard; the optimizer shards are a convenience and need not all be present *(Superseded -- reversed in the 2026-05 run review.)*

> **Recovery draft proposal (2026-02-18 - #ML-6032)** Marek: restart from the newest complete checkpoint, since that is the furthest the run got *(Superseded -- reversed in the 2026-05 run review.)*

- 2026-02-09: The platform team filed a routine observation. A typo in a reference record was corrected before the run started. Referred to the dated decisions and closed.

- 2026-02-19: The operations desk recorded a routine observation. Nightly reconciliation matched exactly and the file was released without comment.

- 2026-02-27: A reviewer on shift noted a routine observation. Late inputs arrived from one feed and were loaded before the cut.

- 2026-02-21: The exceptions queue owner opened a query on a routine observation. A question raised on the floor was withdrawn once the entry was reread. The desk confirmed no downstream impact.

- 2026-02-20: The controls team noted a routine observation. A duplicate order was cancelled at source and never reached the run.

- 2026-02-08: A weekly review filed a routine observation. A query about a prior-period entry was answered from the published schedule.

- 2026-02-17: A stand-up note reviewed a routine observation. Late inputs arrived from one feed and were loaded before the cut. No action was carried forward.

- 2026-02-12: The platform team carried forward a routine observation. An operator asked whether a credit had posted; it had, in the preceding period.

- 2026-02-27: The controls team reviewed a routine observation. The overnight window ran long behind an unrelated platform patch. Referred to the dated decisions and closed.

- 2026-02-27: A stand-up note reviewed a routine observation. Storage on the staging host was extended after the export outgrew its allocation. The desk confirmed no downstream impact.

- 2026-02-15: A shift handover opened a query on a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. The desk confirmed no downstream impact.

- 2026-02-04: A weekly review logged a routine observation. Two accounts showed a same-day transfer the export had not yet picked up.

- 2026-02-21: The audit lead raised and closed a routine observation. Nightly reconciliation matched exactly and the file was released without comment.

- 2026-02-23: The platform team filed a routine observation. The count sat a little above the running mean, entirely from estimated inputs. The desk confirmed no downstream impact.

- 2026-02-23: A reviewer on shift signed off a routine observation. A question raised on the floor was withdrawn once the entry was reread. Referred to the dated decisions and closed.

- 2026-02-25: The duty analyst filed a routine observation. The overnight window ran long behind an unrelated platform patch. Referred to the dated decisions and closed.

- 2026-02-11: A shift handover signed off a routine observation. A batch retried once after a transient timeout and completed on the second pass. The thread was archived after review.

- 2026-02-23: The operations desk opened a query on a routine observation. A query about a prior-period entry was answered from the published schedule. Filed for the record.

- 2026-02-16: The audit lead opened a query on a routine observation. The downstream vendor confirmed receipt inside the agreed window. No action was carried forward.

- 2026-02-12: The duty analyst reviewed a routine observation. Storage on the staging host was extended after the export outgrew its allocation.

- 2026-02-17: An on-call engineer raised and closed a routine observation. The count sat a little above the running mean, entirely from estimated inputs.

- 2026-02-08: The operations desk noted a routine observation. The count sat a little above the running mean, entirely from estimated inputs.

- 2026-02-03: A weekly review logged a routine observation. The overnight window ran long behind an unrelated platform patch. The thread was archived after review.

- 2026-03-04: The duty analyst spot-checked a routine observation. A question raised on the floor was withdrawn once the entry was reread. Filed for the record.

> **Interim decision (2026-03-04 - #ML-6044)** Priya: the re-fetch queue is taken largest shard first, so the biggest gaps close soonest *(Revised -- see the 2026-05 run review.)*

- 2026-03-23: The operations desk signed off a routine observation. Two accounts showed a same-day transfer the export had not yet picked up.

- 2026-03-03: A weekly review spot-checked a routine observation. An operator asked whether a credit had posted; it had, in the preceding period. Nothing here bears on engine behaviour.

- 2026-03-09: A reviewer on shift recorded a routine observation. An operator asked whether a credit had posted; it had, in the preceding period. No follow-up was requested.

- 2026-03-01: The operations desk filed a routine observation. Storage on the staging host was extended after the export outgrew its allocation.

- 2026-03-01: The reconciliation desk reviewed a routine observation. Nightly reconciliation matched exactly and the file was released without comment.

- 2026-03-20: A reviewer on shift raised and closed a routine observation. A typo in a reference record was corrected before the run started. The thread was archived after review.

- 2026-03-15: A stand-up note opened a query on a routine observation. Late inputs arrived from one feed and were loaded before the cut. Closed with no parameter change.

- 2026-03-08: The reconciliation desk filed a routine observation. A question raised on the floor was withdrawn once the entry was reread.

- 2026-03-20: The exceptions queue owner filed a routine observation. The downstream vendor confirmed receipt inside the agreed window. No action was carried forward.

- 2026-03-05: A weekly review recorded a routine observation. Storage on the staging host was extended after the export outgrew its allocation.

- 2026-03-03: The operations desk spot-checked a routine observation. The variance sat inside tolerance and no adjustment was raised. No action was carried forward.

- 2026-03-14: The reconciliation desk noted a routine observation. Nightly reconciliation matched exactly and the file was released without comment.

- 2026-03-17: The duty analyst reviewed a routine observation. The count sat a little above the running mean, entirely from estimated inputs.

- 2026-03-10: A shift handover spot-checked a routine observation. The variance sat inside tolerance and no adjustment was raised. Nothing here bears on engine behaviour.

- 2026-03-18: An on-call engineer raised and closed a routine observation. Nightly reconciliation matched exactly and the file was released without comment. No action was carried forward.

- 2026-03-21: A shift handover noted a routine observation. The variance sat inside tolerance and no adjustment was raised.

- 2026-03-12: The operations desk carried forward a routine observation. The overnight window ran long behind an unrelated platform patch. Filed for the record.

- 2026-03-01: An on-call engineer logged a routine observation. Nightly reconciliation matched exactly and the file was released without comment. The desk confirmed no downstream impact.

- 2026-03-13: The duty analyst raised and closed a routine observation. The variance sat inside tolerance and no adjustment was raised. No action was carried forward.

- 2026-03-14: A shift handover reviewed a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine.

- 2026-03-22: The audit lead spot-checked a routine observation. Storage on the staging host was extended after the export outgrew its allocation. Closed with no parameter change.

- 2026-03-13: The reconciliation desk spot-checked a routine observation. Late inputs arrived from one feed and were loaded before the cut. Nothing here bears on engine behaviour.

- 2026-03-16: The audit lead logged a routine observation. Two accounts showed a same-day transfer the export had not yet picked up. The desk confirmed no downstream impact.

- 2026-03-16: The controls team reviewed a routine observation. Storage on the staging host was extended after the export outgrew its allocation. The thread was archived after review.

- 2026-04-02: A shift handover noted a routine observation. The overnight window ran long behind an unrelated platform patch. Nothing here bears on engine behaviour.

- 2026-04-10: An on-call engineer logged a routine observation. Nightly reconciliation matched exactly and the file was released without comment.

- 2026-04-16: A stand-up note raised and closed a routine observation. The overnight window ran long behind an unrelated platform patch. Filed for the record.

- 2026-04-19: The controls team recorded a routine observation. The overnight window ran long behind an unrelated platform patch. Referred to the dated decisions and closed.

- 2026-04-06: The duty analyst raised and closed a routine observation. An operator asked whether a credit had posted; it had, in the preceding period.

- 2026-04-10: The operations desk raised and closed a routine observation. Nightly reconciliation matched exactly and the file was released without comment.

- 2026-04-06: The controls team filed a routine observation. The downstream vendor confirmed receipt inside the agreed window.

- 2026-04-27: The reconciliation desk raised and closed a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. Closed with no parameter change.

- 2026-04-13: The duty analyst filed a routine observation. A duplicate order was cancelled at source and never reached the run. Closed with no parameter change.

- 2026-04-07: The operations desk filed a routine observation. Late inputs arrived from one feed and were loaded before the cut. No action was carried forward.

- 2026-04-03: The platform team spot-checked a routine observation. A question raised on the floor was withdrawn once the entry was reread. Filed for the record.

- 2026-04-01: A reviewer on shift signed off a routine observation. Late inputs arrived from one feed and were loaded before the cut. Referred to the dated decisions and closed.

- 2026-04-11: The controls team filed a routine observation. A duplicate order was cancelled at source and never reached the run. Nothing here bears on engine behaviour.

- 2026-04-09: A stand-up note noted a routine observation. A query about a prior-period entry was answered from the published schedule.

- 2026-04-25: A weekly review carried forward a routine observation. A duplicate order was cancelled at source and never reached the run.

- 2026-04-01: The platform team spot-checked a routine observation. A duplicate order was cancelled at source and never reached the run. Filed for the record.

- 2026-04-02: The reconciliation desk carried forward a routine observation. A batch retried once after a transient timeout and completed on the second pass.

- 2026-04-10: A weekly review signed off a routine observation. A query about a prior-period entry was answered from the published schedule.

- 2026-04-23: The duty analyst opened a query on a routine observation. Storage on the staging host was extended after the export outgrew its allocation. Closed with no parameter change.

- 2026-04-12: An on-call engineer signed off a routine observation. Nightly reconciliation matched exactly and the file was released without comment. No follow-up was requested.

- 2026-04-01: The controls team carried forward a routine observation. Two accounts showed a same-day transfer the export had not yet picked up. Filed for the record.

- 2026-04-19: The exceptions queue owner recorded a routine observation. A batch retried once after a transient timeout and completed on the second pass. Closed with no parameter change.

- 2026-04-07: The audit lead signed off a routine observation. Late inputs arrived from one feed and were loaded before the cut. Filed for the record.

- 2026-05-18: The operations desk logged a routine observation. The overnight window ran long behind an unrelated platform patch. The desk confirmed no downstream impact.

> **Governance decision (2026-05-06 - #ML-6150)** Priya: Input paths, final. The shard catalogue, the data incident record and the resume policy are always read from their fixed absolute paths under /app/data; `--input` selects the checkpoint registry only. Both `--input` and `--output-dir` keep their documented defaults.

> **Governance decision (2026-05-08 - #ML-6170)** Yusuf: Registry recovery, final (supersedes #ML-6020). Start from the pre-migration snapshot and replay the migrator journal in ascending `seq`, never in file order. An `amend` overwrites the named field in place. An `invalidate` takes the entry out of the registry, but the migrator keeps it as it stood at that moment. A `reinstate` returns an invalidated entry EXACTLY as it then stood: an amendment posted before the invalidation survives, and one posted while the entry was out is lost. A change naming an entry the snapshot never carried is ignored, and a reinstatement of an entry that was never invalidated does nothing.

> **Governance decision (2026-05-09 - #ML-6174)** Yusuf: Recovered shape, final. The rebuilt registry is a JSON array ascending by step, then rank, then kind, then entry id. Each row carries the eight declared fields -- the migrator's bookkeeping (`seq`, `kind`, `posted_by`) never survives the replay.

> **Governance decision (2026-05-13 - #ML-6182)** Lena: Checkpoint completeness, final (supersedes #ML-6026; deviates from the model-only reading). A checkpoint is complete only where every rank of the configured world holds BOTH its model shard and its optimizer shard. A rank missing either one leaves the whole checkpoint unusable, however many other shards landed for that step.

> **Governance decision (2026-05-16 - #ML-6186)** Marek: Resume point, final (supersedes #ML-6032; deviates from the newest-complete reading). The run trained through the poisoned epochs, so a checkpoint written at or after the first step of the earliest poisoned epoch has already learned from the corrupt shards and cannot be resumed from, complete or not. The resume point is the HIGHEST complete checkpoint whose step falls strictly before that first poisoned step. An epoch's first step is its epoch number multiplied by the incident record's steps_per_epoch.

> **Governance decision (2026-05-20 - #ML-6190)** Marek: Re-fetch set, final. A data shard is re-fetched where its stored checksum disagrees with the catalogue's expected checksum. Every shard belonging to a poisoned epoch is re-fetched as well, whatever its checksum says, because the adapter that wrote them is not trusted. A shard to which both apply carries `poisoned_epoch` as its reason: the epoch is the stronger finding, and the checksum tells us nothing further once the writer itself is in doubt.

> **Governance decision (2026-05-24 - #ML-6194)** Priya: Re-fetch order, final (revises #ML-6044; deviates from the largest-first interim). The re-fetch set is taken in ascending epoch, then ascending shard id, so the oldest data the run will read again comes back first. Shards are admitted to the plan in that order until either the policy's refetch_budget_bytes would be exceeded or its max_refetch_shards is reached; every shard not admitted is deferred to the queue in the same order.

> **Governance decision (2026-05-28 - #ML-6196)** Lena: Emission order, final. The plan lists every checkpoint ascending by step, whether complete or not, and its re-fetch list in the admitted order. The deferred queue keeps the same ascending epoch and shard id order.

- 2026-05-02: A shift handover recorded a routine observation. A typo in a reference record was corrected before the run started. The thread was archived after review.

- 2026-05-17: A shift handover noted a routine observation. Two accounts showed a same-day transfer the export had not yet picked up. No action was carried forward.

- 2026-05-13: A weekly review opened a query on a routine observation. A typo in a reference record was corrected before the run started. No follow-up was requested.

- 2026-05-03: The platform team logged a routine observation. A duplicate order was cancelled at source and never reached the run. No action was carried forward.

- 2026-05-16: The controls team spot-checked a routine observation. Storage on the staging host was extended after the export outgrew its allocation. No follow-up was requested.

- 2026-05-23: The audit lead noted a routine observation. The count sat a little above the running mean, entirely from estimated inputs.

- 2026-05-05: The platform team logged a routine observation. A duplicate order was cancelled at source and never reached the run. Referred to the dated decisions and closed.

- 2026-05-05: The reconciliation desk logged a routine observation. A typo in a reference record was corrected before the run started.

- 2026-05-19: A shift handover raised and closed a routine observation. Storage on the staging host was extended after the export outgrew its allocation. Closed with no parameter change.

- 2026-05-23: A shift handover recorded a routine observation. The variance sat inside tolerance and no adjustment was raised. Closed with no parameter change.

- 2026-05-03: A reviewer on shift signed off a routine observation. A question raised on the floor was withdrawn once the entry was reread. No action was carried forward.

- 2026-05-12: A reviewer on shift logged a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. Closed with no parameter change.

- 2026-05-19: A weekly review opened a query on a routine observation. A batch retried once after a transient timeout and completed on the second pass. Filed for the record.

- 2026-05-10: An on-call engineer reviewed a routine observation. A question raised on the floor was withdrawn once the entry was reread. Referred to the dated decisions and closed.

- 2026-05-07: The exceptions queue owner opened a query on a routine observation. The variance sat inside tolerance and no adjustment was raised.

- 2026-05-02: The audit lead carried forward a routine observation. A question raised on the floor was withdrawn once the entry was reread.

- 2026-05-22: An on-call engineer raised and closed a routine observation. The variance sat inside tolerance and no adjustment was raised. Closed with no parameter change.

- 2026-05-23: The exceptions queue owner carried forward a routine observation. A typo in a reference record was corrected before the run started.

- 2026-05-09: The reconciliation desk recorded a routine observation. Nightly reconciliation matched exactly and the file was released without comment. The desk confirmed no downstream impact.

- 2026-05-16: The duty analyst noted a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. No action was carried forward.

- 2026-06-03: A shift handover raised and closed a routine observation. Storage on the staging host was extended after the export outgrew its allocation. The thread was archived after review.

> **Governance decision (2026-06-02 - #ML-6210)** Priya: Resume policy baseline, read from /app/data/resume_policy.json at that fixed absolute path. Any field the policy file omits keeps its baseline: world_size = 16; refetch_budget_bytes = 35000000000; max_refetch_shards = 120.

- 2026-06-14: The platform team filed a routine observation. One record appeared twice in the export after a mid-cycle correction. No follow-up was requested.

- 2026-06-02: The duty analyst opened a query on a routine observation. The overnight window ran long behind an unrelated platform patch. Closed with no parameter change.

- 2026-06-19: The platform team carried forward a routine observation. The count sat a little above the running mean, entirely from estimated inputs. The thread was archived after review.

- 2026-06-16: An on-call engineer reviewed a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine.

- 2026-06-13: The operations desk spot-checked a routine observation. A question raised on the floor was withdrawn once the entry was reread. Filed for the record.

- 2026-06-14: The platform team carried forward a routine observation. A question raised on the floor was withdrawn once the entry was reread.

- 2026-06-11: The reconciliation desk opened a query on a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. Referred to the dated decisions and closed.

- 2026-06-02: The audit lead recorded a routine observation. The overnight window ran long behind an unrelated platform patch.

- 2026-06-16: The reconciliation desk logged a routine observation. Two accounts showed a same-day transfer the export had not yet picked up.

- 2026-06-05: The operations desk signed off a routine observation. The count sat a little above the running mean, entirely from estimated inputs.

- 2026-06-22: A reviewer on shift noted a routine observation. The overnight window ran long behind an unrelated platform patch.

- 2026-06-07: The audit lead noted a routine observation. A query about a prior-period entry was answered from the published schedule.

- 2026-06-05: A weekly review carried forward a routine observation. A question raised on the floor was withdrawn once the entry was reread.

- 2026-06-26: The controls team opened a query on a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. No action was carried forward.

- 2026-06-25: The controls team reviewed a routine observation. The count sat a little above the running mean, entirely from estimated inputs. No action was carried forward.

- 2026-06-26: The platform team opened a query on a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. The desk confirmed no downstream impact.

- 2026-06-23: A weekly review logged a routine observation. The downstream vendor confirmed receipt inside the agreed window. The desk confirmed no downstream impact.

- 2026-06-17: The exceptions queue owner reviewed a routine observation. A question raised on the floor was withdrawn once the entry was reread.

- 2026-06-24: A reviewer on shift logged a routine observation. Nightly reconciliation matched exactly and the file was released without comment. Filed for the record.

- 2026-06-10: The reconciliation desk reviewed a routine observation. The overnight window ran long behind an unrelated platform patch. Filed for the record.

- 2026-06-02: A shift handover carried forward a routine observation. Storage on the staging host was extended after the export outgrew its allocation.
