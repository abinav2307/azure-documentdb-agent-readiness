# 2. Build readiness: retail-semantic-search

**Verdict: ready_with_gaps**

The coding agent can start building the Flask sample. Sources verify the central requirements: ada-002 produces 1,536-dimensional embeddings, Azure DocumentDB supports IVF indexes, and $search/cosmosSearch retrieves the top k products. Live acceptance testing remains conditional on user-supplied database and embedding credentials and permission to seed data and create an index; this run prohibits writes. The largest product friction is contradictory connection guidance, including retryWrites values within the same official authentication page. Other findings are an outdated CLI installation, a moved local-container image, legacy full-text-search assumptions, and IVF parameters copied without regard to catalog size. No required inventory tool is unavailable without a workaround.

## Blockers

None.

## Tools for this sample

| Tool | Kind | Available | Needed for | Detail | If missing | Workaround |
|---|---|---|---|---|---|---|
| Python | cli | yes | Run Flask, catalog ingestion, embedding calls, and PyMongo queries. | Python 3.14.10. This differs from the review's assumed Python 3.11; dependency compatibility was not tested. | The application and seed script cannot execute. | Use the installed runtime after dependency validation, or have the user supply a compatible Python environment. |
| pip and venv | cli | **no** | Install and isolate the Python application dependencies. | Allowed by policy, but installation and functionality are not established by the inventory. This is unknown availability, not a confirmed missing installation. | Dependencies cannot be installed reproducibly. | Use Python's module-based package installation and virtual-environment workflow, documented in the Python vector quickstart; repair packaging support if unavailable. |
| Flask, PyMongo, and openai Python packages | other | **no** | HTTP endpoint, MongoDB-compatible data access, and ada-002 embedding generation. | Package installation and versions were not inventoried. Sources establish PyMongo and openai usage, but not a tested Flask/PyMongo/openai combination on Python 3.14. | Application imports fail. | Install dependencies in a virtual environment and pin versions after validating them. The DocumentDB Python quickstart supplies a PyMongo/openai baseline, not a complete Flask requirements file. |
| documentdb-vector-search | skill | yes | Select IVF, configure cosmosSearch, match vector dimensions, and construct the top-10 query. | Loaded, including vector-knn-query.md and vector-normalize-embeddings.md. Official vector documentation supplies catalog-dependent numLists guidance. | An agent may substitute Atlas or Cosmos DB NoSQL vector-index syntax. | Use https://learn.microsoft.com/azure/documentdb/vector-search. |
| documentdb-driver | skill | yes | Reuse one MongoClient per Flask process. | Loaded driver-singleton-client.md. Its retryWrites=true example conflicts with the official vector quickstart. | A client per request causes unnecessary connections and TLS handshakes. | Follow the singleton pattern but take retryWrites=false from the official Python vector quickstart. |
| documentdb-connection | skill | yes | TLS, authentication, URI configuration, and connection reuse. | Loaded. Recommends retryWrites=true and a non-SRV endpoint on port 10255, conflicting with official managed-service connection guidance. | Incorrect connection configuration can prevent database access. | Use the portal-issued SRV URI, official port-10260 troubleshooting guidance, and the Python vector quickstart's retryWrites=false setting. |
| documentdb-data-modeling | skill | yes | Store product metadata and embeddings together in a small, unsharded catalog. | Loaded. Covers colocating related data and the 16 MB document limit. | The agent has less guidance on document shape and size. | Use the original-data-plus-vector pattern in the official vector documentation. |
| documentdb-security | skill | yes | Require TLS and distinguish firewall access from database authentication. | Installed and loaded. Production CMK and private-endpoint design are outside this sample's assumed scope. | Secrets or certificate-validation exceptions may be handled unsafely. | Use official security and connection documentation; keep secrets outside the repository. |
| documentdb-local-deployment | skill | yes | Optional local integration-test environment and environment-driven seed/configuration conventions. | Loaded. Identifies ghcr.io/documentdb/documentdb/documentdb-local:latest and MongoDB port 10260. | The local engine may be mistaken for a Cosmos DB emulator or launched from the wrong registry path. | Use https://learn.microsoft.com/azure/documentdb/development-loop. Local testing does not replace managed-service acceptance testing. |
| documentdb-azure-deployment | skill | yes | Optional cluster prerequisite documentation and correct Azure resource identity. | Loaded. Supplies Microsoft.DocumentDB/mongoClusters and a generic az resource deployment path. Provisioning is not requested and is prohibited in this run. | Optional infrastructure documentation may target an RU-based Cosmos DB account. | Connect to an existing cluster and reference the official DocumentDB quickstarts. |
| documentdb-mcp-setup | skill | yes | Understand administrator-controlled connection profiles and safely configure the optional data-plane MCP connection. | Loaded. Credentials belong in local configuration, not chat or agent-generated files. | An agent may assume MCP credentials are available to the Flask application. | Configure DOCUMENTDB_URI independently, with the user entering its secret value locally. |
| DocumentDB MCP Toolkit | mcp_server | yes | Optional collection, document, and index inspection during development. | Inventory confirms 18 tools, including aggregate, list_indexes, and sample_documents. Server availability does not establish the target cluster, credentials, or write authorization. | Interactive data-plane inspection is slower, but application development can continue. | Use PyMongo for application operations and user-authorized validation. No MCP writes were performed. |
| Microsoft Learn MCP Server | mcp_server | yes | Verify service identity, vector syntax, embedding dimensions, and conflicting guidance. | Inventory confirms three tools. Search and fetch succeeded in this assessment. | The agent must rely more heavily on inconsistent installed skills or memory. | Read the cited official documentation directly. |
| Azure MCP Server | mcp_server | yes | Optional Azure metadata inspection and Azure/AI best-practice guidance. | Inventory confirms 73 tools. A substantive azure_cosmos capability-discovery call returned 'Error: Function failed'; no DocumentDB data-plane replacement was established. | Optional control-plane discovery is less convenient; Flask and vector retrieval do not depend on this server. | Use the dedicated DocumentDB MCP server, Learn documentation, and existing Azure CLI. |
| Azure CLI | cli | yes | Optional read-only cluster and network inspection. | 2.73.0 with cosmosdb-preview 1.7.0. The current documentdb extension requires Azure CLI 2.75.0 or higher. | Command-line inspection and optional infrastructure instructions are less convenient. | Use the portal or generic resource commands; a user-provided cluster URI avoids a CLI dependency. |
| Azure CLI documentdb extension | cli | **no** | Optional current az documentdb mongocluster inspection commands. | Not in the inventory's extension list, and installed Azure CLI is below the documented minimum. | Current quickstart commands cannot be assumed to work on this machine. | Use portal/generic ARM inspection, or upgrade Azure CLI and install the documentdb extension. |
| Azure sign-in | credential | yes | Optional Azure resource inspection or an explicitly selected Entra authentication path. | Signed in to cosmosdb-programmability-demo-1mqps. This does not prove DocumentDB data-plane access or embedding-provider access. | Azure metadata inspection and Azure Identity token acquisition may fail. | The assumed native database-authentication and public OpenAI path does not require Azure sign-in. |
| DocumentDB application credentials and reachable cluster | credential | **no** | Store products, create the IVF index, and execute live searches. | No application URI, chosen cluster, database privileges, or network reachability is established. A responding MCP server is not proof of these application prerequisites. | Live database acceptance testing cannot complete. | Have the user configure DOCUMENTDB_URI locally for an existing suitable cluster, grant seed/index privileges, and provide network access. Build and mocked tests can start beforehand. |
| Embedding-provider credentials and ada-002 access | credential | **no** | Generate catalog and query embeddings. | No OPENAI_API_KEY or Azure OpenAI endpoint/deployment/access assignment is supplied or inventoried. | Real ingestion embeddings and natural-language searches cannot execute. | Document public OpenAI as an explicit assumption and have the user configure its key locally, or select Azure OpenAI and configure its endpoint, deployment name, and authentication. Mock embedding calls for offline tests. |
| Docker and local DocumentDB image | cli | yes | Optional local database integration tests. | Docker 29.9.3 is installed. Daemon readiness, cached image, and a running container are not established. | Local database integration tests cannot run. | Use an existing managed cluster or have the user prepare the documented gateway image. Do not treat the unverified image cache as a confirmed missing accelerator. |
| mongosh | cli | **no** | Optional manual connectivity and index inspection. | Not found on PATH. | Shell-based instructions cannot be run directly. | Use installed DocumentDB MCP read tools or PyMongo; mongosh is not required by the app. |
| Node.js and npx | cli | yes | Maintain or launch the installed MCP/skill accelerators, not run Flask. | Node v26.13.0; npx 11.20.0. | npx-based MCP launch or skill installation would be unavailable. | Use a prebuilt MCP server or direct documentation/PyMongo. |
| Git | cli | yes | Source control and the documented GitHub-based MCP installation path. | 2.56.0.windows.4. | Repository management and GitHub-based accelerator installation are less convenient. | Use downloaded source archives and an already-installed MCP server. |

