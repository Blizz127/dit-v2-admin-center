const assert=require('node:assert/strict');
const {get,refresh,context}=require('./overview_snapshot_harness.cjs');
const bot={id:'A',name:'Synthetic actor',game:'FFXI',status:'Unknown',source:'Synthetic'};
(async()=>{
  await refresh({bots:[bot]});context.inspectBot('A');
  for(const bots of [null,undefined,{},[null,[],false]]){
    await refresh({bots});
    assert.match(get('bot-count').textContent,/Showing 0 of Unknown/);
    assert.doesNotMatch(get('bot-inspector').textContent,/Synthetic actor/);
    assert.match(get('bot-coverage').textContent,/Unknown/);
  }
  await refresh({bots:[null,bot]});
  assert.match(get('bot-count').textContent,/Showing 1 of Unknown/);
  assert.match(get('bot-inspector').textContent,/Synthetic actor/);
  await refresh({bots:[bot,{id:'B',game:'FFXI',name:{},status:true}]});
  assert.match(get('bot-coverage').textContent,/2 with unknown status/);
  assert.doesNotMatch(get('bots').textContent,/\[object Object\]|undefined/);
  get('bot-search').value='actor';get('bot-search').listeners.input();
  assert.match(get('bot-count').textContent,/Showing 1 of 2/);
  get('bot-search').value='';await refresh({bots:[]});
  assert.match(get('bot-count').textContent,/Showing 0 of 0/);
  for(const id of [undefined,null,42,' ']){
    await refresh({bots:[{id}]});
    const buttons=get('bots').children.flatMap(row=>row.children).filter(n=>n.textContent.startsWith('Inspect'));
    assert.equal(buttons.length,1);assert.equal(buttons[0].disabled,true);
    assert.doesNotMatch(get('bots').textContent,/undefined|\[object Object\]/);
  }
  await refresh({bots:[bot]});assert.match(get('bot-count').textContent,/Showing 1 of 1/);
  console.log('PASS: partial roster collections, malformed labels/status, search and recovery preserve the workspace. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
