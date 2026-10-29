// Selected navigation destination, not a scroll-spy or native history test.
const assert=require('node:assert/strict');
const {get,refresh,context,globalEvents,requestCount}=require('./overview_snapshot_harness.cjs');
const sections=['overview','roster','ffxi','learning','evidence','operations','models','notes'];
const selected=()=>sections.filter(s=>get('nav-'+s).attributes['aria-current']==='location');
(async()=>{
  await refresh({bots:[{id:'one',name:'Synthetic bot',game:'FFXI'}]});
  assert.deepEqual(selected(),['overview']);
  const before=requestCount();
  for(const section of sections){
    get('nav-'+section).listeners.click({button:0});assert.deepEqual(selected(),[section]);
  }
  get('nav-roster').listeners.click({ctrlKey:true});assert.deepEqual(selected(),['notes']);
  get('ffxi-bots').listeners.click();assert.deepEqual(selected(),['roster']);
  get('ffxi-learning').listeners.click();assert.deepEqual(selected(),['learning']);
  get('ffxi-evidence').listeners.click();assert.deepEqual(selected(),['evidence']);
  context.location.hash='#model-calls';globalEvents.hashchange();assert.deepEqual(selected(),['models']);
  context.location.hash='#main-content';globalEvents.hashchange();assert.deepEqual(selected(),[]);
  context.location.hash='#view-ffxi';globalEvents.hashchange();assert.deepEqual(selected(),['ffxi']);
  assert.equal(requestCount(),before,'Location cues make no requests');
  await refresh({bots:[]});assert.deepEqual(selected(),['ffxi'],'Refresh preserves selected destination');
  context.resetPanelSession();assert.deepEqual(selected(),[]);
  get('workspace').hidden=true;
  context.location.hash='#view-roster';globalEvents.hashchange();assert.deepEqual(selected(),[]);
  await refresh({bots:[]});assert.deepEqual(selected(),['roster'],'New session respects a valid fragment');
  console.log('PASS: selected sidebar destination from actual template ancestry, fragments, refresh and reset; no new reads. Native history/rendering NOT RUN.');
})().catch(error=>{console.error(error);process.exitCode=1;});