## Accelerators not installed

- Current Azure CLI documentdb extension: the installed cosmosdb-preview extension is not the current accelerator. The CLI reference requires Azure CLI >=2.75.0 and documents automatic extension installation on first use. Upgrade the CLI, then install the documentdb extension; https://learn.microsoft.com/cli/azure/documentdb/mongocluster.

## Service confusions

The model answered 20 questions from memory before reading any source: 12 correct, 7 wrong or partly wrong, 1 could not be verified.

### Q02: Which CLI command group manages clusters, and is it core or an extension?

- **Outcome:** partly_wrong, confused with `legacy_vcore_naming`
- **From memory:** az cosmosdb mongocluster, provided by cosmosdb-preview.
- **From sources:** The current group is az documentdb mongocluster, provided by the documentdb extension, requiring Azure CLI 2.75.0 or higher. Extension classification was correct; group and extension names were outdated.
- **Source:** https://learn.microsoft.com/cli/azure/documentdb/mongocluster
- **Why the confusion arose:** The answer retained the service's earlier Cosmos DB CLI branding and extension package after the product rename.
- **Risk to the build:** Current README commands would not match the official interface, and installing cosmosdb-preview would not clear the new CLI prerequisite.

### Q04: What connection scheme, host, port, and options should be used?

- **Outcome:** partly_wrong, confused with `unknown`
- **From memory:** mongodb+srv on mongocluster.cosmos.azure.com, port 10260, TLS, SCRAM-SHA-256, retrywrites=false, maxIdleTimeMS=120000; retryable writes are unsupported.
- **From sources:** The SRV scheme, host suffix, port 10260, TLS, and native SCRAM mechanism are supported. Both self and global hostnames are documented. retryWrites=false is explicitly prescribed by the Python vector quickstart, but a blanket claim that the service never supports retryable writes cannot be settled: installed skills and official authentication/migration pages conflict. maxIdleTimeMS is recommended configuration, not an authentication requirement.
- **Source:** https://learn.microsoft.com/azure/documentdb/troubleshoot-common-issues; https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control; https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm; documentdb-connection; documentdb-azure-deployment
- **Why the confusion arose:** The categorical limitation is stronger than the conflicting sources support. This is source inconsistency, not a demonstrated Amazon DocumentDB mix-up.
- **Risk to the build:** The sample's false setting has direct support. Conversely, copying retryWrites=true or port 10255 from the connection skill risks incompatible sample configuration.

