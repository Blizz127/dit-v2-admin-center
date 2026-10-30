// Semantic snapshot only: executes matching app source with a minimal synthetic DOM.
// Does not execute the full artifact driver or implement native layout/default actions.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');

(async () => {
  const artifactPath = path.resolve(process.argv[2] || 'build/inspector-playtest.html');
  const stat = fs.statSync(artifactPath);
  assert.ok(stat.isFile() && stat.size <= 1024 * 1024, 'Expected a bounded generated HTML file');
  const artifact = fs.readFileSync(artifactPath);
  process.env.DIT_TEST_ARTIFACT = artifactPath;
  const {get, refresh, context, requestCount} = require('../tests/overview_snapshot_harness.cjs');
  const projection = JSON.parse(execFileSync('python3', ['-c',
    'import json; from tests.test_wake_verification import receipt; from wake_verification import project; print(json.dumps(project(receipt())))'],
    {encoding: 'utf8', timeout: 5000}));
  const snapshots = [];
  function capture(name, expectedIds, expectedReported) {
    const rows = projection.rows.filter(row => !get('wake-row-' + row.game).hidden)
      .map(row => ({game: row.game, acceptance: get('wake-acceptance-' + row.game).textContent}));
    assert.deepEqual(rows.map(row => row.game), expectedIds, name);
    const count = get('wake-readiness-count').textContent;
    assert.ok(count.includes(`Showing ${rows.length} of 12 mapped games`), name);
    assert.ok(count.includes(`${expectedReported} reported ready readbacks`), name);
    assert.equal(get('wake-filter-empty').hidden, rows.length !== 0, name);
    snapshots.push({name, filter: get('wake-readiness-filter').value, count,
      cutover: get('wake-cutover-status').textContent, emptyNoticeVisible: !get('wake-filter-empty').hidden, rows});
  }
  function filter(value) {
    const before = requestCount();
    get('wake-readiness-filter').value = value;
    get('wake-readiness-filter').listeners.change();
    assert.equal(requestCount(), before, 'Filtering must not request data');
  }
  await refresh({wakeVerification: null});
  capture('No receipt / all', projection.rows.map(row => row.game), 0);
  filter('held');
  capture('Retained holds', ['war', 'marvel-heroes'], 0);
  assert.ok(snapshots.at(-1).rows.every(row => row.acceptance.startsWith('Held')));
  filter('reported');
  capture('No receipt / no reported matches', [], 0);
  await refresh({wakeVerification: projection});
  capture('Synthetic reported readbacks', ['wow-forever', 'enb'], 2);
  assert.ok(snapshots.at(-1).rows.every(row => row.acceptance.includes('Current health unknown')));
  const duplicate = structuredClone(projection);
  duplicate.rows.push(duplicate.rows.find(row => row.game === 'enb'));
  await refresh({wakeVerification: duplicate});
  capture('Synthetic duplicate withheld', ['wow-forever'], 1);
  context.fetch = async () => { throw Error('Synthetic failure'); };
  await get('refresh').listeners.click();
  filter('all'); filter('reported');
  capture('Refresh failed / filter cannot revive claims', [], 0);
  assert.ok(snapshots.at(-1).cutover.includes('receipt unavailable'));
  console.log(JSON.stringify({status: 'semantic-checks-passed',
    artifactSha256: crypto.createHash('sha256').update(artifact).digest('hex'),
    artifactBytes: artifact.length, nativeRendering: 'NOT RUN', nativeKeyboard: 'NOT RUN',
    method: 'Artifact markup parsed; embedded app source matched and executed in synthetic DOM. No full artifact driver, CSS layout or browser engine execution.',
    snapshots}, null, 2));
})().catch(() => {
  console.error('FAIL: readiness semantic snapshot could not verify artifact and scenarios; no native result claimed.');
  process.exitCode = 1;
});
