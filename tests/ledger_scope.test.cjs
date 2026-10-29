// Shared correlation IDs must not broaden an inspector's bot-scoped evidence link.
const assert = require('node:assert/strict');
const {get,refresh,context}=require('./overview_snapshot_harness.cjs');
const bots=['A','B'].map(id=>({id,name:id+'_BOT',game:id==='A'?'FFXI':'SWTOR',status:'Unknown',source:'Synthetic'}));
const ledger=[...bots.map(bot=>({botId:bot.id,bot:bot.name,correlationId:'shared',request:bot.id+'_ACTION',result:'pending',verification:'Unknown'})),
  {bot:'UNSCOPED',correlationId:'shared',request:'UNSCOPED_ACTION'},
  {botId:'A',bot:'A_BOT',correlationId:'other',request:'OTHER_EPISODE'}];
const data={bots,ledger};
function follow(){context.inspectBot('A');
 const buttons=get('bot-inspector').children.flatMap(row=>row.children).filter(n=>n.textContent==='View example episode in ledger');
 assert.equal(buttons.length,2);buttons[0].listeners.click();}
(async()=>{
 await refresh(data);follow();
 assert.match(get('ledger').textContent,/A_ACTION/);
 assert.doesNotMatch(get('ledger').textContent,/B_ACTION|UNSCOPED_ACTION|OTHER_EPISODE/);
 assert.match(get('ledger-filter').textContent,/bot.*A/i);
 assert.match(get('ledger-count').textContent,/Showing 1 of 4.*bot scope applied/);
 context.inspectBot('B');assert.match(get('ledger-filter').textContent,/bot.*A/i);
 await refresh({...data,bots:[...bots,{...bots[0],game:'SWTOR'}]});
 assert.match(get('ledger').textContent,/ambiguous|unknown/i);assert.doesNotMatch(get('ledger').textContent,/A_ACTION|B_ACTION/);
 assert.match(get('ledger-count').textContent,/count unknown/);
 await refresh(data);assert.match(get('ledger').textContent,/A_ACTION/);assert.doesNotMatch(get('ledger').textContent,/B_ACTION/);
 // Explicit manual search is intentionally across loaded bot records.
 get('correlation').value='shared';get('trace-search').listeners.submit({preventDefault(){}});
 assert.match(get('ledger').textContent,/A_ACTION.*B_ACTION.*UNSCOPED_ACTION/);
 assert.doesNotMatch(get('ledger-filter').textContent,/Pinned bot/);
 assert.match(get('ledger-count').textContent,/Showing 3 of 4/);
 follow();get('trace-clear').listeners.click();assert.match(get('ledger').textContent,/A_ACTION.*B_ACTION.*OTHER_EPISODE/);
 follow();context.resetPanelSession();await refresh(data);
 assert.match(get('ledger').textContent,/A_ACTION.*B_ACTION.*OTHER_EPISODE/);
 assert.equal(get('correlation').value,'');
 await refresh({...data,ledger:[]});assert.match(get('ledger-count').textContent,/Showing 0 of 0/);
 for(const partial of [undefined,null,{},[null,[],false]]){
   await refresh({...data,ledger:partial});context.inspectBot('A');
   assert.match(get('ledger').textContent,/coverage.*Unknown/i);
   assert.match(get('ledger-count').textContent,/Showing 0 of Unknown total/);
   assert.match(get('bot-inspector').textContent,/coverage.*Unknown/i);
   assert.doesNotMatch(get('ledger').textContent,/A_ACTION|B_ACTION|undefined|\[object Object\]/);
 }
 await refresh({...data,ledger:[null,ledger[0],{botId:'A',bot:{},request:{},result:{},verification:{},correlationId:'   '}]});
 context.inspectBot('A');
 assert.match(get('bot-inspector').textContent,/coverage.*Unknown.*A_ACTION/i);
 assert.doesNotMatch(get('bot-inspector').textContent,/undefined|\[object Object\]/);
 const links=get('bot-inspector').children.flatMap(row=>row.children).filter(n=>n.textContent==='View example episode in ledger');
 assert.equal(links.length,1,'Blank correlation must not offer an evidence link');
 links[0].listeners.click();assert.match(get('ledger').textContent,/coverage.*Unknown.*A_ACTION/i);
 assert.match(get('ledger-count').textContent,/Showing 1 of Unknown total.*bot scope applied/);
 console.log('PASS: inspector ledger identity/correlation scoping, ambiguity, refresh, explicit broad search and session reset. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
