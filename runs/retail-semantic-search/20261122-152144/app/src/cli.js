import { createInterface } from 'node:readline/promises';
import { stdin, stderr } from 'node:process';
import { loadConfig, reportError } from './config.js';
import { openDatabase, closeDatabase } from './database.js';
import { createModels } from './models.js';
import { SessionMemory } from './memory.js';
import { recommend } from './recommendations.js';

/**
 * Accept a product ID and optional session ID. Without --interactive the CLI
 * exits after one JSON result. Interactive mode retains sessions in the same
 * process; subsequent lines use `productId [sessionId]`, with exit to finish.
 * Prompts go to stderr, leaving stdout as recommendation JSON only.
 */
async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--help')) {
    console.log('Usage: npm start -- sample-p001 [sessionId] [--interactive]\nInteractive input: productId [sessionId]; exit to quit.');
    return;
  }
  const interactive = args.includes('--interactive');
  const [productId, sessionId = 'demo-session'] = args.filter(arg => arg !== '--interactive');
  if (!productId && !interactive) throw new Error('Provide a product ID: npm start -- sample-p001 demo-session --interactive');
  const config = loadConfig();
  const db = await openDatabase(config);
  const { llm } = createModels(config);
  const memory = new SessionMemory();
  // Complete one recommendation and write the validated structured response.
  async function run(id, session) {
    const response = await recommend({ db, llm, memory, productId: id, sessionId: session });
    console.log(JSON.stringify(response, null, 2));
  }
  if (productId) await run(productId, sessionId);
  if (!interactive) return;
  const input = createInterface({ input: stdin, output: stderr });
  try {
    for (;;) {
      const line = (await input.question('productId [sessionId] (exit to quit)> ')).trim();
      if (line === 'exit') break;
      if (!line) continue;
      const [id, session = sessionId] = line.split(/\s+/);
      try { await run(id, session); } catch (error) { console.error(`Error: ${error.message}`); }
    }
  } finally { input.close(); }
}

try { await main(); } catch (error) { reportError(error); } finally { await closeDatabase(); }
