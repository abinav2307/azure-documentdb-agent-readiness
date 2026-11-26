import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';

test('CLI exits nonzero with clear missing/invalid URI messages and no raw secrets', () => {
  const dir = mkdtempSync(join(process.cwd(), 'cli-test-'));
  try {
    const entry = resolve('src/cli.js');
    writeFileSync(join(dir, 'config.json'), JSON.stringify({ connectionStringEnv: 'DOCUMENTDB_URI' }));
    for (const uri of ['', 'invalid-secret-marker']) {
      const result = spawnSync(process.execPath, [entry, 'p0001'], {
        cwd: dir, env: { ...process.env, DOCUMENTDB_URI: uri, OPENAI_API_KEY: '' }, encoding: 'utf8',
      });
      assert.equal(result.status, 1);
      assert.match(result.stderr, /Missing Azure DocumentDB|Invalid Azure DocumentDB/);
      assert(!result.stderr.includes('invalid-secret-marker'));
    }
  } finally { rmSync(dir, { recursive: true }); }
});
