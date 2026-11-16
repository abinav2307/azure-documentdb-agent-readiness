# 2. Build readiness: retail-semantic-search

**Verdict: ready_with_gaps**

Coding can start: the sample's central facts are verified—ada-002 produces 1536-dimensional vectors, Azure DocumentDB supports IVF, numLists=1 is documented for small demos, and $search.cosmosSearch retrieves the top k matches. End-to-end execution is not established: database access, embedding-provider credentials, and Python dependencies were not inventoried. The optional DocumentDB MCP server failed, but PyMongo is a workable substitute. The largest product friction is contradictory connection guidance, including conflicting retryWrites settings and incorrect endpoints in installed skills, plus CLI naming/version drift. No resources or database contents were changed.

## Blockers

None.

## Tools for this sample

| Tool | Kind | Available | Needed for | Detail | If missing | Workaround |
|---|---|---|---|---|---|---|
| python | cli | yes | Run Flask, product ingestion, embedding calls, and tests. | Python 3.14.10. The review's Python 3.11 assumption does not match the machine. | The Python application cannot execute. | Use the installed runtime with compatible dependency versions; select another supported runtime if dependency installation fails. |
| pip and venv | cli | **no** | Install and isolate the application's dependencies. | Availability was not measured; allowed commands are not proof of installation. | Dependency installation and reproducible execution are not established. | During the build, use python -m venv and python -m pip if present; otherwise bootstrap the Python packaging environment. |
| Flask | other | **no** | Expose the /search HTTP endpoint. | Python package installation was not inventoried; this does not establish that Flask is absent. | The HTTP application cannot run. | Install a compatible, pinned Flask release in the project environment. |
| PyMongo | other | **no** | Store products, create the IVF index, aggregate search results, and replace missing data-plane MCP tooling. | Package installation was not inventoried. Official Python vector examples use PyMongo; OIDC requires PyMongo 4.7 or later. | No database operations or live validation. | Install a compatible PyMongo release and its SRV-resolution dependencies in the project environment. |
| openai Python package | other | **no** | Generate product and query embeddings through OpenAI or Azure OpenAI. | Package installation was not inventoried. | Ingestion and semantic queries cannot generate embeddings. | Install a compatible pinned release; choose and document one provider configuration. |
| DocumentDB connection credential and reachable managed cluster | credential | **no** | Authenticate, seed products, create indexes, and search against Azure DocumentDB. | No cluster URI, native database credential, database role assignment, tier, or network reachability was established. Azure sign-in does not establish database access. | Managed-service smoke testing cannot run. | The user supplies DOCUMENTDB_URI locally and confirms database permissions and network access. Coding and mocked tests can proceed meanwhile; the local engine is not proof of managed-service acceptance. |
| Embedding-provider credential and model access | credential | **no** | Call text-embedding-ada-002 for ingestion and /search. | Neither OPENAI_API_KEY nor an Azure OpenAI endpoint, deployment, key, or authorized identity was inventoried. | Live ingestion and semantic search cannot complete. | The user configures credentials locally. For Azure OpenAI, supply an existing ada-002 deployment name and endpoint; use mocks only for offline tests. |
| az | cli | yes | Optional read-only inspection of an existing managed cluster and its networking. | Azure CLI 2.73.0 with cosmosdb-preview 1.7.0. The current documentdb extension requires CLI 2.75.0 or later. | Convenient resource inspection is lost, not application execution. | Use the portal or generic az resource show/az rest against Microsoft.DocumentDB/mongoClusters. |
| Azure CLI documentdb extension | cli | **no** | Current branded cluster-inspection commands and accurate setup documentation. | Not listed among installed extensions; installed CLI is below the documented minimum. | az documentdb mongocluster commands cannot be assumed to work on this machine. | Use generic ARM inspection now; later upgrade CLI to 2.75.0 or newer and install the documentdb extension. |
| az login | credential | yes | Azure resource inspection; optionally provides the local identity for Entra authentication. | Signed in to subscription cosmosdb-programmability-demo-1mqps. Database and embedding-service authorization remain unverified. | Authenticated Azure inspection and CLI-backed token acquisition fail. | Sign in when needed, or use the sample's native database and embedding API credentials. Do not equate Azure sign-in with data-plane permission. |
| documentdb-vector-search | skill | yes | Index selection, dimensions, similarity, and retrieval syntax. | Installed and loaded; IVF guidance is complemented by Microsoft Learn's explicit small-demo numLists recipe. | Greater risk of Atlas or Cosmos NoSQL vector syntax being substituted. | Use https://learn.microsoft.com/azure/documentdb/vector-search. |
| documentdb-driver | skill | yes | One thread-safe MongoClient per process, reused across Flask requests. | Installed and loaded. Its singleton example uses retryWrites=true, conflicting with sample-specific connection guidance. | Per-request client creation can cause connection churn and excess latency. | Follow the singleton rule but take connection settings from the managed-service documentation. |
| documentdb-connection | skill | yes | TLS, authentication, connection reuse, and appropriate timeouts. | Installed and loaded. It presents a non-SRV endpoint on port 10255 and recommends retryWrites=true; these conflict with managed-service connection documentation. | Connection configuration becomes less guided. | Use the portal-provided SRV URI and official connection documentation rather than copying this skill's alternative endpoint. |
| documentdb-data-modeling | skill | yes | Product document design and keeping searchable data with its embedding. | Installed; general modeling guidance, not a ready-made retail schema. | Schema and metadata decisions need more manual design. | Use one bounded document per product with stable IDs and model/dimension metadata. |
| documentdb-indexing | skill | yes | Relevant index-type guidance and avoiding unnecessary catalog indexes. | Installed. The vector-search skill and documentation supply the sample's required index syntax. | Less guidance on index selection and write cost. | Use the vector-search documentation; no broad indexing workflow is necessary for this small demo. |
| documentdb-security | skill | yes | Relevant TLS, firewall, and native-versus-Entra authentication guidance. | Installed. Production CMK and private-endpoint design are outside the assumed local Flask scope. | Higher risk of insecure certificate settings or confusing control-plane and database permissions. | Use official connection/RBAC documentation and keep credentials outside source control. |
| documentdb-local-deployment | skill | yes | Environment-driven configuration, seed workflow, and optional engine-level integration tests. | Installed and loaded. Its environment-config resource contains a managed host ending in mongocluster.documentdb.azure.com, unlike the officially documented cosmos.azure.com endpoints. | Local TLS and configuration setup require manual work. | Use its configuration discipline, but use official managed endpoint values and explicit local-only certificate relaxation. |
| documentdb-azure-deployment | skill | yes | Document cluster prerequisites and distinguish the managed resource from neighboring services. | Installed and loaded. Provisioning is not requested or authorized; its blanket unsupported-retryable-writes claim conflicts with other sources. | Cluster setup documentation is harder to produce accurately. | Assume a user-provided existing cluster and link to the portal quickstart. Do not execute deployment steps. |
| documentdb-mcp-setup | skill | yes | Recover the optional failed DocumentDB MCP accelerator. | Installed and loaded; documents CONNECTION_PROFILES and trusted local stdio settings. | More manual diagnosis of MCP startup and profile errors. | Use PyMongo without MCP or follow the upstream server setup documentation. |
| documentdb MCP server | mcp_server | **no** | Optional schema, query, aggregation, and index inspection during the build. | Inventory recorded a closed connection while starting npx github:microsoft/documentdb-mcp; zero tools returned. The cause was not established. | The agent cannot inspect the live data plane through MCP. | Use PyMongo. For repair, inspect startup logs and follow documentdb-mcp-setup; do not assume the failure was authentication-related. |
| azure MCP server | mcp_server | yes | Relevant documentation/best-practice lookups and optional ARM inspection. | Inventory: 73 tools. A Cosmos child-command discovery call failed during this assessment; server availability remains as inventoried. | Some Azure-specific assistance is lost. | Use Learn and Azure CLI. Cosmos account/container tools are not the sample's MongoDB-compatible data plane. |
| learn MCP server | mcp_server | yes | Verify service-specific facts and find official examples. | Three inventoried tools; search and fetch supplied the grounding in this report. | Contradictory skills and remembered compatibility claims are harder to resolve. | Consult the cited Microsoft Learn pages directly. |
| docker | cli | yes | Optional local engine integration tests. | Docker 29.9.3. Daemon readiness and the local image's presence were not inventoried. | Local real-engine testing is unavailable. | Use mocked tests and later validate against a user-provided managed cluster. |
| mongosh | cli | **no** | Optional manual connection and index inspection. | Not found on PATH. | No standalone MongoDB shell checks. | Use PyMongo ping, list_indexes, and read-only aggregate operations. |
| node, npx, and git | cli | yes | Launch or repair the optional GitHub-based DocumentDB MCP server; git also supports source control. | Node v26.13.0, npx 11.20.0, git 2.56.0.windows.4. | The documented npx/GitHub MCP launch path is unavailable. | The Flask application does not require Node; use PyMongo directly. |

