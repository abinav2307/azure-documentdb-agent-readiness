# Documentation and tooling gaps: retail-semantic-search

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Gallery sample acceptance contract

- **What was missing:** No located gallery-wide rule requires a complete README, verified README commands, offline tests, all dependency pins, optional infrastructure, or documented shard-key rationale. These are listed_not_found checklist expectations. The deployment skill explains how to provision but does not require infrastructure files for existing-cluster samples.
- **Where the agent looked:** Targeted Learn searches for Azure DocumentDB sample README/test/pinning/shard-rationale policies; driver, vector, local and deployment skills and resources.
- **Effect on this build:** The builder supplied README/tests/pins by author choice but omitted infrastructure. README commands were not verified end-to-end. The catalog is unsharded, so the rationale omission does not affect it.
- **Suggested fix (agent_kit_rule):** Ship 'Publishable Azure DocumentDB gallery samples': require demonstration/prerequisite/setup/run/cleanup sections; a complete configuration inventory; exact direct dependency pins and tested runtimes; offline tests plus separately authorized live acceptance; optional parameterized mongoClusters infrastructure even for existing-cluster apps; and shard-key rationale when sharded. Distinguish file generation from permission to deploy.

## [high] BSON vector encoding and validation

- **What was missing:** The reference requires BSON binary vectors, but vector skills and public examples use numeric lists. The vector page's number[] versus double[] warning lacks a precise PyMongo/BSON explanation. P45/P46 remain prior-knowledge-only for the complete finite-value and per-vector validation rules.
- **Where the agent looked:** Loaded vector-search and normalization/query resources; fetched Integrated vector store and Python vector-algorithm quickstart; reviewed supplied vector-encoding searches and readiness findings.
- **Effect on this build:** Binary storage was not implemented. Numeric-array indexing and top-10 managed retrieval were not tested, so changing encoding blindly could make the sample incompatible.
- **Suggested fix (learn_doc):** Ship 'Vector BSON representations supported by Azure DocumentDB': supported array element BSON types, Binary vector subtypes if supported, driver/version requirements, index-algorithm compatibility, query-vector representation, finite-value/dimension validation, and a Python encode/insert/search acceptance example. Correct or explicitly justify the double[] warning and align gallery requirements.

## [high] Connection and retry guidance conflicts

- **What was missing:** The connection skill enables retryWrites and shows managed port 10255; deployment guidance categorically denies retryable writes; the vector quickstart explicitly requires false. Generic reliability guidance calls for bounded exponential backoff without a consistent scenario-specific implementation.
- **Where the agent looked:** Loaded connection/driver/deployment skills; fetched vector quickstart and reliability page; inspected readiness Q04 and supplied authentication/migration conflicts.
- **Effect on this build:** Readiness correctly selected SRV and false, but the application has no bounded exponential-backoff handling for transient database errors. Agents copying another first-party example could choose incompatible settings.
- **Suggested fix (learn_doc):** Ship 'PyMongo connection and retry profiles for Azure DocumentDB': authoritative SRV/hostname/port guidance; a capability matrix for native/OIDC and vector/CRUD scenarios; driver retry versus application retry distinctions; safe idempotent write retries; deadlines, error classification and bounded backoff tests. Update all contradictory skill examples together.

## [high] Complete configuration inventories and .env hygiene

- **What was missing:** The full configuration-inventory convention was found only by name on the MCP Toolkit page; the local skill supplies .env/.gitignore guidance that open discovery missed for P33. The vector app skill does not collect database, Flask and embedding-provider settings into one contract.
- **Where the agent looked:** Targeted .env.example/every-setting searches; fetched MCP Toolkit configuration reference; loaded local-env-driven-config.
- **Effect on this build:** The builder happened to supply a complete safe example, but this depended on author defaults. The discovery classified the complete .env convention as prior knowledge despite an installed rule.
- **Suggested fix (discoverability):** Link 'Sample configuration and secrets' from Python/vector quickstarts and skill entry points. Require inventorying every consumed application setting, marking required/defaulted values, keeping secrets as placeholders, ignoring local .env files, and distinguishing app credentials from MCP profiles. Reuse the existing local rule rather than leaving it local-container-only.

