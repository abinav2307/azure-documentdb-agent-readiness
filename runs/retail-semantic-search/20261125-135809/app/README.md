# Retail recommendations with Azure DocumentDB + LlamaIndex

A small JavaScript CLI that takes a product ID and returns **five ranked items with evidence-based explanations**. Azure DocumentDB is Microsoft's managed MongoDB-compatible document database—not Amazon DocumentDB or Azure Cosmos DB for MongoDB (RU).

## What this sample shows

- One reused official MongoDB client, TLS with certificate verification, SCRAM-SHA-256 and `retryWrites=false`.
- 120 synthetic products embedded with OpenAI `text-embedding-3-small` (1,536 dimensions), stored as normalized numeric arrays with model/version metadata.
- A real **DiskANN** `embedding: cosmosSearch` index (`COS`, `maxDegree=32`, `lBuild=50`). No IVF/HNSW fallback.
- 20,000 synthetic order documents, each containing 3–5 distinct product IDs/quantities. An explicit multikey index on `items.productId` supports co-purchase lookup.
- A LlamaIndex single-tool agent (`gpt-4o-mini`) uses a read-only MongoDB retrieval tool. The documented DocumentDB vector-store adapter is Python-only; this JavaScript sample issues native `$search` / `cosmosSearch` queries.
- LlamaIndex conversation memory and viewed-category preferences are isolated by session label. Memory is **in process**, bounded to six successful chat turns / twenty category views / twenty sessions, and disappears on restart or eviction. Session labels are not authentication.

## Prerequisites

1. Node.js **22 LTS or newer**, with npm. `.nvmrc` selects 22. This build was tested on Node **26.13.0**; Node 22 was not executed in the build environment.
2. An **existing managed Azure DocumentDB M30+ cluster** supporting DiskANN. Verify tier in the portal. This repository does not provision or change region, storage, sharding, HA or firewall settings.
3. A reachable network path (private endpoint/VPN or a narrowly scoped firewall rule). TLS uses the runtime/system CA trust; do not disable certificate verification.
4. A dedicated native database user permitted to read/write the sample database and create indexes. Prefer least privilege, not an administrator account; rotate credentials. For production, consider Entra/RBAC and private networking. This sample implements native authentication only.
5. An OpenAI API key with access to `text-embedding-3-small` and `gpt-4o-mini`. Embedding catalog text and sending recommendation evidence/history incur provider charges. The provider is **OpenAI, not Azure OpenAI**; no additional Azure model resources are created.

## Setup: config selects an environment variable

```sh
npm ci
```

Copy `config.example.json` to `config.json` using your editor or file manager:

```json
{ "connectionStringEnv": "DOCUMENTDB_URI" }
```

**Do not put the connection string itself in a file.** The config file selects the environment variable containing it. This keeps configuration explicit while avoiding secrets on disk. `config.json` and `.env` are gitignored; `.env.example` is a placeholder reference only and is not loaded by the app.

Set `DOCUMENTDB_URI` in the current shell to your cluster's portal-provided SRV connection string, with URL-encoded credentials. Require TLS and `retryWrites=false`; the client enforces these and SCRAM-SHA-256 even if omitted. The validator rejects incompatible TLS/auth/retry options, unsupported host formats and malformed URIs. Azure portal cluster hosts under `mongocluster.cosmos.azure.com` and `mongocluster.documentdb.azure.com` are supported (including regional/global prefixes).

Bash example (prompts avoid storing values in shell history):

```sh
read -rsp 'DocumentDB URI: ' DOCUMENTDB_URI; echo
export DOCUMENTDB_URI
read -rsp 'OpenAI key: ' OPENAI_API_KEY; echo
export OPENAI_API_KEY
```

PowerShell example (the prompts mask input; environment variables necessarily hold plaintext in process memory):

```powershell
$env:DOCUMENTDB_URI = [System.Net.NetworkCredential]::new('', (Read-Host 'DocumentDB URI' -AsSecureString)).Password
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'OpenAI key' -AsSecureString)).Password
```

Missing/malformed config, missing URI, invalid URI, failed connectivity and missing model key produce actionable errors with a nonzero exit code. Raw driver/model errors and stacks are not displayed because they can reveal credentials.

## Ingest and verify

```sh
npm run ingest
npm run verify
```

Ingestion targets only **`retail_semantic_sample_v1.products` and `.orders`**. Existing `retail.products` (which might use IVF or another model) is never touched. The namespace is fixed deliberately to reduce accidental reuse. Foreign sample/schema/model markers or incompatible vector definitions cause refusal; do not remove those guards to migrate real data.

The deterministic generator uses seed 42, four categories, three variants per item, and 80% same-category item picks. It upserts 20,000 stable order IDs in acknowledged batches of at most 500 documents / 1 MiB BSON. Products are embedded sequentially (120 provider calls on first run); compatible existing vectors are reused on rerun. Failed ingestion stops rather than claiming success; rerun to resume partial acknowledged batches. Successful reruns retain exactly 120 products and 20,000 unique orders. Don't run concurrent ingestions.

