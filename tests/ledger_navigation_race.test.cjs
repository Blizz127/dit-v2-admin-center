// Actual UI, synthetic deferred trace responses; no sockets, browser or live ledger.
const assert = require('node:assert/strict');
const {get,refresh,context} = require('./overview_snapshot_harness.cjs');
const bot = {id:'A',name:'Synthetic bot',game:'FFXI',source:'Synthetic'};
const data = {bots:[bot],replyEvents:[{botId:'A',correlationId:'new'}],
  ledger:[{botId:'A',correlationId:'new',request:'CURRENT_EVIDENCE',verification:'Unknown'}]};
const flush = () => new Promise(resolve=>setImmediate(resolve));
function follow(){
  context.inspectBot('A');
  get('reply-source').children.flatMap(row=>row.children)
    .find(n=>n.textContent==='Find loaded ledger evidence').listeners.click();
}
(async()=>{
  await refresh(data);get('trace-game').value='ffxi';
  const pending=[];
  context.fetch=(url,options)=>new Promise((resolve,reject)=>{
    assert.match(url,/^\/api\/trace\?/);assert.equal(options.method||'GET','GET');
    pending.push({resolve,reject});
  });
  for(const mode of ['success','denied','failed','late-json']){
    const job=context.loadHubTrace('old');
    const request=pending.at(-1);
    let finishJson;
    if(mode==='late-json'){
      request.resolve({ok:true,json:()=>new Promise(resolve=>{finishJson=resolve;})});await flush();
    }
    const before=pending.length;follow();
    assert.equal(pending.length,before,'Loaded evidence navigation must not fetch');
    const payload={records:[{kind:'STALE_TRACE'}],coverage:'OLD_COVERAGE'};
    if(mode==='success')request.resolve({ok:true,json:async()=>payload});
    if(mode==='denied')request.resolve({ok:false,status:401});
    if(mode==='failed')request.reject(new Error('PRIVATE_FAILURE'));
    if(mode==='late-json')finishJson(payload);
    await job;
    assert.equal(get('hub-trace').textContent,'');
    assert.match(get('ledger').textContent,/CURRENT_EVIDENCE/);
    assert.match(get('ledger-filter').textContent,/new.*Pinned bot ID: A/);
  }
  // A subsequent explicit trace remains usable after the canceled requests.
  const current=context.loadHubTrace('new');
  pending.at(-1).resolve({ok:true,json:async()=>({records:[],coverage:'CURRENT_TRACE'})});
  await current;assert.match(get('hub-trace').textContent,/CURRENT_TRACE.*No matching trace records/);
  // Source transition retains old scoped evidence only while that snapshot remains loaded.
  let finishOverview;
  const originalFetch=context.fetch;
  context.fetch=(url,options)=>{
    if(url==='/api/overview?source=hub')return new Promise(resolve=>{finishOverview=resolve;});
    if(url==='/api/bridge-status')return Promise.resolve({ok:true,json:async()=>({unit:'unknown',source:'Synthetic'})});
    return originalFetch(url,options);
  };
  follow();get('data-source').value='hub';
  const failedSource=get('data-source').listeners.change();
  assert.match(get('ledger-filter').textContent,/Pinned bot ID: A/);
  assert.equal(get('hub-trace').textContent,'');
  finishOverview({ok:false,status:503});await failedSource;
  assert.match(get('ledger-filter').textContent,/Pinned bot ID: A/);
  assert.match(get('hub-banner').textContent,/previous mock/);
  const changedSource=get('data-source').listeners.change();
  finishOverview({ok:true,json:async()=>({...data,
    learning:[],hubFeeds:[],ownerAttention:{items:[]},
    ledger:[{botId:'A',correlationId:'different',request:'NEW_SOURCE_EVIDENCE'}]})});
  await changedSource;
  assert.equal(get('workspace').hidden,false);
  assert.equal(get('correlation').value,'');
  assert.doesNotMatch(get('ledger-filter').textContent,/Pinned bot/);
  assert.match(get('ledger').textContent,/NEW_SOURCE_EVIDENCE/);
  assert.doesNotMatch(get('ledger').textContent,/CURRENT_EVIDENCE/);
  console.log('PASS: reply-ledger navigation discards late success, denial, failure and JSON; explicit trace recovers. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
