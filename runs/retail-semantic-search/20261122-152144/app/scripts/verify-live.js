import assert from 'node:assert/strict';
import { loadConfig, reportError } from '../src/config.js';
import { openDatabase, closeDatabase } from '../src/database.js';
import { createModels } from '../src/models.js';
import { SessionMemory } from '../src/memory.js';
import { recommend } from '../src/recommendations.js';
import { diskAnnIndex } from '../src/repository.js';

/**
 * One-shot, read-only verification after authorized ingestion: check exact
 * seed counts, DiskANN options, the multikey query's explain output, and a
 * live five-item LlamaIndex recommendation. Never seed or modify indexes here.
 */
async function main() {
  const config = loadConfig();
  const db = await openDatabase(config);
  const { llm } = createModels(config);
  try {
    assert.equal(await db.collection('orders').countDocuments({ _id: /^sample-o/ }), 20000);
    assert.equal(await db.collection('products').countDocuments({ _id: /^sample-p/ }), 60);
    const indexes = await db.collection('products').listIndexes().toArray();
    const vector = indexes.find(index => index.name === diskAnnIndex.name);
    assert.ok(vector, 'DiskANN index missing');
    assert.deepEqual(vector.key, diskAnnIndex.key);
    const options = vector.cosmosSearchOptions || vector.cosmosSearch;
    for (const [key, value] of Object.entries(diskAnnIndex.cosmosSearchOptions)) assert.equal(options[key], value);
    const orderIndexes = await db.collection('orders').listIndexes().toArray();
    assert.ok(orderIndexes.some(index => index.name === 'orders_product_multikey' && index.key['items.productId'] === 1));
    const plan = await db.collection('orders').find({ 'items.productId': 'sample-p001' }).explain('executionStats');
    const serializedPlan = JSON.stringify(plan);
    assert.match(serializedPlan, /orders_product_multikey|IXSCAN|Bitmap Index Scan|Index Scan/i);
    const response = await recommend({ db, llm, memory: new SessionMemory(), productId: 'sample-p001', sessionId: 'live-check' });
    assert.equal(response.recommendations.length, 5);
    assert.equal(new Set(response.recommendations.map(p => p.productId)).size, 5);
    assert.ok(response.recommendations.every(p => p.productId !== response.productId && p.reasoning));
    console.log(JSON.stringify({ verified: true, response }, null, 2));
  } catch {
    throw new Error('Live verification failed. Check seed counts, index definitions/usage, M30+ tier, and model access. No data was changed by this verifier.');
  }
}
try { await main(); } catch (error) { reportError(error); } finally { await closeDatabase(); }
