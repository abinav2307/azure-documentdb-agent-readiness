# 2. Build readiness: retail-semantic-search

**Verdict: blocked**

The agent has the relevant DocumentDB skills, working MCP servers, Azure CLI sign-in, and Python. It can scaffold the Flask app, but cannot confidently implement the prompt as written: no retrieved source establishes that BSON binary vectors, including subtype 9, can be indexed by Azure DocumentDB's vector-ivf index. The official IVF documentation instead specifies numeric arrays. The main product friction is this representation gap, compounded by contradictory retry-write guidance, stale local-image paths, and documentation that sometimes links DocumentDB users to Cosmos DB NoSQL integrations. No resources or database contents were changed.

## Blockers

- The prompt is built around BSON binary vectors indexed by vector-ivf, but no source verifies that managed-service combination. To clear this, the Azure DocumentDB team must provide a supported encoding/version contract and working managed-service example, or the author must explicitly amend the prompt to use the documented numeric-array representation. Do not silently replace binary vectors with arrays.

## Tools for this sample

| Tool | Kind | Available | Needed for | Detail | If missing | Workaround |
|---|---|---|---|---|---|---|
| python | cli | yes | Run Flask, embedding generation, catalog seeding, and PyMongo queries. | Python 3.14.10. The review's assumed Python 3.12 runtime is not the inventoried runtime. | Cannot execute the Python sample. | Use the installed runtime after checking dependency compatibility, or have the user supply the documented Python version. |
| Python package installation and virtual environment | other | **no** | Install Flask, PyMongo, the OpenAI client, and optional python-dotenv; isolate and pin dependencies. | Package installation state and pip availability were not inventoried. This means unconfirmed, not proven absent. Official Python vector quickstart documents pymongo, openai, python-dotenv, and azure-identity for its passwordless variant. | The app cannot import its dependencies; a recent BSON vector API cannot be assumed available. | Have the builder create a virtual environment and install tested dependencies. Include azure-identity only if choosing Azure passwordless authentication. |
| Application-accessible DocumentDB URI and database credentials | credential | **no** | Read products, seed the catalog, and create the IVF index on an existing managed cluster. | No application URI, target cluster, or database permissions were supplied. MCP tool discovery does not establish an application credential contract. | Live seeding and search cannot run. | The user supplies DOCUMENTDB_URI locally through environment configuration, with a reachable endpoint and appropriate database permissions. Do not request secrets in chat. |
| Embedding provider access for text-embedding-ada-002 | credential | **no** | Embed product titles/descriptions and every search query. | Provider, API key or identity permissions, endpoint, deployment name, and model access were not supplied or inventoried. | Neither ingestion nor live semantic search can generate embeddings. | Choose OpenAI API or an existing Azure OpenAI deployment and have the user configure its credentials locally. Mock calls can support isolated tests, but do not satisfy the live embedding requirement. |
| documentdb-vector-search | skill | yes | IVF index configuration, cosmosSearch query syntax, dimensions, similarity, and embedding metadata. | Loaded with vector-knn-query.md and vector-normalize-embeddings.md. Covers IVF on M10+, but does not establish BSON binary-vector indexing. | The agent may substitute Atlas syntax or choose incompatible index parameters. | Use the official DocumentDB vector-search page and Python vector-search quickstart. |
| documentdb-driver | skill | yes | Reuse one thread-safe MongoClient per Flask process. | Loaded with driver-singleton-client.md. Singleton guidance is clear; its example also enables retryWrites, conflicting with other guidance. | Per-request clients increase connection churn and latency. | Follow MongoDB driver connection-management documentation and preserve the verified target URI. |
| documentdb-connection | skill | yes | TLS, native authentication, connection reuse, and contextual pool settings. | Loaded. Recommends retryWrites=true and a non-SRV port of 10255, whereas retrieved managed-service documentation uses SRV and port 10260. | Connection configuration is harder to derive safely. | Use the portal-provided SRV URI and official service connection documentation rather than synthesizing a URI from this skill. |
| documentdb-data-modeling | skill | yes | Keep product metadata and embeddings together, respect BSON size limits, and record schema/model metadata. | Loaded. General modeling guidance does not answer the binary-vector encoding requirement. | The agent may omit model metadata or create an unnecessarily complex schema. | Use one document per product and the vector skill's embeddingModel/embeddingDims guidance. |
| documentdb-indexing | skill | yes | Review the inventory's available index-design guidance for the catalog. | Installed according to inventory. The narrower vector-search skill and official IVF reference were sufficient for this assessment. | Less assistance selecting index shapes; IVF implementation is still possible. | Use documentdb-vector-search and the official vector index command reference. |
| documentdb-local-deployment | skill | yes | Reproducible catalog seeds, environment-driven configuration, and optional local integration tests. | Loaded with local-sample-data-management.md. Specifies ghcr.io/documentdb/documentdb/documentdb-local:latest and MongoDB port 10260. | Local setup and seed reproducibility become easier to get wrong. | Use the official development-loop tutorial and version-controlled idempotent seed scripts. |
| documentdb-security | skill | yes | TLS, secret handling, and determining whether the existing cluster's firewall or private endpoint permits access. | Loaded. Native authentication and Entra ID are supported; this sample can use native credentials without adding Entra configuration. | The agent may relax TLS verification or confuse Azure sign-in with database authorization. | Use official DocumentDB security and connection documentation. |
| documentdb-mcp-setup | skill | yes | Understand administrator-owned connection profiles and troubleshoot agent access without exposing credentials. | Loaded. Identifies microsoft/documentdb-mcp and CONNECTION_PROFILES; tools reference connection_profile rather than accepting a URI. | The agent may expect MCP credentials to be available to the Flask process or ask for secrets in chat. | Have the administrator configure MCP profiles and application environment settings separately. |
| documentdb-azure-deployment | skill | yes | Identify the managed resource, tier prerequisites, and connection-string source; provisioning is outside the assumed sample scope. | Loaded. Specifies Microsoft.DocumentDB/mongoClusters and API 2025-09-01. Conflicts with the connection skill on retryable writes. | The agent has less help distinguishing the managed cluster from Cosmos DB accounts or a local engine. | Use the official resource reference and an existing user-provided cluster; do not provision under this run's policy. |
| documentdb MCP server | mcp_server | yes | Optional schema/index inspection and read-only aggregation checks on an administrator-selected target. | Inventory confirms 18 tools, including sample_documents, list_indexes, aggregate, explain_operation, and index management. No data-plane calls were needed because no target collection or profile was supplied. | Interactive database inspection is lost, but application implementation remains possible. | Use PyMongo for explicit read-only diagnostics. Do not execute seed or index writes during readiness. |
| Microsoft Learn MCP server | mcp_server | yes | Verify service identity, IVF syntax, encoding requirements, model dimensions, and conflicting skills. | Inventory confirms three tools. Search and full-page fetch returned sources throughout this assessment. | The agent must rely more heavily on inconsistent installed guidance. | Read the same first-party pages through an available documentation client. |
| Azure MCP Server | mcp_server | yes | Optional Azure inspection and best-practice guidance during a later build. | Inventory confirms 73 tools. A targeted azure_cosmos command-discovery request failed with 'Function failed'; this does not overturn server availability or prove its DocumentDB coverage. | Azure inspection accelerators are unavailable; the Flask app does not depend on this server. | Use Azure CLI for resource inspection, Learn for documentation, and the dedicated DocumentDB MCP or PyMongo for data-plane work. |
| az with cosmosdb-preview | cli | yes | Optional read-only inspection of the existing cluster and its networking. | Azure CLI 2.73.0; cosmosdb-preview 1.7.0 is installed. The CLI reference confirms az cosmosdb mongocluster belongs to that extension. | Resource inspection is less convenient; application code can still target a supplied URI. | Use the portal or available Azure control-plane tools. No provisioning is required for the assumed scope. |
| az login | credential | yes | Read Azure resource metadata; optionally authenticate through Azure Identity if that route is selected. | Signed in to subscription cosmosdb-programmability-demo-1mqps. Cluster authorization and embedding-provider permissions are not established by this sign-in. | Azure inspection or identity-based access fails; native database credentials remain an alternative. | Use separately supplied native database and embedding-provider credentials, or have the user grant the required identity access. |
| node and npx | cli | yes | Maintain the installed Node-based DocumentDB MCP and agent-kit tooling, not execute the Flask app. | Node v26.13.0 and npx 11.20.0; the MCP setup skill requires Node 20+. | Restarting or reinstalling the Node-based accelerator may fail. | Use PyMongo directly; the application has no Node runtime dependency. |
| git | cli | yes | Version-controlled application, catalog, and seed/index scripts; also an upstream MCP installation prerequisite. | Git 2.56.0.windows.4. | Reproducible source management and Git-based accelerator installation are impaired. | Use downloaded source archives and local files until Git is available. |
| docker and local DocumentDB container | cli | yes | Optional local integration tests that exercise DocumentDB-specific vector syntax. | Docker 29.9.3 is installed. The image cache, daemon readiness, running container, and managed-service binary-vector parity were not inventoried. | Local integration tests need an existing managed cluster instead. | Use a permitted existing test cluster. If the user chooses local tests, obtain the documented image separately; do not treat local behavior as proof of managed binary-vector support. |
| mongosh | cli | **no** | Optional manual index and connectivity checks. | Not found on PATH. | Shell-based diagnostics cannot run on the host; this is not a required application dependency. | Use PyMongo or the dedicated DocumentDB MCP read tools. |

