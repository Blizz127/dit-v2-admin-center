// Fabricated input adapter + real app. Never label this a browser execution.
const assert=require('node:assert/strict'),vm=require('node:vm');
const {verifyDraftReview}=require('../tools/verify_draft_review.cjs');
const {get,refresh,context,requestCount}=require('./overview_snapshot_harness.cjs');
const ids=['bot-draft-goals','bot-draft-personality','bot-draft-preview','bot-draft-cancel'];
for(const id of ids)get(id).focus=()=>{context.document.activeElement=get(id);};
const evaluate=async source=>vm.runInContext(source,context);
const waitFor=async source=>assert.equal(await evaluate(source),true,source);
async function prepare(personalitySummary){
 await refresh({bots:[{id:'offline-inspector-bot',name:'Synthetic bot',game:'FFXI',personalitySummary}],
 botDetails:[{botId:'offline-inspector-bot',goals:[{text:'Fixture goal'}]}]});
 context.inspectBot('offline-inspector-bot');
}
function adapter(fault){return {evaluate,waitFor,
 command:async(method,params)=>{
   assert.equal(method,'Input.insertText');
   if(fault==='typing')return;
   const field=context.document.activeElement;field.value+=params.text;field.listeners.input();
 },
 press:async(key,shift)=>{
   const active=context.document.activeElement;
   if(key==='Tab'){
     if(fault==='focus')return;
     get(ids[ids.indexOf(active.id)+(shift?-1:1)]).focus();
   }else{
     assert.ok(key==='Enter' || key===' ');
     if(active.id==='bot-draft-preview') {
       get('bot-draft-form').listeners.submit({preventDefault(){}});
       if(fault==='validation-focus' && !get('bot-draft-goals').value)active.focus();
     } else if(fault!=='discard' && !(fault==='space' && key===' '))active.listeners.click();
   }
 }
};}
(async()=>{
 await prepare();const before=requestCount();
 const result=await verifyDraftReview(adapter());
 assert.equal(result.unknownBaseline,'personality');assert.equal(result.discardCleared,true);
 assert.equal(result.emptySubmissionFocus,'goals');assert.equal(result.discardActivation,'Space');
 assert.equal(requestCount(),before,'Draft input/review/discard makes no request');
 for(const fault of ['typing','focus','discard','space','validation-focus']){
   await prepare();await assert.rejects(verifyDraftReview(adapter(fault)));
 }
 await prepare('Known personality in wrong fixture');
 await assert.rejects(verifyDraftReview(adapter()),/Unknown/);
 console.log('PASS: draft native-helper orchestration and typing/focus/discard/baseline refusals through simulated app. Native NOT RUN.');
})().catch(e=>{console.error(e);process.exitCode=1;});
