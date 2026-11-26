# Documentation and tooling gaps: retail-semantic-search

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Gallery authoring acceptance contract

- **What was missing:** No general public rule was found for complete README sections, runnable documented commands, offline tests, all-dependency pinning, or documenting shard-key choices. Existing quickstarts exemplify pieces but are not the gallery contract.
- **Where the agent looked:** Learn searches for Azure DocumentDB gallery/sample guidelines, README, offline tests, dependency pinning and shard-key explanations; relevant connection, driver, modeling, indexing and deployment skills.
- **Effect on this build:** README, tests and pins were delivered through builder choices; shard-key guidance was unnecessary. End-to-end documented commands and Node 22 remain unverified. Similar prompts do not reliably produce these artifacts.
- **Suggested fix (agent_kit_rule):** Ship 'Azure DocumentDB Gallery Sample Contract': require the five README sections, secret-free complete config examples, exact tested dependencies/lockfiles and runtime, offline tests, optional live verification, cleanup scope, shard-key rationale when applicable, and explicit verification limitations.

## [high] Driver tested compatibility baseline

- **What was missing:** No public pinned mongodb 6.22.0/Node 22/LlamaIndex/DiskANN compatibility baseline was found. Wire compatibility, npm existence and ping success answer different questions.
- **Where the agent looked:** Learn supported-driver/version searches; FAQ, compatibility table, Node and ORM quickstarts; documentdb-driver; package declarations and events.jsonl.
- **Effect on this build:** Package compatibility was investigated and offline tests passed on Node 26, but target runtime and live vector support remain unassessed. The lockfile also embeds an unlogged package mirror.
- **Suggested fix (sample_or_quickstart):** Publish 'Tested JavaScript Agent Dependency Matrix' with runtime patch versions, exact driver/framework/provider pins, lockfile/registry portability, auth modes, and managed-cluster ingestion/vector tests. Link it from driver and vector skills.

## [high] Connection settings discoverability and consistency

- **What was missing:** Complete connection configuration lives in a specialist skill; driver/security examples set retryWrites=true while connection/deployment guidance asserts false and some current Learn pages make false conditional.
- **Where the agent looked:** Loaded connection, driver-singleton and TLS resources; fetched current vector/LlamaIndex/reliability guidance and searched ORM retry explanations.
- **Effect on this build:** D010 deliberately avoided conflicting true examples and used safe CLI defaults, but the reason could be misread as a universal unsupported-write-retry claim.
- **Suggested fix (discoverability):** Create a canonical 'Azure DocumentDB Node.js Connection and Retry Contract', linked from every skill: separate sample settings, verified deployment capabilities, driver-managed reads/writes and application replay; remove contradictory universal claims and examples.

## [high] Replay safe bulk ingestion

- **What was missing:** Batch limits are public, but no complete service-specific recommendation for bounded batch payload/concurrency, partial results and replay-safe retries was found. P18 comes from MongoDB training rather than an Azure DocumentDB source.
- **Where the agent looked:** Discovery bulkWrite/bounded-concurrency searches; audit bulk-load searches; max-document-size, compatibility table and reliability page; connection skill.
- **Effect on this build:** 500-operation/1 MiB sequential batches were defensible disclosed defaults, but database writes stop on transient errors and depend on manual reruns. The checklist's batching recommendation is not explicitly published.
- **Suggested fix (agent_kit_rule):** Add 'Bounded Node.js Ingestion': stable-ID replacements, byte/operation limits, bounded concurrency, classified transient retries with bounded backoff/jitter, partial/ambiguous outcome handling, and tests. Explain collection.bulkWrite's update/insert commands versus the unsupported server bulkWrite command; reject RU-based Cosmos bulk advice.

## [high] Vector representation and embedding space

- **What was missing:** The hidden binary-vector requirement conflicts with numeric-array examples and the public number[] contract. P05's finite-value validation and P06's complete model/version/input-template migration contract remain training-only; their MongoDB/Cosmos-derived assumptions cannot be graded as service rules.
- **Where the agent looked:** Fetched vector-search and query-knowledge-base; loaded vector normalization and index creation resources; discovery finite-value and same-space searches.
- **Effect on this build:** The builder stores normalized finite 1536-element arrays and model metadata, which matches public examples, but reuses embeddings without an input-template fingerprint. The binary reference was not met.
- **Suggested fix (learn_doc):** Publish 'Azure DocumentDB Embedding Storage and Migration Contract': supported BSON representations by algorithm/version, driver serialization examples, finite/zero/dimension validation, model revision/input-template/normalization fingerprints, safe backfill and index replacement. Reconcile the reference before prescribing binary vectors.

## [high] Catalog sizing and vector evaluation

- **What was missing:** Documented parameter ranges/defaults exist, but the skill does not require a README larger-catalog tuning procedure or supply a reproducible recall/build-cost/latency evaluation harness.
- **Where the agent looked:** Vector skill/index and query resources, vector-search guide, app tests and verify script; readiness target-cluster gaps.
- **Effect on this build:** The app chooses documented 32/50/40 defaults for 120 vectors, but suitability beyond that catalog and P07/P27 measurement clauses remain unassessed.
- **Suggested fix (agent_kit_rule):** Require vector samples to disclose vector count versus transaction count, default rationale and tuning code locations. Provide an exact-search baseline and sweeps for maxDegree/lBuild/lSearch, measuring recall, build resources and latency; explain required cluster capabilities and safe index rebuilding.

