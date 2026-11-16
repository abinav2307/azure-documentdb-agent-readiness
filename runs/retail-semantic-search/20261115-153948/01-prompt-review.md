# 1. Prompt review: retail-semantic-search

**Verdict: sufficient_with_assumptions**

The prompt clearly defines a Flask semantic-search API, its embedding model, and its vector index type. Installed skills cover DocumentDB query syntax, client reuse, and development configuration, but the builder will choose the API contract, catalog, hosting configuration, and several gallery-quality details. No missing detail prevents a sensible start.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Workflow type, Definition of done |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 8: Language and runtime, Target service and tier, Authentication and secrets, Data model, Queries and indexes, AI components, App surface, Provisioning and deployment |
| Missing: builder will guess | 5: Driver and version, Sample data, Run and test instructions, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Store embeddings as BSON binary vectors — the prompt omits the storage representation, and vector-skill examples use numeric arrays rather than prescribing binary vectors.
- Read model credentials from environment variables and keep them out of the repository — database-secret handling is covered, but model-credential handling is not explicitly covered.
- List every setting in .env.example with placeholders — the local skill leads to a database configuration example, not a complete inventory of embedding-provider and app settings.
- Choose IVF parameters for catalog size and explain larger-catalog tuning in the README — the vector skill gives scale guidance and an example, not a catalog-dependent numLists recipe or the required README explanation.
- Return clear errors for empty queries and embedding-call failures — neither the prompt nor loaded skills defines endpoint validation or embedding-provider error handling.
- Pin dependencies in requirements.txt — no prompt or skill requires Python dependency pinning.
- Provide unit tests that run without a live cluster — local guidance calls for real-container integration tests, not mocked offline unit tests.
- Provide cluster infrastructure as code using the Azure DocumentDB resource type — the deployment skill contains the correct Bicep path, but the prompt does not lead the builder to invoke provisioning or include infrastructure files.
- README covers the demonstration, prerequisites, setup, run, and clean-up — no skill requires this complete app-level runbook; cloud teardown guidance is conditional on deployment.
- Use “Azure DocumentDB” throughout with no former or neighbouring product branding — the prompt names the right service, but neither it nor a skill imposes repository-wide naming exclusivity.

## Questions for the prompt author

- Should text-embedding-ada-002 be called through OpenAI's public API or an Azure OpenAI deployment?
- Should the sample include cloud infrastructure as code, or assume an existing cluster? If infrastructure is required, should it target development or production?
- Should /search accept a GET query parameter or a POST JSON body?

## Contradictions and missing references

