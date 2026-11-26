# 1. Prompt review: retail-semantic-search

**Verdict: sufficient_with_assumptions**

The prompt is enough to start a Node.js LlamaIndex recommendation agent, and installed skills cover DocumentDB connection reuse and DiskANN mechanics. Models, co-purchase ranking, session memory, app interface, and testing remain builder choices. The hidden reference describes a materially different Python/IVF search app; those mismatches are risks, not blockers for this build.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Definition of done, Constraints and non-goals |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 10: Workflow type, Language and runtime, Driver and version, Target service and tier, Authentication and secrets, Data model, Sample data, Queries and indexes, AI components, App surface |
| Missing: builder will guess | 3: Provisioning and deployment, Run and test instructions, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Python Flask app: explicitly displaced by the Node.js LlamaIndex requirement.
- Embed product titles/descriptions with text-embedding-ada-002: embedding inputs and exact model are not specified; vector skill examples use another model.
- Store embeddings as BSON binary vectors: prompt does not specify representation; skill examples store numeric arrays.
- Create a vector-ivf index: prompt explicitly requests DiskANN.
- Provide /search accepting a natural-language query and returning 10 products: prompt instead specifies product-ID input and 5 recommendations; no route is required.
- Read connection string and model credentials from environment variables, with none in the repository: prompt requests a connection config file and says nothing about model secrets; skills do not guarantee the environment-variable contract.
- Provide .env.example listing every setting: neither prompt nor relevant skills require this artifact.
- Choose index parameters for catalog size and document larger-catalog tuning in README: skills provide parameter guidance, but catalog size is unknown and README tuning instructions are not required.
- Provide a seed script that loads products, creates the index and is safe to run twice: ingestion and index creation are likely, but idempotency is not required or covered by the loaded skills.
- Return clear /search errors for an empty query and embedding-call failure: no /search route exists in the prompt, and only connection-string errors are requested.
- Pin dependencies in requirements.txt: Node.js implementation will use package.json instead; dependency pinning is not requested.
- Provide unit tests that run without a live cluster: neither prompt nor relevant skills requires offline unit tests.
- Provide cluster infrastructure as code using the Azure DocumentDB resource type: deployment skill knows the correct resource type, but the prompt does not trigger infrastructure delivery.
- README covers demonstration, prerequisites, setup, run and cleanup: some setup instructions are likely, but the full section set and cleanup are not required.
- Use Azure DocumentDB throughout, without former or neighbouring product names: prompt uses the correct name, but does not impose repository-wide naming; data-modeling resources contain former naming.

## Questions for the prompt author

- Should recommendations primarily rank products frequently bought together, semantically similar products, or a defined blend of both?
- Which embedding/chat provider and models should be used, and should embeddings encode product descriptions, co-purchase history, or both?
- Should this be a CLI or an API/web app, and must session memory survive process restarts?
- Should the sample include cluster infrastructure as code, or assume an existing M30+ cluster?
- Is the supplied Python/IVF /search reference intended for this sample, or is the Node.js/DiskANN agent prompt authoritative?

## Contradictions and missing references