## Accelerators not installed

- Azure DocumentDB MCP Toolkit is configured but unusable, rather than simply uninstalled. Repair the documentdb entry using documentdb-mcp-setup: npx -y github:microsoft/documentdb-mcp, a locally supplied CONNECTION_PROFILES JSON string, TRANSPORT=stdio, AUTH_REQUIRED=false, and TRUST_LOCAL_STDIO=true. Keep write/management tool gates disabled for this assessment. The skill also provides the Windows installer: irm https://raw.githubusercontent.com/Azure/documentdb-agent-kit/main/install.ps1 | iex. These are repair instructions, not actions performed.
- Current branded Azure CLI documentdb extension is missing. Microsoft Learn documents CLI 2.75.0 or later and automatic extension installation on first use of az documentdb mongocluster. Generic ARM commands are a workaround.
- The local DocumentDB Gateway image is not confirmed present. Docker itself is installed; the inventory does not establish whether an image pull is needed. Image identified by documentdb-local-deployment: ghcr.io/documentdb/documentdb/documentdb-local:latest. Pin a tested version for reproducible tests.

## Service confusions

The model answered 20 questions from memory before reading any source: 15 correct, 4 wrong or partly wrong, 1 could not be verified.

### Q02: Which CLI group manages clusters, and is it core or an extension?

