# Retail semantic recommendations with Azure DocumentDB

A small JavaScript/Node.js **LlamaIndex function agent** that accepts a product ID and returns **five recommendations with reasoning**. Azure DocumentDB is Microsoft's managed MongoDB-compatible document database—not Amazon DocumentDB, MongoDB Atlas, or Azure Cosmos DB for MongoDB (RU).

## What this sample teaches

1. Ingest **20,000 synthetic purchase transactions** with 2–4 distinct products per order and a 60-product catalog. Stable IDs and upserts make reruns resumable without duplicates.
2. Read co-purchase order history from DocumentDB, enrich each product's embedding text with its top five co-purchase partners, and generate **1536-dimensional `text-embedding-3-small` embeddings** through LlamaIndex's OpenAI provider.
3. Store normalized numeric vectors alongside product metadata. Create a native **DiskANN** index using `cosmosSearch`, `COS`, `maxDegree=32`, `lBuild=50`.
4. Give a **LlamaIndex agent** a read-only MongoDB-driver retrieval tool. It retrieves 30 neighbors (`k=30`, `lSearch=40`), excludes the input product, and reranks with live co-purchase counts and session interests.
5. Explicitly pass completed session turns as agent `chatHistory`. Return trusted database IDs/titles/scores plus validated model explanations.

The documented DocumentDB LlamaIndex vector-store connector is **Python-only**. This Node.js sample follows the documented alternative: use the official MongoDB driver for `$search` / `cosmosSearch` inside an agent tool. It does not substitute Atlas `$vectorSearch` or a local brute-force vector store.

## Prerequisites

- Node.js **22 LTS (latest patch) or newer**, npm, and outbound model API access. Verification in the builder environment used Node.js 26.13.0, not Node.js 22.
- An **existing managed Azure DocumentDB M30-or-higher cluster**. DiskANN requires M30+. No cloud resources, firewall rules, storage settings, HA settings or shards are provisioned/changed by this sample. Confirm the actual tier in your portal; this build could not confirm it.
- A native-authentication user permitted to read/write the dedicated sample database and create indexes. After ingestion the agent needs read access only.
- Network access through your existing firewall client-IP rule or private endpoint. Do not open all IP addresses or disable certificate checks to troubleshoot.
- An OpenAI API key with access to `text-embedding-3-small` and `gpt-4o-mini`. Model access/quota is not established by an Azure CLI login.

Use an empty **`retail_semantic_sample`** database on a nonproduction cluster. The sample intentionally does not touch an existing `retail.products` catalog. Do not put unrelated documents into its collections. Collections remain unsharded; no shard key is needed for this tiny dataset. The service's current quickstart defaults to server version 8.0; this sample does not alter your existing server version (current documented compatibility spans 5.0–8.0).

## Install and configure

```sh
npm ci
```

Copy `.env.example` to `.env` **in your editor**, then populate it locally:

| Config variable | Value |
| --- | --- |
| `DOCUMENTDB_URI` | The native-authentication SRV connection string copied from **Azure portal → cluster → Connection strings**. Replace the portal password placeholder locally; percent-encode credential characters as required by MongoDB URI syntax. Do not construct a host name. |
| `OPENAI_API_KEY` | Your OpenAI key. |

`.env` is a configuration file loaded by Node into environment variables; `src/config.js` validates those variables. You can instead supply them through your shell's secret environment. Existing environment values take precedence over `.env`. Never paste credentials into chat, logs or a committed file. `.env.example` contains placeholders only.

The connected client enforces TLS with normal certificate validation, `SCRAM-SHA-256`, `retryWrites=false`, `retryReads=true`, `maxIdleTimeMS=120000`, and ten-second connection/server-selection timeouts. It reuses one connected MongoClient per process with default pool sizing. TLS bypass URI options are rejected. The `retryWrites=false` choice follows the native-auth quickstart; conflicting examples elsewhere do **not** establish a universal service-wide retryable-write support rule.

Missing/invalid URIs produce readable errors, for example:

```text
Error: DOCUMENTDB_URI is missing. Copy .env.example to .env and paste your Azure portal connection string.
Error: DOCUMENTDB_URI is invalid. Use the portal native-auth mongodb+srv URI ...
```

A syntactically valid but unreachable/unauthorized connection produces a safe error suggesting credentials, firewall/private routing and TLS checks. Raw driver exceptions are not printed because they might include secrets. A successful connect is explicitly pinged before use.

## Ingest

**This command writes sample data and makes paid OpenAI embedding calls.** Run it only on your intended test cluster:

```sh
npm run ingest
```

Expected successful summary: 20,000 orders, 60 products, and up to 60 newly embedded products. Orders are batched in groups of 500. Model calls are sequential with two retries and a 60-second API timeout. Only catalog items—not all orders—are embedded. An input hash and model/version metadata reuse unchanged embeddings on reruns. A changed co-purchase context triggers re-embedding. Interrupted ingestion is not atomic; rerun it to resume.

Each order embeds a bounded `items` array of `{productId, quantity}` references. An ascending **multikey** index on `orders.items.productId` supports the first `$match` in the co-purchase pipeline. The aggregation counts **distinct shared orders**, not quantities or duplicated lines. `_id` indexes support deterministic product/order upserts. No TTL, full-text, extra filter or shard indexes are created.

Each product stores `_id`, title, description, category, `schemaVersion`, embedding, embedding text, source hash, model, dimensions and embedding version. Avoid mixing models in this collection. A model/dimension change requires re-embedding and a deliberate index rebuild; the sample never drops indexes automatically.

