// Actual app handlers + template-backed minimal DOM, not trusted native key input.
const assert = require('node:assert/strict');
const {get, refresh, requestCount} = require('./overview_snapshot_harness.cjs');
(async () => {
  await refresh({bots:[{id:'fixture',name:'Synthetic bot',game:'FFXI'}],learning:[],modelCalls:[]});
  const focused=[],scrolled=[];
  const sections=['overview','roster','ffxi','learning','evidence','operations','models','notes'];
  for (const id of [...sections.map(s=>'view-'+s),'bots','learning','model-calls']) {
    get(id).focus = options => {assert.equal(options.preventScroll,true);focused.push(id);};
    get(id).scrollIntoView = () => scrolled.push(id);
  }
  const before=requestCount();
  get('bot-search').value='retain my filter';
  for (const section of sections) {
    let cancelled=false;
    get('nav-'+section).listeners.click({button:0,preventDefault(){cancelled=true;}});
    assert.equal(cancelled,false,'Keep native anchor fragment/history handling');
    assert.equal(focused.at(-1),'view-'+section);
    assert.equal(get('view-'+section).attributes.tabindex,'-1');
  }
  assert.deepEqual(scrolled,[],'Native sidebar anchors own their scrolling');
  for (const event of [{button:1},{ctrlKey:true},{metaKey:true},{shiftKey:true},{altKey:true},{defaultPrevented:true}]) {
    get('nav-roster').listeners.click(event);
  }
  assert.equal(focused.length,sections.length,'Modified/cancelled clicks must not steal focus');
  for (const row of get('data-coverage').children) {
    row.children.find(n=>n.textContent.startsWith('Review ')).listeners.click();
  }
  assert.deepEqual(focused.slice(-3),['bots','learning','model-calls']);
  assert.deepEqual(scrolled,['bots','learning','model-calls']);
  assert.equal(get('bot-search').value,'retain my filter');
  assert.equal(requestCount(),before,'Navigation uses loaded data, without requests');
  const count=focused.length;
  get('workspace').hidden=true;
  get('nav-roster').listeners.click({button:0});
  assert.equal(focused.length,count,'Do not focus an unavailable workspace');
  console.log('PASS: sidebar/coverage focus destinations, native anchor preservation, modified-click guards and filter retention. Native keyboard/layout NOT RUN.');
})().catch(error=>{console.error(error);process.exitCode=1;});
