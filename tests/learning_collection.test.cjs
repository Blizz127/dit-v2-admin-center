// Partial root learning collection must not close the actual workspace.
const assert=require('node:assert/strict');
const {get,refresh,context}=require('./overview_snapshot_harness.cjs');
const need={id:'need-A',game:'FFXI',topic:'Synthetic party behavior',status:'verified',source:'Synthetic'};
(async()=>{
  await refresh({learning:[need]});context.inspectLearning(need.id);
  for(const learning of [null,undefined,{},[null,[],false]]){
    await refresh({learning});
    assert.match(get('learning-count').textContent,/Showing 0 of Unknown/);
    assert.doesNotMatch(get('learning-inspector').textContent,/Synthetic party behavior/);
    assert.match(get('learning-coverage').textContent,/Unknown/);
  }
  await refresh({learning:[null,need]});
  assert.match(get('learning-count').textContent,/Showing 1 of Unknown/);
  assert.match(get('learning').textContent,/Synthetic party behavior/);
  assert.match(get('learning-inspector').textContent,/Synthetic party behavior/);
  assert.match(get('learning-coverage').textContent,/1 usable loaded.*1 marked as verified tasks/);
  get('learning-game').value='SWTOR';get('learning-game').listeners.change();
  assert.match(get('learning-count').textContent,/Showing 0 of Unknown/);
  assert.match(get('learning').textContent,/coverage.*Unknown/i);
  await refresh({learning:[]});assert.match(get('learning-count').textContent,/Showing 0 of 0/);
  get('learning-game').value='';await refresh({learning:[need]});
  assert.match(get('learning-count').textContent,/Showing 1 of 1/);
  console.log('PASS: missing/mixed learning collections retain workspace, scoped records and Unknown totals; recovery preserves selection. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
