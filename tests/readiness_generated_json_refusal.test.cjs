// Synthetic subprocess output mutations only; no browser or live service.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {execFileSync, spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'dit-readiness-json-'));
try {
  const env = {...process.env, HOME: temp};
  const artifact = path.join(temp, 'synthetic-preview.html');
  const html = execFileSync('python3', ['-c',
    'from tools.build_inspector_playtest import build; print(build(), end="")'],
    {cwd: root, env, encoding: 'utf8', timeout: 10000, maxBuffer: 2 * 1024 * 1024});
  fs.writeFileSync(artifact, html);
  const child = `
    const bad = require('node:fs').readFileSync(0, 'utf8');
    const cp = require('node:child_process'), original = cp.execFileSync;
    cp.execFileSync = (command, args, options) =>
      args[0] === '-c' && args[1].includes('from tests.test_wake_verification import receipt')
        ? bad : original(command, args, options);
    process.argv[2] = process.argv[1];
    require('./tools/readiness_snapshot.cjs');
  `;
  for (const bad of ['{"rows":', 'null', '[]', ' '.repeat(1024 * 1024 + 1)]) {
    const result = spawnSync(process.execPath, ['-e', child, artifact], {
      cwd: root, env, input: bad, encoding: 'utf8', timeout: 10000, maxBuffer: 1024 * 1024,
    });
    assert.ifError(result.error);
    assert.equal(result.status, 1, 'invalid generated JSON must not pass');
    assert.equal(result.stdout, '');
    assert.match(result.stderr, /FAIL: readiness semantic snapshot/);
  }
  console.log('PASS: generated readiness JSON refusal paths; native browser NOT RUN.');
} finally {
  fs.rmSync(temp, {recursive: true, force: true});
}
