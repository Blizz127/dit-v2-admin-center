// Read-only snapshot overview, actual UI with synthetic data in a minimal DOM.
const assert=require('node:assert/strict');
const {get,refresh,context,requestCount}=require('./overview_snapshot_harness.cjs');
(async()=>{
  await refresh({bots:null,learning:[],modelCalls:[null,{latencyMs:0,cost:0,quality:0},{}]});
  let text=get('data-coverage').textContent;
  assert.match(text,/Bot roster · Unavailable collection.*Usable rows: 0 · Loaded total: Unknown/);
  assert.match(text,/Learning needs · Empty loaded collection.*Loaded total: 0/);
  assert.match(text,/Model call metrics · Partial collection.*Usable rows: 2 · Loaded total: Unknown · Rows with unknown numeric fields: 1/);
  await refresh({bots:[{id:'dup'},{id:'dup'},{}],learning:[{id:'L',game:'FFXI',topic:'Synthetic'}],modelCalls:[]});
  text=get('data-coverage').textContent;
  assert.match(text,/Bot roster · Loaded collection.*Rows without usable IDs: 1 · Rows with repeated IDs: 2/);
  assert.match(text,/Learning needs · Loaded collection.*Rows without usable IDs: 0 · Rows with repeated IDs: 0/);
  const before=requestCount();get('bot-search').value='unmatched';get('bot-search').listeners.input();
  assert.equal(get('data-coverage').textContent,text,'Overview is independent of local filters');
  const targets=[];
  for(const id of ['bots','learning','model-calls'])get(id).scrollIntoView=()=>targets.push(id);
  for(const row of get('data-coverage').children)row.children.find(n=>n.textContent.startsWith('Review ')).listeners.click();
  assert.deepEqual(targets,['bots','learning','model-calls']);
  assert.equal(get('bot-search').value,'unmatched');assert.equal(requestCount(),before);
  context.resetPanelSession();assert.equal(get('data-coverage').textContent,'');
  console.log('PASS: loaded coverage states, ambiguous IDs, numeric gaps, filter-independent counts and request-free navigation. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
