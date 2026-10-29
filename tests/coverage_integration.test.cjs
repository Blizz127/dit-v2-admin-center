// Projection + real in-memory handler + shipped UI; simulated DOM, no listener/browser.
const assert=require('node:assert/strict');
const vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const {get,context}=require('./overview_snapshot_harness.cjs');
let scenario='coverage-loaded',requests=0;
context.fetch=async(path,options)=>{
  assert.equal(options.method||'GET','GET');requests++;
  const result=JSON.parse(execFileSync('python3',['tests/inspector_runtime_fixture.py'],{
    input:JSON.stringify({path,token:options.headers.Authorization.slice(7),scenario}),encoding:'utf8',timeout:5000
  }));
  assert.equal(result.headers['Cache-Control'],'no-store');
  assert.equal(Number(result.headers['Content-Length']),Buffer.byteLength(result.body));
  assert.doesNotMatch(result.body,/OMIT_RAW_ANSWER_AND_PLAYER_DATA|fixture-token/);
  for(const key of ['traceCalls','interactionCalls','healthCalls','bridgeRunnerCalls'])assert.equal(result[key],0);
  return {ok:result.status===200,status:result.status,json:async()=>JSON.parse(result.body)};
};
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  vm.runInContext("token='fixture-token'",context);
  await get('refresh').listeners.click();await flush();
  assert.equal(get('workspace').hidden,false);
  assert.match(get('data-coverage').textContent,/Bot roster · Loaded collection.*Learning needs · Loaded collection.*Rows with unknown numeric fields: 1/);
  const before=requests,visited=[];
  get('learning').scrollIntoView=()=>visited.push('learning');
  get('data-coverage').children[1].children.find(n=>n.textContent==='Review learning needs').listeners.click();
  get('learning').children[0].children.find(n=>n.textContent.startsWith('Inspect ')).listeners.click();
  assert.deepEqual(visited,['learning']);
  assert.match(get('learning-inspector').textContent,/Model answer reported: Yes.*Policy verification: Unknown|Policy verification: Unknown.*Model answer reported: Yes/);
  assert.equal((get('learning-evidence').textContent.match(/Evidence state: Unknown/g)||[]).length,5);
  context.inspectBot('coverage-bot');assert.match(get('bot-inspector').textContent,/Synthetic coverage goal/);
  assert.equal(requests,before,'Overview navigation and inspection must remain local');
  scenario='coverage-unavailable';await get('refresh').listeners.click();await flush();
  assert.equal(get('workspace').hidden,false);
  assert.equal((get('data-coverage').textContent.match(/Unavailable collection/g)||[]).length,3);
  assert.doesNotMatch(get('bot-inspector').textContent,/Synthetic coverage goal/);
  scenario='coverage-partial';await get('refresh').listeners.click();await flush();
  assert.equal((get('data-coverage').textContent.match(/Partial collection/g)||[]).length,3);
  assert.match(get('bot-inspector').textContent,/Synthetic coverage goal/);
  assert.match(get('learning-inspector').textContent,/Model answer reported: Yes/);
  vm.runInContext("token='invalid-fixture-token'",context);
  await get('refresh').listeners.click();await flush();
  assert.equal(get('workspace').hidden,true);assert.equal(get('data-coverage').textContent,'');
  assert.doesNotMatch(get('bot-inspector').textContent,/Synthetic coverage goal/);
  console.log('PASS: projected coverage through real memory-only handler into overview/inspectors, partial recovery and auth reset. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
