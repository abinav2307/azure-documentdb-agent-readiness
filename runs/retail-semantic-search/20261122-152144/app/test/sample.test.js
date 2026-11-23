import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { loadConfig, settings } from '../src/config.js';
import { createCatalog, createOrders } from '../src/catalog.js';
import { normalizeVector, vectorPipeline, coPurchasePipeline, diskAnnIndex } from '../src/repository.js';
import { upsertDocuments, ingest } from '../src/ingestion.js';
import { SessionMemory } from '../src/memory.js';
import { recommend, rankCandidates, validateExplanations } from '../src/recommendations.js';
import { createModels } from '../src/models.js';

/** Assemble a nonsecret placeholder URI only in memory for parser tests. */
function fakeUri(query = '') {
  return ['mongodb+srv', '://', 'test-user', ':', 'test-password', '@', 'example.invalid', '/', query].join('');
}

/** Provide six deterministic candidates to exercise the real workflow offline. */
function fixture() {
  return {
    product: { _id: 'sample-p001', category: 'camping' }, counts: [{ _id: 'sample-p002', count: 10 }],
    candidates: Array.from({ length: 6 }, (_, i) => ({
      _id: `sample-p00${i + 2}`, title: `Item ${i + 2}`, category: i % 2 ? 'office' : 'camping', similarityScore: 0.8,
    })),
  };
}

class FakeLLM {
  /** Supply tool capability without network credentials or a mocked agent. */
  constructor() { this.supportToolCall = true; this.metadata = { contextWindow: 128000 }; this.requests = []; }

  /**
   * Stream a real LlamaIndex tool-call chunk, then explain the tool's actual
   * results. Recording inputs lets tests verify explicit session chatHistory.
   */
  async chat(params) {
    this.requests.push(structuredClone(params.messages));
    const result = params.messages.findLast(message => message.options?.toolResult);
    // Yield the same chunk shapes produced by the installed OpenAI adapter.
    async function* chunks() {
      if (!result) {
        yield { delta: '', options: { toolCall: [{ name: 'get_session_recommendations', id: 'call-1', input: {} }] } };
      } else {
        if (result.options.toolResult.isError) { yield { delta: JSON.stringify({ recommendations: [] }) }; return; }
        const ids = [...result.content.matchAll(/productId: ([a-zA-Z0-9_-]+)/g)].map(match => match[1]);
        const counts = [...result.content.matchAll(/coPurchaseCount: ([0-9]+)/g)].map(match => Number(match[1]));
        const affinity = [...result.content.matchAll(/sessionAffinity: ([0-9.]+)/g)].map(match => Number(match[1]));
        const data = { recommendations: ids.map((productId, i) => ({ productId, coPurchaseCount: counts[i], sessionAffinity: affinity[i] })) };
        yield { delta: JSON.stringify({ recommendations: data.recommendations.map(p => ({
          productId: p.productId, reasoning: `Semantic match; ${p.coPurchaseCount} shared orders; session affinity ${p.sessionAffinity}.`,
        })) }) };
      }
    }
    return chunks();
  }
}

test('missing/invalid config is readable, secrets are not echoed and TLS bypasses fail', () => {
  assert.throws(() => loadConfig({}), /DOCUMENTDB_URI is missing/);
  assert.throws(() => loadConfig({ DOCUMENTDB_URI: 'not-a-uri-SENSITIVE' }), error => /invalid/.test(error.message) && !error.message.includes('SENSITIVE'));
  for (const query of ['?tls=false', '?tlsAllowInvalidCertificates=true', '?tlsInsecure=false', '?authMechanism=PLAIN']) {
    assert.throws(() => loadConfig({ DOCUMENTDB_URI: fakeUri(query) }, false), /invalid/);
  }
  assert.throws(() => loadConfig({ DOCUMENTDB_URI: fakeUri() }), /OPENAI_API_KEY is missing/);
  assert.equal(loadConfig({ DOCUMENTDB_URI: fakeUri(), OPENAI_API_KEY: 'test-key' }).database, 'retail_semantic_sample');
});

test('CLI and seed missing-config failures exit nonzero with safe messages', () => {
  for (const script of ['src/cli.js', 'scripts/seed.js']) {
    const result = spawnSync(process.execPath, [script, 'sample-p001'], { env: { ...process.env, DOCUMENTDB_URI: '', OPENAI_API_KEY: '' }, encoding: 'utf8' });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /DOCUMENTDB_URI is missing/);
  }
  const result = spawnSync(process.execPath, ['src/cli.js', 'sample-p001'], { env: { ...process.env, DOCUMENTDB_URI: 'SENSITIVE-invalid' }, encoding: 'utf8' });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /DOCUMENTDB_URI is invalid/);
  assert.ok(!result.stderr.includes('SENSITIVE-invalid'));
});

test('catalog and exactly 20,000 bounded transactions are deterministic and referenced', () => {
  const catalog = createCatalog();
  const orders = [...createOrders(catalog)];
  assert.equal(catalog.length, 60);
  assert.equal(orders.length, 20000);
  assert.equal(new Set(orders.map(order => order._id)).size, 20000);
  assert.deepEqual(orders, [...createOrders(catalog)]);
  const ids = new Set(catalog.map(p => p._id));
  assert.ok(orders.every(o => o.items.length >= 2 && o.items.length <= 4 && new Set(o.items.map(i => i.productId)).size === o.items.length && o.items.every(i => ids.has(i.productId))));
});

