# Documentation and tooling gaps: retail-semantic-search

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Canonical retryable-write support

- **What was missing:** P04 contradicts the model's Amazon DocumentDB-derived belief that retryWrites=false is universally required. Azure migration guidance says remove it, while native/vector quickstarts use false and security/Entra code examples use true. The public record does not settle the applicable rule.
- **Where the agent looked:** Fetched Azure DocumentDB migration, native Node.js, vector and Entra pages; read connection, security and deployment skills; compared supplied readiness findings.
- **Effect on this build:** The builder used false with an explicit caveat. Driver-settings compliance cannot be fully assessed, and ingestion needs an application retry strategy.
- **Suggested fix (learn_doc):** Ship 'Azure DocumentDB driver retry support matrix': native/OIDC authentication, supported operation types, driver/server versions and topology; define retryReads/retryWrites behavior, transient-write recovery and idempotent backoff. Link it prominently from migration/vector quickstarts and synchronize every skill example.

## [high] Gallery packaging and release contract

- **What was missing:** No explicit public gallery contract was found for complete configuration examples, README sections, runnable README commands, offline tests, exact dependency pins/tested drivers, naming consistency or vulnerability gates. Existing quickstarts demonstrate fragments but do not state the combined expectations.
- **Where the agent looked:** Learn searches for .env.example completeness, gallery contribution requirements, README commands, offline tests, dependency pins and naming; driver/local/deployment skills and fetched FAQ/quickstarts.
- **Effect on this build:** Most hygiene was supplied by builder assumptions, but fixed-setting inventory is incomplete under the literal reference, Node.js 22 and live commands remain unverified, the lockfile uses a runner feed, and three high-severity findings lack assessment.
- **Suggested fix (agent_kit_rule):** Ship 'Publishable Azure DocumentDB sample contract': required README sections; complete required-input/fixed-default inventory; placeholder-only examples; exact manifests/lockfiles; clean public-registry installation; tested driver/runtime table; offline tests; separately authorized managed-service tests; successful vulnerability assessment; correct branding with explicit allowances for disambiguation and retained API names.

## [high] Node.js agent recommendation recipe

- **What was missing:** P06, P08, P19, P20 and P22 remain training-derived compound practices: product/order separation, candidate overfetch/reranking, distinct-order counting, minimal provider context and ranked-ID/factual grounding. The LlamaIndex guide documents a Python connector and Node driver fallback, not the requested JavaScript agent/memory composition.
- **Where the agent looked:** Open discovery's retail/co-purchase/grounding searches, fetched LlamaIndex/vector pages, modeling guidance and installed workflow evidence in events.
- **Effect on this build:** The builder implemented defensible versions from assumptions and offline framework inspection. Ranking weights and factual explanation quality are unmeasured; these practices cannot be used as service-specific deductions.
- **Suggested fix (sample_or_quickstart):** Ship 'Node.js LlamaIndex retail recommendations with Azure DocumentDB': a tested SDK release set; product and order schemas; duplicate-line/quantity semantics; 20,000-order/60-product seed; native retrieval tool; exclusion/deduplication/reranking; fixed-ID response merging; provider-context privacy; insufficient-candidate failures; explicit quality limitations and benchmark.

## [high] Vector validation and lifecycle contract

- **What was missing:** P05 and P24 have partial public building blocks but no complete finite-vector validation and source-hash/model-revision lifecycle guidance. The vector skill also lacks the reference's mandatory README scaling/tuning section.
- **Where the agent looked:** Open discovery's finite-vector/content-hash searches, vector-normalize-embeddings, vector-create-diskann-index, fetched vector/LlamaIndex pages and app ingestion.
- **Effect on this build:** Validation/hash caching were implemented by assumption. Default DiskANN parameters were not benchmarked, and larger-catalog tuning instructions are absent.
- **Suggested fix (agent_kit_rule):** Extend the vector skill with finite/nonzero/exact-dimension validation; consistent ingestion/query preprocessing; model/revision/normalization metadata and source hashes; re-embedding/index-rebuild triggers. Require sample READMEs to state vector count, unbenchmarked defaults, adjustment locations and a representative recall/latency/build-cost measurement procedure.

## [high] Session memory ownership boundaries

- **What was missing:** P21's authenticated ownership, unguessable IDs and lifetime contract has no complete public service-specific source. Session/thread persistence examples do not establish these security guarantees.
- **Where the agent looked:** Open discovery agent-memory searches, readiness's JavaScript memory API gap, app memory/CLI/README and LlamaIndex integration guidance.
- **Effect on this build:** Memory is bounded and isolated by label, but not authorized or expiring. This is acceptable only within the explicitly local CLI boundary, not as a ready-to-expose multi-user API.
- **Suggested fix (learn_doc):** Ship 'Secure agent session memory': local CLI versus hosted trust boundaries; authenticated owner binding; random session identifiers; ownership checks; history/time limits; eviction/concurrency; provider-data minimization. Include the exact JavaScript history injection API.