## [high] Current search APIs and compatibility boundaries

- **What was missing:** Full-text and aggregation support were found only by name during reconciliation. Readiness Q09/Q10 retained community/legacy text syntax and an older compatibility snapshot; the indexing skill still recommends a textSearch key that the current BM25 overview rejects.
- **Where the agent looked:** Fetched full-text overview, MQL compatibility and vector pages; loaded indexing guidance; reviewed readiness Q09/Q10.
- **Effect on this build:** The vector-only pipeline uses the correct API. An optional hybrid extension could use the wrong index engine, score metadata, preview assumptions or feature exclusions.
- **Suggested fix (discoverability):** Prominently link a versioned 'Search and MongoDB compatibility map' from vector/indexing skills: BM25 createSearchIndexes, cosmosSearch vector indexes, gated-preview enrollment, current versus forthcoming operators, legacy $text migration, and verified wire versions/cross-shard capabilities. Remove the contradictory textSearch recommendation.

## [high] Current naming, CLI and local-image identities

- **What was missing:** Readiness Q02/Q11 retained old CLI branding and an obsolete registry organization. Correct naming guidance was found only by name. The literal reference ban also conflicts with useful explicit disambiguation.
- **Where the agent looked:** Naming/history search; readiness CLI reference and development-loop sources; loaded local and deployment skills.
- **Effect on this build:** The builder avoided wrong deployment commands and image references by omitting those workflows. README correctly distinguishes services, but fails the reference's literal no-neighbour-name wording.
- **Suggested fix (naming_or_disambiguation):** Ship 'Azure DocumentDB identity and migration naming': current service name, az documentdb/documentdb extension and CLI minimum, current gateway image, unchanged legacy API/hostname identifiers, and explicit distinctions from Amazon DocumentDB and Cosmos RU. Define acceptable disambiguation in gallery naming rules.

## [high] Native authorization scope and runtime identity separation

- **What was missing:** P35 contradicts MongoDB-derived database/collection-scoped native least-privilege assumptions. The limitations page states native role assignment is cluster-wide, while the security skill shows a database-scoped role example. D005 relies on a local SCRAM exception.
- **Where the agent looked:** Fetched limitations authentication section; loaded security-entra-rbac; inspected README and D005.
- **Effect on this build:** README suggests a read-only runtime user but omits cluster-wide scope. Actual runtime identity and permissions are not assessable; a user could reuse seeding/admin credentials.
- **Suggested fix (discoverability):** Ship a prominent 'Read-only runtime identities for catalog samples' section: native cluster-wide roles, supported Entra scopes, separate seed/runtime identity setup, local SCRAM exceptions and permission verification. Correct the database-scoped native role example.

## [high] Live acceptance and existing-cluster posture verification

- **What was missing:** No authorized target, embedding access or acceptance runner was supplied to verify index existence, README commands, relevance, firewall rules, runtime permissions or diagnostic eligibility. Existing MCP discovery does not supply app credentials.
- **Where the agent looked:** App/README verification sections; events.jsonl:95,104-114; readiness guidance and MCP Toolkit tool descriptions.
- **Effect on this build:** Offline tests passed, but index creation, vector encoding acceptance, scored top-10 results and existing-cluster security/monitoring posture remain unverified.
- **Suggested fix (mcp_tool_or_description):** Provide an opt-in 'sample acceptance' runner using an operator-selected disposable profile: prerequisite/access checks without exposing secrets; explicit write consent; seed-twice/index/readiness/endpoint checks; read-only role/network/tier diagnostics; scoped cleanup; and machine-readable results distinguishing offline from live evidence.

## [high] IVF catalog sizing and lifecycle semantics

- **What was missing:** Readiness S03 initially copied numLists=100 for 20 products; S05 treated seed-before-index as mandatory training order. Correct size guidance exists, but public examples differ in ordering and do not settle training/rebuild semantics.
- **Where the agent looked:** Fetched vector and algorithm quickstart pages; readiness S03/S05; D009/D010.
- **Effect on this build:** Corrections produced numLists=1 and a bounded search probe. The builder appropriately avoided claiming mandatory training semantics, but live lifecycle behavior remains unverified.
- **Suggested fix (discoverability):** Add an IVF-specific skill resource with tiny-catalog defaults, integer numLists selection, nProbes bounds and recall measurement. Explain whether index-before-data is supported, how clustering changes with ingestion, and when rebuilding is required. Include a scored readiness test rather than fixed sleeps or listIndexes-only acceptance.

