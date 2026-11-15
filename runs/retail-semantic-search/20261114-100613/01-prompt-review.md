# 1. Prompt review: retail-semantic-search

**Verdict: sufficient_with_assumptions**

The prompt defines a workable Flask semantic-search sample, and installed skills cover DocumentDB query syntax, client reuse, and reproducible seed practices. The builder must still choose runtime versions, embedding provider, catalog data, API details, and deployment scope; the requested BSON binary vector representation is not explained or confirmed by the loaded vector-search guidance.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Workflow type, Definition of done |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 9: Language and runtime, Driver and version, Target service and tier, Authentication and secrets, Data model, Queries and indexes, AI components, App surface, Provisioning and deployment |
| Missing: builder will guess | 4: Sample data, Run and test instructions, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Model credentials from environment variables with none committed: database secrets are covered, but no loaded skill establishes the model credential contract.
- A .env.example listing every setting: the skill supplies database settings, not a complete inventory including model configuration.
- Catalog-sized vector parameters and README guidance for larger catalogs: the skill gives IVF scale guidance but no numLists sizing recipe or required README explanation.
- Clear errors for empty queries and embedding-call failures: neither the prompt nor loaded skills specifies endpoint error handling.
- Pinned dependencies in requirements.txt: no prompt or loaded skill requires Python dependency pinning.
- Unit tests without a live cluster: local guidance covers real-container integration tests, not mocked Flask and embedding tests.
- Cluster infrastructure as code using the Azure DocumentDB resource type: the deployment skill provides the correct implementation, but the prompt does not request provisioning and the builder may omit it.
- README covering purpose, prerequisites, setup, run, and clean-up: neither the prompt nor loaded skills requires this complete documentation set.

## Questions for the prompt author

- Should embeddings use the OpenAI API or an Azure OpenAI deployment?
- Which BSON binary vector subtype and numeric encoding are required? The loaded vector-search skill does not document this storage representation.
- Should the sample include cluster infrastructure as code, or target an existing cluster only? If provisioning is included, is it dev/test or production, and may the builder create cloud resources?

## Contradictions and missing references

- Installed connection guidance conflicts: documentdb-azure-deployment says retryable writes are unsupported and sets retryWrites=false, while documentdb-connection says they are supported and recommends retryWrites=true. This needs source verification before choosing the connection configuration.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | Build a product catalog with natural-language search returning semantically similar products. | - | - | Clearly demonstrates database-backed semantic product retrieval. No exact umbrella skill named 'Azure DocumentDB' is installed, but the DocumentDB skill suite clearly matches the reference. |
| Workflow type | specified | no | The endpoint embeds a query and retrieves similar products. | - | - | A direct, no-agent request pipeline; no agent framework is needed. |
| Language and runtime | ambiguous | no | Python Flask app. | - | Python 3.12 with Flask 3.1.x. | Language and framework are fixed; runtime and framework versions are not. |
| Driver and version | ambiguous | no | - | documentdb-driver; documentdb-connection; documentdb-local-deployment | Synchronous PyMongo 4.x, with one module-level MongoClient shared across requests. | Skills establish PyMongo usage and client reuse, but do not prescribe a version for synchronous Flask. Retry-write guidance conflicts across skills. |
| Target service and tier | ambiguous | no | Azure DocumentDB; product catalog stored in DocumentDB. | documentdb-vector-search; documentdb-azure-deployment | Connect to an existing managed Azure DocumentDB cluster through DOCUMENTDB_URI; document M10 as sufficient for a small IVF catalog, without fixing its region, storage, or HA. | Service identity is clear. Vector guidance gives an M10+ floor for IVF; deployment guidance requires a dev/production choice rather than settling the topology. |
| Authentication and secrets | ambiguous | no | - | documentdb-local-deployment; documentdb-connection; documentdb-security | Use native SCRAM-SHA-256 credentials in DOCUMENTDB_URI and an OPENAI_API_KEY environment variable; keep .env uncommitted. | Environment-driven database configuration is covered. Native versus Entra authentication and model credential configuration remain choices. |
| Data model | ambiguous | no | Products have titles, descriptions, and embeddings stored as BSON binary vectors. | documentdb-data-modeling; documentdb-vector-search | Use retail.products with one document per product: stable _id, title, description, embedding, embeddingModel, and embeddingDims; no sharding. Encode float32 bytes with bson.binary.Binary, potentially using its default subtype 0. | Skills cover modeling principles and embedding metadata, not the required binary subtype, encoding, or compatibility with IVF indexing. |
| Sample data | missing | no | - | documentdb-local-deployment | Create roughly 20 synthetic retail products in a checked-in JSON file, loaded by an idempotent seed script using stable IDs and upserts; no external dataset licence. | The local-deployment skill covers version-controlled, idempotent seed scripts, but not this catalog's source, size, or licence. |
| Queries and indexes | ambiguous | no | Create a vector-ivf index; return the top 10 semantically similar products. | documentdb-vector-search | Index embedding as cosmosSearch with kind vector-ivf, dimensions 1536, similarity COS, and numLists 1 for the small seed catalog; query with $search/cosmosSearch and k=10, projecting searchScore. | Skills confirm IVF and query syntax, but do not provide small-catalog numLists sizing or binary-vector indexing instructions. ANN retrieval is shown; exact top-10 recall is not guaranteed by the guidance. |
| AI components | ambiguous | no | Embed product titles and descriptions using text-embedding-ada-002; embed each search query. | documentdb-vector-search | Use the OpenAI API with text-embedding-ada-002 and 1536-dimensional output; concatenate title and description into one embedding input during seeding and embed queries synchronously in /search. | The skill requires dimension consistency but does not establish this model's output dimensions or provider. Its examples use other models; they do not contradict the requested model. |
| App surface | ambiguous | no | /search takes a natural language query and returns the top 10 products. | - | Expose POST /search accepting JSON {"query":"..."} and returning a JSON list of up to 10 products with scores; no browser UI. | HTTP method, input field, response envelope, validation, and failure responses are unspecified. |
| Provisioning and deployment | ambiguous | no | Build an app with its catalog stored in DocumentDB. | documentdb-azure-deployment | Generate application code for an existing cluster and run Flask locally; do not create cloud resources or include cluster IaC unless requested. | The deployment skill supplies Bicep and confirmation steps if provisioning is requested. The prompt does not establish that provisioning is part of this build. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | Document virtualenv setup, pip install -r requirements.txt, environment setup, python seed.py, flask --app app run, and a curl search example; add no required mocked unit-test suite. | The skill describes container integration testing, not Flask commands or unit tests that run without a live cluster. |
| Definition of done | specified | no | Flask app, stored products and embeddings, vector-ivf index, and a query endpoint returning 10 similar products. | - | - | The requested functional outcome is checkable. Gallery-level quality gates are not stated. |
| Constraints and non-goals | missing | no | - | - | Treat this as a small development demo with no budget cap or compliance requirements; omit chat generation, agents, checkout, and production application authentication. | No cost, licence, or production-readiness constraints are supplied. |
| Repository conventions | missing | no | - | documentdb-local-deployment | Use app.py, seed.py, data/products.json, requirements.txt, .env.example, .gitignore, and a short README; no telemetry or attribution requirements. | Skills cover .env.example, ignored secrets, and versioned seed/schema files, but not a complete Flask repository layout or README standard. |
