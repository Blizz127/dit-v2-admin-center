// Actual UI functions with synthetic snapshots in a minimal DOM, no browser/network.
const assert = require('node:assert/strict');
const {get, refresh, context, requestCount} = require('./overview_snapshot_harness.cjs');
const bots = ['A', 'B'].map(id => ({id, name:'Same name', game:'FFXI', source:'Synthetic'}));
const replyEvents = [
  {botId:'A', correlationId:'Party-1', wordingOrigin:'Model example', generationStatus:'generated', delivery:'Unknown', verification:'Unknown'},
  {botId:'A', correlationId:'Party-10', wordingOrigin:'Canned fallback', delivery:'queued', verification:'Unknown'},
  {botId:'B', correlationId:'Party-1', wordingOrigin:'OTHER_BOT'}
];
const ledger = [
  {botId:'A', correlationId:'Party-1',request:'A_EVIDENCE',result:'pending',verification:'Unknown'},
  {botId:'B', correlationId:'Party-1',request:'B_EVIDENCE'},
  {correlationId:'Party-1',request:'UNSCOPED_EVIDENCE'}
];
const data = {bots, replyEvents, ledger};
const links = () => get('reply-source').children.flatMap(row=>row.children).filter(n=>n.textContent==='Find loaded ledger evidence');
const filter = value => {get('reply-correlation').value=value; get('reply-correlation').listeners.input();};
(async()=>{
  await refresh(data);context.inspectBot('A');
  assert.match(get('reply-count').textContent,/Showing 2 of 2/);
  const before=requestCount();filter('Party-1');
  assert.match(get('reply-count').textContent,/Showing 1 of 2/);
  assert.match(get('reply-source').textContent,/Generation: generated.*Delivery: Unknown.*Verification: Unknown/);
  assert.doesNotMatch(get('reply-source').textContent,/Party-10|OTHER_BOT/);
  get('hub-trace').textContent='Previous trace';links()[0].listeners.click();
  assert.match(get('ledger').textContent,/A_EVIDENCE.*pending.*Unknown/);
  assert.doesNotMatch(get('ledger').textContent,/B_EVIDENCE|UNSCOPED_EVIDENCE/);
  assert.equal(get('hub-trace').textContent,'');
  assert.match(get('ledger-filter').textContent,/Pinned bot ID: A/);
  assert.equal(requestCount(),before,'Ledger shortcut uses loaded evidence only');
  filter('party-1');assert.match(get('reply-source').textContent,/No matching correlation/);
  filter(' Party-1 ');assert.match(get('reply-count').textContent,/Showing 1 of 2/);
  assert.equal(requestCount(),before);
  await refresh(data);assert.match(get('reply-count').textContent,/Showing 1 of 2/);
  get('reply-reset').listeners.click();links()[1].listeners.click();
  assert.match(get('ledger').textContent,/No matching evidence.*not proof/);
  await refresh({...data,replyEvents:[{botId:'A',correlationId:' '},{botId:'A',correlationId:42}]});
  assert.equal(links().length,0,'Invalid correlation cannot navigate to broader evidence');
  await refresh(data);
  get('reply-reset').listeners.click();assert.match(get('reply-count').textContent,/Showing 2 of 2/);
  filter('Party-10');context.inspectBot('B');assert.equal(get('reply-correlation').value,'');
  assert.match(get('reply-source').textContent,/OTHER_BOT/);
  assert.doesNotMatch(get('reply-source').textContent,/Canned fallback/);
  await refresh({...data,bots:[bots[1],bots[1]]});
  assert.doesNotMatch(get('reply-source').textContent,/OTHER_BOT/);
  await refresh(data);context.inspectBot('A');
  await refresh({...data,replyEvents:[null,[],false,{}, {botId:' ',wordingOrigin:'DO_NOT_ATTRIBUTE'},...replyEvents]});
  assert.match(get('reply-count').textContent,/Showing 2 of Unknown total/);
  assert.match(get('reply-source').textContent,/coverage unknown.*Model example.*Canned fallback/);
  assert.doesNotMatch(get('reply-source').textContent,/OTHER_BOT|DO_NOT_ATTRIBUTE/);
  filter('Party-1');assert.match(get('reply-count').textContent,/Showing 1 of Unknown total/);
  for(const replyEvents of [null,undefined,{}]){
    await refresh({...data,replyEvents});
    assert.match(get('reply-count').textContent,/Showing 0 of Unknown total/);
    assert.doesNotMatch(get('reply-source').textContent,/Model example|Canned fallback/);
  }
  await refresh({...data,replyEvents:[]});assert.match(get('reply-count').textContent,/Showing 0 of 0/);
  await refresh(data);assert.match(get('reply-count').textContent,/Showing 1 of 2/);
  context.resetPanelSession();assert.equal(get('reply-correlation').value,'');
  assert.match(get('reply-count').textContent,/Select a bot/);
  console.log('PASS: exact bot-scoped reply filter, local requests, refresh persistence, selection reset and unknown delivery. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
