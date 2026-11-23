import { MongoClient } from 'mongodb';

export const settings = Object.freeze({
  database: 'retail_semantic_sample',
  embeddingModel: 'text-embedding-3-small',
  dimensions: 1536,
  embeddingVersion: 1,
  chatModel: 'gpt-4o-mini',
});

/**
 * Read secrets only from environment variables (npm loads the local .env file).
 * Validate the portal URI before network access, including native authentication
 * and TLS safety. Never echo parser errors: they can contain the secret URI.
 * The MongoDB driver remains the authority for complete URI parsing.
 */
export function loadConfig(env = process.env, requireModel = true) {
  const uri = env.DOCUMENTDB_URI?.trim();
  if (!uri || uri.startsWith('REPLACE_')) {
    throw new Error('DOCUMENTDB_URI is missing. Copy .env.example to .env and paste your Azure portal connection string.');
  }
  try {
    if (!uri.startsWith('mongodb+srv://') || /[<>\s]/.test(uri)) throw new Error();
    const parsed = new URL(uri);
    if (!parsed.username || !parsed.password || !parsed.hostname) throw new Error();
    const params = new Map([...parsed.searchParams].map(([k, v]) => [k.toLowerCase(), v]));
    for (const name of ['tlsinsecure', 'tlsallowinvalidcertificates', 'tlsallowinvalidhostnames']) {
      if (params.has(name)) throw new Error();
    }
    if (params.get('tls') === 'false' || params.get('ssl') === 'false') throw new Error();
    if (params.has('authmechanism') && params.get('authmechanism') !== 'SCRAM-SHA-256') throw new Error();
    // Constructing the driver parses options without connecting or reading data.
    const parser = new MongoClient(uri, { tls: true, authMechanism: 'SCRAM-SHA-256', retryWrites: false });
    void parser.close();
  } catch {
    throw new Error('DOCUMENTDB_URI is invalid. Use the portal native-auth mongodb+srv URI with an encoded username/password, TLS and SCRAM-SHA-256; remove placeholders and TLS bypass options.');
  }
  const apiKey = env.OPENAI_API_KEY?.trim();
  if (requireModel && (!apiKey || apiKey.startsWith('REPLACE_'))) {
    throw new Error('OPENAI_API_KEY is missing. Set it locally in .env or your environment.');
  }
  return { ...settings, uri, apiKey };
}

/**
 * Present safe, actionable CLI errors. Only application-authored errors are
 * printed by entry points; raw driver/provider errors must be wrapped first.
 */
export function reportError(error) {
  console.error(`Error: ${error.message}`);
  process.exitCode = 1;
}