## Accelerators not installed

None.

## Service confusions

The model answered 20 questions from memory before reading any source: 12 correct, 7 wrong or partly wrong, 1 could not be verified.

### Q03: Which Bicep and Terraform resource types deploy a cluster?

- **Outcome:** partly_wrong, confused with `unknown`
- **From memory:** In Bicep, deploy Microsoft.DocumentDB/mongoClusters, for example resource cluster 'Microsoft.DocumentDB/mongoClusters@2025-04-01'. In Terraform, use azurerm_mongo_cluster, or azapi_resource with type Microsoft.DocumentDB/mongoClusters@2025-04-01 when the AzureRM resource lacks a required property.
- **From sources:** The resource types are correct, but the API version is not. The resource reference lists 2025-04-01-preview, not 2025-04-01. The installed deployment skill uses the documented stable 2025-09-01 API and azurerm_mongo_cluster, with AzAPI as an alternative.
- **Source:** documentdb-azure-deployment; https://learn.microsoft.com/azure/templates/microsoft.documentdb/2025-04-01-preview/mongoclusters; https://learn.microsoft.com/azure/templates/microsoft.documentdb/2025-09-01/mongoclusters
- **Why the confusion arose:** The model retained a resource schema date but dropped its preview suffix. This is API-version fabrication, not evidence of choosing another database service.
- **Risk to the build:** Bicep or AzAPI deployment would target an undocumented API version. Not central if the builder uses an existing cluster.