- **Outcome:** partly_wrong, confused with `legacy_vcore_naming`
- **From memory:** az cosmosdb mongocluster, from cosmosdb-preview.
- **From sources:** Current documentation uses az documentdb mongocluster from the documentdb extension, requiring Azure CLI 2.75.0 or later. This is not a core command group. The installed 2.73.0 CLI is below that requirement.
- **Source:** https://learn.microsoft.com/cli/azure/documentdb/mongocluster?view=azure-cli-latest
- **Why the confusion arose:** The remembered command retains the service's former Cosmos DB branding and extension name; current documentation has moved to a DocumentDB-branded extension.
- **Risk to the build:** Generated prerequisites and current CLI examples would disagree, and current commands would not work unchanged on the installed CLI.

### Q09: How are full-text and hybrid search done?

- **Outcome:** partly_wrong, confused with `mongodb_atlas_or_server`
- **From memory:** Create text indexes and use $text/textScore; do not use $search.text. Fuse keyword and cosmosSearch rankings with application RRF.
- **From sources:** Installed service guidance uses createSearchIndexes and $search.text with BM25 and searchScore, not the community text-index/$text path. Application-side reciprocal rank fusion with vector rankings is supported by the hybrid skill.
- **Source:** documentdb-full-text-search; documentdb-full-text-search/fts-hybrid-search.md
- **Why the confusion arose:** Shared MongoDB query conventions led to substituting community MongoDB text indexes, while overcorrecting against Atlas caused the cold answer to reject the service's documented $search.text path.
- **Risk to the build:** A later keyword/hybrid extension would use the wrong index and query path. This sample only requires vector search, so no lexical feature should be added merely to address this answer.

### Q10: Which compatibility versions and common feature limitations apply?