- The hidden reference requires Python Flask, while the starter explicitly requires Node.js LlamaIndex. This is a reference mismatch, not an internal blocker.
- The hidden reference requires vector-ivf and natural-language /search returning 10 products; the starter requires DiskANN and product-ID recommendations returning 5 items with reasoning.
- The hidden reference requires environment-variable connection configuration; the starter requests a connection-string config file. A file that reads environment variables could satisfy both, but the prompt does not require that interpretation.
- Installed skill examples disagree on retryable writes: driver-singleton-client.md uses retryWrites=true, while documentdb-azure-deployment explicitly says to use retryWrites=false.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | Personalise product recommendations using co-purchase order history; return the top 5 items with reasoning. | - | - | Clearly identifies the recommendation scenario and database-backed vector retrieval. |
| Workflow type | ambiguous | no | “a Node.js LlamaIndex agent” using “agent memory” per session. | - | One LlamaIndex tool-calling agent with a recommendation retrieval tool and in-process conversation memory keyed by session ID; memory disappears on restart. | Framework and single-agent intent are clear; memory lifecycle and how it changes recommendations are not covered by installed skills. |
| Language and runtime | ambiguous | no | “Node.js” | - | JavaScript ES modules on Node.js 22 LTS, using a compatible current LlamaIndex release. | No runtime version or JavaScript-versus-TypeScript choice. |
| Driver and version | ambiguous | no | - | documentdb-driver; documentdb-connection | Use the official mongodb Node.js driver, version range ^6.0.0, with a process-wide MongoClient and retryWrites=false. | Skills establish MongoClient reuse, not a package version. The driver's example sets retryWrites=true, whereas the deployment skill explicitly requires false. |
| Target service and tier | ambiguous | no | “Azure DocumentDB” and “DiskANN index” | documentdb-vector-search; documentdb-azure-deployment | Connect to an existing managed Azure DocumentDB cluster supporting DiskANN, at least M30; leave its region, storage and HA unchanged. | Vector skill confirms DiskANN requires M30+. Other topology settings are unspecified. “Azure DocumentDB skill” clearly matches the installed domain skills; no exact umbrella skill is required. |
| Authentication and secrets | ambiguous | no | “Use a config file for the Azure DocumentDB connection string” and clearly report missing or invalid strings. | documentdb-connection | Use SCRAM-SHA-256 credentials in a gitignored config.json connection string with TLS and retryWrites=false; read model credentials from OPENAI_API_KEY. | Connection skill supplies native authentication and TLS. Config format, repository exclusion and AI credential handling are not settled. |
| Data model | ambiguous | no | Co-purchase order history, products, product embeddings and per-session memory. | documentdb-data-modeling; documentdb-vector-search | Use retail.products with product ID, title, description, category, numeric embedding array and model metadata; retail.orders with order ID and embedded item IDs/quantities. Keep memory in process and collections unsharded. | Skills guide bounded order-item embedding and vector metadata, but do not define this application's schema or relationship between purchases and embeddings. |
| Sample data | ambiguous | no | “a script to ingest 20,000 product purchase transactions” | - | Generate 20,000 synthetic order documents over a small synthetic catalog, with several items per order and category-based co-purchase patterns; insert in batches without an external dataset. | Count and ingestion script are specified. Transaction granularity, catalog size, source, licence and repeat-run behavior are not. |
| Queries and indexes | ambiguous | no | Read co-purchase history, store product embeddings in DiskANN, and return top 5 recommendations for a product ID. | documentdb-vector-search; documentdb-data-modeling | Create embedding:cosmosSearch with kind=vector-diskann, COS similarity, maxDegree=32, lBuild=50 and dimensions matching the model. Query with $search/cosmosSearch, lSearch=40 and k=20, exclude the input product, rerank using co-purchase counts and session preferences, then return 5. Add an orders.items.productId index. | Skill confirms DiskANN and query syntax. Co-purchase aggregation, ranking weights, exclusions and candidate count remain guesses; embeddings are stored on documents, with the index built over the field. |
| AI components | ambiguous | no | Generate product embeddings and use a LlamaIndex agent to provide reasoning and personalisation. | documentdb-vector-search | Use OpenAI text-embedding-3-small at 1536 dimensions on product titles/descriptions during ingestion, and gpt-4o-mini for tool calling and explanations during recommendation requests. | Vector examples use text-embedding-3-small but do not mandate it. No installed skill selects the provider, chat model, embedding content or LlamaIndex integration. |
| App surface | ambiguous | no | “accept a product ID and return the top 5 recommended items with reasoning” | - | Provide an interactive CLI accepting product IDs, keeping one session per CLI process, and printing five product IDs/titles with scores and explanations; use npm run ingest for loading data. | Input and main output are clear; CLI versus API/UI and session identification are not. |
| Provisioning and deployment | missing | no | - | - | Require a pre-existing cluster and run the agent locally; do not create Azure resources or include infrastructure files. | documentdb-azure-deployment provides deployment procedures, but does not establish that this connection-string-based sample must include or execute provisioning. |
| Run and test instructions | missing | no | - | - | Document npm install, configuration, npm run ingest and npm start; manually smoke-test one known product and missing/invalid connection strings. No automated test suite. | No skill supplies application-level run commands, offline tests or a test requirement. |
| Definition of done | specified | no | Ingest 20,000 transactions; generate and index embeddings; recommend 5 items with reasoning; personalise per session; clearly report missing/invalid connection strings. | - | - | These are checkable functional outcomes. No recommendation-quality threshold or measurable personalisation criterion is supplied. |
| Constraints and non-goals | specified | no | “Keep the code as simple and readable as possible” and “detailed comments before each method”. | - | - | Explicit readability constraints are actionable. No special compliance, licence or cost restriction is stated. |
| Repository conventions | missing | no | - | - | Use package.json, src/, scripts/ingest.js, config.example.json, a gitignored config.json and a short README with setup/run guidance; no telemetry, attribution or cleanup conventions. | No gallery-specific repository skill is installed. Some data-modeling resources use former service naming, so consistent public-facing naming is not guaranteed. |
