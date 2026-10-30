// Actual application, loaded mock data and minimal DOM. No browser or write endpoint.
const assert=require('node:assert/strict');
const vm=require('node:vm');
const {get,refresh,context,requestCount}=require('./overview_snapshot_harness.cjs');
const bots=[{id:'one',name:'Same name',game:'FFXI',personalitySummary:'Existing summary'},
 {id:'two',name:'Same name',game:'SWTOR'}, {id:'repeated',name:'Duplicate',game:'FFXI'},
 {id:'repeated',name:'Duplicate',game:'SWTOR'}];
const submit=()=>get('bot-draft-form').listeners.submit({preventDefault(){}});
const goals=get('bot-draft-goals'),personality=get('bot-draft-personality');
(async()=>{
 await refresh({bots});
 assert.equal(get('bot-draft-fields').disabled,true);
 context.inspectBot('one');
 assert.equal(get('bot-draft-fields').disabled,false);
 const before=requestCount();
 submit();assert.match(get('bot-draft-status').textContent,/Enter at least one/);
 goals.value='  Explore safely\nReturn with evidence  ';personality.value='<img src=x onerror=bad()> & patient';submit();
 assert.match(get('bot-draft-result').textContent,/Local draft · one · FFXI.*Explore safely/);
 assert.match(get('bot-draft-result').textContent,/<img src=x onerror=bad\(\)> & patient/,'Draft is text, never HTML');
 assert.match(get('bot-draft-status').textContent,/Not saved, applied, verified or sent/);
 assert.equal(vm.runInContext('currentSnapshot.bots[0].personalitySummary',context),'Existing summary');
 goals.value='Changed after preview';goals.listeners.input();
 assert.equal(get('bot-draft-result').textContent,'');
 assert.match(get('bot-draft-status').textContent,/Preview again/);
 for(const [g,p] of [['x'.repeat(1001),'ok'],['ok','x'.repeat(501)],['ok\u0000bad','ok']]){
   goals.value=g;personality.value=p;submit();
   assert.equal(get('bot-draft-result').textContent,'','Invalid input clears previous preview');
   assert.match(get('bot-draft-status').textContent,/Draft not previewed/);
 }
 goals.value='x'.repeat(1000);personality.value='x'.repeat(500);submit();
 assert.match(get('bot-draft-status').textContent,/Preview ready/);
 get('bot-draft-cancel').listeners.click();assert.equal(goals.value,'');assert.equal(personality.value,'');
 assert.equal(get('bot-draft-result').textContent,'');
 goals.value='FFXI only';submit();context.inspectBot('two');
 assert.equal(goals.value,'');assert.equal(get('bot-draft-result').textContent,'');
 personality.value='SWTOR draft';submit();assert.match(get('bot-draft-result').textContent,/two · SWTOR.*No change proposed/);
 assert.doesNotMatch(get('bot-draft-result').textContent,/FFXI only/);
 context.inspectBot('repeated');goals.value='must not preview';submit();
 assert.equal(get('bot-draft-fields').disabled,true);assert.equal(goals.value,'');
 context.inspectBot('one');goals.value='unsent';submit();
 assert.equal(requestCount(),before,'Preview/validation/cancel/select emit no request');
 const originalFetch=context.fetch;
 let release,refreshCalls=0;
 context.fetch=async()=>{refreshCalls++;return new Promise(resolve=>{release=resolve;});};
 try {
   const pending=get('refresh').listeners.click();
   assert.equal(goals.value,'','Starting refresh clears unsent text immediately');
   assert.equal(get('bot-draft-result').textContent,'');
   assert.equal(get('bot-draft-fields').disabled,true);
   goals.value='Attempt during loading';submit();
   assert.equal(goals.value,'');assert.equal(get('bot-draft-result').textContent,'');
   release({ok:false,status:503});await pending;
   assert.equal(get('bot-draft-result').textContent,'','Failed refresh must not revive a preview');
   assert.equal(get('bot-draft-fields').disabled,true);
   assert.equal(refreshCalls,1);
 } finally {context.fetch=originalFetch;}
 await refresh({bots});assert.equal(goals.value,'');assert.equal(get('bot-draft-result').textContent,'');
 assert.equal(get('bot-draft-fields').disabled,false,'Successful mock refresh allows a new draft');
 goals.value='old draft';submit();get('clear-bot').listeners.click();
 assert.equal(get('bot-draft-fields').disabled,true);assert.equal(goals.value,'');
 context.inspectBot('one');vm.runInContext("loadedSource='hub'",context);goals.value='not allowed';submit();
 assert.equal(get('bot-draft-fields').disabled,true);assert.equal(goals.value,'');
 await refresh({bots});context.inspectBot('one');goals.value='private local draft';submit();
 context.resetPanelSession();assert.equal(goals.value,'');assert.equal(get('bot-draft-result').textContent,'');
 assert.equal(get('bot-draft-fields').disabled,true);
 console.log('PASS: local draft bounds, text-only preview, exact-ID isolation, cancel/refresh/session/source reset; no writes. Native NOT RUN.');
})().catch(e=>{console.error(e);process.exitCode=1;});
