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
 context.inspectBot('B');assert.match(get('ledger-filter').textContent,/bot.*A/i);
 await refresh({...data,bots:[...bots,{...bots[0],game:'SWTOR'}]});
 assert.match(get('ledger').textContent,/ambiguous|unknown/i);assert.doesNotMatch(get('ledger').textContent,/A_ACTION|B_ACTION/);
 await refresh(data);assert.match(get('ledger').textContent,/A_ACTION/);assert.doesNotMatch(get('ledger').textContent,/B_ACTION/);
 // Explicit manual search is intentionally across loaded bot records.
 get('correlation').value='shared';get('trace-search').listeners.submit({preventDefault(){}});
 assert.match(get('ledger').textContent,/A_ACTION.*B_ACTION.*UNSCOPED_ACTION/);
 assert.doesNotMatch(get('ledger-filter').textContent,/Pinned bot/);
 follow();get('trace-clear').listeners.click();assert.match(get('ledger').textContent,/A_ACTION.*B_ACTION.*OTHER_EPISODE/);
 follow();context.resetPanelSession();await refresh(data);
 assert.match(get('ledger').textContent,/A_ACTION.*B_ACTION.*OTHER_EPISODE/);
 assert.equal(get('correlation').value,'');
 console.log('PASS: inspector ledger identity/correlation scoping, ambiguity, refresh, explicit broad search and session reset. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
