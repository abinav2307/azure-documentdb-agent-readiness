# Decision log

| Reason came from | Decisions |
|---|---|
| tool_result | 9 |
| model_default | 3 |
| readiness_report | 2 |
| skill | 2 |
| operator | 1 |
| prompt | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T22:04:55+00:00

## D002 (build): I used installed DocumentDB skills and Microsoft Learn instead of the Azure AI best-practices router after two failures.

- **Instead of:** Retry the failed router again
- **Because:** The router is unavailable; service-specific skills and current Learn remain accessible.
- **Reason came from:** `tool_result`
- **Evidence:** azure_get_azure_bestpractices returned 'Error: Function failed.' twice.
- **When:** 2026-11-25T22:05:26+00:00

## D003 (build): I chose JavaScript ES modules targeting Node.js 22 LTS, with llamaindex 0.12.1, @llamaindex/openai 0.4.22, @llamaindex/workflow 1.1.24 and mongodb 6.22.0 pinned and a lockfile.

- **Instead of:** TypeScript or Python; Latest @llamaindex/openai 0.4.23; MongoDB driver 7
- **Because:** The review defaults to JavaScript/Node 22 and driver 6; registry metadata shows these exact LlamaIndex versions share core 0.6.22/env 0.1.30, unlike the latest provider. Tests will run on available Node 26; Node 22 remains unverified.
- **Reason came from:** `tool_result`
- **Evidence:** npm view: llamaindex 0.12.1 depends on core 0.6.22; openai 0.4.22 and workflow 1.1.24 peer core 0.6.22/env 0.1.30; node --version v26.13.0.
- **When:** 2026-11-25T22:05:49+00:00

## D004 (build): I chose a non-secret config.json that references DOCUMENTDB_URI, with all database and model secrets read only from environment variables and placeholder-only examples.

- **Instead of:** Put a credential-bearing URI in gitignored config.json; Entra OIDC
- **Because:** The user requests a config file, but developer limits prohibit writing any full connection string to a file. An environment reference satisfies config-driven connection setup without storing secrets. Native SCRAM-SHA-256 is the review's simple default; document least-privilege credentials and TLS with certificate validation.
- **Reason came from:** `prompt`
- **Evidence:** User: 'Use a config file for the Azure DocumentDB connection string'; developer: 'Never write a secret ... or full connection string into a file. Read them from environment variables'.
- **When:** 2026-11-25T22:05:55+00:00

## D005 (build): I chose an existing M30+ cluster with no provisioning or management changes and isolated retail_semantic_sample_v1.products/orders collections, leaving retail.products untouched.

- **Instead of:** Migrate existing retail.products; Provision a new cluster; Use local Docker as DiskANN proof
- **Because:** DiskANN requires M30+, existing retail.products has an IVF index, and no resource changes or migration are authorized. A dedicated database also makes cleanup narrowly scoped; application credentials/tier are not supplied.
- **Reason came from:** `readiness_report`
- **Evidence:** guidance_for_builder: 'Use a new product collection ... unless ... explicitly authorizes migration'; 'Assume an existing cluster'; live listIndexes showed embedding_ivf.
- **When:** 2026-11-25T22:06:01+00:00

## D006 (build): I chose bounded order item arrays referencing product _id strings, separate product documents with schema/model metadata, unsharded collections, and deterministic upserts for 20,000 synthetic orders over 120 products.

- **Instead of:** Embed all order history in products; Shard this small dataset; Download an external dataset; Append duplicates on rerun
- **Because:** The bounded embedded items follow modeling guidance; the review defaults to a small unsharded synthetic catalog. Catalog size 120, 3–5 distinct items/order, seed 42, 80% same-category baskets, and 500-order batches below 1 MiB BSON are readability defaults, not measured optimal tuning. Refuse foreign schema/data instead of overwriting it.
- **Reason came from:** `model_default`
- **Evidence:** Prompt review: 'Generate 20,000 synthetic order documents over a small synthetic catalog ... insert in batches'; model-embed-vs-reference.md: embed bounded children and reference growing history.
- **When:** 2026-11-25T22:06:08+00:00

## D007 (build): I chose a DiskANN embedding index with COS, dimensions 1536, maxDegree 32 and lBuild 50, an ascending multikey orders.items.productId index, and automatic _id indexes for lookups.

