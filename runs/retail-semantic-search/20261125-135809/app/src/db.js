import { SampleError } from './errors.js';
import { MongoClient } from 'mongodb';
import { DATABASE, DIMENSIONS } from './config.js';

let client;
let connection;
export const VECTOR_INDEX = {
  name: 'products_embedding_diskann',
  key: { embedding: 'cosmosSearch' },
  cosmosSearchOptions: {
    kind: 'vector-diskann', dimensions: DIMENSIONS, similarity: 'COS', maxDegree: 32, lBuild: 50,
  },
};

/**
 * Lazily connect once per process and ping before doing application work.
 * Default pools suit this sequential CLI; 10s selection/connect deadlines give
 * actionable startup errors without placing a deadline on lengthy index builds.
 * Driver errors are hidden because they might contain URI credentials.
 */
export async function connectDatabase(config) {
  if (!connection) {
    client = new MongoClient(config.uri, {
      tls: true, authMechanism: 'SCRAM-SHA-256', retryWrites: false, retryReads: true,
      connectTimeoutMS: 10_000, serverSelectionTimeoutMS: 10_000,
      appName: 'retail-semantic-search',
    });
    connection = client.connect().then(async () => {
      await client.db(DATABASE).command({ ping: 1 });
      return client.db(DATABASE);
    });
  }
  try { return await connection; }
  catch {
    await closeDatabase();
    throw new SampleError('Cannot connect to Azure DocumentDB. Check URI credentials, DNS, firewall/private network access and TLS CA trust. No connection details were logged.');
  }
}

/** Close the shared client only when the CLI/script exits, including failures. */
export async function closeDatabase() {
  if (client) await client.close();
  client = undefined;
  connection = undefined;
}

/**
 * Inspect real vector options, accepting either server metadata property name.
 * Refuse incompatible indexes; never drop or convert an existing vector index.
 */
export function assertDiskAnn(indexes) {
  const index = indexes.find(i => i.key?.embedding === 'cosmosSearch');
  const options = index?.cosmosSearchOptions ?? index?.cosmosSearch;
  if (!index || index.name !== VECTOR_INDEX.name ||
      Object.entries(VECTOR_INDEX.cosmosSearchOptions).some(([k, v]) => options?.[k] !== v)) {
    throw new SampleError('Missing or incompatible DiskANN index. Run npm run ingest in the isolated sample database on M30+. Existing vector indexes are never migrated automatically.');
  }
}

/**
 * Create exactly two explicit indexes using the documented createIndexes shape.
 * Validate any existing vector definition before requesting index creation.
 * Index failures are sanitized and no existing indexes are ever dropped.
 */
export async function ensureIndexes(db) {
  const products = db.collection('products');
  if (await db.listCollections({ name: 'products' }).hasNext()) {
    const indexes = await products.listIndexes().toArray();
    if (indexes.some(i => i.key?.embedding === 'cosmosSearch')) assertDiskAnn(indexes);
  }
  try {
    await db.command({ createIndexes: 'products', indexes: [VECTOR_INDEX] });
    await db.collection('orders').createIndex({ 'items.productId': 1 }, { name: 'orders_product_lookup' });
  } catch {
    throw new SampleError('Index creation failed. Verify M30+ DiskANN support and create-index permissions; inspect existing sample indexes. No indexes were dropped.');
  }
  assertDiskAnn(await products.listIndexes().toArray());
}
