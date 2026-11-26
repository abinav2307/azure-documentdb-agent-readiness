import { createInterface } from 'node:readline/promises';
import { stdin, stdout } from 'node:process';
import { loadConfig } from './config.js';
import { connectDatabase, closeDatabase, assertDiskAnn } from './db.js';
import { createRecommendationAgent } from './agent.js';
import { displayError } from './errors.js';

/**
 * Run a single-user interactive CLI; every product ID starts a recommendation turn.
 * /session LABEL isolates memory, /reset clears the active session, /quit exits.
 * A positional product ID performs one request and exits for smoke testing.
 */
async function main() {
  let terminal;
  try {
    const config = loadConfig();
    const db = await connectDatabase(config);
    assertDiskAnn(await db.collection('products').listIndexes().toArray());
    const service = createRecommendationAgent(db, config.apiKey);
    if (process.argv[2]) {
      console.log(JSON.stringify(await service.recommend(process.argv[2]), null, 2));
      return;
    }
    terminal = createInterface({ input: stdin, output: stdout });
    let sessionId = 'default';
    console.log('Enter p0001–p0120. Commands: /session LABEL, /reset, /quit. Memory is local and disappears on restart.');
    while (true) {
      let line;
      try { line = (await terminal.question(`[${sessionId}] product> `)).trim(); }
      catch { break; }
      if (line === '/quit') break;
      if (line === '/reset') { service.resetSession(sessionId); console.log('Session cleared.'); continue; }
      if (line.startsWith('/session ')) {
        const label = line.slice(9).trim();
        if (/^[a-zA-Z0-9_-]{1,64}$/.test(label)) sessionId = label;
        else console.log('Invalid session label. Use 1–64 letters, digits, underscores or hyphens.');
        continue;
      }
      if (!line) continue;
      try { console.log(JSON.stringify(await service.recommend(line, sessionId), null, 2)); }
      catch (error) { console.error(displayError(error)); }
    }
  } catch (error) {
    console.error(displayError(error));
    process.exitCode = 1;
  } finally {
    terminal?.close();
    await closeDatabase();
  }
}

await main();
