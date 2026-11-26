import { SampleError } from './errors.js';
import { readFileSync } from 'node:fs';
import { MongoClient } from 'mongodb';

export const DATABASE = 'retail_semantic_sample_v1';
export const EMBEDDING_MODEL = 'text-embedding-3-small';
export const DIMENSIONS = 1536;
export const CHAT_MODEL = 'gpt-4o-mini';
export const SAMPLE_VERSION = 'retail-semantic-v1';

/**
 * Validate a native-auth Azure DocumentDB URI without connecting or revealing it.
 * The official driver also parses the URI to catch malformed ports/options.
 * This sample accepts portal SRV hosts, enforces certificate verification, and
 * refuses TLS/retry/auth overrides rather than silently weakening security.
 */
export function validateConnectionString(uri) {
  if (typeof uri !== 'string' || !uri.trim() || uri.startsWith('<')) {
    throw new SampleError('Missing Azure DocumentDB connection string: set DOCUMENTDB_URI (or the config-selected environment variable).');
  }
  try {
    const url = new URL(uri);
    const host = url.hostname.toLowerCase();
    if (url.protocol !== 'mongodb+srv:' || !url.username || !url.password ||
        !/^(?:[a-z0-9-]+\.)+(?:mongocluster\.cosmos\.azure\.com|mongocluster\.documentdb\.azure\.com)$/.test(host)) throw new SampleError();
    for (const [key, value] of url.searchParams) {
      const option = key.toLowerCase();
      if (['tls', 'ssl'].includes(option) && value !== 'true') throw new SampleError();
      if (option === 'retrywrites' && value !== 'false') throw new SampleError();
      if (option === 'authmechanism' && value !== 'SCRAM-SHA-256') throw new SampleError();
      if (['tlsinsecure', 'tlsallowinvalidcertificates', 'tlsallowinvalidhostnames'].includes(option) && value !== 'false') throw new SampleError();
    }
    // Construction performs the driver's syntax validation; it opens no sockets.
    new MongoClient(uri, { tls: true, retryWrites: false, authMechanism: 'SCRAM-SHA-256' });
    return uri;
  } catch {
    throw new SampleError('Invalid Azure DocumentDB connection string. Use the portal mongodb+srv URI with URL-encoded SCRAM credentials, TLS enabled, retryWrites=false, and certificate verification. URI omitted for safety.');
  }
}

/**
 * Read a secret-free config file that selects the URI environment variable.
 * No credentials are loaded from disk and parse failures never echo file contents.
 * Set requireModel=false for the database-only verification command.
 */
export function loadConfig({ path = 'config.json', env = process.env, requireModel = true } = {}) {
  let config;
  try { config = JSON.parse(readFileSync(path, 'utf8')); }
  catch { throw new SampleError('Missing or invalid config.json. Copy config.example.json to config.json; keep connectionStringEnv as an environment-variable name, not a URI.'); }
  if (!config || typeof config.connectionStringEnv !== 'string' || !/^[A-Z][A-Z0-9_]*$/.test(config.connectionStringEnv)) {
    throw new SampleError('Invalid config.json: connectionStringEnv must name an environment variable such as DOCUMENTDB_URI.');
  }
  const uri = validateConnectionString(env[config.connectionStringEnv]);
  if (requireModel && (!env.OPENAI_API_KEY || env.OPENAI_API_KEY.startsWith('<'))) {
    throw new SampleError('Missing OPENAI_API_KEY. Set it in your shell for embeddings and agent explanations.');
  }
  return { uri, apiKey: env.OPENAI_API_KEY };
}