### Q08: Which vector index types are supported, and what does the command that creates one look like?

- **Outcome:** partly_wrong, confused with `unknown`
- **From memory:** The vector index kinds are vector-ivf, vector-hnsw, and vector-diskann, subject to tier restrictions. For the sample, run db.runCommand({createIndexes:'products',indexes:[{name:'product_vector_ivf',key:{embedding:'cosmosSearch'},cosmosSearchOptions:{kind:'vector-ivf',numLists:100,dimensions:1536,similarity:'COS'}}]}).
- **From sources:** The kinds and command shape are correct. For the review's assumed roughly 20-product catalog, numLists=100 is not the documented small-demo choice: start with numLists=1. The vector page gives documentCount/1000 sizing up to one million documents and explains recall/latency tuning.
- **Source:** documentdb-vector-search; https://learn.microsoft.com/azure/documentdb/vector-search
- **Why the confusion arose:** A plausible larger-catalog parameter was copied into a tiny sample without considering catalog size. The service-specific cosmosSearch syntax itself is correctly identified.
- **Risk to the build:** Oversized clustering can impair small-catalog retrieval or index construction; searching one list does not guarantee the global top 10.

### Q09: How are full-text search and hybrid search done?

- **Outcome:** partly_wrong, confused with `mongodb_atlas_or_server`
- **From memory:** For lexical full-text search, create a MongoDB text index, such as db.products.createIndex({title:'text',description:'text'}), and query with {$text:{$search:query}} and textScore metadata. For hybrid search, execute that lexical search and a vector search using $search.cosmosSearch, then combine their ranked result lists using reciprocal rank fusion in the application.
- **From sources:** The current documented BM25 path uses createSearchIndexes, a named search index, $search with text, and searchScore metadata. RRF in the application is valid; a server-side $unionWith fusion variant is also documented. The fetched hybrid page labels full-text search gated preview.
- **Source:** documentdb-full-text-search; https://learn.microsoft.com/azure/documentdb/full-text-search-hybrid
- **Why the confusion arose:** The cold answer substitutes community MongoDB text indexes and $text/textScore for DocumentDB's documented BM25 search-index API. Shared MongoDB query syntax encourages this substitution.
- **Risk to the build:** A later lexical/hybrid extension would not implement the documented search engine. Full-text search is not required for this semantic-only sample.

