// Actual UI functions with synthetic snapshots in a minimal DOM, no browser/network.
const assert = require('node:assert/strict');
const {get, refresh, context, requestCount} = require('./overview_snapshot_harness.cjs');
const bots = ['A', 'B'].map(id => ({id, name:'Same name', game:'FFXI', source:'Synthetic'}));
const replyEvents = [
  {botId:'A', correlationId:'Party-1', wordingOrigin:'Model example', generationStatus:'generated', delivery:'Unknown', verification:'Unknown'},
  {botId:'A', correlationId:'Party-10', wordingOrigin:'Canned fallback', delivery:'queued', verification:'Unknown'},
  {botId:'B', correlationId:'Party-1', wordingOrigin:'OTHER_BOT'}
];
const data = {bots, replyEvents};
const filter = value => {get('reply-correlation').value=value; get('reply-correlation').listeners.input();};
(async()=>{
  await refresh(data);context.inspectBot('A');
  assert.match(get('reply-count').textContent,/Showing 2 of 2/);
  const before=requestCount();filter('Party-1');
  assert.match(get('reply-count').textContent,/Showing 1 of 2/);
  assert.match(get('reply-source').textContent,/Generation: generated.*Delivery: Unknown.*Verification: Unknown/);
  assert.doesNotMatch(get('reply-source').textContent,/Party-10|OTHER_BOT/);
  filter('party-1');assert.match(get('reply-source').textContent,/No matching correlation/);
  filter(' Party-1 ');assert.match(get('reply-count').textContent,/Showing 1 of 2/);
  assert.equal(requestCount(),before);
  await refresh(data);assert.match(get('reply-count').textContent,/Showing 1 of 2/);
  get('reply-reset').listeners.click();assert.match(get('reply-count').textContent,/Showing 2 of 2/);
  filter('Party-10');context.inspectBot('B');assert.equal(get('reply-correlation').value,'');
  assert.match(get('reply-source').textContent,/OTHER_BOT/);
  assert.doesNotMatch(get('reply-source').textContent,/Canned fallback/);
  await refresh({...data,bots:[bots[1],bots[1]]});
  assert.doesNotMatch(get('reply-source').textContent,/OTHER_BOT/);
  context.resetPanelSession();assert.equal(get('reply-correlation').value,'');
  assert.match(get('reply-count').textContent,/Select a bot/);
  console.log('PASS: exact bot-scoped reply filter, local requests, refresh persistence, selection reset and unknown delivery. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
