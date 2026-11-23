import { createCatalog, createOrders } from './catalog.js';
import { createHash } from 'node:crypto';
import { settings } from './config.js';
import { ensureIndexes, readCoPurchases, normalizeVector, compatibleEmbedding } from './repository.js';

/**
 * Upsert deterministic documents in bounded batches of 500 using one shared
 * client. This does not promise atomic ingestion: a failed run can be rerun.
 * Each replacement uses the stable _id, so neither orders nor products duplicate.
 */
export async function upsertDocuments(collection, documents) {
  let batch = [];
  for (const document of documents) {
    batch.push({ replaceOne: { filter: { _id: document._id }, replacement: document, upsert: true } });
    if (batch.length === 500) {
      await collection.bulkWrite(batch, { ordered: true });
      batch = [];
    }
  }
  if (batch.length) await collection.bulkWrite(batch, { ordered: true });
}

/**
 * Seed exactly 20,000 orders, then read their co-purchase counts from DocumentDB
 * to enrich each product's embedding text. Embed only 60 catalog items with
 * sequential, bounded calls. A source hash avoids paying again on reruns;
 * changed catalog/history/model input triggers a replacement embedding.
 */
export async function ingest(db, embeddingModel, progress = console.error) {
  const catalog = createCatalog();
  await upsertDocuments(db.collection('orders'), createOrders(catalog));
  await db.collection('orders').createIndex({ 'items.productId': 1 }, { name: 'orders_product_multikey' });
  progress('Upserted 20,000 synthetic orders. Generating/checking 60 product embeddings...');
  const productsById = new Map(catalog.map(product => [product._id, product]));
  let embedded = 0;
  for (const product of catalog) {
    const counts = await readCoPurchases(db, product._id);
    const context = counts.filter(row => productsById.has(row._id)).slice(0, 5)
      .map(row => `${productsById.get(row._id).title} (${row.count} shared orders)`).join(', ');
    const embeddingText = `${product.title}. ${product.description}\nFrequently purchased with: ${context || 'No shared orders yet'}.`;
    const sourceHash = createHash('sha256').update(embeddingText).digest('hex');
    const previous = await db.collection('products').findOne({ _id: product._id });
    if (previous?.sourceHash === sourceHash && compatibleEmbedding(previous)) {
      normalizeVector(previous.embedding);
      continue;
    }
    const embedding = normalizeVector(await embeddingModel.getTextEmbedding(embeddingText));
    await db.collection('products').replaceOne({ _id: product._id }, {
      ...product, embedding, embeddingText, sourceHash,
      embeddingModel: settings.embeddingModel, embeddingDims: settings.dimensions,
      embeddingVersion: settings.embeddingVersion,
    }, { upsert: true });
    embedded++;
  }
  await ensureIndexes(db);
  const orders = await db.collection('orders').countDocuments({ _id: /^sample-o/ });
  const products = await db.collection('products').countDocuments({ _id: /^sample-p/ });
  if (orders !== 20000 || products !== 60) throw new Error('Seed counts differ from 20,000 orders/60 products. Use a clean isolated sample database.');
  return { orders, products, newlyEmbedded: embedded };
}
