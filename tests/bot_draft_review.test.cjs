// Real app draft review with synthetic snapshots; no DOM engine or writes.
const assert=require('node:assert/strict');
const vm=require('node:vm');
const {get,refresh,context,requestCount}=require('./overview_snapshot_harness.cjs');
const bot={id:'one',name:'Shared name',game:'FFXI',personalitySummary:'Patient',source:'Synthetic roster',observedAt:'fixture-roster-time'};
const detail={botId:'one',goals:[{text:'Observe'},{text:'Report evidence'}],source:'Synthetic goal record',observedAt:'fixture-goal-time'};
const submit=()=>get('bot-draft-form').listeners.submit({preventDefault(){}});
const goalReview=()=>get('bot-draft-result').children[1];
const personalityReview=()=>get('bot-draft-result').children[2];
async function load(botDetails=[detail],bots=[bot]) {
 await refresh({bots,botDetails});context.inspectBot('one');
 get('bot-draft-goals').value='Observe\nReport evidence';get('bot-draft-personality').value='More patient';
}
(async()=>{
 await load();const before=requestCount();
 const original=vm.runInContext('JSON.stringify(currentSnapshot)',context);
 submit();
 assert.match(goalReview().textContent,/Matches loaded text/);
 assert.match(goalReview().textContent,/Current loaded text.*Observe\nReport evidence.*Proposed local text.*Observe\nReport evidence/s);
 assert.match(goalReview().textContent,/Synthetic goal record.*fixture-goal-time/);
 assert.match(personalityReview().textContent,/Proposed text differs.*Current loaded text.*Patient.*Proposed local text.*More patient/);
 assert.match(personalityReview().textContent,/Synthetic roster.*fixture-roster-time/);
 assert.equal(goalReview().attributes['aria-label'],'Proposed goals review');
 assert.equal(goalReview().children[2].children.length,2);
 assert.equal(requestCount(),before);
 assert.equal(vm.runInContext('JSON.stringify(currentSnapshot)',context),original);
 get('bot-draft-goals').value='';submit();
 assert.match(goalReview().textContent,/No change proposed/);
 assert.match(goalReview().textContent,/current value is not cleared/);
 for (const botDetails of [null,[],[detail,detail],[{...detail,goals:null}],
   [{...detail,goals:[{text:'PREFIX_MUST_NOT_BECOME_BASELINE'},null]}],
   [{...detail,goals:[{text:'x'.repeat(4001)}]}],
   [{...detail,goals:Array.from({length:21},()=>({text:'Observe'}))}]]) {
   await load(botDetails);submit();
   assert.match(goalReview().textContent,/Comparison unavailable: current value Unknown/);
   assert.doesNotMatch(goalReview().textContent,/Matches loaded text|PREFIX_MUST_NOT_BECOME_BASELINE/);
 }
 await load([{...detail,goals:[]}]);submit();
 assert.match(goalReview().textContent,/Proposed text differs.*Empty supplied goal list/);
 await load([detail], [{...bot,personalitySummary:null},{id:'two',name:bot.name,game:'SWTOR',personalitySummary:'WRONG_BOT'}]);submit();
 assert.match(personalityReview().textContent,/current value Unknown/);
 assert.doesNotMatch(personalityReview().textContent,/WRONG_BOT/);
 await load([{...detail,goals:[{text:'<script>not-executable</script>'}]}]);
 get('bot-draft-goals').value='<script>not-executable</script>';get('bot-draft-personality').value='Patient';submit();
 assert.match(goalReview().textContent,/Matches loaded text/);
 assert.match(personalityReview().textContent,/Matches loaded text/);
 assert.equal(goalReview().children[2].children[0].children[1].children.length,0,'Current text never becomes parsed markup');
 assert.equal(goalReview().children[2].children[1].children[1].children.length,0,'Proposed text never becomes parsed markup');
 get('bot-draft-cancel').listeners.click();assert.equal(get('bot-draft-result').textContent,'');
 console.log('PASS: current/proposed review, exact text, Unknown/empty distinctions, scoped provenance, bounds and text-only rendering. Native NOT RUN.');
})().catch(e=>{console.error(e);process.exitCode=1;});