- **Outcome:** partly_wrong, confused with `azure_cosmos_db_for_mongodb_ru`
- **From memory:** 5.0, 6.0, 7.0, with 8.0 release-dependent; avoid mapReduce, capped/time-series collections, cross-shard transactions, and Atlas $vectorSearch/Search configuration.
- **From sources:** Official documentation lists wire protocol versions 5.0, 6.0, 7.0, and 8.0. Capped and time-series collections are listed as unsupported/not prioritized. Cross-shard read/write transactions are explicitly supported. Release notes also report $vectorSearch support, so treating that stage as necessarily Atlas-only is incorrect. No retrieved source settled mapReduce.
- **Source:** https://learn.microsoft.com/azure/documentdb/compare-amazon-documentdb; https://learn.microsoft.com/azure/documentdb/compatibility-features; https://learn.microsoft.com/azure/documentdb/partitioning; https://learn.microsoft.com/azure/documentdb/release-notes
- **Why the confusion arose:** The cross-shard transaction restriction matches the RU sibling's documented restriction. Shared MongoDB compatibility branding and an older feature snapshot also obscure newer 8.0 and $vectorSearch support.
- **Risk to the build:** Unnecessary feature avoidance and inaccurate README claims. The sample's documented cosmosSearch pipeline remains valid and needs neither transactions nor a different search stage.

### Q12: Are change streams supported and what must be enabled?

- **Outcome:** partly_wrong, confused with `legacy_vcore_naming`
- **From memory:** Enable previewFeatures=['ChangeStreams'] on the cluster, then call watch().
- **From sources:** Change streams and watch() are documented. Current documentation identifies multishard streams and pre-images as previews requiring a support request; it does not prescribe a universal previewFeatures=['ChangeStreams'] enablement step.
- **Source:** https://learn.microsoft.com/azure/documentdb/change-streams
- **Why the confusion arose:** An older gated-preview mental model appears to have been generalized into a current cluster-flag recipe. The exact proposed flag was not established by the source.
- **Risk to the build:** Unnecessary or unsupported cluster updates and misleading setup instructions. Change streams are not needed for this sample.

### Q06: Which authentication methods are supported, including Python Entra authentication?

- **Outcome:** could_not_verify, confused with `unknown`
- **From memory:** Native SCRAM-SHA-256 or MONGODB-OIDC, authSource=$external, OIDC_CALLBACK returning OIDCCallbackResult, scope https://ossrdbms-aad.database.windows.net/.default; separately authorize the identity.
- **From sources:** Native and Entra OIDC authentication are documented. The Python callback, token scope, and separate database authorization match official examples. Those examples do not explicitly set authSource=$external, so that particular setting was not independently established by the retrieved service documentation.
- **Source:** https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control; https://learn.microsoft.com/azure/documentdb/how-to-build-python-console-app
- **Why the confusion arose:** Most details are verified, but generic MongoDB OIDC settings can be carried into a service answer without appearing in that service's examples.
- **Risk to the build:** Not central under native-auth assumptions. If Entra is chosen, follow the official Python callback example and verify any additional settings rather than treating every cold detail as established.

## Information nobody could supply

- No target managed cluster, tier, URI, database permissions, or firewall/DNS reachability was established. These are user-specific inputs, not missing vector-search documentation.
- The embedding provider remains a choice: public OpenAI versus an existing Azure OpenAI ada-002 deployment. Account/model access, credentials, endpoint, quota, and any Azure deployment name are unverified.
- The inventory does not establish pip/venv or package availability, nor an exact tested Flask/PyMongo/openai dependency set on Python 3.14.10.
- Retryable-write support remains contradictory across installed skills and official pages. Even the RBAC page recommends false in its settings table but uses true in Python code. The documented false setting is sufficient to proceed with this vector demo, but the universal service claim is unresolved.
- Installed skills contain endpoint drift: documentdb-connection offers mongodb:// on 10255, while local-env-driven-config shows a managed documentdb.azure.com suffix. Neither should override the official SRV cosmos.azure.com endpoints.
- Official vector documentation says number[] works but double[] does not, while its Python examples use ordinary floating-point lists. The retrieved sources do not explain that distinction precisely in BSON/PyMongo terms. Use the documented Python-list pattern and validate live indexing later.
- The DocumentDB MCP startup failure's root cause is unknown; the inventory's generic Connection closed message does not distinguish package/build, transport, auth, or profile errors.
- The complete Q06 authSource=$external detail and Q10 mapReduce assertion were not verified; neither is central to the native-auth IVF sample.
- The user still needs an explicit API contract, synthetic catalog, error behavior, and dependency/test policy. The review's POST JSON, approximately 30 synthetic products, and local Flask assumptions are reasonable choices, not service-established requirements.
- The current read-only policy prevents this agent from seeding products or creating the required managed-service index. Those acceptance steps must be run by the user or in a separately authorized build phase.

