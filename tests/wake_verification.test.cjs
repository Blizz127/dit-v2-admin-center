// Real UI refresh/render functions with synthetic local receipt projection, no browser/network.
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const vm = require('node:vm');
const {get, refresh, context} = require('./overview_snapshot_harness.cjs');
const projected = JSON.parse(execFileSync('python3', ['-c',
  'import json; from tests.test_wake_verification import receipt; from wake_verification import project; print(json.dumps(project(receipt())))'],
  {encoding: 'utf8', timeout: 5000}));
(async () => {
  await refresh({wakeVerification: projected});
  assert.match(get('wake-acceptance-enb').textContent, /Verified readback \(reported\).*2026-01-01.*synthetic-enb/);
  assert.match(get('wake-acceptance-ffxi').textContent, /^Unverified$/);
  assert.match(get('wake-acceptance-war').textContent, /^Held/);
  const duplicate = structuredClone(projected); duplicate.rows.push(duplicate.rows.find(r => r.game === 'enb'));
  await refresh({wakeVerification: duplicate});
  assert.equal(get('wake-acceptance-enb').textContent, 'Unverified');
  await refresh({wakeVerification: projected});
  vm.runInContext('resetPanelSession()', context);
  assert.equal(get('wake-acceptance-enb').textContent, 'Unverified');
  await refresh({wakeVerification: projected});
  await refresh({wakeVerification: null});
  assert.equal(get('wake-acceptance-enb').textContent, 'Unverified');
  await refresh({wakeVerification: projected});
  const fetch = context.fetch;
  context.fetch = async () => { throw Error('synthetic transport failure'); };
  await get('refresh').listeners.click();
  assert.equal(get('wake-acceptance-enb').textContent, 'Unverified');
  context.fetch = fetch;
  console.log('PASS: local receipt projection to actual UI refresh; individual/held/duplicate/reset/missing states. Native browser NOT RUN.');
})().catch(error => { console.error(error); process.exitCode = 1; });