`npm run verify` is database-only and does not need `OPENAI_API_KEY`. It checks counts, stored embedding metadata, actual DiskANN options, vector retrieval, distinct top-five IDs and the co-purchase `executionStats` plan. It prints both vector and order query plans for inspection. If the order lookup has no reported index access, verification fails. If search returns too few indexed vectors, let indexing finish and retry; index creation and propagation must succeed on the actual managed tier.

## Run the agent

```sh
npm start
# Or perform a single request and exit:
node src/cli.js p0001
```

Interactive input:

```text
/session alice
p0001
p0002
/session bob
p0002
/session alice
/reset
/quit
```

`p0001` is an Everyday Hiking backpack; `p0002` is Everyday Trail shoes. Alice's second request uses her prior outdoor view and conversation; Bob's first request starts with empty memory. Observe `priorViewedCategories` and `evidence.sessionPreference` in the JSON. Alice's second-turn outdoor candidates get a preference boost; after `/reset`, the boost disappears. Rankings can remain identical when the same candidates already lead—personalisation changes scores, not a guarantee of different items.

Every item includes `productId`, `title`, `category`, blended `score`, evidence (`semanticRank`, raw `vectorScore`, `coPurchaseCount`, `sessionPreference`) and a short generated `reason`. The code validates that the agent explains exactly the retrieved five IDs in order. Invalid model output is rejected, not replaced by invented items. Explanations are concise evidence summaries, not hidden chain-of-thought. Their factual quality still requires live review.

## How ranking works

1. Fetch the input product's stored embedding; check model and dimensions.
2. DiskANN retrieves twenty candidates with `k=20`, `lSearch=40` (`lSearch >= k`), explicitly projecting `searchScore`.
3. Aggregate orders containing the product, unwind items, exclude the input, and count **distinct co-purchase orders**, not purchased units.
4. Union ANN candidates with the top twenty co-purchased products, so complementary items can compete even when they are not semantically similar substitutes. Exclude the input product.
5. Rank with `0.45 × semanticRank + 0.40 × (coPurchaseCount / maxCount) + 0.15 × priorCategoryFrequency`. Semantic rank is `1 - ANN_position / 20`; co-purchase-only candidates get zero semantic rank. Raw search scores are diagnostic, not assumed to have a particular range. Break ties by product ID and return five.
6. The LlamaIndex agent explains the tool evidence, and only successful turns update session memory. The model cannot choose another session, run arbitrary MongoDB queries or write data.

Weights, batch sizes, synthetic distribution and memory limits are disclosed sample defaults, **not trained or benchmarked recommendations**. Co-purchase is synthetic association, not causation or real customer behavior. No real customer data, telemetry or recommendation-quality benchmark is included. A larger system should evaluate relevance/recall, apply inventory/business constraints, use authenticated session ownership, and design persistent memory retention intentionally.

## Tests and build verification

```sh
npm test
npm run check
npm audit --omit=dev
```

Offline tests cover deterministic 20,000-order generation, normalization, index definition checks, query shapes, category-based score changes, actual LlamaIndex tool execution with a mocked streaming LLM, session isolation/reset, invalid agent output, missing configuration/URI handling and idempotent ingestion with an in-memory collection fixture. Mocks live only in tests; the application never generates fake embeddings or substitutes an offline model at runtime.

Build verification: 12 tests passed; 12 JavaScript files passed syntax checking; dependency audit reported zero vulnerabilities. Read-only MCP inspection confirmed an existing `retail.products` IVF index and an empty isolated namespace. **Live ingestion, DiskANN query/index creation, model calls, M30+ tier and permissions were not verified** because OPENAI_API_KEY was missing and no sample data/index writes were performed. A runtime environment check subsequently found DOCUMENTDB_URI; an application-driver TLS connection and ping passed and confirmed the sample namespace was empty. Write permissions and cluster tier remain unconfirmed. MCP profiles do not export application credentials. The optional parser dependency emitted an npm install-script warning; the CLI, embeddings and workflow imports worked without approving that unrelated script.

## Cleanup

1. Exit the CLI (`/quit`); the singleton closes. Clear the shell environment variables (`unset DOCUMENTDB_URI OPENAI_API_KEY` in Bash; `Remove-Item Env:DOCUMENTDB_URI, Env:OPENAI_API_KEY` in PowerShell).
2. After confirming it contains only this sample's data, use the Azure DocumentDB VS Code extension or the portal's MongoDB data tools to delete **only** `retail_semantic_sample_v1.products` and `.orders`, or drop that isolated sample database. This removes its sample indexes too. No cleanup script is provided to avoid accidental destructive execution.
3. Remove local `config.json` if desired. Do **not** delete the cluster, `retail.products`, other databases or model resources; none were provisioned by this sample.

## References

- [Azure DocumentDB vector search / DiskANN](https://learn.microsoft.com/azure/documentdb/vector-search)
- [LlamaIndex integration and JavaScript driver guidance](https://learn.microsoft.com/azure/documentdb/query-knowledge-base)
- [Node.js MongoDB driver quickstart](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs)
- [Entra ID and RBAC](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control)
- [LlamaIndex.TS](https://github.com/run-llama/LlamaIndexTS)