## [medium] Driver pins and tested runtime matrix

- **What was missing:** The team expects a pinned supported driver, but no exact-version validation matrix was found. D004 chooses package versions and Python compatibility from model defaults; offline constructor tests do not establish managed-service support.
- **Where the agent looked:** Targeted supported/pinned PyMongo searches; driver skill; Python quickstart, vector quickstart and MQL compatibility page.
- **Effect on this build:** PyMongo 4.15.3 was pinned and tested offline on Python 3.14.10, while Python 3.11-3.13 and live cluster behavior remain unverified.
- **Suggested fix (learn_doc):** Ship 'Validated Python stacks for Azure DocumentDB samples': tested Python/PyMongo/provider-SDK combinations, authentication and vector coverage, minimum versus tested versions, dependency pin/update policy, and CI evidence. Avoid implying every broad wire-compatible version has been tested.

## [medium] Bounded data-model guidance

- **What was missing:** Explicit unbounded-array avoidance was found only through the named data-modeling resource, whose text still uses former vCore branding.
- **Where the agent looked:** Targeted bounded-array searches; documentdb-data-modeling and model-embed-vs-reference.
- **Effect on this build:** The app is bounded and correct, but open discovery found the document limit without exposing the complete growth rule. Former branding can encourage neighbouring-service assumptions.
- **Suggested fix (discoverability):** Add a bounded-growth section to Azure DocumentDB data-modeling Learn guidance and link it from product-catalog quickstarts. Update model resources to current naming; illustrate fixed embedding arrays and separately referenced unbounded children.

## [medium] Infrastructure and cleanup discovery from application prompts

- **What was missing:** Bicep resource-type guidance, parameterized dev settings and cleanup instructions were found only through targeted searches/loading deployment resources, not the open practice list. D015 treated existing-cluster scope as a reason to omit all infrastructure.
- **Where the agent looked:** Bicep/Terraform and cleanup searches; deployment skill Step 0.5 and canonical Bicep resource; Python vector quickstart cleanup.
- **Effect on this build:** Cleanup is documented, but optional infrastructure and tier/storage/region parameters are missing. Low-cost cluster values exist only as README prose.
- **Suggested fix (discoverability):** Link 'Optional infrastructure for application samples' from Flask/Python/vector entry points to a canonical parameterized mongoClusters template, explicit dev overrides, scoped firewall setup and safe dedicated-resource cleanup. State that templates may be shipped without deploying resources.

## [medium] Feature-state assumptions inherited from older releases

- **What was missing:** Readiness Q12 assumed a universal change-stream preview flag; Q10 assumed older compatibility exclusions. These are older-service-state beliefs, not demonstrated Amazon DocumentDB confusion.
- **Where the agent looked:** Supplied readiness findings grounded in change-stream, release-note and compatibility pages.
- **Effect on this build:** No change streams or cross-shard transactions were added, so the app avoided these errors. Future extensions could introduce unnecessary flags or workarounds.
- **Suggested fix (discoverability):** Add a dated feature-status table to skill entry points: generally available behavior, tier/version requirements and narrowly gated options such as multishard streams or pre-images. Link current release notes and prohibit inventing universal preview flags from historical guidance.

## [medium] Pool defaults versus mandatory explicit tuning

- **What was missing:** P29 contradicts the prior MongoDB-derived belief that every Flask app must explicitly set maxPoolSize and waitQueueTimeoutMS. The connection skill instead retains defaults absent workload justification and reserves queue tuning for relevant workloads.
- **Where the agent looked:** P29 source and loaded documentdb-connection context-first/default-pool sections.
- **Effect on this build:** The builder correctly retained defaults. Without prominent correction, agents may add arbitrary pool knobs and misleading performance claims.
- **Suggested fix (discoverability):** Place a 'Do not tune pools by template' callout in Python/Flask connection guidance: default pool behavior, workload/concurrency evidence required for overrides, queue-timeout scenarios and measurable validation criteria.