- **Instead of:** IVF or HNSW; Additional catalog indexes; Atlas $vectorSearch
- **Because:** DiskANN is explicitly requested; skill syntax and parameters match the review. Order matching benefits from a single multikey path; _id already supports product lookup. Retrieval uses cosmosSearch k=20/lSearch=40 then excludes the input, with no additional prefilter index.
- **Reason came from:** `skill`
- **Evidence:** vector-create-diskann-index.md, vector-knn-query.md and index-multikey-arrays.md; https://learn.microsoft.com/azure/documentdb/vector-search
- **When:** 2026-11-25T22:06:16+00:00

## D008 (build): I chose OpenAI text-embedding-3-small at 1536 dimensions and gpt-4o-mini for one LlamaIndex tool-calling agent with per-session in-process memory.

- **Instead of:** Azure OpenAI deployments; Python vector-store adapter; Persisted session collection
- **Because:** These are the prompt-review defaults where the user is silent. Generate normalized catalog text embeddings through the provider, store model metadata, and use a custom MongoDB retrieval tool because the documented vector-store integration is Python-only. Session chat and viewed-category preferences disappear on restart.
- **Reason came from:** `model_default`
- **Evidence:** Prompt review AI components/workflow assumptions; Learn query-knowledge-base says 'vector store integration is Python-only' and directs TypeScript to mongodb.
- **When:** 2026-11-25T22:06:21+00:00

## D009 (build): I chose a CLI with explicit session switching, bounded chat/view memory, deterministic top-five reranking and grounded per-item explanations, plus offline automated tests and a one-shot live verification script.

- **Instead of:** Web server; Rely on agent text alone for item identity/ranking; No automated tests
- **Because:** The CLI is the review default. Blend semantic rank 0.45, normalized co-purchase count 0.40 and prior viewed-category frequency 0.15; union ANN and top co-purchases so complements are not excluded. Memory excludes the current turn from preference weights and never implies purchases. Validate agent JSON IDs/reasons rather than trusting hallucinated items. Offline tests are necessary since credentials are missing.
- **Reason came from:** `model_default`
- **Evidence:** Readiness information gaps: 'Adopt disclosed weights and an explicit two-turn demonstration; distinguish related substitutes from frequently bought-together complements'.
- **When:** 2026-11-25T22:06:28+00:00

## D010 (build): I used one process-wide MongoClient with TLS, SCRAM-SHA-256, retryWrites=false, retryReads=true, default pool sizing and a 10-second connection/server-selection deadline.

- **Instead of:** Copy retryWrites=true from driver skill; Create clients per turn; Tune OLTP pools for this CLI
- **Because:** Singleton and TLS follow connection guidance; readiness overrides stale true examples. The single-user sequential CLI does not justify custom pool sizing; 10 seconds is a disclosed fail-fast startup default, with no socket deadline that might interrupt index builds.
- **Reason came from:** `skill`
- **Evidence:** documentdb-connection: reuse one client, TLS required, retryable reads; readiness: 'Reuse one MongoClient but set retryWrites=false'.
- **When:** 2026-11-25T22:06:34+00:00

## D011 (build): I used LlamaIndex createMemory/getLLM/add for each session and agent.run with chatHistory, keeping only six successful turns and twenty viewed categories across at most twenty sessions.

- **Instead of:** Deprecated ChatMemoryBuffer; Reuse workflow scratchpad across unrelated sessions; Unlimited memory
- **Because:** Installed type declarations establish the actual compatible memory/agent APIs, closing the review gap. Persist only validated user/assistant messages, not raw tool scratchpads, and rebuild bounded memory after success. Limits are sample defaults and CLI runs sequentially.
- **Reason came from:** `tool_result`
- **Evidence:** Installed @llamaindex/core/memory declarations expose createMemory, getLLM, add, clear; @llamaindex/workflow declarations expose agent.run(userInput, {chatHistory}).
- **When:** 2026-11-25T22:07:22+00:00

## D012 (build): I chose to pin @llamaindex/core 0.6.22 as a direct dependency because the sample imports its supported memory API directly.

