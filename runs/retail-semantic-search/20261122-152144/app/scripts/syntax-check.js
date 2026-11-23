import { readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

/** Check every application/script/test JavaScript file with Node's syntax parser. */
function check() {
  let count = 0;
  for (const folder of ['src', 'scripts', 'test']) {
    for (const file of readdirSync(folder).filter(name => name.endsWith('.js'))) {
      const result = spawnSync(process.execPath, ['--check', `${folder}/${file}`], { encoding: 'utf8' });
      if (result.status !== 0) throw new Error(result.stderr || `Syntax check failed: ${file}`);
      count++;
    }
  }
  console.log(`Syntax checks passed: ${count} files`);
}
check();