- No exact skill named “Azure DocumentDB skill” is installed, but the installed documentdb-* skills clearly match the reference; this is not a missing-skill blocker.
- Installed guidance conflicts on retryable writes: documentdb-azure-deployment says they are unsupported and uses retrywrites=false, while documentdb-connection says they are supported and recommends retryWrites=true; documentdb-driver also shows true. The prompt does not resolve this, and the service claim requires source verification.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | A product catalog with natural-language search returning semantically similar products. | - | - | Clearly demonstrates database-backed semantic product discovery. |
| Workflow type | specified | no | Embed the query and return similar products through a Flask endpoint. | - | - | A direct, no-agent embedding-and-retrieval workflow; no agent framework is needed. |
| Language and runtime | ambiguous | no | “Python Flask app” | - | Python 3.11 with Flask 3.1.x. | Language and framework are explicit; runtime and framework versions are not. |
| Driver and version | missing | no | - | - | Synchronous PyMongo 4.x, using one module-level MongoClient. | Connection and local-deployment skills identify PyMongo, and documentdb-driver requires client reuse, but none pins a synchronous Python driver version. |
| Target service and tier | ambiguous | no | “Azure DocumentDB” and “stored in DocumentDB” | - | An existing managed Azure DocumentDB M10 cluster, one shard, 32 GiB storage, HA disabled; use eastus2 if generating a development deployment example. | The service is clear. The vector skill places IVF at M10+; the deployment skill requires confirmation of dev versus production and region rather than silently selecting them. |
| Authentication and secrets | ambiguous | no | The app must access DocumentDB and an embedding model. | - | SCRAM-SHA-256 over TLS, DOCUMENTDB_URI and OPENAI_API_KEY from environment variables, with an ignored local .env file. | Local-deployment guidance explicitly covers database URI environment variables and .env.example. Model credentials and Entra versus native authentication are not settled; skills also disagree on retryable writes. |
| Data model | ambiguous | no | Product catalog; product titles and descriptions are embedded. | - | Database retail, collection products; one document per product with stable _id, title, description, price, category, embedding as a numeric array, and embedding model/dimension metadata; no sharding. | Data-modeling guidance is general. The vector skill recommends model/dimension metadata but does not prescribe this catalog schema or BSON binary vectors. |
| Sample data | missing | no | - | - | Approximately 30 synthetic products checked into the repository, loaded and embedded by a repeatable seed command; no external dataset licence. | The local-deployment skill supplies version-controlled, idempotent seeding guidance, but not a catalog source, size, or licence. |
| Queries and indexes | ambiguous | no | “create a vector-ivf index” and return “the top 10 semantically similar products” | - | A cosmosSearch index on embedding with kind vector-ivf, dimensions 1536, similarity COS, and numLists 1 for the small seed catalog; query using $search/cosmosSearch with k 10 and project searchScore. | documentdb-vector-search confirms IVF and the query syntax, including scores and dimension matching. It does not settle catalog-specific IVF parameters or supply a scaling recipe. |
| AI components | ambiguous | no | “text-embedding-ada-002”; embed product titles/descriptions and each search query. | - | OpenAI's public API through the Python openai SDK, 1536-dimensional embeddings; concatenate title and description during seeding and call the same model during search; no chat model. | The loaded skills do not mention text-embedding-ada-002 or establish its output size. This is not a documented contradiction; provider, deployment name, and API configuration remain unspecified. |
| App surface | ambiguous | no | “/search endpoint that takes a natural language query ... returns the top 10 ... products” | - | POST /search with JSON {"query":"..."}; return JSON containing up to 10 products and scores, excluding embeddings; no web UI. | Route and purpose are clear; HTTP method, payload shape, response envelope, and error contract are not. |
| Provisioning and deployment | ambiguous | no | “Using the Azure DocumentDB skill” | - | Run Flask locally against a user-provided cluster URI; document cluster setup, but do not create cloud resources or necessarily include infrastructure files. | Clearly matching DocumentDB skills are installed. documentdb-azure-deployment recommends Bicep and the correct resource type when provisioning is requested, but this prompt does not request provisioning or authorize cloud creation. |
| Run and test instructions | missing | no | - | - | README commands for venv creation, pip install -r requirements.txt, environment setup, python seed.py, flask --app app run, and a curl search example; manual smoke testing, with no mandatory offline unit suite. | Local-deployment guidance covers container integration testing, not a complete Flask runbook or required unit tests. |
| Definition of done | specified | no | Products stored in DocumentDB, embedded with the named model, indexed with vector-ivf, and retrieved through /search as the top 10 matches. | - | - | These are checkable functional acceptance criteria. Publication-quality requirements are not stated. |
| Constraints and non-goals | missing | no | - | - | A small development demo with no explicit spend cap, no user authentication, no checkout or catalog administration, no chat/RAG layer, and no compliance commitments. | No budget, licensing policy, or explicit scope exclusions are supplied. |
| Repository conventions | missing | no | - | - | A flat Flask project with app.py, seed.py, sample_products.json, requirements.txt, README.md, .env.example, and .gitignore; no telemetry or attribution machinery. | Local-deployment guidance covers .env.example and versioned seed/schema files, but not gallery layout, complete README sections, dependency pinning, or exclusive product naming. |
