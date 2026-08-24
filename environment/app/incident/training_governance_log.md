# Planning governance log

How the resume planner is *meant* to behave -- the recovery of the truncated checkpoint registry, what makes a checkpoint complete, which checkpoint the run may resume from after the data incident, and which shards come back and in what order -- was settled incrementally by the training governance board, and those decisions live in the review entries below, not in any single summary. Several stages deliberately DEVIATE from the intuitive reading: completeness needs the optimizer shards as well as the model shards, the resume point rolls back behind the poisoned epochs rather than taking the newest complete checkpoint, a poisoned shard is re-fetched whatever its checksum says, and the queue is taken oldest-epoch first rather than largest first. The February draft proposals were revisited during the 2026-05 run review and several were reversed; where a draft or interim conflicts with a later decision, the later dated decision governs. `/app/docs/resume_contract.json` is the output contract only.

- 2026-02-04: Platform desk noted retry storms on the parameter server in window 1003. Raised with the storage owner; the resume parameters were not touched.

> **Recovery draft proposal (2026-02-05 - #ML-6020)** Rosa: rebuild the truncated registry by concatenating the pre-migration snapshot with the migrator journal and keeping the last row seen for each entry; a reinstated entry is re-read from the snapshot *(Superseded -- reversed in the 2026-05 run review.)*

> **Recovery draft proposal (2026-02-12 - #ML-6026)** Anders: a checkpoint counts as complete once every rank has written its model shard; the optimizer shards are a convenience and need not all be present *(Superseded -- reversed in the 2026-05 run review.)*

> **Recovery draft proposal (2026-02-18 - #ML-6032)** Marek: restart from the newest complete checkpoint, since that is the furthest the run got *(Superseded -- reversed in the 2026-05 run review.)*

- 2026-02-09: Engineer on call logged a routine observation for the shard loader during review window 1005. Throughput drift reviewed; no policy change requested.

- 2026-02-19: Engineer on call logged a routine observation for the run telemetry pipeline during review window 1007. Throughput drift reviewed; no policy change requested.

- 2026-02-27: Engineer on call logged a routine observation for the run telemetry pipeline during review window 1010. Throughput drift reviewed; no policy change requested.

- 2026-02-21: Platform desk noted retry storms on the object-store gateway in window 1013. Raised with the storage owner; the resume parameters were not touched.

- 2026-02-20: Run review of the shard loader in window 1014 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-02-08: Platform desk noted retry storms on the object-store gateway in window 1015. Raised with the storage owner; the resume parameters were not touched.

- 2026-02-17: Training stand-up recorded a routine note against the shard loader for window 1017. The restart backlog was cleared with no amendment raised.

- 2026-02-12: Platform desk noted retry storms on the parameter server in window 1020. Raised with the storage owner; the resume parameters were not touched.

- 2026-02-27: Engineer on call logged a routine observation for the parameter server during review window 1023. Throughput drift reviewed; no policy change requested.

- 2026-02-27: Training stand-up recorded a routine note against the checkpoint writer for window 1025. The restart backlog was cleared with no amendment raised.

- 2026-02-15: Training stand-up recorded a routine note against the run telemetry pipeline for window 1028. The restart backlog was cleared with no amendment raised.

- 2026-02-04: Engineer on call logged a routine observation for the parameter server during review window 1029. Throughput drift reviewed; no policy change requested.

- 2026-02-21: Platform desk noted retry storms on the checkpoint writer in window 1030. Raised with the storage owner; the resume parameters were not touched.

- 2026-02-23: Training stand-up recorded a routine note against the parameter server for window 1033. The restart backlog was cleared with no amendment raised.

- 2026-02-23: Engineer on call logged a routine observation for the parameter server during review window 1035. Throughput drift reviewed; no policy change requested.

- 2026-02-25: Platform desk noted retry storms on the shard loader in window 1036. Raised with the storage owner; the resume parameters were not touched.

- 2026-02-11: Engineer on call logged a routine observation for the object-store gateway during review window 1039. Throughput drift reviewed; no policy change requested.

- 2026-02-23: Engineer on call logged a routine observation for the shard loader during review window 1042. Throughput drift reviewed; no policy change requested.

- 2026-02-16: Engineer on call logged a routine observation for the shard loader during review window 1043. Throughput drift reviewed; no policy change requested.

- 2026-02-12: Platform desk noted retry storms on the run telemetry pipeline in window 1046. Raised with the storage owner; the resume parameters were not touched.

- 2026-02-17: Run review of the checkpoint writer in window 1048 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-02-08: Training stand-up recorded a routine note against the checkpoint writer for window 1049. The restart backlog was cleared with no amendment raised.

- 2026-02-03: Training stand-up recorded a routine note against the object-store gateway for window 1051. The restart backlog was cleared with no amendment raised.

- 2026-03-04: Run review of the object-store gateway in window 1052 closed with no action; the standing thresholds were reconfirmed as they are.

> **Interim decision (2026-03-04 - #ML-6044)** Priya: the re-fetch queue is taken largest shard first, so the biggest gaps close soonest *(Revised -- see the 2026-05 run review.)*

- 2026-03-23: Engineer on call logged a routine observation for the checkpoint writer during review window 1053. Throughput drift reviewed; no policy change requested.

- 2026-03-03: Training stand-up recorded a routine note against the checkpoint writer for window 1056. The restart backlog was cleared with no amendment raised.

- 2026-03-09: Engineer on call logged a routine observation for the object-store gateway during review window 1058. Throughput drift reviewed; no policy change requested.

- 2026-03-01: Platform desk noted retry storms on the parameter server in window 1059. Raised with the storage owner; the resume parameters were not touched.

- 2026-03-01: Run review of the parameter server in window 1061 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-03-20: Platform desk noted retry storms on the run telemetry pipeline in window 1062. Raised with the storage owner; the resume parameters were not touched.

- 2026-03-15: Engineer on call logged a routine observation for the shard loader during review window 1065. Throughput drift reviewed; no policy change requested.

- 2026-03-08: Run review of the parameter server in window 1067 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-03-20: Training stand-up recorded a routine note against the run telemetry pipeline for window 1068. The restart backlog was cleared with no amendment raised.

- 2026-03-05: Training stand-up recorded a routine note against the checkpoint writer for window 1070. The restart backlog was cleared with no amendment raised.

- 2026-03-03: Run review of the run telemetry pipeline in window 1073 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-03-14: Training stand-up recorded a routine note against the parameter server for window 1076. The restart backlog was cleared with no amendment raised.

- 2026-03-17: Training stand-up recorded a routine note against the parameter server for window 1079. The restart backlog was cleared with no amendment raised.

- 2026-03-10: Platform desk noted retry storms on the parameter server in window 1080. Raised with the storage owner; the resume parameters were not touched.

- 2026-03-18: Engineer on call logged a routine observation for the run telemetry pipeline during review window 1082. Throughput drift reviewed; no policy change requested.

- 2026-03-21: Run review of the parameter server in window 1084 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-03-12: Platform desk noted retry storms on the run telemetry pipeline in window 1087. Raised with the storage owner; the resume parameters were not touched.

- 2026-03-01: Engineer on call logged a routine observation for the checkpoint writer during review window 1088. Throughput drift reviewed; no policy change requested.

- 2026-03-13: Run review of the object-store gateway in window 1091 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-03-14: Platform desk noted retry storms on the checkpoint writer in window 1094. Raised with the storage owner; the resume parameters were not touched.

- 2026-03-22: Run review of the run telemetry pipeline in window 1096 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-03-13: Run review of the parameter server in window 1097 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-03-16: Platform desk noted retry storms on the parameter server in window 1100. Raised with the storage owner; the resume parameters were not touched.

- 2026-03-16: Platform desk noted retry storms on the checkpoint writer in window 1103. Raised with the storage owner; the resume parameters were not touched.

- 2026-04-02: Run review of the shard loader in window 1106 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-04-10: Engineer on call logged a routine observation for the object-store gateway during review window 1107. Throughput drift reviewed; no policy change requested.

- 2026-04-16: Training stand-up recorded a routine note against the parameter server for window 1110. The restart backlog was cleared with no amendment raised.

- 2026-04-19: Engineer on call logged a routine observation for the shard loader during review window 1111. Throughput drift reviewed; no policy change requested.

- 2026-04-06: Platform desk noted retry storms on the checkpoint writer in window 1112. Raised with the storage owner; the resume parameters were not touched.

- 2026-04-10: Run review of the run telemetry pipeline in window 1113 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-04-06: Training stand-up recorded a routine note against the shard loader for window 1115. The restart backlog was cleared with no amendment raised.

- 2026-04-27: Platform desk noted retry storms on the checkpoint writer in window 1117. Raised with the storage owner; the resume parameters were not touched.

- 2026-04-13: Platform desk noted retry storms on the checkpoint writer in window 1119. Raised with the storage owner; the resume parameters were not touched.

- 2026-04-07: Engineer on call logged a routine observation for the object-store gateway during review window 1120. Throughput drift reviewed; no policy change requested.

- 2026-04-03: Engineer on call logged a routine observation for the shard loader during review window 1122. Throughput drift reviewed; no policy change requested.

- 2026-04-01: Platform desk noted retry storms on the checkpoint writer in window 1124. Raised with the storage owner; the resume parameters were not touched.

- 2026-04-11: Run review of the parameter server in window 1126 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-04-09: Training stand-up recorded a routine note against the shard loader for window 1129. The restart backlog was cleared with no amendment raised.

- 2026-04-25: Training stand-up recorded a routine note against the object-store gateway for window 1132. The restart backlog was cleared with no amendment raised.

- 2026-04-01: Training stand-up recorded a routine note against the run telemetry pipeline for window 1135. The restart backlog was cleared with no amendment raised.

- 2026-04-02: Platform desk noted retry storms on the object-store gateway in window 1137. Raised with the storage owner; the resume parameters were not touched.

- 2026-04-10: Platform desk noted retry storms on the shard loader in window 1140. Raised with the storage owner; the resume parameters were not touched.

- 2026-04-23: Engineer on call logged a routine observation for the run telemetry pipeline during review window 1143. Throughput drift reviewed; no policy change requested.

- 2026-04-12: Run review of the object-store gateway in window 1146 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-04-01: Engineer on call logged a routine observation for the run telemetry pipeline during review window 1147. Throughput drift reviewed; no policy change requested.

- 2026-04-19: Training stand-up recorded a routine note against the shard loader for window 1149. The restart backlog was cleared with no amendment raised.

- 2026-04-07: Engineer on call logged a routine observation for the parameter server during review window 1152. Throughput drift reviewed; no policy change requested.

- 2026-05-18: Training stand-up recorded a routine note against the run telemetry pipeline for window 1153. The restart backlog was cleared with no amendment raised.

> **Governance decision (2026-05-06 - #ML-6150)** Priya: Input paths, final. The shard catalogue, the data incident record and the resume policy are always read from their fixed absolute paths under /app/data; `--input` selects the checkpoint registry only. Both `--input` and `--output-dir` keep their documented defaults.

> **Governance decision (2026-05-08 - #ML-6170)** Yusuf: Registry recovery, final (supersedes #ML-6020). Start from the pre-migration snapshot and replay the migrator journal in ascending `seq`, never in file order. An `amend` overwrites the named field in place. An `invalidate` takes the entry out of the registry, but the migrator keeps it as it stood at that moment. A `reinstate` returns an invalidated entry EXACTLY as it then stood: an amendment posted before the invalidation survives, and one posted while the entry was out is lost. A change naming an entry the snapshot never carried is ignored, and a reinstatement of an entry that was never invalidated does nothing.

> **Governance decision (2026-05-09 - #ML-6174)** Yusuf: Recovered shape, final. The rebuilt registry is a JSON array ascending by step, then rank, then kind, then entry id. Each row carries the eight declared fields -- the migrator's bookkeeping (`seq`, `kind`, `posted_by`) never survives the replay.

> **Governance decision (2026-05-13 - #ML-6182)** Lena: Checkpoint completeness, final (supersedes #ML-6026; deviates from the model-only reading). A checkpoint is complete only where every rank of the configured world holds BOTH its model shard and its optimizer shard. A rank missing either one leaves the whole checkpoint unusable, however many other shards landed for that step.

> **Governance decision (2026-05-16 - #ML-6186)** Marek: Resume point, final (supersedes #ML-6032; deviates from the newest-complete reading). The run trained through the poisoned epochs, so a checkpoint written at or after the first step of the earliest poisoned epoch has already learned from the corrupt shards and cannot be resumed from, complete or not. The resume point is the HIGHEST complete checkpoint whose step falls strictly before that first poisoned step. An epoch's first step is its epoch number multiplied by the incident record's steps_per_epoch.

> **Governance decision (2026-05-20 - #ML-6190)** Marek: Re-fetch set, final. A data shard is re-fetched where its stored checksum disagrees with the catalogue's expected checksum. Every shard belonging to a poisoned epoch is re-fetched as well, whatever its checksum says, because the adapter that wrote them is not trusted.

> **Governance decision (2026-05-24 - #ML-6194)** Priya: Re-fetch order, final (revises #ML-6044; deviates from the largest-first interim). The re-fetch set is taken in ascending epoch, then ascending shard id, so the oldest data the run will read again comes back first. Shards are admitted to the plan in that order until either the policy's refetch_budget_bytes would be exceeded or its max_refetch_shards is reached; every shard not admitted is deferred to the queue in the same order.

> **Governance decision (2026-05-28 - #ML-6196)** Lena: Emission order, final. The plan lists every checkpoint ascending by step, whether complete or not, and its re-fetch list in the admitted order. The deferred queue keeps the same ascending epoch and shard id order.

- 2026-05-02: Engineer on call logged a routine observation for the object-store gateway during review window 1155. Throughput drift reviewed; no policy change requested.

- 2026-05-17: Training stand-up recorded a routine note against the parameter server for window 1158. The restart backlog was cleared with no amendment raised.

- 2026-05-13: Engineer on call logged a routine observation for the parameter server during review window 1161. Throughput drift reviewed; no policy change requested.

- 2026-05-03: Platform desk noted retry storms on the checkpoint writer in window 1162. Raised with the storage owner; the resume parameters were not touched.

- 2026-05-16: Run review of the run telemetry pipeline in window 1165 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-05-23: Engineer on call logged a routine observation for the object-store gateway during review window 1166. Throughput drift reviewed; no policy change requested.

- 2026-05-05: Engineer on call logged a routine observation for the run telemetry pipeline during review window 1169. Throughput drift reviewed; no policy change requested.

- 2026-05-05: Engineer on call logged a routine observation for the shard loader during review window 1171. Throughput drift reviewed; no policy change requested.

- 2026-05-19: Platform desk noted retry storms on the shard loader in window 1174. Raised with the storage owner; the resume parameters were not touched.

- 2026-05-23: Run review of the checkpoint writer in window 1176 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-05-03: Engineer on call logged a routine observation for the parameter server during review window 1177. Throughput drift reviewed; no policy change requested.

- 2026-05-12: Engineer on call logged a routine observation for the checkpoint writer during review window 1180. Throughput drift reviewed; no policy change requested.

- 2026-05-19: Engineer on call logged a routine observation for the shard loader during review window 1182. Throughput drift reviewed; no policy change requested.

- 2026-05-10: Platform desk noted retry storms on the checkpoint writer in window 1184. Raised with the storage owner; the resume parameters were not touched.

- 2026-05-07: Run review of the run telemetry pipeline in window 1186 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-05-02: Engineer on call logged a routine observation for the object-store gateway during review window 1187. Throughput drift reviewed; no policy change requested.

- 2026-05-22: Platform desk noted retry storms on the parameter server in window 1188. Raised with the storage owner; the resume parameters were not touched.

- 2026-05-23: Training stand-up recorded a routine note against the parameter server for window 1191. The restart backlog was cleared with no amendment raised.

- 2026-05-09: Run review of the object-store gateway in window 1193 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-05-16: Run review of the checkpoint writer in window 1195 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-06-03: Training stand-up recorded a routine note against the run telemetry pipeline for window 1198. The restart backlog was cleared with no amendment raised.

> **Governance decision (2026-06-02 - #ML-6210)** Priya: Resume policy baseline, read from /app/data/resume_policy.json at that fixed absolute path. Any field the policy file omits keeps its baseline: world_size = 16; refetch_budget_bytes = 35000000000; max_refetch_shards = 120.

- 2026-06-14: Platform desk noted retry storms on the object-store gateway in window 1199. Raised with the storage owner; the resume parameters were not touched.

- 2026-06-02: Run review of the object-store gateway in window 1200 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-06-19: Training stand-up recorded a routine note against the object-store gateway for window 1201. The restart backlog was cleared with no amendment raised.

- 2026-06-16: Run review of the shard loader in window 1204 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-06-13: Platform desk noted retry storms on the checkpoint writer in window 1206. Raised with the storage owner; the resume parameters were not touched.

- 2026-06-14: Engineer on call logged a routine observation for the run telemetry pipeline during review window 1209. Throughput drift reviewed; no policy change requested.

- 2026-06-11: Training stand-up recorded a routine note against the object-store gateway for window 1212. The restart backlog was cleared with no amendment raised.

- 2026-06-02: Platform desk noted retry storms on the shard loader in window 1214. Raised with the storage owner; the resume parameters were not touched.

- 2026-06-16: Run review of the object-store gateway in window 1215 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-06-05: Platform desk noted retry storms on the checkpoint writer in window 1218. Raised with the storage owner; the resume parameters were not touched.

- 2026-06-22: Run review of the shard loader in window 1219 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-06-07: Platform desk noted retry storms on the parameter server in window 1222. Raised with the storage owner; the resume parameters were not touched.

- 2026-06-05: Run review of the parameter server in window 1223 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-06-26: Training stand-up recorded a routine note against the shard loader for window 1224. The restart backlog was cleared with no amendment raised.

- 2026-06-25: Training stand-up recorded a routine note against the checkpoint writer for window 1226. The restart backlog was cleared with no amendment raised.

- 2026-06-26: Training stand-up recorded a routine note against the parameter server for window 1229. The restart backlog was cleared with no amendment raised.

- 2026-06-23: Training stand-up recorded a routine note against the run telemetry pipeline for window 1232. The restart backlog was cleared with no amendment raised.

- 2026-06-17: Engineer on call logged a routine observation for the parameter server during review window 1234. Throughput drift reviewed; no policy change requested.

- 2026-06-24: Run review of the run telemetry pipeline in window 1236 closed with no action; the standing thresholds were reconfirmed as they are.

- 2026-06-10: Platform desk noted retry storms on the checkpoint writer in window 1239. Raised with the storage owner; the resume parameters were not touched.

- 2026-06-02: Run review of the parameter server in window 1240 closed with no action; the standing thresholds were reconfirmed as they are.