## Corrections passed to the builder

- Use an existing managed Azure DocumentDB cluster and PyMongo; do not substitute Cosmos NoSQL SDKs, the Cosmos emulator, or a generic Azure Cosmos MCP data plane. Sources: quickstart-python and documentdb-mcp-setup.
- For current branded CLI documentation, use az documentdb mongocluster from the documentdb extension, requiring CLI 2.75.0 or later. On this machine, use generic read-only ARM inspection until upgraded. Source: https://learn.microsoft.com/cli/azure/documentdb/mongocluster?view=azure-cli-latest.
- Read the actual managed URI from local configuration. Use mongodb+srv, the portal-assigned cosmos.azure.com host, TLS, and the sample-supported retryWrites=false setting. Do not copy 10255 or the documentdb.azure.com host from conflicting skills. Sources: troubleshoot-common-issues and how-to-connect-role-based-access-control.
- Implement the verified sample configuration: 1536-dimensional numeric vectors, createIndexes with embedding:cosmosSearch, kind=vector-ivf, similarity=COS, numLists=1, and $search.cosmosSearch with k=10 plus searchScore projection. Sources: https://learn.microsoft.com/azure/documentdb/rag and https://learn.microsoft.com/azure/documentdb/vector-search.
- Do not describe cross-shard transactions or $vectorSearch as categorically unsupported. Current documentation supports cross-shard transactions and lists 8.0 compatibility; release notes report $vectorSearch support. Keep this sample on its verified cosmosSearch path rather than adding unrelated features.
- If keyword/hybrid search is later added, use createSearchIndexes and $search.text with BM25/searchScore, then fuse rankings as described by documentdb-full-text-search. Do not implement the cold $text/text-index recipe or add hybrid search to this vector-only prompt.
- Do not add previewFeatures=['ChangeStreams'] as a sample prerequisite. Change streams are unnecessary here; current change-stream documentation specifies support-request enablement for multishard preview scenarios.
- Reuse one MongoClient per process, but do not copy the singleton resource's retryWrites=true setting blindly. Separate the verified client-reuse rule from the unresolved service-wide retryability claim.
- Keep secrets in user-populated local environment variables, never chat or committed files. Choose the embedding provider explicitly; Azure OpenAI model must be the deployment name. Source: https://learn.microsoft.com/azure/developer/ai/how-to/switching-endpoints.
- For optional local integration tests, use the Gateway on 10260 with documented credentials, TLS, and explicit local-only certificate trust configuration. A passing open-source engine test is not a managed-service acceptance test. Source: documentdb-local-deployment/local-connection-config.md.
- Proceed with code and offline tests using the review's disclosed assumptions. Have the user perform managed seeding, index creation, and live search validation under appropriate authorization; do not execute those writes under the current policy.

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
| MCP `documentdb` | no | Failed to create MCP session for server 'C:\Program Files\nodejs\npx.CMD -y github:microsoft/documentdb-mcp': Connection closed |
| MCP `azure` | yes | 73 tools: azure_documentation, azure_azd, azure_foundry, azure_arm, azure_get_azure_bestpractices, azure_adme, azure_aks, azure_appconfig, azure_applens, azure_appservice, azure_role, azure_azurebackup ... |
| MCP `learn` | yes | 3 tools: learn_microsoft_docs_search, learn_microsoft_code_sample_search, learn_microsoft_docs_fetch |
| Agent skills | yes | documentdb-azure-deployment, documentdb-connection, documentdb-data-modeling, documentdb-driver, documentdb-full-text-search, documentdb-high-availability, documentdb-indexing, documentdb-local-deployment, documentdb-mcp-setup, documentdb-monitoring, documentdb-natural-language-querying, documentdb-query-optimization, documentdb-query-optimizer, documentdb-security, documentdb-sharding, documentdb-storage, documentdb-vector-search |