- **Instead of:** Rely only on a transitive core package
- **Because:** The installed compatible release exposes createMemory and the sample directly uses it; explicit dependencies make installs reproducible.
- **Reason came from:** `tool_result`
- **Evidence:** Installed node_modules/@llamaindex/core/memory/dist/index.d.ts documents createMemory; llamaindex/openai/workflow resolve core 0.6.22.
- **When:** 2026-11-25T22:09:27+00:00

## D013 (build): I used an explicit JSON string as the recommendation tool result instead of returning an object for LlamaIndex to format.

- **Instead of:** Parse JavaScript inspection syntax in the test; Depend on implicit object serialization
- **Because:** The real workflow test exposed non-JSON formatting of object tool results. An explicit JSON string is readable to the model and reliably parseable in tests without changing retrieval evidence.
- **Reason came from:** `tool_result`
- **Evidence:** npm test: 10 passed, 1 failed; mocked model parsing tool content raised 'Expected property name or ... in JSON at position 4'.
- **When:** 2026-11-25T22:11:23+00:00

## D014 (build): I used object tool evidence and changed the offline LLM fixture to use captured retrieval evidence rather than parsing LlamaIndex's presentation format as JSON.

- **Instead of:** Continue returning JSON strings; Patch dependency formatting; Use eval on tool content
- **Because:** Inspection shows this release intentionally presents objects as readable text and also transforms JSON strings by stripping quotes; neither presentation is a JSON API. The model can read object evidence, and the test should verify tool execution with captured evidence instead of assuming serialization. The failed direct callTool diagnostic also lacked its required logger; source inspection avoids further retries.
- **Reason came from:** `tool_result`
- **Evidence:** Second test: 'Expected property name ... JSON at position 1'; stringifyJSONToMessageContent({items:[]}) prints '{ items: [] }', while a JSON string prints escaped unquoted keys. Direct callTool failed 'Cannot read properties of undefined (reading error)'.
- **When:** 2026-11-25T22:12:23+00:00

## D015 (build): I used output.data.result to read the final LlamaIndex workflow event payload.

- **Instead of:** Read output.result directly; Bypass the workflow for a direct chat call
- **Because:** The installed workflow returns the final event wrapper, not the payload. The actual workflow test caught the mistaken access before shipping.
- **Reason came from:** `tool_result`
- **Evidence:** npm test failed 'Agent returned a non-text response'; installed workflow run() lines 696–701 returns finalEvent; stop event payload contains result.
- **When:** 2026-11-25T22:12:48+00:00

## D016 (build): I used read-only MCP inspection plus offline integration tests instead of mutating the connected cluster to demonstrate DiskANN.

- **Instead of:** Create sample indexes/data via MCP; Reuse the existing IVF embeddings for a fake DiskANN demo
- **Because:** No application credentials or model key are supplied, resource changes are forbidden, and the isolated namespace is empty. The MCP profile only supplies administrator-managed tool access, not an application URI. Tier, permissions, live vector-query plans, model outputs and quality remain unverified.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness: application connection configuration and embedding/chat credentials unavailable; MCP listDatabases retail_semantic_sample_v1 returned collections: []; run_policy: Azure resource changes allowed False.
- **When:** 2026-11-25T22:13:27+00:00

## D017 (build): I used a separate CLI smoke-test file written with the file tool instead of a complex Python inline edit.

- **Instead of:** Retry nested command quoting
- **Because:** The command runner's Windows quoting broke the inline test append; a separate test is clearer and avoids quoting workarounds.
- **Reason came from:** `tool_result`
- **Evidence:** python inline append failed: SyntaxError: '(' was never closed.
- **When:** 2026-11-25T22:14:42+00:00

## D018 (build): I used the discovered DOCUMENTDB_URI environment variable for a read-only application-driver connectivity check, with a secret-free config.json reference.

- **Instead of:** Assume no application URI because the readiness report said none; Print or export the URI; Run live ingestion without a model key
- **Because:** Runtime presence checks found a URI but no OpenAI key, superseding the inventory assumption. Test connection and inspect the sample namespace without writes; live model-backed ingestion still cannot run.
- **Reason came from:** `tool_result`
- **Evidence:** Environment presence check returned {documentdbUriPresent:true,openaiKeyPresent:false}; no secret value was displayed.
- **When:** 2026-11-25T22:15:38+00:00