### Q09: How are full-text and hybrid search done?

- **Outcome:** partly_wrong, confused with `mongodb_atlas_or_server`
- **From memory:** Use a text index, $text, and textScore; combine lexical and vector rankings with application-side RRF.
- **From sources:** The current BM25 engine uses createSearchIndexes, named-index $search/text queries, and searchScore. It is gated preview. Hybrid search combines BM25 and cosmosSearch rankings using RRF, either in application code or a documented server-side union pipeline. The legacy $text engine is documented as superseded, not simply nonexistent.
- **Source:** https://learn.microsoft.com/azure/documentdb/full-text-search-overview; https://learn.microsoft.com/azure/documentdb/full-text-search-hybrid; documentdb-full-text-search
- **Why the confusion arose:** The answer reused community MongoDB text-index syntax that also appeared in this service's legacy PostgreSQL TSVector search implementation. Shared $search vocabulary then caused it to reject a now-documented text operator.
- **Risk to the build:** An optional hybrid extension would use the wrong index engine and scoring metadata and could omit preview enrollment. This vector-only sample does not require full-text search.

### Q10: Which compatibility versions and MongoDB limitations apply?

- **Outcome:** partly_wrong, confused with `legacy_vcore_naming`
- **From memory:** Versions 5.0, 6.0, and 7.0; avoid server-side JavaScript, cross-shard transactions, Atlas-specific search APIs, and replica-set administration.
- **From sources:** Sources list wire-protocol compatibility versions 5.0, 6.0, 7.0, and 8.0. The official Atlas comparison explicitly supports ACID transactions across collections and shards. Managed administration and JavaScript limitations remain relevant, but blanket rejection of Atlas-like search primitives is inaccurate because $search/text is now documented.
- **Source:** https://learn.microsoft.com/azure/documentdb/compatibility-query-language; https://learn.microsoft.com/azure/documentdb/compare-mongodb-atlas; https://learn.microsoft.com/azure/documentdb/full-text-search-overview
- **Why the confusion arose:** An older service feature snapshot was treated as current, while wire compatibility was used to infer broad exclusions instead of checking the feature matrix.
- **Risk to the build:** The builder may unnecessarily constrain versions or invent transaction workarounds. No cross-shard transaction is needed for this sample.

