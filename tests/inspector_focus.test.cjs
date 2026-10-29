const assert=require('node:assert/strict');
const {get,refresh,requestCount}=require('./overview_snapshot_harness.cjs');
const bots=[{id:'one',name:'Same name',game:'FFXI'},
  {id:'two',name:'Same name',game:'SWTOR'},
  {id:'duplicate',name:'Ambiguous',game:'FFXI'},{id:'duplicate',name:'Ambiguous',game:'SWTOR'}];
const botDetails=[{botId:'one',goals:[{text:'ONLY_FIRST_ID'}],memories:[]},{botId:'two',goals:[{text:'OTHER_ID_GOAL'}],memories:[]}];
const learning=[{id:'need',game:'FFXI',topic:'Fixture need',status:'verified'}];
const inspect=id=>get(id).children.flatMap(row=>row.children).filter(n=>n.textContent.startsWith('Inspect'));
(async()=>{
  const focused=[];
  for(const id of ['bots','bot-inspector','learning-inspector'])get(id).focus=()=>focused.push(id);
  await refresh({bots,learning,botDetails});
  assert.deepEqual(focused,[],'Refreshing must not steal focus');
  get('bot-game').value='FFXI';get('bot-game').listeners.change();
  get('bot-search').value='same';get('bot-search').listeners.input();
  const before=requestCount();
  inspect('bots')[0].listeners.click();
  assert.equal(focused.at(-1),'bot-inspector');
  assert.match(get('bot-inspector').textContent,/ONLY_FIRST_ID/);
  assert.doesNotMatch(get('bot-inspector').textContent,/OTHER_ID_GOAL/);
  get('back-to-roster').listeners.click();
  assert.equal(focused.at(-1),'bots');
  assert.equal(get('bot-game').value,'FFXI');assert.equal(get('bot-search').value,'same');
  assert.match(get('bot-count').textContent,/Showing 1 of 4/);
  assert.match(get('bot-inspector').textContent,/ONLY_FIRST_ID/,'Return keeps selection');
  inspect('learning')[0].listeners.click();
  assert.equal(focused.at(-1),'learning-inspector');
  assert.match(get('learning-inspector').textContent,/Policy verification: Unknown/);
  assert.equal(requestCount(),before,'Inspect/return are local only');
  const count=focused.length;
  await refresh({bots,learning,botDetails});
  assert.equal(focused.length,count,'Refreshing a selected inspector must not move focus');
  get('bot-reset').listeners.click();
  assert.ok(inspect('bots').filter(b=>b.textContent.includes('unavailable')).every(b=>b.disabled));
  console.log('PASS: manual inspector focus, same-name ID isolation, filtered roster return, disabled ambiguous rows and refresh focus preservation. Native keys NOT RUN.');
})().catch(error=>{console.error(error);process.exitCode=1;});
