# 1. Prompt review: retail-semantic-search

**Verdict: sufficient_with_assumptions**

The prompt is actionable: it specifies a Node.js LlamaIndex recommendation agent, DiskANN retrieval, session personalisation, and ingestion of 20,000 transactions. Installed skills cover database connection patterns and vector-index mechanics, but the builder must choose models, schemas, session-memory behaviour, and the app interface. The reference describes a materially different Python/IVF search app; those mismatches are recorded as risks, not counted against the verdict.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Definition of done, Constraints and non-goals |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 9: Language and runtime, Driver and version, Target service and tier, Authentication and secrets, Data model, Sample data, Queries and indexes, AI components, App surface |
| Missing: builder will guess | 3: Provisioning and deployment, Run and test instructions, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Python Flask app: directly conflicts with the requested Node.js LlamaIndex agent.
- Product titles and descriptions embedded with text-embedding-ada-002: neither the prompt nor a skill selects this model; vector examples use text-embedding-3-small.
- BSON binary vectors: the prompt does not specify the representation, and loaded vector examples store numeric arrays.
- vector-ivf index on the embedding field: directly conflicts with the requested DiskANN index.
- /search accepts natural language and returns 10 similar products: the prompt instead requires product-ID input and five recommendations, without an HTTP route.
- Connection string and model credentials exclusively from environment variables, with none committed: database-secret guidance is covered, but model-credential handling is not specified; the config-file wording also permits other interpretations.
- A .env.example lists every setting: the local skill supplies database/TLS examples, not a complete inventory of agent and model settings.
- Index parameters chosen for catalog size, with README guidance for larger catalogs: skills provide tuning guidance, but the catalog size and required README explanation are absent.
- /search reports clear errors for empty queries and embedding failures: only connection-string errors are requested, and the intended input is a product ID.
- Dependencies pinned in requirements.txt: incompatible with the requested Node.js runtime; no skill requires this Python artifact.
- Unit tests run without a live cluster: neither the prompt nor a skill requires mocked unit tests; local guidance concerns container integration tests.
- Cluster infrastructure provided as code using the Azure DocumentDB resource type: deployment guidance exists, but provisioning artifacts are not requested and may be omitted.
- README covers purpose, prerequisites, setup, run, and clean-up: neither the prompt nor a skill requires this complete README structure.
- Use Azure DocumentDB throughout, with no former or neighbouring product names: the prompt uses the correct name but does not require repository-wide consistency; loaded data-modeling resources still use former product terminology.

## Questions for the prompt author

- Should the deliverable expose a CLI, an HTTP API, or a web UI?
- Should embeddings represent product text, co-purchase relationships, or both, and how should those signals determine recommendation ranking?
- Which embedding/chat provider and models should be used?
- How is a session identified, what should memory retain, and must it survive application restarts?
- Are the 20,000 transactions synthetic orders with multiple items, individual purchase line items, or records from a supplied dataset?
- Should the sample include cluster infrastructure code, or only connect to an existing M30-or-higher cluster?

## Contradictions and missing references

