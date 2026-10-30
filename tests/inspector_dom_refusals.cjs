// Explicit offline jsdom checks. Run with DIT_JSDOM_MODULE set; never installs.
// Mutations exist only in child-process memory, not in source or the preview.
const assert = require('node:assert/strict');
const path = require('node:path');
const {execFileSync, spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
require.resolve(process.env.DIT_JSDOM_MODULE || 'jsdom');
const html = execFileSync('python3', ['-c',
  'from tools.build_inspector_playtest import build; print(build(), end="")'],
  {cwd: root, encoding: 'utf8', timeout: 10000, maxBuffer: 2 * 1024 * 1024});
const cases = [
  ['positive sidebar tabindex', 'id="nav-roster"', 'id="nav-roster" tabindex="1"',
    'Sidebar DOM Tab candidates'],
  ['wrong download filename', '`roster-gap-row-${report.selectedSnapshotRow}.json`',
    '`wrong-row.json`', 'Gap download filename'],
  ['different Blob bytes', 'new Blob([json],', 'new Blob([json + " "],',
    'Gap Blob bytes equal'],
  ['stalled driver', 'const readinessFilter =', 'await new Promise(() => {}); const readinessFilter =',
    'Harness did not finish within five seconds'],
  ['script parse error', 'const requests = [];', 'const requests = ;', 'DOM runtime errors:'],
];
const child = `
  const html = require('node:fs').readFileSync(0, 'utf8');
  // Replace only artifact generation; the real runner still executes its DOM,
  // network guards, assertion aggregation, failure path and cleanup.
  require('node:child_process').execFileSync = () => html;
  require('./tools/run_inspector_playtest.cjs');
`;
for (const [name, before, after, failure] of cases) {
  assert.equal(html.split(before).length, 2, name + ': mutation target must be unique');
  const result = spawnSync(process.execPath, ['-e', child], {
    cwd: root, env: process.env, input: html.replace(before, after), encoding: 'utf8',
    timeout: 10000, maxBuffer: 1024 * 1024,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 1, name + ': must fail, not pass or block');
  assert.ok(result.stderr.includes('FAIL:') && result.stderr.includes(failure), result.stderr);
  assert.equal(result.stdout, '', name + ': must not emit a successful receipt');
  const diagnostic = JSON.parse(result.stderr.split('\n').find(line => line.startsWith('DIAGNOSTIC: ')).slice(12));
  assert.equal(diagnostic.status, 'failed');
  assert.equal(diagnostic.artifactSha256, require('node:crypto').createHash('sha256').update(html.replace(before, after)).digest('hex'));
  assert.ok(diagnostic.lastCheck.length <= 240);
  if (name === 'stalled driver') {
    assert.equal(diagnostic.reason, 'completion-timeout');
    assert.ok(diagnostic.completedChecks > 0);
    assert.match(diagnostic.lastCheck, /Sidebar DOM navigation/);
    assert.ok(diagnostic.completionWaitMs >= 5000 && diagnostic.completionWaitMs < 8000);
  }
  if (name === 'script parse error') {
    assert.equal(diagnostic.reason, 'runtime-or-assertion');
    assert.equal(diagnostic.completedChecks, 0);
    assert.ok(diagnostic.runtimeErrors > 0);
  }
  console.log('PASS — refuses ' + name);
}
