import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { loadConfig, validateConnectionString } from '../src/config.js';
import { assertDiskAnn, VECTOR_INDEX } from '../src/db.js';
import { generateProducts, generateOrders, normalizeEmbedding, batches } from '../src/data.js';
import { rankCandidates, vectorPipeline, coPurchasePipeline, retrieveRecommendations } from '../src/recommendations.js';
import { createRecommendationAgent, validateExplanations } from '../src/agent.js';
import { ingest } from '../scripts/ingest.js';
import { displayError } from '../src/errors.js';

// Deliberately no valid credential-bearing URI is written into any test file.
test('missing and invalid connection strings have clear, redacted errors', () => {
  assert.throws(() => validateConnectionString(undefined), /Missing Azure DocumentDB/);
  for (const value of ['not-a-uri', '<placeholder>', 'https://invalid.example/']) {
    assert.throws(() => validateConnectionString(value), /Missing|Invalid/);
  }
  assert(!displayError(new Error('secret-test-marker')).includes('secret-test-marker'));
});

test('config reads an environment reference and rejects malformed/missing config', () => {
  const dir = mkdtempSync(join(process.cwd(), 'config-test-'));
  try {
    const path = join(dir, 'config.json');
    assert.throws(() => loadConfig({ path, env: {} }), /Missing or invalid config/);
    writeFileSync(path, JSON.stringify({ connectionStringEnv: 'DOCUMENTDB_URI' }));
    assert.throws(() => loadConfig({ path, env: {} }), /Missing Azure DocumentDB/);
    writeFileSync(path, JSON.stringify({ connectionStringEnv: 'not a variable' }));
    assert.throws(() => loadConfig({ path, env: {} }), /must name an environment/);
  } finally { rmSync(dir, { recursive: true }); }
});

test('catalog and 20,000 transactions are deterministic, bounded and valid', () => {
  const products = generateProducts();
  const orders = [...generateOrders(products)];
  assert.equal(products.length, 120);
  assert.equal(orders.length, 20_000);
  assert.equal(new Set(orders.map(o => o._id)).size, 20_000);
  const ids = new Set(products.map(p => p._id));
  assert(orders.every(o => o.items.length >= 3 && o.items.length <= 5 && new Set(o.items.map(i => i.productId)).size === o.items.length && o.items.every(i => ids.has(i.productId))));
  assert.deepEqual(orders.slice(0, 10), [...generateOrders(products, 10)]);
  assert.equal([...batches(orders)].length, 40);
  assert.equal([...batches(orders, 500, 1500)].flat().length, 20_000);
});

test('embeddings normalize and reject zero, NaN and wrong dimensions', () => {
  assert.deepEqual(normalizeEmbedding([3, 4], 2), [0.6, 0.8]);
  assert.throws(() => normalizeEmbedding([0, 0], 2), /zero/);
  assert.throws(() => normalizeEmbedding([NaN, 1], 2), /finite/);
  assert.throws(() => normalizeEmbedding([1], 2), /dimensions/);
});

test('DiskANN verifies options, not index name, accepts server metadata alias', () => {
  assert.doesNotThrow(() => assertDiskAnn([VECTOR_INDEX]));
  assert.doesNotThrow(() => assertDiskAnn([{ ...VECTOR_INDEX, cosmosSearchOptions: undefined, cosmosSearch: VECTOR_INDEX.cosmosSearchOptions }]));
  assert.throws(() => assertDiskAnn([{ ...VECTOR_INDEX, cosmosSearchOptions: { ...VECTOR_INDEX.cosmosSearchOptions, kind: 'vector-ivf' } }]), /incompatible/);
  assert.throws(() => assertDiskAnn([]), /Missing/);
});

test('queries use DiskANN cosmosSearch and indexed first-stage order match', () => {
  assert.equal(vectorPipeline([1])[0].$search.cosmosSearch.lSearch, 40);
  assert.equal(vectorPipeline([1])[0].$search.cosmosSearch.k, 20);
  assert.equal(coPurchasePipeline('p0001')[0].$match['items.productId'], 'p0001');
  assert.equal(vectorPipeline([1])[1].$project.score.$meta, 'searchScore');
});

test('prior session category preferences change ranking without including input', () => {
  const products = Array.from({ length: 7 }, (_, i) => ({ _id: `p000${i}`, title: `Item ${i}`, category: i === 1 ? 'outdoor' : 'office' }));
  const hits = products.slice(1).map(p => ({ ...p, score: 0.8 }));
  const base = rankCandidates('p0000', hits, [], products);
  const personalized = rankCandidates('p0000', hits, [], products, ['office']);
  assert.equal(base.length, 5);
  assert.equal(base[0].productId, 'p0001');
  assert.equal(personalized[0].productId, 'p0002');
  assert(base.every(p => p.productId !== 'p0000'));
  assert.equal(personalized[0].evidence.sessionPreference, 1);
});