- The reference requires Python Flask, text-embedding-ada-002, a vector-ivf index, and a natural-language /search endpoint returning 10 products. The starter instead requests Node.js LlamaIndex, DiskANN, and product-ID recommendations returning five items. This is a prompt/reference mismatch, not an internal blocker.
- documentdb-driver's singleton example sets retryWrites=true, while documentdb-connection and documentdb-azure-deployment explicitly require retryWrites=false. A builder following examples literally could inherit conflicting settings.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | Read co-purchase order history, generate product embeddings, and personalise recommendations per session. | - | - | Demonstrates database-backed product recommendations using purchase history and vector retrieval. |
| Workflow type | specified | no | Build a Node.js LlamaIndex agent using agent memory. | - | - | A single LlamaIndex agent is specified. No installed skill supplies LlamaIndex-specific integration or memory semantics. |
| Language and runtime | ambiguous | no | Node.js. | - | JavaScript on Node.js 22 LTS, with npm and the current compatible LlamaIndex release. | Language family is clear; runtime version and JavaScript versus TypeScript are not fixed. |
| Driver and version | ambiguous | no | Reads history from Azure DocumentDB. | - | Use the official mongodb Node.js driver, version 6.x, with one process-wide MongoClient. | documentdb-driver confirms MongoClient reuse, but neither it nor documentdb-connection pins a Node.js driver version. |
| Target service and tier | ambiguous | no | Azure DocumentDB with a DiskANN index. | - | Target an existing managed Azure DocumentDB M30 cluster; leave its region, storage, and HA unchanged. If provisioning files are added, use a single shard, 128 GiB storage, and ZoneRedundantPreferred HA, with region supplied by the user. | documentdb-vector-search states that DiskANN requires M30+. Remaining cluster choices are unspecified; deployment guidance requires user confirmation before provisioning. |
| Authentication and secrets | ambiguous | no | Use a config file for the connection string and clearly report missing or invalid values. | - | Use an uncommitted .env configuration file with DOCUMENTDB_URI and OPENAI_API_KEY; authenticate with SCRAM-SHA-256 over TLS, with retryWrites=false. | Connection skills supply native-authentication settings. local-env-driven-config requires environment-driven secrets and a committed .env.example; treating .env as the config file reconciles this with the prompt. |
| Data model | ambiguous | no | Co-purchase order history, products, embeddings, and session memory. | - | Use a retail database with products and orders collections. Products contain IDs, titles, descriptions, numeric embedding arrays, and model metadata; orders contain bounded item arrays referencing product IDs. Keep session memory in a process-local map keyed by sessionId; use one unsharded collection per entity. | Data-modeling skills provide embed/reference principles, not a retail schema or a session-memory persistence policy. |
| Sample data | ambiguous | no | Include a script to ingest 20,000 product purchase transactions. | - | Generate 20,000 synthetic order documents containing multiple product IDs, plus a small synthetic catalog. Use deterministic IDs and upserts so ingestion can be repeated without duplicates. | Source, license, catalog size, and whether a transaction means an order or a line item are unspecified. The local-deployment skill calls for version-controlled, idempotent seed scripts. |
| Queries and indexes | ambiguous | no | DiskANN index; accept a product ID and return the top 5 recommended items. | - | Look up the input product, retrieve vector candidates using $search/cosmosSearch, exclude the input item, and rerank using co-purchase counts and session context. Use COS similarity, maxDegree=32, lBuild=50, lSearch=40, and dimensions matching the model; add an orders.items.productId multikey index. | documentdb-vector-search supplies DiskANN creation and query parameters. It does not settle how purchase history, semantic similarity, and personalisation combine into the final ranking. |
| AI components | ambiguous | no | Generate product embeddings and use agent memory to personalise recommendations with reasoning. | - | Use OpenAI text-embedding-3-small with 1536 dimensions and gpt-4o-mini for agent decisions and explanations. Embed product title/description plus co-purchase context during ingestion; retain recent interactions in per-session in-memory history until process restart. | Vector-skill examples suggest the embedding model but do not mandate it. No installed skill selects the provider, chat model, embedding input, memory limits, or LlamaIndex APIs. |
| App surface | ambiguous | no | Accept a product ID and return the top 5 recommended items with reasoning. | - | Provide a CLI accepting productId and an optional sessionId, with an interactive loop for repeated recommendations. Return JSON containing five product IDs, titles, similarity scores, and explanations; provide a separate npm ingestion command. | CLI, HTTP API, and web UI are all plausible. Session identification and unknown-product behaviour are not defined. |
| Provisioning and deployment | missing | no | - | - | Require a user-provided existing Azure DocumentDB connection string; run locally and do not create cloud resources or include infrastructure code. | documentdb-azure-deployment supplies Bicep and CLI procedures if provisioning is requested, but the prompt does not request provisioning or authorize resource creation. |
| Run and test instructions | missing | no | - | - | Document npm install, configuration setup, npm run ingest, and npm start. Verify a seeded product returns five recommendations and configuration failures produce readable errors; omit automated tests unless independently added. | The local-deployment skill describes container integration tests, but no skill establishes this agent's run commands or required unit tests. |
| Definition of done | specified | no | Ingest 20,000 transactions; return top 5 items with reasoning; personalise per session; clearly report missing or invalid connection strings. | - | - | These are checkable acceptance criteria. Recommendation-quality thresholds and restart persistence are not required. |
| Constraints and non-goals | specified | no | Keep code simple and readable; add detailed comments before each method. | - | - | Readability constraints are explicit. No spending ceiling, compliance target, or production-hardening requirement is stated. |
| Repository conventions | missing | no | - | - | Use package.json, package-lock.json, src/, scripts/, README.md, .env.example, and .gitignore. Include basic setup/run documentation and no telemetry. | The local-deployment skill covers configuration examples and seed/schema organization, but not complete gallery README, naming, attribution, or dependency-pinning conventions. |
