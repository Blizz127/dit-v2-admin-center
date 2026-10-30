// Actual UI/refresh path; synthetic DOM and responses, no browser or live calls.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const {get, refresh, snapshot, context} = require('./overview_snapshot_harness.cjs');
(async () => {
  await refresh({});
  assert.match(get('operation-sources').textContent, /Not checked in standalone preview/);
  const data = structuredClone(snapshot.operationSources);
  data.rows[0].state = 'Reviewed bytes match';
  data.rows[1].state = 'Source changed — review required';
  data.rows[2].state = 'Source unavailable';
  await refresh({operationSources: data});
  for (const row of data.rows) assert.ok(get('operation-sources').textContent.includes(row.state));
  assert.equal(get('wake-acceptance-enb').textContent, 'Unverified');
  assert.match(get('wake-acceptance-war').textContent, /^Held/);
  data.rows.push(data.rows[0]);
  await refresh({operationSources: data});
  assert.ok(!get('operation-sources').textContent.includes('Reviewed bytes match'));
  vm.runInContext('resetPanelSession()', context);
  assert.match(get('operation-sources').textContent, /Source coverage unknown/);
  await refresh({});
  context.fetch = async () => { throw Error('synthetic failure'); };
  await get('refresh').listeners.click();
  assert.ok(!get('operation-sources').textContent.includes('Dated report:'));
  console.log('PASS: operation source states, exact identities, reset/failure and acceptance separation; native browser NOT RUN.');
})().catch(error => { console.error(error); process.exitCode = 1; });
