# Retail semantic search — Azure DocumentDB + Flask

A small API-only sample that stores 20 synthetic products and their embeddings together in **Microsoft Azure DocumentDB**, creates a native **vector-ivf** index, and returns the top 10 products for a natural-language query.

This targets the managed MongoDB-compatible Azure service (`Microsoft.DocumentDB/mongoClusters`), **not Amazon DocumentDB or Azure Cosmos DB for MongoDB (RU)**. Legacy `cosmosSearch` names are the correct native vector API here.

## What happens

1. `seed.py` embeds `title + "\n" + description` with public OpenAI **text-embedding-ada-002**, validates **1,536** finite numbers, normalizes them, and upserts by stable SKU `_id`.
2. Products contain price (illustrative USD number), category, schema version, embedding model/dimension/version and text hash. This tiny collection is unsharded; there is no shard key. Embeddings stay in the product document and are never returned by the API.
3. The seed creates `embedding_ivf` with `{embedding: "cosmosSearch"}` and `cosmosSearchOptions = {kind: "vector-ivf", dimensions: 1536, similarity: "COS", numLists: 1}`. The only other index is the service's built-in unique `_id` index.
4. `POST /search` embeds the query with the same model and normalization, runs `$search` / `cosmosSearch` with `k=10`, `nProbes=1`, and projects product fields plus `$meta: "searchScore"`.

There is no chat, lexical/hybrid search, UI, checkout, or resource deployment. Clients are reused once per process; no client is constructed per request. Database connections enforce TLS, certificate/hostname validation, SCRAM-SHA-256 and **retryWrites=false**, following the Python vector quickstart rather than contradictory skill examples. Default pool sizes are retained; an entire database operation has a 30-second budget. OpenAI calls have a 30-second timeout and no automatic retries.

## Prerequisites

- Python **3.11+** and pip/venv. This build was tested on **Python 3.14.10**, not every supported runtime. Direct dependencies are pinned in `requirements.txt`; transitive dependencies are not locked.
- An **existing managed Azure DocumentDB cluster**, tier **M10+** for IVF, accessible from your machine. An illustrative dev configuration is M10, 32 GiB per shard, one shard, HA Disabled, eastus2; confirm region availability and quota yourself. These are dev defaults, not a production topology.
- A dedicated database for this sample (default `retail`, collection `products`). Seed credentials need read/write and index-creation permissions. After seeding, use a least-privilege read-only user for the API when possible.
- Your developer IP allowed by the cluster firewall, or a working private network route. Do not allow the entire Internet. Troubleshooting for managed connections uses port **10260**, not 10255; use the portal-issued SRV string rather than constructing an endpoint.
- A **public OpenAI API** account/key with access to `text-embedding-ada-002` and billing enabled. Public OpenAI is a disclosed author assumption, not Azure OpenAI. Query text and product title/description are sent to that provider. Embedding API calls and the cluster incur costs.

No Azure CLI, Docker, mongosh, or MCP setup is required. MCP connection profiles do **not** provide the Flask app's credentials. If you need a cluster, follow the [portal quickstart](https://learn.microsoft.com/azure/documentdb/quickstart-portal) separately; this repository creates no Azure resources.

## Setup

Create and activate a **fresh** virtual environment inside the clone:

```bash
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell instead:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create `.env` locally using `.env.example` as a guide, then enter your values locally (never paste credentials into chat or commit them):

- `DOCUMENTDB_URI`: exact `mongodb+srv://` connection string from **cluster → Connection strings** in the portal, with your credentials substituted. Percent-encode reserved characters in username/password. Preserve portal options; the code explicitly enforces TLS and `retryWrites=false`.
- `OPENAI_API_KEY`: your public OpenAI key.
- `DOCUMENTDB_DATABASE`: dedicated database name, default `retail`.

The shipped `.env.example` contains placeholders only. Environment variables take precedence over `.env`. Do not disable certificate validation to fix a managed connection. Keep your OS CA trust store up to date.

## Seed and run

**The following seed command writes documents and creates the vector index. Run it only with permission against your dedicated sample database.**

```bash
python seed.py
flask --app app run
```

The first seed generates 20 product embeddings. Reruns skip unchanged embeddings and documents; changed titles/descriptions are re-embedded, while price/category changes reuse the cached embedding. It never deletes unrelated products. A partial failure may leave some products saved; rerun safely after fixing the cause. Avoid concurrent seeding or manually mixing models in this collection.

Data is loaded **before** index creation. A matching existing index is reused; a conflicting embedding index causes a failure instead of being dropped. Index metadata may be returned under `cosmosSearch` or `cosmosSearchOptions`; both are recognized. The seed probes for **10 scored search hits** for up to 60 attempts separated by 3 seconds (plus query execution time). It only prints `Ready` after that check. If readiness times out or the service reports a query error, wait a few minutes and rerun. This is a smoke check, not a guarantee of recall across all products.