### Q10: Which MongoDB wire protocol or server versions are supported, and which commonly used MongoDB features are not?

- **Outcome:** partly_wrong, confused with `unknown`
- **From memory:** I would select MongoDB compatibility version 7.0 for a new cluster and use a current MongoDB driver. My understanding is that compatibility versions include 5.0, 6.0, 7.0, and newer 8.0 offerings. Compatibility is not complete MongoDB server equivalence: I would disable retryable writes and avoid mapReduce, server-side JavaScript such as $where, capped collections, and time-series collections.
- **From sources:** The FAQ and compatibility tables confirm versions 5.0, 6.0, 7.0, and 8.0. Capped/time-series collections are unavailable and mapReduce is not a supported path. However, retrieved compatibility guidance explicitly lists $where as supported. Retryable-write support could not be settled: installed skills and official pages disagree.
- **Source:** https://learn.microsoft.com/azure/documentdb/faq; https://learn.microsoft.com/azure/documentdb/compatibility-features; https://learn.microsoft.com/azure/documentdb/compatibility-query-language; https://learn.microsoft.com/azure/documentdb/compare-amazon-documentdb; documentdb-connection; documentdb-azure-deployment
- **Why the confusion arose:** The model applies a generic MongoDB-compatible-service limitations list rather than the current per-feature matrix. Sources also disagree internally, so the retry statement cannot be assigned confidently to one neighbour.
- **Risk to the build:** Unnecessary compatibility workarounds and incorrect support claims in the README. The proposed Flask pipeline does not require the disputed operators.

### Q11: How do you run the database locally for development and tests: which image or emulator, and which port?

- **Outcome:** partly_wrong, confused with `open_source_documentdb`
- **From memory:** For service-oriented local tests, run docker run -d --name documentdb-local -p 10260:10260 ghcr.io/microsoft/documentdb/documentdb-local:latest and connect through the MongoDB-compatible endpoint on localhost:10260. This is the open-source DocumentDB local image, not the Cosmos DB NoSQL emulator. A regular MongoDB container is useful for basic CRUD tests but does not reproduce the DocumentDB vector-search extensions.
- **From sources:** The documented image is ghcr.io/documentdb/documentdb/documentdb-local:latest, not the microsoft namespace path. The gateway uses port 10260 and local TLS configuration. It runs the open-source engine, not the managed Azure service or Cosmos DB NoSQL emulator.
- **Source:** documentdb-local-deployment; https://learn.microsoft.com/azure/documentdb/development-loop
- **Why the confusion arose:** The model carries the Microsoft repository ownership into the container registry path instead of using the documented DocumentDB registry namespace.
- **Risk to the build:** The documented local setup cannot be reproduced with the supplied image reference; local tests stall before exercising search.

### Q12: Are change streams supported, and does anything have to be enabled first?

- **Outcome:** partly_wrong, confused with `unknown`
- **From memory:** Change streams are supported, but I would enable the cluster's EnableChangeStreams capability before using collection.watch() in PyMongo. I would treat this as an explicit cluster feature rather than assume watch() works on every default deployment.
- **From sources:** Change streams are supported and the current page demonstrates collection.watch(). It specifically requires a support request for multishard preview support. It does not prescribe an EnableChangeStreams capability for every cluster.
- **Source:** https://learn.microsoft.com/azure/documentdb/change-streams
- **Why the confusion arose:** The answer turns feature-gating knowledge into an undocumented universal capability flag. Older release notes mention gated change-stream preview, but do not establish this exact flag.
- **Risk to the build:** An unnecessary or invalid control-plane change would be added. Change streams are outside this sample's scope.

### S03: What index command should the Python sample execute?