## [medium] Flask process lifecycle and diagnostic application names

- **What was missing:** P24/P30 carry MongoDB-derived fork-safety and appName beliefs without located Azure DocumentDB recommendations.
- **Where the agent looked:** Supplied site-specific fork/Gunicorn and appName searches; driver and connection skills; MCP configuration example.
- **Effect on this build:** Lazy client creation and a prefork warning are present; appName is not explicitly set. No production worker configuration is supplied, and neither practice was used to mark the app down.
- **Suggested fix (learn_doc):** Ship 'Flask and PyMongo lifecycle on Azure DocumentDB': whether upstream fork constraints apply, lazy per-worker initialization, shutdown behavior, safe prefork examples, and appName support/diagnostic value or an explicit statement that no service-specific requirement exists.

## [medium] Secret-safe error handling and bounded HTTP contracts

- **What was missing:** P34's complete redaction rule and D011's input limits/error contract come from model defaults rather than a service sample rule. Database-secret guidance does not cover all embedding-provider failure paths.
- **Where the agent looked:** Supplied redaction searches; app error handlers/tests; security/local configuration guidance.
- **Effect on this build:** Generic errors and input limits were implemented, but the tests do not directly inject an OpenAI failure. Other builders may leak provider exceptions or allow unbounded request spend.
- **Suggested fix (agent_kit_rule):** Add a Python API sample rule: validate empty/type/length/body limits before dependencies; use stable nonsecret dependency errors; never echo raw connection/provider exceptions; inject database and embedding failures in offline tests; disclose timeout/retry budgets. State which limits are sample choices, not database requirements.

## [medium] Embedding freshness, model separation and cache invariants

- **What was missing:** P41/P42/P47 remain prior-knowledge-only for source-change regeneration, model-space separation and deterministic input composition. D010/D016 choose text hashes and cached-vector reuse without a complete public sample contract.
- **Where the agent looked:** Supplied re-embedding/model-mixing/title-description searches; vector normalization resource; seed code and tests.
- **Effect on this build:** The builder implements deterministic text hashing and versioned reuse, but cached vectors are checked for validity rather than unit norm. There is no documented multiple-model migration layout.
- **Suggested fix (agent_kit_rule):** Extend vector sample guidance with deterministic source composition, source/model/dimension/normalization version metadata, re-embedding on source changes, model-space separation or an explicit applicability statement, and cache invariants. Provide rerun/change/migration tests without unnecessary re-normalization writes.

## [medium] Embedding provider selection and authentication exceptions

- **What was missing:** D005 selects public OpenAI rather than Azure OpenAI from an author default. Provider selection, credentials, data transfer and ada-002 availability are not specified by the starter prompt. First-party endpoint-switching and passwordless guidance could answer configuration differences but is not prominent in the vector skill.
- **Where the agent looked:** D005, README prerequisites, readiness provider findings and the recorded endpoint-switching source.
- **Effect on this build:** The provider choice is disclosed and plausible, but live model access is unverified and Azure OpenAI cannot be substituted by changing only the key.
- **Suggested fix (discoverability):** Link 'Choose an embedding provider for Azure DocumentDB samples' from the vector skill: public versus Azure endpoints, model versus deployment names, environment inventories, Entra/API-key choices, access/billing checks and data-transfer disclosure. Ask for provider choice or label the assumption explicitly.

## [low] Illustrative prices versus monetary accounting

- **What was missing:** P39 carries a MongoDB-derived integer-minor-unit/Decimal128 recommendation; no Azure DocumentDB monetary-modeling recommendation was located.
- **Where the agent looked:** Supplied monetary/Decimal128 searches; data-modeling skill; synthetic product data and D007.
- **Effect on this build:** Prices are floating-point display examples, explicitly not accounting. The app was not marked down against an unsupported service-specific standard.
- **Suggested fix (learn_doc):** Add a retail data-model note distinguishing illustrative display prices from accounting values; document supported decimal BSON types, serialization considerations and recommended monetary representations, or state that upstream application-domain guidance applies.