### Q11: Which local image and port should development use?

- **Outcome:** partly_wrong, confused with `open_source_documentdb`
- **From memory:** ghcr.io/microsoft/documentdb/documentdb-local:latest on localhost:10260.
- **From sources:** The documented gateway image is ghcr.io/documentdb/documentdb/documentdb-local:latest. MongoDB traffic uses port 10260. Local connections require credentials and TLS, with certificate-validation relaxation confined to the self-signed local environment.
- **Source:** documentdb-local-deployment; https://learn.microsoft.com/azure/documentdb/development-loop
- **Why the confusion arose:** The answer remembered the engine's earlier Microsoft repository/registry ownership rather than the current DocumentDB organization path.
- **Risk to the build:** The supplied image reference may not pull, and merely exposing the port does not complete local authentication and TLS configuration.

### Q12: Are change streams supported, and what must be enabled?

- **Outcome:** partly_wrong, confused with `legacy_vcore_naming`
- **From memory:** Enable a cluster-wide ChangeStreams preview feature before collection.watch().
- **From sources:** Change streams are supported and official examples use collection.watch(). Current documentation specifically gates multishard support and pre-images through support requests; it does not prescribe a universal ChangeStreams flag for every cluster.
- **Source:** https://learn.microsoft.com/azure/documentdb/change-streams; https://learn.microsoft.com/azure/documentdb/release-notes
- **Why the confusion arose:** The older gated-preview release state was generalized into a permanent, universal activation requirement.
- **Risk to the build:** The builder could add unnecessary provisioning steps or an unsupported flag. Change streams are outside this sample's scope.

### S03: What IVF index definition should the small catalog use?

- **Outcome:** partly_wrong
- **From memory:** createIndexes on embedding with cosmosSearch, vector-ivf, numLists=100, COS, dimensions=1536.
- **From sources:** The shape, kind, metric, and dimensions are correct. For the review's roughly 20-product demonstration, official guidance recommends starting with numLists=1. Larger values must be selected from document count and validated for recall/latency; nProbes defaults to one.
- **Source:** https://learn.microsoft.com/azure/documentdb/vector-search; https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm
- **Why the confusion arose:** A plausible generic IVF example value was promoted to a catalog-specific recommendation without considering the tiny dataset or number of probed clusters.
- **Risk to the build:** Overpartitioning a tiny catalog with one probed cluster can reduce recall and jeopardize the expected top-10 results. A creation failure was not demonstrated.

### S05: Must ingestion precede IVF creation, and what Flask/JSON contract should be used?

- **Outcome:** could_not_verify, confused with `unknown`
- **From memory:** Populate embeddings before IVF creation so it establishes useful clusters; POST /search accepts query, embeds it, searches, and stringifies ObjectIds.
- **From sources:** The official Python comparison sample inserts documents before creating indexes, so that workflow has a source-backed precedent. However, the general vector tutorial creates IVF before insertion, and neither source establishes a mandatory training-order rule. The selected POST contract and ObjectId serialization are application design decisions, not a verified DocumentDB-specific requirement.
- **Source:** https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm; https://learn.microsoft.com/azure/documentdb/vector-search
- **Why the confusion arose:** General IVF training intuition was treated as a service requirement despite opposite ordering in official examples. The reviewed sources do not settle that causal claim.
- **Risk to the build:** Not central: seed-before-index with numLists=1 is a supported example workflow. Do not claim that opposite ordering is forbidden, and explicitly define and test the Flask JSON contract.