The Flask development server binds to localhost by default. Do not expose it publicly; this sample has no caller authentication or rate limiting. Do not preload the clients before forking production workers. For a production app, add auth, rate limiting, a production WSGI server, managed identity/Entra authentication, private networking and monitoring as appropriate.

### Search example

From another terminal (use `curl.exe` in Windows PowerShell if `curl` is an alias):

```bash
curl -X POST http://127.0.0.1:5000/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"lightweight gear for a rainy hiking trip"}'
```

Response shape (illustrative; actual scores/order come from DocumentDB):

```json
{"results":[{"_id":"sku-001","title":"Trail Daypack 20L","description":"...","price":59.99,"currency":"USD","category":"outdoors","score":0.84}]}
```

A ready 20-product catalog should return 10 products in similarity order. The API requests **up to 10**; an empty or incompletely indexed collection may return fewer. Scores are cosine similarity search metadata, not probabilities or guarantees of product suitability.

Contract: JSON object with a nonempty string `query` of at most 2,000 characters; surrounding whitespace is stripped. The entire request body is limited to 16 KiB. Malformed/invalid JSON input returns 400, non-JSON content returns 415, oversized bodies return 413, upstream/configuration failures return 503 with generic nonsecret messages. Other HTTP methods return 405. No embeddings or embedding metadata are projected into results.

## Verification

Offline tests perform **no network calls or database writes**:

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py catalog.py seed.py tests
```

Tests cover model/dimensions, vector validation/normalization, native IVF command and pipeline shapes, safe projection, request/error handling, client reuse/TLS settings, seed idempotency, and readiness requiring 10 scored hits. They use fakes, not a simulated proof of service compatibility.

For managed-service acceptance after configuring secrets: run `python seed.py` and confirm its top-10 scored readiness check; run the endpoint and check that 10 products are returned and embeddings are absent. Repeat seeding and expect `0 products updated, 20 unchanged`. Try a coffee-related and an outdoor-related query and inspect relevance. Do not infer acceptance merely from `listIndexes` succeeding.

This build executed offline tests only. Live embeddings, index creation/readiness, BSON numeric-array acceptance and managed search relevance were **not verified**, because application secrets/target cluster were not supplied and this run prohibited writes. Read-only MCP discovery found an unrelated `sales_forecast_db`, not this sample catalog.

## Tuning and troubleshooting

- **Small demo:** `numLists=1` searches all vectors (brute-force-like accuracy). Do not copy `100` from a large-dataset example into a 20-product catalog.
- **Growth:** the [vector documentation](https://learn.microsoft.com/azure/documentdb/vector-search) recommends approximately `documentCount / 1000` lists up to one million documents. Increase `nProbes` for recall, but keep `1 <= nProbes <= numLists`; measure recall and latency. For more than one million documents, prefer DiskANN on M30+. This sample deliberately keeps IVF as requested.
- **Model changes:** keep ingestion and query models/dimensions aligned; changing model or normalization needs a version bump and a full re-embedding migration. Do not casually change the dimensions constant.
- **Connection failure:** check SRV DNS, firewall/private route, percent-encoded credentials, TLS trust and least-privilege database access. `retryWrites=false` is an explicit vector-sample choice; service-wide retryable-write guidance is inconsistent.
- **No hits:** wait for index construction, rerun the seed probe, verify index path/dimensions, and verify at least ten valid vectors. Python stores ordinary lists of floats, as in official examples; no binary or typed-array encoding is invented here. Actual managed BSON/vector acceptance needs the live check.
- **OpenAI failure:** verify key, model access, billing and network. Ada-002 availability was not checked live. Azure OpenAI would require its own endpoint/auth configuration and a deployment name, not simply a replacement public API key.

## Cleanup

Stop the local server. In the Azure DocumentDB VS Code extension or another authorized database client, review and **delete only the dedicated sample database or `products` collection** when you no longer need it (this deletes its vector index too). Do not delete a shared database. No cleanup script runs automatically. Remove your local `.env` and virtual environment if desired, and revoke/rotate temporary credentials. If you separately created a dedicated cluster, delete that cluster through the portal to stop its charges; never delete a shared resource group for sample cleanup.

## References

- [Integrated vector store: IVF, native commands, query and tuning](https://learn.microsoft.com/azure/documentdb/vector-search)
- [Python vector algorithm quickstart: retryWrites=false and readiness](https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm)
- [Python vector search quickstart: seed before index](https://learn.microsoft.com/azure/documentdb/quickstart-python-vector-search)
- [Managed connection troubleshooting](https://learn.microsoft.com/azure/documentdb/troubleshoot-common-issues)
- [Entra/RBAC authentication](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control)

Product data is fictional and created for this sample; it contains no customer data or external catalog assets.
