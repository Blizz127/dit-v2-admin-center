// Actual panel click/session code in a simulated DOM; no browser or live data.
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const vm = require('node:vm');
const {get, refresh, context} = require('./overview_snapshot_harness.cjs');
const report = JSON.parse(execFileSync('python3', ['-m', 'tools.correlate_delivery', '--enable-offline', '--capture', 'tests/fixtures/delivery-correlation/ffxi.json'], {encoding:'utf8',timeout:5000}));
(async () => {
  await refresh({});
  const panel = get('delivery-capture'), button = get('delivery-capture-load');
  let response = report;
  context.fetch = async (path, options) => {
    assert.equal(path, '/api/delivery-capture');
    assert.equal(options.method || 'GET', 'GET');
    assert.equal(options.headers.Authorization, 'Bearer synthetic-test-token');
    assert.equal(options.cache, 'no-store');
    return {ok:true, json:async()=>response};
  };
  await button.listeners.click();
  assert.match(panel.textContent, /Actual game delivery: Unknown/);
  assert.match(panel.textContent, /2 publication matches · 0 synthetic native matches/);
  assert.match(panel.textContent, /Inbox sequence 41/);
  assert.match(panel.textContent, /Inbox sequence 42/);
  assert.match(panel.textContent, /Independent of roster selection/);
  for (const property of ['nativeDeliveryVerified', 'replayAuthorized', 'deliveredInGame']) {
    response = structuredClone(report); response[property] = true;
    await button.listeners.click();
    assert.match(panel.textContent, /Delivery evidence unavailable/);
    assert.ok(!panel.textContent.includes('yes, that same entrance'));
  }
  response = structuredClone(report);
  response.records[0].publication = 'Conflict';
  response.records[0].text = response.records[0].bot = null;
  response.counts.publicationMatched = 1; response.counts.conflicted = 1;
  await button.listeners.click();
  assert.match(panel.textContent, /Wording withheld: publication conflict/);
  response = {...report, status:'Not configured', counts:null, records:[]};
  await button.listeners.click();
  assert.equal(panel.textContent, 'No offline delivery evidence configured.');
  response = {...report, status:'Unavailable', counts:null, records:[]};
  await button.listeners.click();
  assert.match(panel.textContent, /Previous content has been cleared/);
  let resolve;
  context.fetch = () => new Promise(done => {resolve=done;});
  const pending = button.listeners.click();
  assert.equal(button.disabled, true);
  vm.runInContext('resetPanelSession()', context);
  resolve({ok:true, json:async()=>report});
  await pending;
  assert.equal(panel.textContent, 'Not requested in this session.');
  assert.equal(button.disabled, false);
  console.log('PASS: delivery panel scope/unknown labels, auth fetch, invalid-claim clearing, conflict wording and late-session suppression; native browser NOT RUN.');
})().catch(error => {console.error(error); process.exitCode=1;});