- **Outcome:** partly_wrong, confused with `unknown`
- **From memory:** Create the service-specific index with db.command({'createIndexes':'products','indexes':[{'name':'product_vector_ivf','key':{'embedding':'cosmosSearch'},'cosmosSearchOptions':{'kind':'vector-ivf','numLists':100,'dimensions':1536,'similarity':'COS'}}]}). A normal ascending index on embedding is not a vector index.
- **From sources:** The Python command structure and cosmosSearch key are correct. For the assumed tiny catalog, the official IVF guide recommends starting with numLists=1 rather than copying 100. The command does not itself establish support for a binary-valued embedding field.
- **Source:** https://learn.microsoft.com/azure/documentdb/vector-search; https://learn.microsoft.com/azure/documentdb/quickstart-python-vector-search
- **Why the confusion arose:** A valid algorithm configuration is mistaken for a dataset-independent sample default. Index syntax and supported field representation are also conflated.
- **Risk to the build:** Poor small-catalog behavior and reduced recall; even a valid index command cannot fix an unsupported embedding representation.

### S02: Which BSON binary-vector encoding and PyMongo API can this sample use with Azure DocumentDB IVF?

- **Outcome:** could_not_verify, confused with `mongodb_atlas_or_server`
- **From memory:** Store each product's embedding as a BSON binary vector using bson.binary.Binary.from_vector(embedding, bson.binary.BinaryVectorDtype.FLOAT32), which uses BSON vector subtype 9. Use a recent PyMongo version that exposes this API.
- **From sources:** Could not verify this as an Azure DocumentDB IVF storage contract. The vector skill, official vector-search page, Python quickstart, and targeted Learn searches for BSON binary vectors, subtype 9, and Binary.from_vector provide no managed-service binary-vector example or supported encoding/version matrix. The IVF page explicitly says vectors must be number[] to be indexed. A client serialization API alone would not establish service index support.
- **Source:** none found; searched with learn_microsoft_docs_search; inspected documentdb-vector-search, https://learn.microsoft.com/azure/documentdb/vector-search and https://learn.microsoft.com/azure/documentdb/quickstart-python-vector-search
- **Why the confusion arose:** The answer extrapolates a MongoDB/PyMongo BSON representation to a different MongoDB-compatible service's custom cosmosSearch index. Wire compatibility does not establish binary-vector indexing compatibility.
- **Risk to the build:** Products may be stored successfully but omitted from the IVF index, leaving /search empty or failing. This is central to the explicit prompt and blocks the build as specified.

## Information nobody could supply

- Central missing contract: whether managed Azure DocumentDB IVF indexes BSON binary vectors at all; supported subtypes, FLOAT32 byte encoding, driver/server requirements, and query-vector representation were not established.
- Retryable writes remain contradictory: documentdb-connection, the driver example, and the passwordless Python quickstart enable them; deployment/native connection guidance disables them; Amazon migration guidance says to remove retryWrites=false. No retrieved source reconciles versions, authentication modes, or rollout differences.
- The supplied environment does not establish an application-accessible cluster, connection profile, database permissions, or allowed network path. A returned MCP tool list is not evidence that the Flask process can connect.
- Embedding provider and live ada-002 access are unspecified. The user must choose a provider and supply its local credential/deployment contract; model documentation does not prove access in this subscription or account.
- Dependency installation and compatibility with inventoried Python 3.14.10 are unconfirmed. In particular, no source establishes a tested package matrix for the requested binary-vector implementation.
- Catalog size/source, HTTP method, request/response envelope, validation, error behavior, and exact-versus-approximate retrieval expectations remain author choices, not answered service facts. The review's small synthetic catalog and POST JSON assumptions are reasonable but must be disclosed.
- The general Azure MCP server's exact managed DocumentDB data-plane coverage could not be determined; targeted azure_cosmos discovery failed. The dedicated server supplies a workaround.
- Documentation introduces neighbouring-product hazards: the DocumentDB vector page links LangChain users to an azure_cosmos_db_no_sql integration; the Python quickstart contains an unused Cosmos token-scope helper; the vector skill's unsupported-$vectorSearch claim conflicts with release notes. None is needed for the chosen direct PyMongo pipeline.
- No local image installation or running-container state was established. Docker availability is confirmed, so this is not a proven missing accelerator.
- This readiness run permits no database or Azure writes. Live seeding and index creation must be performed later by the user or under separately authorized execution; code generation alone does not require provisioning.

## Corrections passed to the builder

