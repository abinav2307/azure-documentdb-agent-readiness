import { SampleError } from './errors.js';
import { DIMENSIONS, EMBEDDING_MODEL, SAMPLE_VERSION } from './config.js';
import { normalizeEmbedding } from './data.js';

/**
 * Match indexed order items before unwinding, then count distinct co-purchase
 * orders per other product. Generated baskets contain unique product IDs.
 * The extra order/product grouping also handles duplicate line items safely.
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

/**
 * Use the service's native DiskANN query, never the Atlas vector-store adapter.
 * k=20 and lSearch=40 oversample before excluding the input product. Project the
 * score explicitly and leave large embeddings out of tool/LLM context.
 */
export function vectorPipeline(vector) {
  return [
    { $search: { cosmosSearch: { vector, path: 'embedding', k: 20, lSearch: 40 }, returnStoredSource: true } },
    { $project: { _id: 1, title: 1, category: 1, score: { $meta: 'searchScore' } } },
  ];
}

/**
 * Blend semantic rank, co-purchase evidence and previous session category views.
 * Semantic rank avoids assuming a service score range; raw scores remain visible
 * as diagnostics. The current input is excluded from prior preference weights.
 * Weights are illustrative, not trained, and ties sort by ID deterministically.
 */
export function rankCandidates(productId, hits, coPurchases, products, viewedCategories = []) {
  const semantic = new Map(hits.map((p, i) => [p._id, { rank: 1 - i / 20, raw: p.score }]));
  const counts = new Map(coPurchases.map(p => [p._id, p.count]));
  const maxCount = Math.max(1, ...counts.values());
  const preferences = new Map();
  for (const category of viewedCategories) preferences.set(category, (preferences.get(category) ?? 0) + 1);
  return products.filter(p => p._id !== productId).map(p => {
    const semanticRank = semantic.get(p._id)?.rank ?? 0;
    const coPurchaseCount = counts.get(p._id) ?? 0;
    const sessionPreference = (preferences.get(p.category) ?? 0) / Math.max(1, viewedCategories.length);
    return {
      productId: p._id, title: p.title, category: p.category,
      score: 0.45 * semanticRank + 0.40 * coPurchaseCount / maxCount + 0.15 * sessionPreference,
      evidence: { semanticRank, vectorScore: semantic.get(p._id)?.raw ?? null, coPurchaseCount, sessionPreference },
    };
  }).sort((a, b) => b.score - a.score || a.productId.localeCompare(b.productId)).slice(0, 5);
}

/**
 * Retrieve product embeddings and real co-purchase counts from DocumentDB.
 * Union twenty ANN hits with twenty strongest co-purchases so lexical similarity
 * does not hide complements. Missing products or too few hits are clear errors,
 * not fabricated recommendations. Reuse the stored vector for product-ID input.
 */
export async function retrieveRecommendations(db, productId, viewedCategories = []) {
  const products = db.collection('products');
  const input = await products.findOne({ _id: productId });
  if (!input) throw new SampleError('Unknown product ID. Try p0001–p0120 after ingestion.');
  if (input.sampleVersion !== SAMPLE_VERSION || input.embeddingModel !== EMBEDDING_MODEL || input.embeddingDims !== DIMENSIONS) {
    throw new SampleError('Incompatible product embedding metadata. Do not mix models; use the isolated sample database.');
  }
  const vector = normalizeEmbedding(input.embedding);
  const hits = await products.aggregate(vectorPipeline(vector)).toArray();
  const coPurchases = await db.collection('orders').aggregate(coPurchasePipeline(productId)).toArray();
  const ids = [...new Set([...hits.map(p => p._id), ...coPurchases.slice(0, 20).map(p => p._id)])];
  const candidates = await products.find({ _id: { $in: ids } }, { projection: { _id: 1, title: 1, category: 1 } }).toArray();
  const items = rankCandidates(productId, hits, coPurchases, candidates, viewedCategories);
  if (items.length !== 5 || hits.length < 6) {
    throw new SampleError('Not enough indexed candidates. Finish ingestion and allow DiskANN indexing to complete, then run npm run verify.');
  }
  return { input: { productId: input._id, title: input.title, category: input.category }, priorViewedCategories: viewedCategories, items };
}
