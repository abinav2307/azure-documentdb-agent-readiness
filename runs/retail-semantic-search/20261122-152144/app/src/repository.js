import { settings } from './config.js';

export const diskAnnIndex = {
  name: 'products_embedding_diskann',
  key: { embedding: 'cosmosSearch' },
  cosmosSearchOptions: {
    kind: 'vector-diskann', dimensions: settings.dimensions,
    similarity: 'COS', maxDegree: 32, lBuild: 50,
  },
};

/**
 * Create the order multikey and DiskANN indexes via the driver's command API.
 * Same-name incompatible indexes fail rather than silently accepting drift.
 * No resources are provisioned and no existing indexes are dropped.
 */
export async function ensureIndexes(db) {
  await db.collection('orders').createIndex({ 'items.productId': 1 }, { name: 'orders_product_multikey' });
  await db.command({ createIndexes: 'products', indexes: [diskAnnIndex] });
}

/**
 * Count distinct orders shared with the anchor product. Match first to use the
 * multikey index; deduplicate order/product pairs before summing, so accidental
 * duplicate line items cannot inflate counts. Do not count the anchor itself.
 */
export function coPurchasePipeline(productId) {
  return [
    { $match: { 'items.productId': productId } },
    { $unwind: '$items' },
    { $match: { 'items.productId': { $ne: productId } } },
    { $group: { _id: { order: '$_id', product: '$items.productId' } } },
    { $group: { _id: '$_id.product', count: { $sum: 1 } } },
    { $sort: { count: -1, _id: 1 } },
  ];
}

/** Read bounded co-purchase counts from order history, never model-generated MQL. */
export async function readCoPurchases(db, productId) {
  return db.collection('orders').aggregate(coPurchasePipeline(productId)).toArray();
}

/**
 * Search 30 DiskANN neighbors with lSearch=40, returning only the fields needed
 * for reranking. The single anchor exclusion is applied after this small
 * over-fetch, avoiding an additional prefilter index. No Atlas syntax is used.
 */
export function vectorPipeline(vector) {
  return [
    { $search: { cosmosSearch: { path: 'embedding', vector, k: 30, lSearch: 40 } } },
    { $project: {
      _id: 1, title: 1, category: 1, embeddingModel: 1, embeddingDims: 1,
      embeddingVersion: 1, similarityScore: { $meta: 'searchScore' },
    } },
  ];
}

/**
 * Read the requested product, its vector neighbors and live co-purchase counts.
 * A version mismatch is actionable: reingest using the fixed model rather than
 * mixing incompatible vectors. Unknown products and short candidate pools fail
 * explicitly; recommendations must never invent catalog items.
 */
export async function retrieveCandidates(db, productId) {
  let product;
  let candidates;
  let counts;
  try {
    product = await db.collection('products').findOne({ _id: productId });
    if (product) {
      normalizeVector(product.embedding);
      [candidates, counts] = await Promise.all([
        db.collection('products').aggregate(vectorPipeline(product.embedding)).toArray(),
        readCoPurchases(db, productId),
      ]);
    }
  } catch {
    throw new Error('Recommendation retrieval failed. Run npm run ingest and check M30+ DiskANN support, index readiness, embedding dimensions, and database permissions.');
  }
  if (!product) throw new Error('Product ID not found. Try sample-p001 after running npm run ingest.');
  if (!compatibleEmbedding(product)) throw new Error('Product embedding metadata differs from this sample. Re-run ingestion with the fixed embedding model.');
  return { product, counts, candidates: candidates.filter(p => p._id !== productId && compatibleEmbedding(p)) };
}

/** Check the embedding identity, dimension and version to prevent model drift. */
export function compatibleEmbedding(product) {
  return product.embeddingModel === settings.embeddingModel &&
    product.embeddingDims === settings.dimensions && product.embeddingVersion === settings.embeddingVersion;
}

/**
 * Require a finite, nonzero number array of the selected model's dimensions,
 * then L2-normalize it for COS indexing. Called for ingestion and query vectors.
 */
export function normalizeVector(vector) {
  if (!Array.isArray(vector) || vector.length !== settings.dimensions || !vector.every(Number.isFinite)) {
    throw new Error('Embedding must be a finite 1536-dimensional numeric array.');
  }
  const norm = Math.hypot(...vector);
  if (!Number.isFinite(norm) || norm === 0) throw new Error('Embedding must not be zero.');
  return vector.map(value => value / norm);
}
