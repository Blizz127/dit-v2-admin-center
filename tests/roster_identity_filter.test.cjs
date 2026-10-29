const assert=require('node:assert/strict');
const {get,refresh,context,requestCount}=require('./overview_snapshot_harness.cjs');
const bots=[{id:'unique',name:'Unique actor',game:'FFXI'},
  {id:'shared',name:'Repeated FFXI',game:'FFXI'},
  {id:'shared',name:'Repeated SWTOR',game:'SWTOR'},
  {name:'Missing ID',game:'FFXI'}];
const filter=value=>{get('bot-identity').value=value;get('bot-identity').listeners.change();};
(async()=>{
  await refresh({bots});const before=requestCount();
  filter('unavailable');assert.match(get('bot-count').textContent,/Showing 3 of 4/);
  assert.doesNotMatch(get('bots').textContent,/Unique actor/);
  get('bot-game').value='FFXI';get('bot-game').listeners.change();
  assert.match(get('bot-count').textContent,/Showing 2 of 4/);
  for(const row of get('bots').children){
    const inspect=row.children.find(n=>n.textContent.startsWith('Inspect'));
    assert.equal(inspect.disabled,true);
  }
  filter('unique');assert.match(get('bot-count').textContent,/Showing 1 of 4/);
  assert.match(get('bots').textContent,/Unique actor/);assert.doesNotMatch(get('bots').textContent,/Repeated/);
  assert.equal(requestCount(),before);
  await refresh({bots});assert.match(get('bot-count').textContent,/Showing 1 of 4/);
  filter('unavailable');await refresh({bots:[bots[0],bots[1]]});
  assert.match(get('bot-count').textContent,/Showing 0 of 2/);
  get('bot-reset').listeners.click();assert.equal(get('bot-identity').value,'');
  assert.match(get('bot-count').textContent,/Showing 2 of 2/);
  filter('unavailable');get('ffxi-bots').listeners.click();
  assert.equal(get('bot-identity').value,'');assert.match(get('bot-count').textContent,/Showing 2 of 2/);
  filter('unavailable');context.resetPanelSession();assert.equal(get('bot-identity').value,'');
  console.log('PASS: roster identity triage retains full-snapshot uniqueness across game filters, refresh and reset. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
