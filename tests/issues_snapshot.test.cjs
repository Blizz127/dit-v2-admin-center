// In-memory overview fixtures only; no issue store, hub or coordinator records.
const assert=require('node:assert/strict');
const {get,refresh,context}=require('./overview_snapshot_harness.cjs');
const data={bots:[{id:'A',name:'Synthetic bot',game:'FFXI',status:'Unknown'}],
 learning:[{id:'L',game:'FFXI',topic:'Synthetic need',status:'unverified'}]};
const issue={botId:'A',learningId:'L',title:'LINKED_ISSUE',detail:'Synthetic description',status:'Open',scope:'Bots'};
(async()=>{
 await refresh({...data,issues:[issue]});context.inspectBot('A');context.inspectLearning('L');
 assert.match(get('bot-inspector').textContent,/LINKED_ISSUE/);assert.match(get('learning-inspector').textContent,/LINKED_ISSUE/);
 for(const issues of [undefined,null,{},[null,[],false]]){
   await refresh({...data,issues});
   for(const id of ['issues','issue-coverage','bot-inspector','learning-inspector']){
     assert.match(get(id).textContent,/coverage.*Unknown/i);
     assert.doesNotMatch(get(id).textContent,/LINKED_ISSUE|undefined|\[object Object\]/);
   }
   assert.match(get('issue-count').textContent,/of Unknown/);
 }
 await refresh({...data,issues:[null,issue,{title:{},detail:[],status:false,scope:{},suggestedFix:{},bridgeObservation:'true',ownerAttention:'false'}]});
 for(const id of ['issues','bot-inspector','learning-inspector']){
   assert.match(get(id).textContent,/LINKED_ISSUE/);assert.doesNotMatch(get(id).textContent,/undefined|\[object Object\]/);
 }
 const buttons=get('issues').children.flatMap(n=>n.children).map(n=>n.textContent);
 assert.ok(!buttons.includes('View current bridge observation'));
 assert.ok(!buttons.includes('View owner decision summary'));
 get('issue-search').value='LINKED';get('issue-search').listeners.input();
 assert.match(get('issue-count').textContent,/Showing 1 of Unknown/);
 get('issue-reset').listeners.click();
 await refresh({...data,issues:[]});
 assert.match(get('issue-count').textContent,/Showing 0 of 0/);
 assert.doesNotMatch(get('bot-inspector').textContent,/LINKED_ISSUE/);
 await refresh({...data,issues:[issue]});
 assert.match(get('issue-count').textContent,/Showing 1 of 1/);
 assert.match(get('learning-inspector').textContent,/LINKED_ISSUE/);
 console.log('PASS: missing/mixed linked issues, Unknown count, typed text/navigation flags, search and recovery. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