test('batched order upserts are repeatable without duplicates', async () => {
  const documents = new Map(); const sizes = [];
  const collection = {
    // Simulate replacement semantics, preserving stable IDs across repeated runs.
    async bulkWrite(batch) { sizes.push(batch.length); for (const op of batch) documents.set(op.replaceOne.filter._id, op.replaceOne.replacement); },
  };
  await upsertDocuments(collection, createOrders());
  await upsertDocuments(collection, createOrders());
  assert.equal(documents.size, 20000);
  assert.equal(sizes.length, 80);
  assert.ok(sizes.every(size => size === 500));
});

test('vectors and query/index contracts match DiskANN and distinct-order semantics', () => {
  const vector = normalizeVector(Array(1536).fill(2));
  assert.ok(Math.abs(Math.hypot(...vector) - 1) < 1e-10);
  assert.throws(() => normalizeVector([1]), /1536/);
  assert.throws(() => normalizeVector(Array(1536).fill(0)), /zero/);
  assert.throws(() => normalizeVector(Array(1536).fill(NaN)), /finite/);
  const search = vectorPipeline(vector)[0].$search.cosmosSearch;
  assert.equal(search.k, 30); assert.equal(search.lSearch, 40);
  assert.equal(diskAnnIndex.cosmosSearchOptions.kind, 'vector-diskann');
  assert.equal(diskAnnIndex.cosmosSearchOptions.dimensions, 1536);
  const pipeline = coPurchasePipeline('sample-p001');
  assert.deepEqual(pipeline[0], { $match: { 'items.productId': 'sample-p001' } });
  assert.deepEqual(pipeline[3].$group._id, { order: '$_id', product: '$items.productId' });
});

test('real ingestion orchestrates 20,000 upserts and caches 60 model embeddings', async () => {
  const products = new Map(); const orders = new Map(); let calls = 0; const commands = [];
  const db = {
    // Minimal driver double: database semantics only, not mocked ingestion logic.
    collection(name) {
      const store = name === 'products' ? products : orders;
      return {
        async bulkWrite(batch) { for (const op of batch) store.set(op.replaceOne.filter._id, op.replaceOne.replacement); },
        async createIndex() {},
        aggregate() { return { async toArray() { return []; } }; },
        async findOne(filter) { return store.get(filter._id); },
        async replaceOne(filter, doc) { store.set(filter._id, doc); },
        async countDocuments() { return store.size; },
      };
    },
    async command(command) { commands.push(command); },
  };
  const provider = { async getTextEmbedding() { calls++; return Array(1536).fill(1); } };
  assert.deepEqual(await ingest(db, provider, () => {}), { orders: 20000, products: 60, newlyEmbedded: 60 });
  assert.deepEqual(await ingest(db, provider, () => {}), { orders: 20000, products: 60, newlyEmbedded: 0 });
  assert.equal(calls, 60);
  assert.equal(commands[0].indexes[0].cosmosSearchOptions.kind, 'vector-diskann');
});

test('session categories alter reranking; anchor and duplicates are excluded', () => {
  const data = fixture();
  const plain = rankCandidates(data.candidates, [], [], 'sample-p001');
  const personal = rankCandidates([...data.candidates, data.candidates[0]], [], [{ category: 'office' }], 'sample-p001');
  assert.notEqual(plain[0].productId, personal[0].productId);
  assert.equal(personal[0].category, 'office');
  assert.equal(personal.length, 5);
  assert.equal(new Set(personal.map(p => p.productId)).size, 5);
});

test('bounded memory isolates sessions, evicts LRU, and limits turns', () => {
  const memory = new SessionMemory(2, 2);
  for (let i = 0; i < 5; i++) memory.remember('a', { _id: 'sample-p001', category: 'camping' }, {});
  assert.equal(memory.history('a').length, 4);
  assert.equal(memory.history('b').length, 0);
  memory.get('a'); memory.get('c');
  assert.ok(!memory.sessions.has('b'));
  assert.throws(() => memory.get('unsafe/session'), /Session ID/);
});

test('real LlamaIndex workflow invokes retrieval and receives isolated session history', async () => {
  const llm = new FakeLLM(); const memory = new SessionMemory(); let reads = 0;
  const retrieve = async () => { reads++; return fixture(); };
  const args = { db: {}, llm, memory, productId: 'sample-p001', sessionId: 'a', retrieve };
  const response = await recommend(args);
  assert.equal(response.recommendations.length, 5);
  assert.equal(reads, 1);
  await recommend(args);
  assert.equal(reads, 2);
  assert.ok(llm.requests[2].some(m => m.role === 'assistant' && typeof m.content === 'string' && m.content.includes('recommendations')));
  await recommend({ ...args, sessionId: 'b' });
  assert.ok(!llm.requests[4].some(m => m.role === 'assistant'));
});

test('agent refuses fewer than five candidates and does not commit failed memory', async () => {
  const memory = new SessionMemory();
  await assert.rejects(recommend({ db: {}, llm: new FakeLLM(), memory, productId: 'sample-p001', sessionId: 'a', retrieve: async () => ({ ...fixture(), candidates: [] }) }), /Fewer than five/);
  assert.equal(memory.history('a').length, 0);
});

test('model provider constructors and output validation fail closed', () => {
  const models = createModels({ ...settings, apiKey: 'test-key' });
  assert.equal(models.embeddingModel.dimensions, 1536);
  assert.equal(models.llm.supportToolCall, true);
  const ranked = rankCandidates(fixture().candidates, [], [], 'sample-p001');
  assert.throws(() => validateExplanations('not json', ranked), /invalid JSON/);
  assert.throws(() => validateExplanations(JSON.stringify({ recommendations: Array(5).fill({ productId: 'invented', reasoning: 'bad' }) }), ranked), /invalid recommendation/);
});
