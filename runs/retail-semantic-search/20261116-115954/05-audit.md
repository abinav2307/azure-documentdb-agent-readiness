# 5. Best-practice audit: retail-semantic-search

**Verdict: pass_with_findings** (37 followed, 15 not assessable, 2 not applicable, 8 violated)

The Flask, ada-002, native IVF and top-10 search implementation is present, with environment-backed secrets, reusable clients, idempotent seeding, scored results and offline tests. The trace confirms successful offline verification, not managed-service acceptance. Before publishing, add bounded transient-fault handling and batched seeding, supply optional cluster infrastructure, and resolve the reference requirement for BSON binary vectors against the documented numeric-array examples. Of the nine requirements predicted at risk, binary storage and infrastructure were missed; the other seven were delivered. The literal prohibition on mentioning neighbouring names was also not met, although the README correctly distinguishes the services rather than confusing them. Documentation search was reachable. Important product-team findings are conflicting connection/retry guidance, incomplete vector-encoding guidance, missing gallery-wide acceptance rules, and guidance found only through targeted searches. The 19 decision records contain two different decisions named D002 and no D003.

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Public availability of best practices

| Outcome | Count | What it means |
|---|---|---|
| On the checklist, no public source found | 6 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 9 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 24 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 10 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 13 | Public and discoverable. |

### On the checklist, no public source found

This section lists checklist items where neither the agent’s open search nor a search by name found a public source. Of the six, only one is a real documentation gap. The other five are showing up here because of how I wrote the starter checklist, not because the docs are missing something.

- The driver version is pinned and is one the service supports. (searched: Searched Azure DocumentDB supported/pinned PyMongo versions and loaded documentdb-driver. The compatibility page accepts wire-protocol drivers and the quickstart gives minimum versions, but no exact-version validation matrix or pinning recommendation was found.)
- If sharded, explain the shard key choice. (searched: Searched Azure DocumentDB shard-key explanation and data-modeling/sharding guidance. Found selection recommendations, not a requirement that gallery samples document the rationale.)
- README states demonstration, prerequisites, setup, run and cleanup. (searched: Searched Azure DocumentDB sample README guidelines and prerequisite/setup/run/cleanup requirements; loaded local/deployment skills. Found example sections, not a complete gallery README rule.)
- The sample runs with the README commands. (searched: Searched sample command-verification guidance and inspected build commands. No live application credentials or authorized target was supplied, and no complete README-command acceptance run was recorded.)
- Tests exist and pass without live cloud resources, or their prerequisites are documented. (searched: Searched Azure DocumentDB offline/cloud-free sample-test requirements and loaded local-prod-parity. It covers container integration tests, not this gallery acceptance rule.)
- Dependencies are pinned. (searched: Searched Azure DocumentDB dependency-pinning/sample policy and loaded driver/local/vector skills. Some tutorials pin individual packages, but no recommendation to pin all sample dependencies was found.)

### On the checklist, found only when searched for by name

