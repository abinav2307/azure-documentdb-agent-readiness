# Decision log

| Reason came from | Decisions |
|---|---|
| operator | 1 |
| model_default | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-22T23:29:22+00:00

## D002 (build): I chose default pool sizing, maxIdleTimeMS=120000, and 10-second connect/server-selection timeouts for this sequential local CLI.

- **Instead of:** Large prewarmed pool; Unbounded startup waits; Short query socket timeout
- **Because:** Sequential ingestion and one interactive request at a time do not need pool tuning; bounded startup enables a useful failure message without imposing a short limit on index builds.
- **Reason came from:** `model_default`
- **Evidence:** documentdb-connection requires workload context; review assumes a local CLI with bounded provider calls.
- **When:** 2026-11-22T23:31:01+00:00

## D002b (build): I chose exact pins llamaindex 0.12.1, @llamaindex/openai 0.4.22, and mongodb 6.22.0, with npm and a committed lockfile.

- **Instead of:** @llamaindex/openai 0.4.23; mongodb 7.x; Unpinned latest releases
- **Because:** Provider peers match the current umbrella package; driver matches review's 6.x assumption and lockfile fixes transitive versions.
- **Reason came from:** `tool_result`
- **Evidence:** npm view: llamaindex 0.12.1 uses core 0.6.22/env 0.1.30; openai 0.4.22 peers match those, while 0.4.23 requires core 0.6.23/env 0.1.31; mongodb 6.22.0 is latest returned 6.x.
- **When:** 2026-11-22T23:31:01+00:00
