import { OpenAIEmbedding } from '@llamaindex/openai';
import { loadConfig, EMBEDDING_MODEL, DIMENSIONS, SAMPLE_VERSION } from '../src/config.js';
import { connectDatabase, closeDatabase, ensureIndexes } from '../src/db.js';
import { generateProducts, generateOrders, normalizeEmbedding, batches, ORDER_COUNT } from '../src/data.js';
import { SampleError, displayError } from '../src/errors.js';

/**
 * Refuse foreign data or older embedding metadata before touching a namespace.
 * The fixed database name prevents accidentally ingesting into retail.products.
 * Upserts permit partial ingestion to resume; this check is not a migration tool.
 */
export async function assertSampleNamespace(db) {
  for (const name of ['products', 'orders']) {
    const foreign = await db.collection(name).findOne({ $or: [
      { sampleVersion: { $ne: SAMPLE_VERSION } }, { schemaVersion: { $ne: 1 } },
    ] });
    if (foreign) throw new SampleError('Sample namespace contains foreign data. Stop and choose a separate cluster or review the fixed sample database; no data was overwritten.');
  }
  if (await db.collection('products').findOne({ $or: [
    { embeddingModel: { $ne: EMBEDDING_MODEL } }, { embeddingDims: { $ne: DIMENSIONS } }, { embeddingVersion: { $ne: 1 } },
  ] })) throw new SampleError('Existing product model metadata differs. Do not mix embedding models; no products were overwritten.');
}

/**
 * Ingest 120 catalog embeddings and exactly 20,000 deterministic synthetic orders.
 * Embed products sequentially to keep provider traffic and the code simple.
 * Reuse compatible stored embeddings on rerun; order upserts retain stable IDs.
 * Every write is acknowledged. A failure stops the script; rerun to resume rather
 * than assuming an unordered partial batch succeeded. Count both collections.
 */
export async function ingest(db, embedder, log = console.log) {
  await assertSampleNamespace(db);
  await ensureIndexes(db);
  const products = generateProducts();
  for (const product of products) {
    const existing = await db.collection('products').findOne({ _id: product._id });
    const vector = existing?.embedding ?? await embedder.getTextEmbedding(`${product.title}\n${product.description}\nCategory: ${product.category}`);
    await db.collection('products').replaceOne({ _id: product._id }, {
      ...product, embedding: normalizeEmbedding(vector), embeddingModel: EMBEDDING_MODEL,
      embeddingDims: DIMENSIONS, embeddingVersion: 1,
    }, { upsert: true });
  }
  log('Catalog ready: 120 products with normalized 1536-dimensional embeddings.');
  let processed = 0;
  for (const batch of batches(generateOrders(products))) {
    await db.collection('orders').bulkWrite(batch.map(order => ({ replaceOne: {
      filter: { _id: order._id }, replacement: order, upsert: true,
    } })), { ordered: true });
    processed += batch.length;
    log(`Orders acknowledged: ${processed}/${ORDER_COUNT}`);
  }
  const productCount = await db.collection('products').countDocuments({});
  const orderCount = await db.collection('orders').countDocuments({});
  if (productCount !== products.length || orderCount !== ORDER_COUNT) {
    throw new SampleError('Unexpected sample counts. Inspect the isolated sample namespace; expected 120 products and 20,000 unique orders.');
  }
  log(`Ingestion complete: ${productCount} products, ${orderCount} unique orders. Run npm run verify to check DiskANN query readiness.`);
}

/** Load secrets from the shell, perform ingestion, and always close the singleton. */
async function main() {
  try {
    const config = loadConfig();
    const db = await connectDatabase(config);
    const embedder = new OpenAIEmbedding({ model: EMBEDDING_MODEL, dimensions: DIMENSIONS, apiKey: config.apiKey });
    await ingest(db, embedder);
  } catch (error) {
    console.error(displayError(error));
    process.exitCode = 1;
  } finally { await closeDatabase(); }
}

if (process.argv[1]?.endsWith('ingest.js')) await main();
