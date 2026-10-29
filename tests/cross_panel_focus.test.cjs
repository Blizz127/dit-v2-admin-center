// Real UI handlers with loaded synthetic rows. No browser focus/keys claimed.
const assert=require('node:assert/strict');
const {get,refresh,context,requestCount}=require('./overview_snapshot_harness.cjs');
(async()=>{
  const focused=[];
  for(const id of ['bots','learning','issues','trace-search','ledger','bridge-status','owner-attention'])get(id).focus=()=>focused.push(id);
  const bots=[{id:'one',name:'Same name',game:'FFXI'},{id:'two',name:'Same name',game:'SWTOR'}];
  await refresh({bots,learning:[{id:'need',topic:'Fixture learning',game:'FFXI'}],
    issues:[{title:'Fixture observation',scope:'FFXI',bridgeObservation:true,ownerAttention:true}],
    ledger:[{botId:'one',correlationId:'SHARED',bot:'MATCHED_BOT',request:'Fixture'},
      {botId:'two',correlationId:'SHARED',bot:'OTHER_BOT',request:'Fixture'},
      {correlationId:'SHARED',bot:'UNSCOPED',request:'Fixture'}]});
  const before=requestCount();
  get('bot-search').value='old';get('bot-identity').value='unavailable';
  get('ffxi-bots').listeners.click();
  assert.equal(focused.at(-1),'bots');assert.equal(get('bot-game').value,'FFXI');
  assert.equal(get('bot-search').value,'');assert.equal(get('bot-identity').value,'');
  assert.match(get('bot-count').textContent,/Showing 1 of 2/);
  get('ffxi-learning').listeners.click();assert.equal(focused.at(-1),'learning');
  assert.equal(get('learning-game').value,'FFXI');
  get('ffxi-issues').listeners.click();assert.equal(focused.at(-1),'issues');
  for(const [label,destination] of [['View current bridge observation','bridge-status'],['View owner decision summary','owner-attention']]){
    get('issues').children.flatMap(r=>r.children).find(n=>n.textContent===label).listeners.click();
    assert.equal(focused.at(-1),destination);
  }
  context.showBotLedgerExample(bots[0],'SHARED');
  assert.equal(focused.at(-1),'ledger');assert.match(get('ledger').textContent,/MATCHED_BOT/);
  assert.doesNotMatch(get('ledger').textContent,/OTHER_BOT|UNSCOPED/);
  assert.equal(get('correlation').value,'SHARED');assert.equal(get('trace-game').value,'ffxi');
  get('ffxi-evidence').listeners.click();assert.equal(focused.at(-1),'trace-search');
  assert.equal(get('correlation').value,'');
  assert.match(get('ledger-filter').textContent,/all loaded examples/);
  assert.equal(requestCount(),before,'Local navigation does not request bridge, hub or ledger data');
  console.log('PASS: cross-panel focus with FFXI filters, exact-bot ledger isolation and no additional reads. Native behavior NOT RUN.');
})().catch(error=>{console.error(error);process.exitCode=1;});
