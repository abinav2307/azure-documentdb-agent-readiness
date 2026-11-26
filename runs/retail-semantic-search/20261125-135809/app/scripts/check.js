import { readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

/** Check all authored JavaScript files without starting servers or needing secrets. */
function main() {
  let count = 0;
  for (const folder of ['src', 'scripts', 'test']) {
    for (const name of readdirSync(folder).filter(name => name.endsWith('.js'))) {
      const result = spawnSync(process.execPath, ['--check', `${folder}/${name}`], { stdio: 'inherit' });
      if (result.status !== 0) process.exit(1);
      count++;
    }
  }
  console.log(`Syntax check passed: ${count} files.`);
}

main();