## Information nobody could supply

- No chosen managed cluster, application URI, database permissions, or confirmed firewall/private-network route is supplied. MCP discovery does not answer these application prerequisites.
- No embedding provider is selected and no live ada-002 access or credentials are established. Public OpenAI is a disclosed review assumption, not a user requirement.
- The inventory does not establish pip/venv, installed Python packages, or a tested dependency combination on Python 3.14.10.
- The service-wide retryable-write capability remains contradictory across skills and official documentation, including false in the authentication URI table and true in its Python example. The Python vector quickstart does provide a usable false setting for this sample.
- Official sources show both seed-before-IVF and IVF-before-seed ordering without explaining mandatory training behavior, rebuild requirements, or small-catalog clustering semantics.
- The vector page says number[] is accepted but double[] is not, while its Python examples use float lists. A precise cross-language BSON encoding explanation is missing; use the provided Python list representation and validate indexed results rather than inventing a binary-vector requirement.
- The catalog contents, license, HTTP request/response/error contract, dependency-pinning policy, and offline test acceptance criteria remain author choices. Roughly 20 synthetic products and POST JSON are reasonable disclosed assumptions.
- Docker is installed, but the local image cache, daemon availability, running gateway, and exact managed/local feature parity are not established.
- Current documentation and installed skills disagree on broader search capability boundaries. This is noncentral to the verified IVF pipeline, but agents should not infer that shared Atlas-style operator names prove either compatibility or incompatibility.

## Corrections passed to the builder

- Start with an API-only Flask app against an existing managed cluster. Do not provision resources automatically. This run permits no writes; provide seed/index scripts for user-authorized execution and use mocked tests until credentials and permissions are configured.
- Use one PyMongo MongoClient per process, the portal-issued mongodb+srv URI, TLS, and retryWrites=false for this vector sample. Override the installed connection/driver examples that use true. Sources: documentdb-driver/driver-singleton-client.md and https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm.
- Do not use the connection skill's managed non-SRV port-10255 example. Official troubleshooting prescribes the portal SRV string and port 10260. Source: https://learn.microsoft.com/azure/documentdb/troubleshoot-common-issues.
- For the approximately 20-product demonstration, create the requested vector-ivf index with embedding:'cosmosSearch', dimensions:1536, similarity:'COS', and numLists:1 rather than copying 100. Explain larger-catalog numLists/nProbes tuning. Source: https://learn.microsoft.com/azure/documentdb/vector-search.
- Keep the verified $search/cosmosSearch pipeline with k=10 and project searchScore and product fields, excluding embeddings. Ensure at least ten successfully indexed products and account for index readiness. Sources: https://learn.microsoft.com/azure/documentdb/vector-search and https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm.
- For optional current CLI instructions, use az documentdb mongocluster from the documentdb extension. The installed CLI 2.73.0 is below its 2.75.0 minimum; portal or generic ARM inspection is the immediate workaround. Source: https://learn.microsoft.com/cli/azure/documentdb/mongocluster.
- For optional local tests, use ghcr.io/documentdb/documentdb/documentdb-local:latest on port 10260 with configured credentials and local TLS settings. Never propagate local certificate-validation relaxation to the managed URI. Sources: documentdb-local-deployment and https://learn.microsoft.com/azure/documentdb/development-loop.
- Do not add lexical/hybrid search to satisfy this vector-only prompt. If later requested, use the new createSearchIndexes/BM25 path and arrange gated-preview access rather than presenting legacy $text/textScore as the current full-text engine. Source: https://learn.microsoft.com/azure/documentdb/full-text-search-overview.
- Keep text-embedding-ada-002 for both ingestion and query generation, with a 1,536-element numeric vector. If Azure OpenAI is selected, model refers to the configured deployment name; public OpenAI uses the model name. Sources: https://learn.microsoft.com/azure/search/vector-search-how-to-generate-embeddings and https://learn.microsoft.com/azure/foundry-classic/openai/how-to/switching-endpoints.
- Have the user enter database and embedding secrets locally, not in chat or agent-generated files. An existing MCP connection profile does not supply Flask's DOCUMENTDB_URI. Source: documentdb-mcp-setup.

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