- A .env.example lists every required setting with placeholder values. ([Azure DocumentDB MCP Toolkit configuration reference; local-env-driven-config](https://learn.microsoft.com/azure/documentdb/mcp-toolkit#configuration-reference))
- Documents cannot grow without bound; no unbounded arrays. ([documentdb-data-modeling: model-embed-vs-reference](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md))
- Full-text or hybrid search uses the supported mechanism. ([Full-text search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/full-text-search-overview))
- Aggregation pipelines use only supported stages and operators. ([MongoDB Query Language compatibility in Azure DocumentDB; Integrated vector store](https://learn.microsoft.com/azure/documentdb/compatibility-query-language))
- Bulk loads are batched. ([Quickstart: Vector index with Python in Azure DocumentDB, insert_data](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm))
- Infrastructure is code using the service's own resource type. ([Quickstart: Deploy an Azure DocumentDB cluster using Bicep](https://learn.microsoft.com/azure/documentdb/quickstart-bicep))
- Tier, storage and region are parameters with low-cost defaults. (documentdb-azure-deployment: Step 0.5 and references/bicep-cluster-template.md, no public address recorded)
- Clean-up steps are provided. ([Quickstart: Vector index with Python in Azure DocumentDB, Clean up resources](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm))
- Name the service correctly; do not call it a former or neighbouring product. ([What is Azure DocumentDB?, Naming and history](https://learn.microsoft.com/azure/documentdb/overview#naming-and-history))

### Found publicly, not on the checklist

- Create IVF with createIndexes, an embedding cosmosSearch key and vector-ivf kind. ([Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index))
- Retrieve through $search/cosmosSearch with indexed path, query vector and k=10. ([Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index))
- Project similarity with $meta: searchScore. ([Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index))
- Use a bounded representative-search readiness loop after vector-index construction. ([Quickstart: Vector index with Python in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm))
- Keep one vector index per path; explicitly replace it when changing algorithms. ([Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search))
- Normalize COS text embeddings at ingestion. ([documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md))
- Create indexes after the initial bulk data load. ([Indexing Best Practices in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-create-indexes#queryable-fields-should-always-have-indexes-created))
- Review explain output for important queries. ([Frequently asked questions about Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/faq#how-do-i-scale-performance-in-azure-documentdb))
- Include schemaVersion in product documents. ([documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md))
- Keep product BSON documents below 16 MB. ([Document size and batch write limits in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/max-document-size))
- Leave small catalogs unsharded unless single-shard capacity is exceeded. ([Sharding for horizontal scalability in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/partitioning#best-practices-for-sharding-data))
- Export diagnostic logs on eligible cluster tiers. ([Monitor Azure DocumentDB diagnostics logs with Azure Monitor](https://learn.microsoft.com/azure/documentdb/how-to-monitor-diagnostics-logs))
- Provide workload-appropriate resource-saturation alerts. ([documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md))
- Exclude sensitive information from resource names and tags. ([Sharding for horizontal scalability in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/partitioning#best-practices-for-sharding-data))
- Use the portal-issued SRV URI and preserve service hostname/options. ([Troubleshoot common issues in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/troubleshoot-common-issues))
- Retain default maxPoolSize unless workload context justifies tuning. ([documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md))
- Percent-encode reserved credential characters when inserting them into a connection URI. ([Use VisuaLeaf to connect to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-connect-visualeaf#connect-by-using-visualeaf))
- Use a separate read-only runtime user while accounting for cluster-wide native roles. ([Azure DocumentDB service limits and quotas reference](https://learn.microsoft.com/azure/documentdb/limitations#authentication-and-access-control-role-based-access-control))
- Restrict cluster access using private endpoints or narrowly scoped firewall rules. ([Secure your Azure DocumentDB cluster](https://learn.microsoft.com/azure/documentdb/security#transport-security))
- Use stable IDs and idempotent upserts when seeding. ([Build a Python console app with Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-build-python-console-app#perform-common-operations))
- Store embedding model and version metadata to support migration. ([documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md))
- Use the same ada-002 model for query and catalog embeddings. ([Tutorial: Generate AI advertisements with Azure DocumentDB and Azure OpenAI](https://learn.microsoft.com/azure/documentdb/tutorial-ai-advertisement-generation))
- Record the BSON vector storage representation decision explicitly. (Audit of decisions.jsonl against implementation, no public address recorded)
- Decision IDs uniquely identify each logged choice. (Machine trace and decision log, no public address recorded)

### Known to the model, no public source, not on the checklist

- Initialize MongoClient after prefork worker creation. (MongoDB prior belief, no public address recorded)
- Configure appName for application-identifiable database diagnostics. (MongoDB prior belief, no public address recorded)
- Ignore real .env files and commit only placeholder .env.example values. (General prior belief; corroborating local-env-driven-config found during audit, no public address recorded)
- Redact secrets from logs and exception responses. (General prior belief, no public address recorded)
- Use integer minor units or Decimal128 for monetary prices. (MongoDB prior belief, no public address recorded)
- Regenerate embeddings when embedded source text changes. (General prior belief, no public address recorded)
- Separate embeddings from different models into different fields or collections. (General prior belief, no public address recorded)
- Store flat BSON numeric arrays containing finite values. (Azure Cosmos DB prior belief; partial Azure DocumentDB numeric-array examples, no public address recorded)
- Validate every stored and query vector has exactly 1536 elements. (General prior belief, no public address recorded)
- Embed a deterministic combination of title and description. (General prior belief; starter prompt independently requires both fields, no public address recorded)

### On the checklist and found by open discovery

- One client is created and reused for the life of the process. ([Use LangGraph with Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/persist-agent-state#get-started-install-dependencies))
- Connection settings follow the service's recommendation for the chosen driver. ([Quickstart: Vector index with Python in Azure DocumentDB; documentdb-connection](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm))
- No password, key or full connection string appears in source, config, tests or README. ([Quickstart: Use vector search with Python in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-vector-search#create-utility-functions))
- Use requested authentication; use Microsoft Entra ID when available or state why not. ([Secure your Azure DocumentDB cluster](https://learn.microsoft.com/azure/documentdb/security#transport-security))
- Document shapes match demonstrated access patterns. ([Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#how-does-a-vector-store-work))
- Every app query pattern is served by an index, and no index is unused. ([Indexing Best Practices in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-create-indexes#queryable-fields-should-always-have-indexes-created))
- Vector index type and parameters suit data size, and dimensions match the model. ([Tutorial: Generate AI advertisements with Azure DocumentDB and Azure OpenAI; Integrated vector store](https://learn.microsoft.com/azure/documentdb/tutorial-ai-advertisement-generation))
- Transient failures are retried as the service recommends. ([Reliability in Azure DocumentDB](https://learn.microsoft.com/azure/reliability/reliability-documentdb#resilience-to-transient-faults))
- Use numLists=1 for a tiny demonstration and document catalog-growth tuning. ([Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index))
- Tune nProbes against recall/latency and keep it no greater than numLists. ([Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index))
- Use IVF on M10+ for demonstrations; prefer DiskANN on M30+ for production. ([Quickstart: Vector index with Python in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm))
- Require TLS with certificate and hostname validation for managed connections. ([documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md))
- Choose finite connection timeouts based on application latency context. ([documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md))

## How the app measures up

### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Transient failures are retried as the service recommends. | Reliability | app/app.py:30-37 immediately returns 503; app/seed.py:25-54,80-82 aborts on database errors. No bounded exponential-backoff wrapper exists; retryWrites is disabled. | Retry documented transient database failures with bounded exponential backoff within the operation deadline. Preserve retryWrites=False for this vector sample and retry only safely idempotent seed operations; test eventual success and exhaustion. | [Reliability in Azure DocumentDB](https://learn.microsoft.com/azure/reliability/reliability-documentdb#resilience-to-transient-faults) |
| Bulk loads are batched. | Reliability | app/seed.py:28-49 performs separate reads and writes for every product; no batch operation exists. | Collect changed stable-ID replacement operations into bounded collection.bulk_write batches, retaining cached embeddings and idempotency. Respect service batch-count and payload limits. | [Quickstart: Vector index with Python in Azure DocumentDB, insert_data](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm) |
| Infrastructure is code using the service's own resource type. | Provisioning | D015 and app/README.md:24 explicitly omit infrastructure. The README identifies Microsoft.DocumentDB/mongoClusters correctly but supplies no template. | Ship optional parameterized cluster infrastructure and safe deployment/teardown instructions without executing them automatically. | [Quickstart: Deploy an Azure DocumentDB cluster using Bicep](https://learn.microsoft.com/azure/documentdb/quickstart-bicep) |
| Tier, storage and region are parameters with low-cost defaults. | Provisioning | app/README.md:19 lists illustrative M10/32 GiB/eastus2 values, but there is no infrastructure or parameter file. | Add tier, storage and location parameters with explicit development defaults and no hard-coded production-region assumption. | documentdb-azure-deployment: Step 0.5 and references/bicep-cluster-template.md |
| Review explain output for important queries. | query optimization | app/catalog.py:106-107 only executes the aggregation; app/README.md:82-104 provides result smoke checks but no explain workflow. Build events record no explain operation for this catalog. | Add a user-authorized query-plan diagnostic command or README procedure and document expected index use. Do not replace live plan evidence with mocked assertions. | [Frequently asked questions about Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/faq#how-do-i-scale-performance-in-azure-documentdb) |
| Provide workload-appropriate resource-saturation alerts. | observability | app/README.md:60 only suggests adding monitoring later; there are no alert definitions or actionable configuration steps. | Provide optional tier-aware alert examples or link an actionable monitoring setup procedure, clearly separated from the local demonstration. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |
| Record the BSON vector storage representation decision explicitly. | audit trail | app/catalog.py:81 and app/seed.py:44 choose ordinary float-array storage. D007/D008 discuss vectors and validation, but no decision explicitly compares BSON array versus Binary storage; app/README.md:103 does. | Log the storage encoding, its source and unverified service acceptance, including why binary encoding was not selected. | Audit of decisions.jsonl against implementation |
| Decision IDs uniquely identify each logged choice. | audit trail | decisions.jsonl:2-3 and events.jsonl:67-68 record two different decisions as D002; D003 is absent. | Make the decision logger assign unique monotonic IDs atomically; do not rely on record count as proof of uniqueness. | Machine trace and decision log |

### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| The driver version is pinned and is one the service supports. | Connection | Searched Azure DocumentDB supported/pinned PyMongo versions and loaded documentdb-driver. The compatibility page accepts wire-protocol drivers and the quickstart gives minimum versions, but no exact-version validation matrix or pinning recommendation was found. | checklist only |
| The sample runs with the README commands. | Sample hygiene | Searched sample command-verification guidance and inspected build commands. No live application credentials or authorized target was supplied, and no complete README-command acceptance run was recorded. | checklist only |
| Export diagnostic logs on eligible cluster tiers. | observability | Inspected README, app and build trace for target tier and diagnostic settings. The M10 illustration is not evidence of the user's actual cluster or log eligibility. | [Monitor Azure DocumentDB diagnostics logs with Azure Monitor](https://learn.microsoft.com/azure/documentdb/how-to-monitor-diagnostics-logs) |
| Initialize MongoClient after prefork worker creation. | connection handling | Open discovery searched Azure DocumentDB PyMongo/Gunicorn fork initialization and site-specific fork guidance without finding a service-specific source. | MongoDB prior belief |
| Configure appName for application-identifiable database diagnostics. | observability | Open discovery searched Azure DocumentDB MongoClient appName diagnostics without finding a service-specific recommendation. The MCP page shows appName configuration but does not establish this recommendation. | MongoDB prior belief |
| Ignore real .env files and commit only placeholder .env.example values. | authentication and secrets | Open discovery did not find the complete convention. During this audit, loading local-env-driven-config explicitly revealed .gitignore/.env.example guidance; the supplied practice's prior-knowledge classification is retained. | General prior belief; corroborating local-env-driven-config found during audit |
| Redact secrets from logs and exception responses. | authentication and secrets | Open discovery searched Azure DocumentDB redact/password/API-key/logging recommendations without finding the complete service-specific rule. | General prior belief |
| Use a separate read-only runtime user while accounting for cluster-wide native roles. | authentication and authorization | Inspected configuration and README and fetched native-role limitations. No runtime identity or role assignments were supplied; README omits the cluster-wide scope caveat. | [Azure DocumentDB service limits and quotas reference](https://learn.microsoft.com/azure/documentdb/limitations#authentication-and-access-control-role-based-access-control) |
| Restrict cluster access using private endpoints or narrowly scoped firewall rules. | provisioning and security | Inspected app, README and build trace for networking definitions or target-cluster inspection. No infrastructure or relevant live cluster configuration was supplied. | [Secure your Azure DocumentDB cluster](https://learn.microsoft.com/azure/documentdb/security#transport-security) |
| Use integer minor units or Decimal128 for monetary prices. | data modeling | Open discovery searched Azure DocumentDB monetary-price modeling. Decimal128 support and example float prices do not establish a recommendation. | MongoDB prior belief |
| Regenerate embeddings when embedded source text changes. | data modeling | Open discovery searched Azure DocumentDB source-text changes and re-embedding without finding an explicit service recommendation. | General prior belief |
| Separate embeddings from different models into different fields or collections. | vector search | Open discovery searched Azure DocumentDB multiple-model vector-space separation without finding the specific fields/collections rule. | General prior belief |
| Store flat BSON numeric arrays containing finite values. | vector data modeling | The vector page requires number[] and shows float lists but also warns against double[]; it does not precisely establish the complete BSON/finite-value rule or binary-vector alternative. | Azure Cosmos DB prior belief; partial Azure DocumentDB numeric-array examples |
| Validate every stored and query vector has exactly 1536 elements. | vector search | Open discovery found dimension-matching guidance but not an explicit requirement to validate every vector before submission. | General prior belief |
| Embed a deterministic combination of title and description. | embedding generation | Open discovery searched deterministic Azure DocumentDB product title/description embedding guidance without locating a public service rule. | General prior belief; starter prompt independently requires both fields |

### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| One client is created and reused for the life of the process. | Connection | app/catalog.py:20-22,32-51; app/tests/test_sample.py:157-173. | [Use LangGraph with Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/persist-agent-state#get-started-install-dependencies) |
| Connection settings follow the service's recommendation for the chosen driver. | Connection | app/catalog.py:40-48 enforces SRV, validated TLS, SCRAM and retryWrites=False; D006 discloses the 30-second operation budget and resolves conflicting examples for this vector scenario. | [Quickstart: Vector index with Python in Azure DocumentDB; documentdb-connection](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm) |
| No password, key or full connection string appears in source, config, tests or README. | Authentication and secrets | app/catalog.py:38-49; app/.env.example:3-4; app/tests/test_sample.py:158 uses an invalid test URI; app/tests/test_driver_options.py:13 generates a throwaway password. No real application credentials were observed. | [Quickstart: Use vector search with Python in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-vector-search#create-utility-functions) |
| Use requested authentication; use Microsoft Entra ID when available or state why not. | Authentication and secrets | The prompt specifies no authentication method. D005 states the simplest local-sample rationale; app/README.md:14,20,60 describes SCRAM and the production Entra alternative. | [Secure your Azure DocumentDB cluster](https://learn.microsoft.com/azure/documentdb/security#transport-security) |
| A .env.example lists every required setting with placeholder values. | Authentication and secrets | app/.env.example:3-6 lists the settings consumed at app/catalog.py:38-39,67; secret values are placeholders. | [Azure DocumentDB MCP Toolkit configuration reference; local-env-driven-config](https://learn.microsoft.com/azure/documentdb/mcp-toolkit#configuration-reference) |
| Document shapes match demonstrated access patterns. | Data model | app/seed.py:44-46 colocates product fields and vectors; app/catalog.py:98-102 returns display data without a second lookup. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#how-does-a-vector-store-work) |
| Documents cannot grow without bound; no unbounded arrays. | Data model | app/data/products.json:2-21 has fixed scalar product fields; app/catalog.py:73-81 fixes vector length; app/seed.py:44-49 replaces documents rather than appending arrays. | [documentdb-data-modeling: model-embed-vs-reference](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Every app query pattern is served by an index, and no index is unused. | Indexing and queries | app/seed.py:31,49 uses _id point operations; app/catalog.py:93-107,120-124 pairs semantic retrieval with the embedding index. No unrelated indexes are created. | [Indexing Best Practices in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-create-indexes#queryable-fields-should-always-have-indexes-created) |
| Vector index type and parameters suit data size, and dimensions match the model. | Indexing and queries | app/catalog.py:12-19,96 uses ada-002, 1536 dimensions and one IVF list/probe for 20 products; app/README.md:99-100 explains scaling. | [Tutorial: Generate AI advertisements with Azure DocumentDB and Azure OpenAI; Integrated vector store](https://learn.microsoft.com/azure/documentdb/tutorial-ai-advertisement-generation) |
| Aggregation pipelines use only supported stages and operators. | Indexing and queries | app/catalog.py:93-103 uses documented $search/cosmosSearch, $project and $meta: searchScore. | [MongoDB Query Language compatibility in Azure DocumentDB; Integrated vector store](https://learn.microsoft.com/azure/documentdb/compatibility-query-language) |
| Clean-up steps are provided. | Provisioning | app/README.md:106-108 explains dedicated database/collection deletion, local-secret cleanup and optional dedicated-cluster deletion. | [Quickstart: Vector index with Python in Azure DocumentDB, Clean up resources](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm) |
| README states demonstration, prerequisites, setup, run and cleanup. | Sample hygiene | app/README.md:1-14,16-45,47-80,106-108. | checklist only |
| Tests exist and pass without live cloud resources, or their prerequisites are documented. | Sample hygiene | app/tests/test_sample.py:16-173; app/tests/test_driver_options.py:9-20; app/README.md:82-95; events.jsonl:114 records successful offline tests. | checklist only |
| Dependencies are pinned. | Sample hygiene | app/requirements.txt:1-4 pins direct dependencies; app/README.md:18 explicitly says transitives are not locked. | checklist only |
| Name the service correctly; do not call it a former or neighbouring product. | Sample hygiene | app/README.md:1-5 correctly names Azure DocumentDB and explicitly excludes neighbouring services. This satisfies correct naming, unlike the reference file's stricter literal ban on mentioning them. | [What is Azure DocumentDB?, Naming and history](https://learn.microsoft.com/azure/documentdb/overview#naming-and-history) |
| Create IVF with createIndexes, an embedding cosmosSearch key and vector-ivf kind. | vector indexing | app/catalog.py:16-19,120-124. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |
| Retrieve through $search/cosmosSearch with indexed path, query vector and k=10. | vector queries | app/catalog.py:93-107. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |
| Project similarity with $meta: searchScore. | vector queries | app/catalog.py:101. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |
| Use numLists=1 for a tiny demonstration and document catalog-growth tuning. | vector tuning | app/catalog.py:18; app/README.md:99-100. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |
| Tune nProbes against recall/latency and keep it no greater than numLists. | vector tuning | app/catalog.py:18,96 uses one list/probe; app/README.md:100 instructs measurement and bounds. No tuning is necessary for the single-list demo. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index) |
| Use IVF on M10+ for demonstrations; prefer DiskANN on M30+ for production. | vector indexing and sizing | app/README.md:19 requires M10+; lines 99-100 distinguish the tiny IVF sample from larger workloads. | [Quickstart: Vector index with Python in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm) |
| Use a bounded representative-search readiness loop after vector-index construction. | vector index lifecycle | app/seed.py:57-66,76-78 checks ten finite scored hits; app/README.md:58 notes query errors require rerunning. | [Quickstart: Vector index with Python in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm) |
| Keep one vector index per path; explicitly replace it when changing algorithms. | vector index lifecycle | app/catalog.py:110-124 reuses a matching index and refuses a conflicting one. It does not silently create or drop an alternative index. | [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search) |
| Normalize COS text embeddings at ingestion. | embedding generation | app/catalog.py:72-86; app/seed.py:43. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Create indexes after the initial bulk data load. | seeding and indexing | app/seed.py:75-76 loads products before first index creation. | [Indexing Best Practices in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-create-indexes#queryable-fields-should-always-have-indexes-created) |
| Include schemaVersion in product documents. | data modeling | app/seed.py:44. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Keep product BSON documents below 16 MB. | data modeling | app/data/products.json:2-21 has small fixed product strings; app/catalog.py:73 fixes vectors at 1536 elements; app/seed.py:44-46 adds only bounded metadata. | [Document size and batch write limits in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/max-document-size) |
| Leave small catalogs unsharded unless single-shard capacity is exceeded. | sharding | app/README.md:10; app/seed.py:73-77 issues no sharding command for the 20-product catalog. | [Sharding for horizontal scalability in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/partitioning#best-practices-for-sharding-data) |
| Exclude sensitive information from resource names and tags. | naming and security | app/catalog.py:67-68 uses retail/products; no personal resource names or tags are supplied. | [Sharding for horizontal scalability in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/partitioning#best-practices-for-sharding-data) |
| Use the portal-issued SRV URI and preserve service hostname/options. | connection handling | app/catalog.py:38,40-48 consumes the provided URI rather than reconstructing a host; app/README.md:41 explains preserving portal options, with the disclosed retry/TLS overrides. | [Troubleshoot common issues in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/troubleshoot-common-issues) |
| Require TLS with certificate and hostname validation for managed connections. | connection security | app/catalog.py:43-44; app/tests/test_sample.py:168-170. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Choose finite connection timeouts based on application latency context. | connection handling | app/catalog.py:46-49 bounds database operations and embedding calls; D006 and app/README.md:14 disclose the small synchronous-demo assumption rather than claiming universal timeout values. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Retain default maxPoolSize unless workload context justifies tuning. | connection handling | app/catalog.py:42-48 supplies no pool-size override; D006 and app/README.md:14 disclose why defaults remain. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Percent-encode reserved credential characters when inserting them into a connection URI. | authentication and secrets | app/README.md:41 instructs encoding; app/catalog.py:38-42 consumes an already prepared URI and does not interpolate credentials. | [Use VisuaLeaf to connect to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-connect-visualeaf#connect-by-using-visualeaf) |
| Use stable IDs and idempotent upserts when seeding. | data modeling and seeding | app/data/products.json:2-21 supplies stable IDs; app/seed.py:49 uses replace_one(..., upsert=True), an equivalent stable-ID upsert rather than the discovered example's update_one. | [Build a Python console app with Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-build-python-console-app#perform-common-operations) |
| Store embedding model and version metadata to support migration. | data modeling | app/seed.py:32-46 stores and checks model/dimension/version/hash metadata; app/README.md:101 describes versioned migration. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Use the same ada-002 model for query and catalog embeddings. | vector search | app/catalog.py:12,65-69,84-86 provides the shared embedding function used by app/app.py:32 and app/seed.py:43. | [Tutorial: Generate AI advertisements with Azure DocumentDB and Azure OpenAI](https://learn.microsoft.com/azure/documentdb/tutorial-ai-advertisement-generation) |

### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| If sharded, explain the shard key choice. | Data model | app/README.md:10 explicitly states the catalog is unsharded. | checklist only |
| Full-text or hybrid search uses the supported mechanism. | Indexing and queries | app/README.md:14 excludes lexical/hybrid search; app/catalog.py:93-103 is vector-only. | [Full-text search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/full-text-search-overview) |

## Reference requirements

15 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| Embeddings are stored as BSON binary vectors. | not_met | skill_silent | app/catalog.py:81 returns ordinary float lists; app/seed.py:44 stores those lists directly. No BSON Binary vector conversion exists. | Add a vector-skill rule defining the service-supported BSON representation, subtype and driver conversion. Do not require binary storage until its IVF support is documented and tested; otherwise change the reference requirement to supported numeric arrays. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No infrastructure files were supplied; app/README.md:14,24 explicitly excludes resource deployment. D015 deliberately omitted even an optional template. | Add a gallery-sample rule: ship optional parameterized Microsoft.DocumentDB/mongoClusters infrastructure even when the app consumes an existing cluster; generating files does not authorize deployment. |
| The sample uses the name Azure DocumentDB throughout, and no former or neighbouring product name. | partly_met | prompt_silent | app/README.md:1-5 names the target correctly, but line 5 explicitly mentions Amazon DocumentDB and Azure Cosmos DB for MongoDB (RU) to disambiguate it. Native cosmosSearch identifiers are required API names, not incorrect branding. | Define the naming rule as: name the target Azure DocumentDB; permit explicit disambiguation and required legacy API identifiers. If the literal ban is intentional, state it in the gallery-sample skill. |
| A vector-ivf index exists on the embedding field. | not_checkable | tool_unavailable | app/catalog.py:16-19,110-124 defines and creates the correct index; app/seed.py:76 invokes creation. app/README.md:95 explicitly says live creation was not verified. | Supply an authorized disposable application cluster and acceptance runner with permission to seed, create the index and inspect its definition. |
| The app is a Python Flask app. | met | - | app/app.py:2,10-11,43 creates and exports a Flask application. | - |
| Products are stored in an Azure DocumentDB collection. | met | - | app/catalog.py:38-48,65-69 connects using the managed SRV URI and selects products; app/seed.py:44-49 persists product documents. Actual ingestion was not executed. | - |
| Product titles and descriptions are embedded with text-embedding-ada-002. | met | - | app/catalog.py:12,84-90 fixes the model and combines title and description; app/seed.py:29,43 embeds that text. | - |
| /search takes a natural language query, embeds it, and returns the 10 most similar products. | met | - | app/app.py:19-38 validates and embeds query text; app/catalog.py:93-107 requests k=10 through native cosmosSearch. app/seed.py:57-66 checks ten scored hits. Live relevance remains unverified. | - |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/catalog.py:25-29,37-49 reads DOCUMENTDB_URI and OPENAI_API_KEY; app/.env.example:3-4 contains placeholders. Tests use invalid or generated throwaway credentials, not application secrets. | - |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example:3-6 lists both required secrets and the optional database setting. retail is the documented nonsecret sample default; app/catalog.py:38-39,67 uses exactly these application settings. | - |
| The vector index dimensions match the embedding model's output. | met | - | app/catalog.py:12-18 uses ada-002 with dimensions=1536; lines 72-86 validate every generated vector. | - |
| The vector index parameters are chosen for the catalog size, and the README says how to change them for a larger one. | met | - | app/catalog.py:18,96 uses numLists=1 and nProbes=1; app/data/products.json:2-21 contains 20 products; app/README.md:99-100 explains growth tuning. | - |
| One database client is created and reused across requests. | met | - | app/catalog.py:20-22,32-51 implements a locked process-wide singleton; app/tests/test_sample.py:157-173 checks reuse. | - |
| A seed script loads sample products and creates the index, and can be run twice without duplicating data. | met | - | app/seed.py:17-54,73-77 loads stable IDs, performs replace_one upserts and creates the index; app/tests/test_sample.py:132-145 checks repeated seeding. | - |
| /search returns a clear error for an empty query and when the embedding call fails. | met | - | app/app.py:27-37 returns 400 for empty input and generic 503 errors for OpenAI/configuration failures. The offline suite does not specifically inject an OpenAIError. | - |
| Search results include the similarity score. | met | - | app/catalog.py:98-102 projects score using $meta: searchScore; app/app.py:38 returns it. | - |
| Dependencies are pinned in requirements.txt. | met | - | app/requirements.txt:1-4 pins all four direct dependencies. | - |
| Unit tests run without a live cluster. | met | - | app/tests/test_sample.py:16-28,41-173 uses fakes and mocks; app/tests/test_driver_options.py:11-20 uses connect=False. events.jsonl:114 records a successful final offline test run. | - |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md:1-14,16-45,47-80,106-108 covers all five sections. | - |

## Review of the builder's decisions

| Decision | Assessment | Comment |
|---|---|---|
| D001 | sound | Operator approval permits proceeding despite acknowledged gaps; it is not a claim that live acceptance passed. The readiness guidance at 02-readiness.json:450-460 explicitly limits execution. |
| D002 (decisions.jsonl:2) | sound | events.jsonl:51,58 confirms two Azure best-practices failures, specifically missing chat-client configuration. Lines 52-66 confirm skills and Learn fallback. The logged error wording is paraphrased, but the unavailable-capability claim is supported. |
| D002 (decisions.jsonl:3) | sound | API-only POST design fits the prompt. 02-readiness.json:451 prohibits automatic provisioning/live writes. Providing optional infrastructure files would still have been permissible. This record improperly shares D002 with another decision. |
| D004 | sound | Pins match app/requirements.txt:1-4; events.jsonl:69,106,114 supports testing on the available runtime. Python 3.11+ is an explicitly untested compatibility claim, not a verified runtime matrix. |
| D005 | questionable | Public OpenAI and SCRAM are disclosed local-sample choices and do not contradict the prompt. However, the loaded security rule and Python vector quickstart prefer Entra/passwordless authentication. The README supplies the exception rationale; it should also explain native roles' cluster-wide scope. |
| D006 | sound | events.jsonl:53-54,60-62,70-71 confirms the cited skills/docs were loaded. The vector quickstart explicitly supports false; retaining default pools and disclosing an operation budget follows context-first guidance despite conflicting generic connection examples. |
| D007 | sound | events.jsonl:55,64 confirms data-modeling guidance was loaded. app/seed.py:44-46 colocates bounded product data and vectors; the tiny unsharded catalog fits public sharding guidance. Illustrative floating-point prices are not an accounting implementation. |
| D008 | sound | The prompt fixes ada-002; app/catalog.py:12-18,72-90 implements shared 1536-dimensional normalized embeddings. events.jsonl:59 confirms the normalization rule was read. Binary storage was neither requested nor established by that rule. |
| D009 | sound | Fetched vector guidance supports numLists=1 for tiny demos, nProbes<=numLists, native cosmosSearch and searchScore. app/catalog.py:16-19,93-103,120-124 matches these choices. |
| D010 | sound | Stable-ID replacement upserts and readiness polling are implemented and tested. The documented seed-before-index precedent holds; the decision correctly avoids claiming mandatory IVF training order. Readiness polling retries empty results, not raised transient errors. |
| D011 | sound | Offline tests, limits and generic errors are implemented at app/app.py:12-37 and app/tests/test_sample.py. No-retry OpenAI behavior is a disclosed budget choice, not a service recommendation. Add an explicit embedding-error test before publication. |
| D012 | sound | events.jsonl:80-84 confirms venv creation, refusal of the POSIX path and subsequent use of the Windows executable. This was a recoverable platform-path mismatch. |
| D013 | sound | events.jsonl:84-86 records package installation and the isolated-target fallback; lines 106,114 confirm isolated imports/tests. Package-conflict output is truncated in the trace, so the stronger claim about executable resolution is not independently established. |
| D014 | sound | events.jsonl:95 shows only sales_forecast_db. Readiness prohibits writes and supplies no retail application target. Deferring live acceptance and not mutating unrelated data was correct. |
| D015 | questionable | M10/32 GiB/single-shard development sizing has first-party precedent, and events.jsonl:97 confirms deployment-skill loading. Keeping an existing-cluster scope is defensible, but the no-resource-change restriction does not prevent shipping optional infrastructure files. |
| D016 | sound | app/seed.py:32-46 checks metadata and validity while preserving cached values; app/tests/test_sample.py:132-145 supports skipped writes. This avoids unnecessary recomputation, but does not prove externally modified cached vectors remain unit-normalized. |
| D017 | sound | events.jsonl:100 records the quoting SyntaxError; lines 101-102 show the logged fallback and direct file replacement. |
| D018 | sound | events.jsonl:107-109 records the failing constructor probe and correction; app/catalog.py:43-44 retains validated TLS without redundant tlsInsecure. The final real-driver offline test is present. |
| D019 | sound | events.jsonl:110-114 records the second constructor failure, generated-credential regression test and successful final run. app/tests/test_driver_options.py:11-20 uses connect=False and never persists a password. |

Documentation gaps: 19 (see `doc-gaps.md`).