## [high] Read only target readiness inventory

- **What was missing:** The auditor cannot assess P03, P13, P18 or P25 fully: target tier/version/features, runtime roles, executed index plans and networking are not available. Documentation describes the controls but the tools do not establish this target's readiness.
- **Where the agent looked:** Readiness/build events, README, seed/runtime configuration, live verifier, security/secondary-user/compatibility/vector guidance.
- **Effect on this build:** The verifier stopped for missing model credentials; no seeded DiskANN/explain results exist. One URI serves both setup and runtime, and network/role posture is unknown.
- **Suggested fix (mcp_tool_or_description):** Provide an authorized read-only 'inspect_sample_target' tool: resource identity, tier/version/vector support, network posture, current data-plane roles, collection/index definitions and winning/executed explain plan. Redact credentials, distinguish ARM from database roles, and return unknown rather than assuming readiness. Add explicit separate setup/runtime credential-switch instructions.

## [high] Reliable decision logging

- **What was missing:** log_decision reused D002 for distinct calls, lost records and then failed validation. Supplemental Markdown and events preserve intent, but the structured decision file is incomplete.
- **Where the agent looked:** decisions.jsonl, app/DECISIONS.md and events.jsonl:83-101,106,126.
- **Effect on this build:** Only three decisions survive in decisions.jsonl; auth/index/model/interface/isolation choices require event reconstruction. The builder's fallback is supported by actual exceptions.
- **Suggested fix (mcp_tool_or_description):** Make log_decision append-only and atomic with unique IDs, validation before write, corruption recovery and a structured fallback sink. Preserve reason_source and evidence for every record; never overwrite earlier IDs.

## [high] Current identity and product terminology

- **What was missing:** Readiness exposed legacy Cosmos CLI/extension guidance, older deployment API defaults, synthesized endpoint examples and former vCore terminology in modeling resources. Current documentation distinguishes products, but skills/examples remain inconsistent.
- **Where the agent looked:** Supplied readiness Q02/Q03/Q04 findings, loaded deployment/local/security/modeling resources, current Bicep/Node.js/Entra/FAQ pages.
- **Effect on this build:** The sample avoided obsolete provisioning and copied the portal URI, but future generated templates or copied skill hosts can be wrong. Correct naming required deliberate disambiguation.
- **Suggested fix (naming_or_disambiguation):** Synchronize deployment guidance with az documentdb mongocluster/documentdb extension and explain supported versus recommended API versions. Replace synthesized mongocluster.documentdb.azure.com hosts with portal-URI placeholders. Rename modeling prose to Azure DocumentDB while preserving valid cosmosSearch/resource/URI identifiers. Add dated legacy-command migration notes.

## [high] Reference scenario disambiguation

- **What was missing:** The supplied reference labels Python/Flask, ada-002, BSON binary, IVF and a ten-result /search route as starter requirements even though the actual prompt requests Node.js, DiskANN and five product-ID recommendations. Binary vector storage also conflicts with the fetched service representation guidance.
- **Where the agent looked:** requirements.md:12-17, prompt.md, prompt-review risks, vector skill and fetched vector page.
- **Effect on this build:** Several reference misses measure an inconsistent fixture rather than shortcomings in the builder or public documentation.
- **Suggested fix (other):** Version and validate scenario requirements against the starter prompt before runs. Flag explicit runtime/index/interface conflicts and unsupported representation demands; keep desired gallery additions separate from contradictory example requirements.

## [medium] Sample infrastructure inclusion policy

- **What was missing:** The deployment skill teaches correct IaC but does not say whether every gallery app must include nonexecuted templates. The prompt never requested provisioning; the run policy prohibited resource changes, not writing optional infrastructure.
- **Where the agent looked:** Deployment skill and Bicep template, current Bicep quickstart, app README, events.jsonl:91 and reference requirements.
- **Effect on this build:** No infrastructure artifacts were generated, despite the team's checklist/reference expecting them.
- **Suggested fix (agent_kit_rule):** Add: 'Gallery samples include optional parameterized Microsoft.DocumentDB/mongoClusters IaC, unless an approved existing-cluster-only exception is documented. Generating templates does not authorize deployment. Feature prerequisites override cheap generic defaults: DiskANN needs a supported paid tier.' Include cleanup scoped to resources actually created.

## [medium] Findable service practice entry point

