// Actual UI with synthetic projection/DOM. No browser or live requests.
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const vm = require('node:vm');
const {get, refresh, context, requestCount} = require('./overview_snapshot_harness.cjs');
const data = JSON.parse(execFileSync('python3', ['-c',
  'import json; from tests.test_wake_verification import receipt; from wake_verification import project; print(json.dumps(project(receipt())))'],
  {encoding: 'utf8', timeout: 5000}));
const games = data.rows.map(row => row.game);
const visible = () => games.filter(game => !get('wake-row-' + game).hidden);
function filter(value) {
  const before = requestCount();
  get('wake-readiness-filter').value = value;
  get('wake-readiness-filter').listeners.change();
  assert.equal(requestCount(), before, 'Filtering must not fetch evidence');
}
(async () => {
  await refresh({wakeVerification: data});
  assert.equal(visible().length, 12);
  assert.match(get('wake-readiness-count').textContent, /2 reported ready readbacks · 8 unverified · 2 retained holds/);
  filter('held');
  assert.deepEqual(visible(), ['war', 'marvel-heroes']);
  filter('reported');
  assert.deepEqual(visible(), ['wow-forever', 'enb']);
  const duplicate = structuredClone(data);
  duplicate.rows.push(duplicate.rows.find(row => row.game === 'enb'));
  await refresh({wakeVerification: duplicate});
  assert.equal(get('wake-readiness-filter').value, 'reported');
  assert.deepEqual(visible(), ['wow-forever']);
  assert.match(get('wake-readiness-count').textContent, /Showing 1 of 12/);
  filter('unverified');
  assert.equal(visible().length, 9);
  assert.ok(visible().includes('enb'));
  filter('reported');
  const originalFetch = context.fetch;
  context.fetch = async () => { throw Error('synthetic refresh failure'); };
  await get('refresh').listeners.click();
  assert.equal(visible().length, 0);
  assert.equal(get('wake-filter-empty').hidden, false);
  filter('all');
  filter('reported');
  assert.equal(visible().length, 0, 'Filter changes cannot revive stale readbacks');
  assert.match(get('wake-readiness-count').textContent, /0 reported ready readbacks · 10 unverified · 2 retained holds/);
  context.fetch = originalFetch;
  await refresh({wakeVerification: data});
  assert.deepEqual(visible(), ['wow-forever', 'enb']);
  assert.equal(get('wake-filter-empty').hidden, true);
  filter('invalid');
  assert.equal(get('wake-readiness-filter').value, 'all');
  filter('held');
  vm.runInContext('resetPanelSession()', context);
  assert.equal(get('wake-readiness-filter').value, 'all');
  assert.equal(visible().length, 12);
  assert.equal(get('wake-acceptance-enb').textContent, 'Unverified');
  console.log('PASS: local readiness filters, counts, holds, refresh persistence, stale-claim clearing and recovery. Native browser NOT RUN.');
})().catch(error => { console.error(error); process.exitCode = 1; });
