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
 const need={id:'shared-need',game:'FFXI',topic:'FIRST_NEED',status:'verified',evidence:'Present',source:'Synthetic'};
 const learningData={learning:[need],issues:[{learningId:'shared-need',title:'SCOPED_LEARNING_ISSUE'}]};
 await refresh(learningData);context.inspectLearning('shared-need');
 assert.match(get('learning-inspector').textContent,/FIRST_NEED/);
 assert.doesNotMatch(get('learning-inspector').textContent,/undefined|\[object Object\]/);
 assert.match(get('learning-inspector').textContent,/Datasets: Unknown.*Policy verification: Unknown/);
 for(const game of ['FFXI','SWTOR']){
   await refresh({...learningData,learning:[need,{...need,game,topic:'SECOND_NEED'}]});
   assert.match(get('learning-inspector').textContent,/ambiguous/i);
   assert.match(get('learning-count').textContent,/ambiguous/i);
   assert.doesNotMatch(get('learning-inspector').textContent,/FIRST_NEED|SECOND_NEED|SCOPED_LEARNING_ISSUE/);
   get('learning-evidence-selected').listeners.click();
   assert.doesNotMatch(get('learning-evidence').textContent,/FIRST_NEED|SECOND_NEED|Assessment: Unknown/);
   get('learning-game').value='FFXI';get('learning-game').listeners.change();
   context.inspectLearning('shared-need');assert.match(get('learning-inspector').textContent,/ambiguous/i);
   for(const row of get('learning').children){
     for(const button of row.children.filter(c=>c.textContent.startsWith('Inspect '))) assert.equal(button.disabled,true);
   }
 }
 get('learning-game').value='';await refresh(learningData);
 assert.match(get('learning-inspector').textContent,/FIRST_NEED.*SCOPED_LEARNING_ISSUE/);
 assert.match(get('learning-evidence').textContent,/Assessment: Unknown/);
 await refresh({learning:[{...need,topic:{private:'OMIT_RAW'},phase:[],reason:false,source:{},datasets:{},policy:null}],issues:[]});
 assert.doesNotMatch(get('learning-inspector').textContent,/undefined|\[object Object\]|OMIT_RAW/);
 assert.match(get('learning-inspector').textContent,/Learning detail · FFXI · Unknown/);
 console.log('PASS: duplicate bot/learning IDs suppress scoped inspection across filters and games; recovery with unique IDs. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