## Run recommendations

One turn (JSON to stdout):

```sh
npm start -- sample-p001 demo-session
```

Multiple turns in the **same process**:

```sh
npm start -- sample-p001 alice --interactive
```

Then enter:

```text
sample-p031 alice
sample-p002 alice
sample-p002 bob
exit
```

Input syntax is `productId [sessionId]`; omitting the session uses the initial session ID. Prompts/errors go to stderr. Use `npm start -- --help` for usage. Product IDs run from `sample-p001` to `sample-p060`.

Output is an object with `sessionId`, input `productId`, and five `recommendations`. Each has `productId`, `title`, `category`, the database's `similarityScore`, `coPurchaseCount`, `sessionAffinity`, `rankingScore`, and `reasoning`. The model cannot change the trusted IDs, order, titles or scores. Invalid/missing/duplicated IDs or explanations fail closed rather than being shown as recommendations.

### Ranking and memory

This is a teaching heuristic, **not a trained recommender**:

```text
rankingScore = 0.55 × clamp(COS score, 0, 1)
             + 0.35 × (shared orders / largest candidate shared-order count)
             + 0.10 × (fraction of recent inputs in the candidate's category)
```

Ties break by product ID. Input categories are implicit session interests, not inferred purchases or explicit dislikes. Scores may change with history without changing all five selected IDs. The agent explains the fixed ranking evidence and reads previous completed turns to contextualize its response. Reasoning is model-generated and can still be inaccurate despite structural validation; review it before production use.

Memory is a per-session process-local map, bounded to **100 LRU sessions and ten completed turns each**. A fresh workflow gets that session's history on every call, so no workflow memory is shared between sessions. Separate one-shot CLI processes do not share memory. Restart/exit clears it; an evicted session starts empty. This CLI processes turns sequentially; it is not a concurrent authenticated multi-user API. Session IDs are not an authorization system.

The tool's closure fixes the current product and session; the agent cannot issue arbitrary MQL or write to DocumentDB. Catalog/previous output are treated as untrusted data in the prompt. Only synthetic titles/descriptions and aggregate co-purchase context are sent for embedding; recommendation candidates and recent session turns are sent to OpenAI for chat. Review privacy/provider policies before using real customer data. No telemetry is added by this sample.

If fewer than five valid indexed neighbors exist, the app returns an explicit error. It never fills results with invented items. Confirm ingestion completed, the index is ready and the cluster is M30+. Unknown IDs, provider failures and incompatible embedding metadata also produce actionable errors.

## Verification

Offline:

```sh
npm test
npm run check
```

Tests use Node's built-in runner and execute the **real installed LlamaIndex workflow** with a fake streaming tool-calling model and database doubles. They cover configuration/error redaction, deterministic 20,000-order generation, batched idempotent upserts, ingestion embedding caching, native query/index shape, finite vectors, ranking, bounded session isolation, explicit chat-history injection, five-item output and failure behavior. These are not live model/database integration tests.

After your authorized ingestion, run the read-only integration check (it includes a paid chat call):

```sh
npm run verify:live
```

It verifies counts, DiskANN settings, order index existence and a query explain with evidence of index usage, then runs a real five-item agent recommendation. It does not create, delete or modify data. Live ingestion, DiskANN build/queries, model access and recommendation quality were **not executed in the builder environment**: OPENAI_API_KEY was missing and the isolated sample database was empty. A DocumentDB URI supplied through the runner environment did allow a successful driver connect/ping and read-only checks: zero sample collections/documents, an accepted co-purchase aggregation returning an empty result, and the expected unknown-product error. No data or indexes were changed. A configured MCP database profile is not proof of M30 readiness.

**Dependency security:** installation reported three high-severity findings. Detailed `npm audit` failed with HTTP 429 from the package proxy, so affected-package details/remediation and a clean audit remain unverified. Review `npm audit` when the registry permits it before using this sample beyond a controlled demo; do not blindly force upgrades across the matched LlamaIndex peer versions.

## Clean up

- Exit the CLI to release the shared database pool and clear session memory.
- In the DocumentDB portal/extension, verify you are targeting **only `retail_semantic_sample`**, then delete that dedicated database (both products/orders and their indexes) if no longer needed. Do not delete your preexisting cluster or unrelated retail database.
- Delete your local `.env` when finished. Revoke the key/user if created solely for this sample.
- The existing cluster continues to incur charges; deleting sample data does not remove it. Manage its lifecycle separately with its owner.

## Code map and references

- `src/config.js`, `database.js`: safe env config, singleton connection and ping.
- `src/catalog.js`, `ingestion.js`, `scripts/seed.js`: deterministic seed and cached embeddings.
- `src/repository.js`: co-purchase aggregation and DiskANN command/query.
- `src/memory.js`, `recommendations.js`: bounded session memory, agent tool, ranking and validation.
- `src/models.js`, `cli.js`: provider setup and interactive CLI.
- `scripts/verify-live.js`, `test/sample.test.js`: live verifier and offline tests.
- `DECISIONS.md`: supplemental decisions after the audit tool failed.

Service references:
- [Node.js quickstart](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs)
- [Integrated vector store / DiskANN](https://learn.microsoft.com/azure/documentdb/vector-search)
- [LlamaIndex integration and Node.js driver alternative](https://learn.microsoft.com/azure/documentdb/query-knowledge-base)

SDK contracts were checked against the installed declarations for LlamaIndex 0.12.1, workflow 1.1.24 and OpenAI provider 0.4.22 (matching core/env peers). Versions are exact-pinned and the npm lockfile is committed.
