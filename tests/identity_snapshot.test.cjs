// Ambiguous fixture IDs must never select a first record or attach scoped evidence.
const assert = require('node:assert/strict');
const {get, refresh, context}=require('./overview_snapshot_harness.cjs');
const first={id:'shared',name:'FIRST_BOT',game:'FFXI',status:'Unknown',source:'Synthetic'};
const evidence={
  bots:[first],botDetails:[{botId:'shared',goals:[{text:'SCOPED_GOAL'}],memories:[]}],
  safetyRecords:[{botId:null,scope:'NETWORK_ONLY'},{botId:'shared',scope:'SCOPED_SAFETY'}],
  replyEvents:[{botId:'shared',wordingOrigin:'SCOPED_REPLY'}],
  assignmentHistory:[{botId:'shared',requested:'SCOPED_MODEL'}],
  issues:[{botId:'shared',title:'SCOPED_ISSUE',detail:'Synthetic',scope:'Bots'}]
};
(async()=>{
 await refresh(evidence);context.inspectBot('shared');assert.match(get('bot-inspector').textContent,/SCOPED_GOAL/);
 for(const game of ['FFXI','SWTOR']){
   await refresh({...evidence,bots:[first,{...first,name:'SECOND_BOT',game}]});
   assert.match(get('bot-inspector').textContent,/ambiguous/i);
   for(const id of ['bot-inspector','reply-source','assignment-history','safety-records'])
     assert.doesNotMatch(get(id).textContent,/FIRST_BOT|SECOND_BOT|SCOPED_/);
   assert.match(get('safety-records').textContent,/NETWORK_ONLY/);
   assert.match(get('bot-count').textContent,/ambiguous/i);
   for(const row of get('bots').children){
     for(const button of row.children.filter(c=>c.textContent.startsWith('Inspect '))) assert.equal(button.disabled,true);
   }
   get('issue-selected-bot').checked=true;get('issue-selected-bot').listeners.change();
   assert.doesNotMatch(get('issues').textContent,/SCOPED_ISSUE/);
   get('bot-game').value='FFXI';get('bot-game').listeners.change();
   context.inspectBot('shared');assert.match(get('bot-inspector').textContent,/ambiguous/i);
 }
 get('bot-game').value='';await refresh(evidence);
 assert.match(get('bot-inspector').textContent,/FIRST_BOT.*SCOPED_GOAL/);
 assert.match(get('reply-source').textContent,/SCOPED_REPLY/);
 console.log('PASS: duplicate bot IDs suppress scoped inspection across filters and games; recovery with a unique ID. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
