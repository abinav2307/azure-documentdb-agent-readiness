import assert from 'node:assert/strict';
import { loadConfig, DIMENSIONS, EMBEDDING_MODEL } from '../src/config.js';
import { connectDatabase, closeDatabase, assertDiskAnn } from '../src/db.js';
import { retrieveRecommendations, coPurchasePipeline, vectorPipeline } from '../src/recommendations.js';
import { displayError } from '../src/errors.js';

/**
 * Collect names/stages recursively from a winning/execution plan, not rejected
 * alternatives. DocumentDB may expose PostgreSQL-style Index Scan nodes as well
 * as MongoDB IXSCAN. Print the complete plan for manual inspection too.
 */
export function planUsesIndex(value) {
  if (!value || typeof value !== 'object') return false;
  if (/index|bitmap/i.test(value.stage ?? value['Node Type'] ?? '') || value.indexName || value['Index Name']) return true;
  return Object.entries(value).some(([key, child]) => key !== 'rejectedPlans' && planUsesIndex(child));
}

/**
 * One-shot live verification: counts, stored model/vector metadata, actual DiskANN
 * settings, co-purchase plan and vector query plan, five distinct non-input hits.
 * Needs database credentials but no model key; this script never changes data.
 */
async function main() {
  try {
    const config = loadConfig({ requireModel: false });
    const db = await connectDatabase(config);
    const products = db.collection('products');
    const orders = db.collection('orders');
    assert.equal(await products.countDocuments({}), 120);
    assert.equal(await orders.countDocuments({}), 20_000);
    assertDiskAnn(await products.listIndexes().toArray());
    assert((await orders.listIndexes().toArray()).some(i => i.key?.['items.productId'] === 1));
    const input = await products.findOne({ _id: 'p0001' });
    assert.equal(input.embeddingModel, EMBEDDING_MODEL);
    assert.equal(input.embedding.length, DIMENSIONS);
    const coPlan = await orders.aggregate(coPurchasePipeline('p0001')).explain('executionStats');
    console.log('Co-purchase execution plan:', JSON.stringify(coPlan, null, 2));
    assert(planUsesIndex(coPlan), 'Co-purchase lookup did not report index use; inspect the printed plan.');
    const vectorPlan = await products.aggregate(vectorPipeline(input.embedding)).explain('executionStats');
    console.log('DiskANN execution plan:', JSON.stringify(vectorPlan, null, 2));
    const result = await retrieveRecommendations(db, 'p0001');
    assert.equal(result.items.length, 5);
    assert.equal(new Set(result.items.map(p => p.productId)).size, 5);
    assert(result.items.every(p => p.productId !== 'p0001' && Number.isFinite(p.score)));
    console.log(JSON.stringify(result, null, 2));
    console.log('PASS: 120 products, 20,000 orders, DiskANN definition/query and indexed co-purchase plan.');
  } catch (error) {
    console.error(displayError(error));
    process.exitCode = 1;
  } finally { await closeDatabase(); }
}

if (process.argv[1]?.endsWith('verify.js')) await main();