- **What was missing:** Authentication preference, access-aligned/bounded modeling, complete query-index lifecycle, aggregation compatibility, IaC parameters/resource type, cleanup and lexical/hybrid mechanisms were found only when searched by checklist name or loaded directly.
- **Where the agent looked:** Named searches and documentdb-security, documentdb-data-modeling, documentdb-indexing, documentdb-full-text-search and documentdb-azure-deployment; compatibility and Bicep/Node.js quickstarts.
- **Effect on this build:** Several practices were followed, but an open search did not surface the full expectations. Infrastructure inclusion was missed; Entra's rationale exists only in the event trail.
- **Suggested fix (discoverability):** Ship 'Build and review an Azure DocumentDB sample' as the landing-page/agent-kit entry point. Link explicitly to security-entra-rbac, bounded/access-pattern modeling, query/index usage review, compatibility matrix, current deployment templates, cleanup and createSearchIndexes hybrid guidance. Keep supported-versus-recommended distinctions visible.

## [medium] Repeatable setup and readiness

- **What was missing:** P17's insert-only seed prescription and P23's definition-drift/readiness contract were not publicly confirmed. Public examples provide upserts, index listing and name-based idempotency separately.
- **Where the agent looked:** Open discovery seed/setup searches, fetched Node.js/LlamaIndex/vector guidance, app seed and live verifier.
- **Effect on this build:** Stable replacement upserts work offline, but setup does not explicitly compare index drift or gate recommendations on bounded readiness checks.
- **Suggested fix (agent_kit_rule):** Ship 'Repeatable seed and vector setup': deterministic IDs; replacement versus $setOnInsert tradeoffs; batch/transient recovery; existing-definition comparison; no silent index substitution/deletion; bounded readiness probe and clear drift errors. State which requirements are service rules versus sample policy.

## [medium] Startup errors and timeout profiles

- **What was missing:** P11 and P14's complete startup/redaction and universal timeout rules were not publicly established. D002 is labeled model_default even though the connection skill and native quickstart answer most of its choices.
- **Where the agent looked:** Connection/driver/security skills, native Node.js quickstart, open discovery timeout/startup searches, D002 and events.jsonl:55,77,90.
- **Effect on this build:** Safe parsing, two finite startup timeouts and ping exist, but auth/connectivity categories are combined; the auditor cannot impose remembered queue/query limits universally.
- **Suggested fix (discoverability):** Link context-first connection guidance from the Node.js quickstart and add profiles for sequential CLI, long index builds and concurrent APIs. Define safe startup error categories and redaction tests, and explicitly say when waitQueueTimeoutMS/maxTimeMS should or should not be set.

## [medium] Model default verification assumptions

- **What was missing:** Supplemental model_default choices cover offline workflow tests, fail-closed output and safe error presentation. No consolidated service sample guidance states their expected contract or verifies live factual reasoning.
- **Where the agent looked:** app/DECISIONS.md:8,10-11; test/recommendation/config code; fetched LlamaIndex and relevant skills.
- **Effect on this build:** Offline behavior is strong, but agent explanations can still be inaccurate and live model/vector behavior is unverified.
- **Suggested fix (agent_kit_rule):** Add a sample-agent rule requiring real-framework offline tests with provider/database doubles, captured retrieval errors, fixed-ID/trusted-field merging, safe provider/driver errors and separately declared live/quality evidence. Link the Node.js recommendation recipe instead of relying on framework memory.

## [medium] Neighbor feature assumptions

- **What was missing:** Readiness also exposed remembered MongoDB community $text as the recommended search path, outdated cross-shard transaction restrictions, a wrong local GHCR organization/emulator assumption and a universal remembered EnableChangeStreams flag.
- **Where the agent looked:** Supplied readiness Q09/Q10/Q11/Q12, loaded full-text/local skills, fetched compatibility matrix and supplied grounding links.
- **Effect on this build:** These features are not used by this app, so no violation is assigned. They remain documented risks for agents extending it from memory.
- **Suggested fix (discoverability):** Prominently distinguish supported community $text from recommended preview BM25 createSearchIndexes; publish dated cross-shard transaction support; provide the current authenticated/TLS local gateway setup with a managed-DiskANN parity caveat; separate ordinary change streams, multishard preview and pre-image prerequisites without inventing a universal flag.

## [low] Documented shard rationale

- **What was missing:** Public guidance explains how to choose shard keys, but no explicit requirement to publish a sample's shard-key rationale was found.
- **Where the agent looked:** Azure DocumentDB partitioning/FAQ searches and gallery packaging searches.
- **Effect on this build:** No immediate effect: the sample deliberately remains unsharded. Future sharded samples may omit rationale.
- **Suggested fix (agent_kit_rule):** Add to the gallery schema rule: 'When sharding, document dominant query/write patterns, cardinality/distribution, expected scale, supporting index and why this key was chosen; otherwise explain why one shard suffices.'

