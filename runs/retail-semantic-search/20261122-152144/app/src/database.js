import { MongoClient } from 'mongodb';

let client;
let connecting;

/**
 * Reuse one process-wide MongoClient and one connection promise. A local CLI
 * has sequential calls, so keep default pool sizing. Fail startup within ten
 * seconds; do not impose a short socket timeout on potentially long index
 * builds. TLS verification stays enabled regardless of URI defaults.
 */
export async function openDatabase(config) {
  if (!client) {
    client = new MongoClient(config.uri, {
      tls: true,
      authMechanism: 'SCRAM-SHA-256',
      retryWrites: false,
      retryReads: true,
      maxIdleTimeMS: 120000,
      serverSelectionTimeoutMS: 10000,
      connectTimeoutMS: 10000,
      appName: 'retail-semantic-search',
    });
    connecting = client.connect().then(() => client.db('admin').command({ ping: 1 }));
  }
  try {
    await connecting;
    return client.db(config.database);
  } catch {
    await closeDatabase();
    throw new Error('Cannot connect to Azure DocumentDB. Check DOCUMENTDB_URI credentials, client IP firewall/private endpoint routing, TLS trust, and cluster availability.');
  }
}

/** Close the shared pool only when the CLI or ingestion process shuts down. */
export async function closeDatabase() {
  if (client) await client.close();
  client = undefined;
  connecting = undefined;
}
