# 1. Prompt review: retail-semantic-search

**Verdict: sufficient_with_assumptions**

The prompt clearly defines a buildable Flask semantic-search sample, and installed skills supply DocumentDB vector-query syntax, connection reuse, and configuration patterns. The builder must still choose runtime and driver versions, embedding provider, catalog data, API contract, and deployment scope; gallery-quality testing and documentation are not assured.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Workflow type, Definition of done |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 9: Language and runtime, Driver and version, Target service and tier, Authentication and secrets, Data model, Queries and indexes, AI components, App surface, Provisioning and deployment |
| Missing: builder will guess | 4: Sample data, Run and test instructions, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Embeddings stored as BSON binary vectors: neither the prompt nor loaded vector guidance requires this; examples store numeric arrays.
- Model credentials supplied through environment variables with no credentials in the repository: database secrets are covered, but embedding-provider configuration is not explicitly covered.
- .env.example lists every setting with placeholders: the local skill supplies database settings, not a complete Flask and embedding-provider configuration inventory.
- IVF parameters chosen for catalog size and README explains larger-catalog tuning: skill gives index-type scale thresholds, but no catalog-specific numLists rule or required tuning documentation.
- /search gives clear errors for an empty query and embedding-call failure: neither behavior is requested or covered by the relevant skills.
- Dependencies pinned in requirements.txt: no prompt or skill requires Python dependency pinning.
- Unit tests run without a live cluster: local guidance calls for container integration tests, not offline unit tests or mocked embedding calls.
- Cluster infrastructure provided as code using the Azure DocumentDB resource type: a correct Bicep template is available, but providing infrastructure is not requested and may be skipped for an existing cluster.
- README covers demonstration, prerequisites, setup, run, and clean-up: skills supply pieces of setup and teardown, but do not require this complete application README.

## Questions for the prompt author

- Should the sample target public OpenAI or Azure OpenAI, and what model deployment settings should it expose?
- Should the repository include cluster infrastructure, and may the agent deploy it? If deployment is intended, is it dev/test or production, and which subscription and region should be used?
- What HTTP method and request/response contract should /search implement?

## Contradictions and missing references

- Installed guidance conflicts on retryable writes: documentdb-azure-deployment says Azure DocumentDB does not support them and requires retrywrites=false; documentdb-connection says it supports them and recommends retryWrites=true, also used in the driver example. This needs source verification, not a ruling from memory.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | Build a product catalog search that returns the top 10 semantically similar products for a natural-language query. | - | - | Clearly demonstrates semantic product retrieval using database vector search. |
| Workflow type | specified | no | Embed the query and return semantically similar products. | - | - | Direct embedding-and-retrieval workflow; no agent or orchestration framework is requested. |
| Language and runtime | ambiguous | no | Python Flask app. | - | Python 3.11 with Flask 3.x. | Language and framework are explicit; runtime and framework versions are not settled by the skills. |
| Driver and version | ambiguous | no | Store the catalog in DocumentDB. | documentdb-driver; documentdb-connection; documentdb-local-deployment | Use synchronous PyMongo 4.x, one MongoClient per process, with an unpinned pymongo dependency. | Skills support PyMongo and singleton reuse, but do not select a synchronous-driver version. Connection and deployment skills disagree on retryWrites. |
| Target service and tier | ambiguous | no | Azure DocumentDB. | documentdb-azure-deployment; documentdb-vector-search; documentdb-local-deployment | Connect to an existing managed Azure DocumentDB cluster; document a dev configuration of M10, 32 GiB per shard, one shard, HA Disabled, in eastus2. | Service identity is clear. Skills establish IVF on M10+ and offer cloud/local options, but deployment guidance requires user selection of environment and region. |
| Authentication and secrets | ambiguous | no | - | documentdb-connection; documentdb-local-deployment; documentdb-azure-deployment | Use native SCRAM-SHA-256 database credentials in DOCUMENTDB_URI and an OPENAI_API_KEY environment variable; keep .env uncommitted. | Database URI, TLS, and secret-exclusion patterns are covered. Embedding-provider authentication and credential settings are not. |
| Data model | ambiguous | no | Product catalog stored in DocumentDB; embed product titles and descriptions. | documentdb-data-modeling; documentdb-vector-search | Use a retail database with a products collection containing stable _id, title, description, price, category, embedding as a numeric array, and embedding model/dimension metadata; no collection sharding. | Skills guide colocating related data and storing embedding metadata, but do not prescribe this catalog schema or BSON binary vectors. |
| Sample data | missing | no | - | - | Include roughly 20 synthetic products in a repository JSON file and load them with a version-controlled, idempotent seed script that generates embeddings. | Local-deployment guidance covers vetted, idempotent seeds; no skill selects the product source, size, or licence. |
| Queries and indexes | ambiguous | no | Create a vector-ivf index; return the top 10 semantically similar products. | documentdb-vector-search | Index embedding using cosmosSearchOptions.kind=vector-ivf, dimensions=1536, similarity=COS, and numLists=1 for the small catalog; query with $search/cosmosSearch and k=10, projecting searchScore. | The skill confirms IVF as a cosmosSearch subtype and supplies query syntax. It does not settle catalog-dependent IVF parameters. |
| AI components | ambiguous | no | Use text-embedding-ada-002 for product titles/descriptions and search queries. | documentdb-vector-search | Use the public OpenAI API and a 1536-dimensional embedding; concatenate title and description during ingestion and call the same model inside /search. No chat model. | Model and call sites are specified. Skills require matching dimensions but do not mention ada-002 or establish its output size; provider and deployment settings remain unspecified. |
| App surface | ambiguous | no | /search takes a natural language query and returns the top 10 semantically similar products. | - | Expose POST /search with JSON {"query":"..."}; return a JSON results array containing product fields and similarity scores, omitting embeddings. No web UI. | Route and broad behavior are explicit; HTTP method, payload keys, response envelope, and error contract are not. |
| Provisioning and deployment | ambiguous | no | Build an app with a catalog stored in DocumentDB. | documentdb-azure-deployment; documentdb-local-deployment | Run Flask locally against a user-provided cluster URI; do not create billable resources automatically. If infrastructure is included, use parameterized Bicep targeting Microsoft.DocumentDB/mongoClusters. | A canonical Bicep template and deployment/teardown flow are installed, but the prompt does not request provisioning or establish permission to deploy. |
| Run and test instructions | missing | no | - | - | Document venv creation, pip install -r requirements.txt, environment setup, python seed.py, flask --app app run, and a curl search example; provide manual smoke testing rather than mandatory offline unit tests. | Local skills offer container integration-test patterns, not Flask run commands or required unit tests. |
| Definition of done | specified | no | Flask app, stored products, ada-002 product embeddings, IVF index, and /search embedding queries and returning top 10 matches. | - | - | These are checkable functional acceptance criteria; no broader publication gate is stated. |
| Constraints and non-goals | missing | no | - | - | Build a small API-only demonstration without checkout, user accounts, chat, or production compliance controls; impose no explicit Azure or embedding-spend cap. | No cost ceiling, licensing policy, or production-readiness requirement is given. |
| Repository conventions | missing | no | - | - | Use app.py, seed.py, data/products.json, requirements.txt, .env.example, .gitignore, and a basic README; no telemetry or attribution machinery. | Skills give configuration and seed/schema conventions, but no complete gallery layout, dependency-pinning policy, or README checklist. |