## [high] Retail recommendation schema and ranking

- **What was missing:** P08/P09/P20 are general or MongoDB training-only: no public canonical product/order vector schema, complete co-purchase pipeline, or semantic/complement/session blending contract was found.
- **Where the agent looked:** Discovery retail canonical-vector, co-purchase sequence and candidate reranking searches; data-modeling resources and native vector guide.
- **Effect on this build:** D006/D009 selected synthetic distributions and ranking weights; code is coherent, but service documentation does not validate those choices or define recommendation quality.
- **Suggested fix (sample_or_quickstart):** Ship 'Retail Recommendations with Azure DocumentDB and LlamaIndex.TS': separate canonical products/orders, bounded baskets, distinct-order co-purchase counts, indexed early match, candidate union and exclusion, illustrative weights, substitute-versus-complement examples and two-turn personalization evaluation.

## [high] JavaScript memory and grounding contract

- **What was missing:** P22/P25 remain general training-only beliefs. No complete compatible JavaScript memory lifecycle, ownership/isolation/expiry policy or untrusted-database-text explanation contract was found.
- **Where the agent looked:** Readiness JavaScript/session searches; discovery session retention and recommendation grounding searches; LlamaIndex how-to and installed package declarations in the trace.
- **Effect on this build:** The builder resolved APIs through dependency inspection and several failed tests. Sessions are bounded but lack idle expiry; offline tests do not fully assert chat-history content or factual explanation accuracy.
- **Suggested fix (sample_or_quickstart):** Provide a pinned LlamaIndex.TS agent-memory example with explicit session ownership, token/history/session limits, eviction/expiry/reset, failed-turn semantics, actual chatHistory assertions, evidence-grounded output and prompt-injection/factuality tests.

## [high] Existing cluster readiness visibility

- **What was missing:** The audit cannot establish target tier/capacity, index permissions, identity scope or firewall/private-network configuration from data-plane ping/read access. These are tooling/evidence gaps, not proof that documentation is absent.
- **Where the agent looked:** README prerequisites, readiness inventory, decisions and events; vector/search/security/deployment guidance.
- **Effect on this build:** P04/P17 and live command execution remain unassessed; no managed-cluster vector/model acceptance run occurred.
- **Suggested fix (mcp_tool_or_description):** Supply a read-only 'verify_sample_prerequisites' tool accepting an authorized resource ID/profile, returning tier, feature capability, server version, network posture and nonsecret permission checks; distinguish application identity from MCP identity and never export credentials. Provide an opt-in integration test with explicit mutation approval.

## [high] Authentication choice and privilege guidance

- **What was missing:** The conditional authentication recommendation was found only by name in security guidance; the local CLI default and separate ingestion/runtime privilege contract are not prominent in the Node agent path.
- **Where the agent looked:** security-entra-rbac, current Node authentication pages, secondary-users custom roles, D004 and README prerequisites.
- **Effect on this build:** Native simplicity is logged but not clearly explained in README; one identity is required to read/write and create indexes.
- **Suggested fix (discoverability):** Add a Node-agent auth decision table: local evaluation versus Azure hosting, Entra preference and exceptions, dedicated native users, separate read-only runtime and index-management identities, preview role limitations and narrowly scoped OIDC allowedHosts examples.

## [high] Service naming and immutable identifiers

- **What was missing:** No public blanket ban on former/neighbour names was found; official pages themselves use negative disambiguation and preserve cosmos-containing endpoints. Modeling skill resources still lead with former service naming.
- **Where the agent looked:** overview#naming-and-history, at-a-glance naming guidance, data-modeling resources and README.
- **Effect on this build:** The literal reference/checklist naming ban is not met, but README correctly distinguishes the services. This is a contract ambiguity rather than actual app misidentification.
- **Suggested fix (agent_kit_rule):** Ship a naming rule: use Azure DocumentDB for the managed service; explicitly distinguish Amazon, RU Cosmos and open-source DocumentDB; allow negative disambiguation, existing endpoint domains and immutable SDK/API names. Rename stale skill prose and label historical sources.

## [high] Current management commands and APIs

- **What was missing:** Readiness Q02/Q03 retained legacy cosmosdb-preview/cosmosdb command names and older deployment APIs; deployment skill examples lag current quickstarts.
- **Where the agent looked:** Supplied readiness findings; documentdb-azure-deployment; current Bicep quickstart and readiness CLI links.
- **Effect on this build:** No IaC or management mutations were produced, so there was no direct runtime effect. A future deployment addition could use obsolete commands/defaults.
- **Suggested fix (naming_or_disambiguation):** Update deployment skill/templates to current quickstart versions and az documentdb extension commands; add a legacy-command/flag migration table and explain that persistent Microsoft.DocumentDB resource namespace does not imply Cosmos DB RU.