/** Simulate OpenAI streaming chunks while executing the real LlamaIndex workflow. */
function fakeLLM(getEvidence) {
  return {
    supportToolCall: true,
    metadata: { contextWindow: 128000, model: 'offline-test', tokenizer: undefined },
    /** Emit a tool call first, then explain the actual tool output, without network. */
    async *chat({ messages }) {
      const result = messages.findLast(m => m.options?.toolResult);
      if (!result) {
        yield { delta: '', options: { toolCall: [{ id: 'test-call', name: 'recommend_items', input: {} }] }, raw: {} };
      } else {
        const evidence = getEvidence();
        assert(result.content.includes(evidence.items[0].productId));
        yield { delta: JSON.stringify({ items: evidence.items.map(p => ({ productId: p.productId, reason: `Related item with ${p.evidence.coPurchaseCount} synthetic co-purchase orders.` })) }), raw: {} };
      }
    },
  };
}

/** Produce deterministic mock database evidence; tests never substitute this at runtime. */
function fakeEvidence(viewed) {
  return {
    input: { productId: 'p0001', category: 'outdoor', title: 'Backpack' },
    priorViewedCategories: viewed,
    items: Array.from({ length: 5 }, (_, i) => ({ productId: `p000${i + 2}`, title: 'Sample', category: 'outdoor', score: 0.5, evidence: { coPurchaseCount: 10, semanticRank: 1, sessionPreference: viewed.length ? 1 : 0 } })),
  };
}

test('actual LlamaIndex tool workflow retains two-turn memory and isolates sessions', async () => {
  const calls = [];
  let currentEvidence;
  const service = createRecommendationAgent(null, undefined, {
    llm: fakeLLM(() => currentEvidence),
    /** Capture the session history passed to the retrieval tool for isolation assertions. */
    retrieve: async (_db, id, viewed) => { calls.push({ id, viewed }); currentEvidence = fakeEvidence(viewed); return currentEvidence; },
  });
  assert.equal((await service.recommend('p0001', 'alice')).items.length, 5);
  await service.recommend('p0002', 'alice');
  await service.recommend('p0001', 'bob');
  assert.deepEqual(calls.map(c => c.viewed), [[], ['outdoor'], []]);
  service.resetSession('alice');
  await service.recommend('p0001', 'alice');
  assert.deepEqual(calls.at(-1).viewed, []);
});

test('agent rejects fabricated IDs and invalid JSON', () => {
  const items = fakeEvidence([]).items;
  assert.throws(() => validateExplanations('not json', items), /invalid JSON/);
  assert.throws(() => validateExplanations(JSON.stringify({ items: items.map(p => ({ productId: 'fake', reason: 'Invented' })) }), items), /five retrieved/);
});

test('unknown products fail clearly without a model request', async () => {
  const db = { collection: () => ({ findOne: async () => null }) };
  await assert.rejects(retrieveRecommendations(db, 'p9999'), /Unknown product/);
});

test('ingestion upserts exactly 20,000 orders and reruns without duplicate IDs', async () => {
  const collections = { products: new Map(), orders: new Map() };
  const db = {
    listCollections: () => ({ hasNext: async () => true }),
    command: async () => ({}),
    /** Model a small in-memory acknowledged collection for ingestion tests only. */
    collection(name) {
      const store = collections[name];
      return {
        findOne: async query => query._id ? store.get(query._id) : null,
        listIndexes: () => ({ toArray: async () => [VECTOR_INDEX] }),
        createIndex: async () => 'orders_product_lookup',
        replaceOne: async (query, document) => store.set(query._id, document),
        bulkWrite: async operations => { for (const op of operations) store.set(op.replaceOne.filter._id, op.replaceOne.replacement); },
        countDocuments: async () => store.size,
      };
    },
  };
  let embeddings = 0;
  const embedder = {
    /** Return a valid-shaped offline vector; no fake embeddings enter the live app. */
    getTextEmbedding: async () => { embeddings++; return Array.from({ length: 1536 }, (_, i) => i === 0 ? 1 : 0); },
  };
  await ingest(db, embedder, () => {});
  await ingest(db, embedder, () => {});
  assert.equal(collections.products.size, 120);
  assert.equal(collections.orders.size, 20_000);
  assert.equal(embeddings, 120);
});