- Do not implement Binary.from_vector/subtype 9 as a verified Azure DocumentDB IVF feature. Resolve S02 first; the current official IVF documentation requires numeric arrays: https://learn.microsoft.com/azure/documentdb/vector-search.
- For the review's tiny synthetic catalog, replace the cold answers' numLists=100 with numLists=1 and k=10. Explain larger-catalog numLists/nProbes tuning and its recall trade-off, using https://learn.microsoft.com/azure/documentdb/vector-search.
- Use the documented local image ghcr.io/documentdb/documentdb/documentdb-local:latest on port 10260 if local testing is selected. Keep local TLS relaxation environment-controlled; do not use the cold answer's microsoft registry path. Sources: documentdb-local-deployment and https://learn.microsoft.com/azure/documentdb/development-loop.
- If infrastructure is later requested, use a documented API version such as Microsoft.DocumentDB/mongoClusters@2025-09-01, not @2025-04-01. The latter date exists as 2025-04-01-preview. Sources: documentdb-azure-deployment and the ARM resource reference.
- Preserve the existing cluster's portal-provided SRV URI rather than reconstructing it from the connection skill. The native Python quickstart supports TLS, SCRAM-SHA-256, and retrywrites=false; treat that as a conservative sample setting, not proof that retryable writes are universally unsupported.
- Use one MongoClient per Flask process, a separate embedding client, and ada-002 for both ingestion and query embeddings with 1536 dimensions. Do not reuse the official quickstart's text-embedding-3-small precalculated dataset.
- Keep the verified $search/cosmosSearch pipeline and searchScore projection. Do not broaden the skill's Atlas warning into an unverified claim that all $vectorSearch use is unsupported.
- Keep full-text search and change streams out of this sample. If subsequently added, use createSearchIndexes plus BM25 $search and verify preview access; use the documented change-stream prerequisites rather than inventing a universal EnableChangeStreams flag.
- Before live execution, have the user supply database and embedding settings locally and authorize seed/index writes separately. Use PyMongo and the dedicated DocumentDB MCP as workarounds for missing mongosh and failed general Cosmos command discovery.

## Machine inventory (collected by code)

| Item | Available | Detail |
|---|---|---|
| CLI `az` | yes | { "azure-cli": "2.73.0", "azure-cli-core": "2.73.0", "azure-cli-telemetry": "1.1.0", "extensions": { "cosmosdb-preview": "1.7.0", "fleet": "1.5.2" } } |
| CLI `azd` | no | not found on PATH |
| CLI `bicep` | no | not found on PATH |
| CLI `terraform` | no | not found on PATH |
| CLI `node` | yes | v26.13.0 |
| CLI `npx` | yes | 11.20.0 |
| CLI `python` | yes | Python 3.14.10 |
| CLI `dotnet` | yes | 9.0.321 |
| CLI `docker` | yes | Docker version 29.9.3, build 5457199 |
| CLI `mongosh` | no | not found on PATH |
| CLI `git` | yes | git version 2.56.0.windows.4 |
| Azure sign-in | yes | { "subscription": "cosmosdb-programmability-demo-1mqps", "tenant": "72f988bf-86f1-41af-91ab-2d7cd011db47" } |
| MCP `documentdb` | yes | 18 tools: documentdb_list_databases, documentdb_drop_database, documentdb_drop_collection, documentdb_rename_collection, documentdb_sample_documents, documentdb_current_ops, documentdb_get_statistics, documentdb_find_documents, documentdb_count_documents, documentdb_insert_documents, documentdb_update_documents, documentdb_delete_documents ... |
| MCP `azure` | yes | 73 tools: azure_documentation, azure_azd, azure_foundry, azure_arm, azure_get_azure_bestpractices, azure_adme, azure_aks, azure_appconfig, azure_applens, azure_appservice, azure_role, azure_azurebackup ... |
| MCP `learn` | yes | 3 tools: learn_microsoft_docs_search, learn_microsoft_code_sample_search, learn_microsoft_docs_fetch |
| Agent skills | yes | documentdb-azure-deployment, documentdb-connection, documentdb-data-modeling, documentdb-driver, documentdb-full-text-search, documentdb-high-availability, documentdb-indexing, documentdb-local-deployment, documentdb-mcp-setup, documentdb-monitoring, documentdb-natural-language-querying, documentdb-query-optimization, documentdb-query-optimizer, documentdb-security, documentdb-sharding, documentdb-storage, documentdb-vector-search |
