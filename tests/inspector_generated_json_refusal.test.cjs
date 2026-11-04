// Mutate generated synthetic JSON only in memory; jsdom is not a native browser.
const assert = require('node:assert/strict');
const path = require('node:path');
const {execFileSync, spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
require.resolve(process.env.DIT_JSDOM_MODULE || 'jsdom');
const html = execFileSync('python3', ['-c',
  'from tools.build_inspector_playtest import build; print(build(), end="")'],
  {cwd: root, encoding: 'utf8', timeout: 10000, maxBuffer: 2 * 1024 * 1024});
const child = `
  const html = require('node:fs').readFileSync(0, 'utf8');
  require('node:child_process').execFileSync = () => html;
  require('./tools/run_inspector_playtest.cjs');
`;
const cases = [
  ['truncated', 'const exportedGap = JSON.parse(await exportBlob.text());', 'const exportedGap = JSON.parse("{");'],
  ['wrong type', 'const exportedGap = JSON.parse(await exportBlob.text());', 'const exportedGap = JSON.parse("null");'],
  ['oversized', 'check(exportBlob.size <= 256 * 1024,', 'check((256 * 1024 + 1) <= 256 * 1024,'],
];
for (const [name, before, after] of cases) {
  assert.equal(html.split(before).length, 2, name);
  const result = spawnSync(process.execPath, ['-e', child], {
    cwd: root, env: process.env, input: html.replace(before, after), encoding: 'utf8',
    timeout: 15000, maxBuffer: 1024 * 1024,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 1, name + ': no successful receipt');
  assert.equal(result.stdout, '');
  assert.match(result.stderr, /FAIL:/);
}
console.log('PASS: generated report JSON refusal paths in jsdom; native browser NOT RUN.');