## [high] Operator specific compatibility guidance

- **What was missing:** Readiness Q09/Q10/Q12 carried older MongoDB/legacy-vCore assumptions about $search.text, transaction scope, version ceiling and universal change-stream preview enablement. Skills also overgeneralize Atlas exclusions and lexical mechanisms.
- **Where the agent looked:** Supplied readiness sources: compatibility-query-language, full-text overview/hybrid, Atlas comparison and change-streams; indexing skill and vector kNN resource.
- **Effect on this build:** The implemented native vector/co-purchase path avoids these issues. Future lexical, transaction or change-stream extensions risk unnecessary workarounds or invalid enablement changes.
- **Suggested fix (discoverability):** Provide current feature/version prerequisite tables and tested operator shapes. Distinguish GA $text from preview BM25/createSearchIndexes, ordinary versus multishard change streams, and supported transactions. Reconcile compatibility tables with preview pages and remove blanket syntax exclusions.

## [medium] Complete examples discoverability

- **What was missing:** The all-variable .env.example pattern was found only by name in the MCP Toolkit configuration reference, not during open application guidance discovery.
- **Where the agent looked:** Learn searches for Azure DocumentDB .env.example; fetched mcp-toolkit#configuration-reference.
- **Effect on this build:** The builder supplied both required settings anyway; other sample builders may omit an example or assume .env is automatically loaded.
- **Suggested fix (discoverability):** Link the configuration-example contract from Node quickstarts and connection skill. State that every required setting needs a placeholder and that environment-file loading behavior must be explicit.

## [medium] Safe startup errors

- **What was missing:** P15's complete startup configuration/ping/error-classification contract is carried over from MongoDB training; public sources provide pieces but not the complete redacted taxonomy.
- **Where the agent looked:** Discovery URI/ping/serverSelectionTimeoutMS searches; connection skill, configuration code and Node troubleshooting guidance.
- **Effect on this build:** Missing/malformed configuration errors are clear, but auth and connectivity failures are combined into one message.
- **Suggested fix (agent_kit_rule):** Add a startup-validation rule distinguishing missing config, parser failure, auth rejection, DNS/network/TLS and server-selection timeout using safe names/codes, never raw URIs or provider errors; include offline fixtures.

## [medium] Access pattern guidance entry points

- **What was missing:** General access-pattern modeling and complete query-index coverage were found only after name-directed skill/page inspection; open discovery retained narrower canonical-retail and multikey practices.
- **Where the agent looked:** model-embed-vs-reference and how-to-create-indexes#queryable-fields-should-always-have-indexes-created.
- **Effect on this build:** Main recommendation paths are indexed, but namespace/model guards scan collections. The small sample works while scaling costs are undisclosed.
- **Suggested fix (discoverability):** Link modeling and query-index inventory rules from the Node/vector quickstarts and gallery entry point. Include preflight/maintenance queries, intentional bounded scans, explain verification and avoidance of speculative indexes.

## [medium] IaC and cleanup discoverability

- **What was missing:** Correct resource type, parameterized defaults and scoped cleanup exist in deployment skills/quickstarts, but open app discovery did not retain these sample-delivery practices. No gallery rule triggers optional IaC when the prompt only asks for an app.
- **Where the agent looked:** documentdb-azure-deployment and Bicep/Prisma quickstarts; app inventory and README.
- **Effect on this build:** No IaC or tier/storage/region parameters were supplied; cleanup was nevertheless documented safely.
- **Suggested fix (discoverability):** Link deployment and scoped cleanup from the gallery/vector-agent starter; require optional nonexecuted IaC or an explicit existing-cluster exemption. Provide inexpensive defaults compatible with the requested algorithm, cost approval and narrowly scoped teardown.

## [medium] Local image and DiskANN parity

- **What was missing:** Readiness Q11 recalled ghcr.io/microsoft/documentdb/documentdb-local rather than the canonical ghcr.io/documentdb/documentdb/documentdb-local. Local guidance does not establish pinned-image DiskANN parity.
- **Where the agent looked:** Supplied local-deployment skill/development-loop findings and readiness prerequisites.
- **Effect on this build:** The builder correctly did not use local CRUD/Docker availability as DiskANN proof; optional local integration tests remain unresolved.
- **Suggested fix (naming_or_disambiguation):** Prominently state the canonical image coordinate and MongoDB/PostgreSQL ports, warn against the obsolete coordinate, and publish a pinned-image feature matrix including DiskANN and local-only TLS exceptions.

## [medium] Approval and AI router diagnostics

- **What was missing:** D001's operator approval has no independently visible approval event. The AI best-practices router failed twice because no chat client was configured; D002 logs different error wording.
- **Where the agent looked:** decisions.jsonl:1–2 and events.jsonl:51,64,69; available tool inventory.
- **Effect on this build:** Database guidance remained reachable, but no AI-router guidance was supplied. Approval scope cannot be independently verified from the audit trace.
- **Suggested fix (mcp_tool_or_description):** Record immutable operator approval events with scope and mutation permissions. Add router preflight/capability diagnostics and preserve exact structured failures, distinguishing unavailable guidance from missing model configuration.

