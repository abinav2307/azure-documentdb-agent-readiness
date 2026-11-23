import { loadConfig, reportError } from '../src/config.js';
import { openDatabase, closeDatabase } from '../src/database.js';
import { createModels } from '../src/models.js';
import { ingest } from '../src/ingestion.js';

/**
 * Run the repeatable paid embedding/seed operation against the dedicated
 * sample database. Wrap driver/provider errors without printing raw secrets;
 * a partial seed can be resumed by running this command again.
 */
async function main() {
  const config = loadConfig();
  const db = await openDatabase(config);
  const { embeddingModel } = createModels(config);
  try {
    console.log(JSON.stringify(await ingest(db, embeddingModel), null, 2));
  } catch {
    throw new Error('Ingestion failed. Check database write/index permissions, M30+ DiskANN support, OPENAI_API_KEY, model quota and network access. Re-run to resume; deterministic orders and unchanged embeddings are reused.');
  }
}
try { await main(); } catch (error) { reportError(error); } finally { await closeDatabase(); }
