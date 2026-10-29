// Gap inspection uses snapshot row positions, never inferred native entity identity.
const assert=require('node:assert/strict');
const {get,refresh,context,requestCount}=require('./overview_snapshot_harness.cjs');
const bots=[{id:'valid',name:'Selected unique bot',game:'FFXI'},
  {id:'repeated',name:'Same name',game:'FFXI',source:'FIRST_SOURCE'},
  {id:'repeated',name:'Same name',game:'SWTOR',source:'SECOND_SOURCE'},
  {name:'Same name',game:'FFXI',source:'NO_ID_SOURCE'},null];
const links=()=>get('roster-gaps').children.flatMap(row=>row.children).filter(n=>n.textContent.startsWith('Review gap'));
const show=()=>get('roster-gap-detail').children.find(n=>n.textContent==='Show matching roster row');
(async()=>{
  await refresh({bots});context.inspectBot('valid');
  assert.equal(links().length,3);
  assert.match(get('roster-gaps').textContent,/Snapshot row 5 · Unusable record/);
  const before=requestCount();links()[0].listeners.click();
  assert.match(get('roster-gap-detail').textContent,/Snapshot row 2.*Repeated loaded ID: 2 rows.*FIRST_SOURCE/);
  assert.doesNotMatch(get('roster-gap-detail').children[0].textContent,/SECOND_SOURCE|NO_ID_SOURCE/);
  const oldShow=show(),oldReview=links()[0];oldShow.listeners.click();
  assert.match(get('bot-count').textContent,/Showing 1 of Unknown.*Pinned snapshot row: 2/);
  assert.match(get('bots').textContent,/FIRST_SOURCE/);assert.doesNotMatch(get('bots').textContent,/SECOND_SOURCE|NO_ID_SOURCE/);
  const inspect=get('bots').children.flatMap(row=>row.children).find(n=>n.textContent.startsWith('Inspect'));
  assert.equal(inspect.disabled,true);
  assert.match(get('bot-inspector').textContent,/Selected unique bot/,'Gap review must not select an ambiguous bot');
  links()[2].listeners.click();show().listeners.click();
  assert.match(get('bot-count').textContent,/Pinned snapshot row: 4/);
  assert.match(get('bots').textContent,/NO_ID_SOURCE/);
  get('bot-reset').listeners.click();assert.doesNotMatch(get('bot-count').textContent,/Pinned snapshot/);
  assert.equal(requestCount(),before,'Detail review/navigation must not fetch');
  await refresh({bots:[bots[3],bots[0]]});
  assert.match(get('roster-gap-detail').textContent,/Select a loaded roster gap/);
  oldShow.listeners.click();oldReview.listeners.click();
  assert.doesNotMatch(get('bot-count').textContent,/Pinned snapshot/);
  assert.doesNotMatch(get('roster-gap-detail').textContent,/FIRST_SOURCE/);
  links()[0].listeners.click();show().listeners.click();
  get('bot-search').value='no-match';get('bot-search').listeners.input();
  assert.doesNotMatch(get('bot-count').textContent,/Pinned snapshot/);
  await refresh({bots:null});assert.match(get('roster-gaps').textContent,/Roster gaps unknown/);
  context.resetPanelSession();assert.equal(get('roster-gaps').textContent,'');
  assert.match(get('roster-gap-detail').textContent,/Select a loaded roster gap/);
  console.log('PASS: per-record gap details, exact row navigation, ambiguous identity isolation, stale link rejection and reset. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
