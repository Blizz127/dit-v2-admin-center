// Real overview refresh code, synthetic responses and a minimal DOM; no listener/browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const python = (...args) => execFileSync('python3', args, {encoding:'utf8',timeout:5000});
const template = JSON.parse(python('tests/inspector_runtime_fixture.py','--template'));
const snapshot = JSON.parse(python('-c','import json; from tools.build_inspector_playtest import snapshot; print(json.dumps(snapshot()))'));
class Element {
  constructor(spec={}) { this.attributes={...spec.attrs}; this.children=[];this.listeners={};this.text='';this.value=spec.value||'';this.hidden=Object.hasOwn(spec.attrs||{},'hidden'); }
  append(...items){this.children.push(...items);}
  replaceChildren(){this.children=[];this.text='';}
  set textContent(value){this.children=[];this.text=String(value);}
  get textContent(){return this.text+this.children.map(c=>c.textContent).join(' ');}
  addEventListener(name,fn){this.listeners[name]=fn;}
  setAttribute(key,value){this.attributes[key]=String(value);}
  get lastElementChild(){return this.children.at(-1);}
}
const elements=new Map(Object.entries(template).map(([id,spec])=>[id,new Element(spec)]));
const get=id=>{assert.ok(elements.has(id),'Missing template ID '+id);return elements.get(id);};
let data=snapshot;
const storage=new Map();
const context={document:{querySelector:s=>get(s.slice(1)),getElementById:get,createElement:()=>new Element()},
  sessionStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
  fetch:async(path, options)=>{
    assert.equal(options.method||'GET','GET');
    if(path==='/api/bridge-status')return {ok:true,json:async()=>({unit:'Unknown',source:'Synthetic'})};
    assert.equal(path,'/api/overview?source=mock');return {ok:true,json:async()=>data};
  }};
vm.createContext(context);vm.runInContext(fs.readFileSync('static/app.js','utf8'),context);
async function refresh(changes){
  data={...snapshot,...changes};
  vm.runInContext("token = 'synthetic-test-token'",context);
  await get('refresh').listeners.click();
  assert.equal(get('workspace').hidden,false,'Partial telemetry must not close the workspace');
  return get('model-calls').textContent;
}
(async()=>{
  for(const modelCalls of [undefined,null,{},'bad']) assert.match(await refresh({modelCalls}),/Unknown/);
  assert.match(await refresh({modelCalls:[]}),/No model call examples/);
  assert.match(await refresh({modelCalls:[null,[],false]}),/Unknown/);
  const text=await refresh({modelCalls:[null,{model:'Good example',purpose:'Synthetic',latencyMs:0,cost:0,quality:0},{}]});
  assert.match(text,/Good example.*Latency: 0 ms.*Cost: 0.*Quality: 0/);
  assert.match(text,/coverage.*Unknown/i);
  assert.doesNotMatch(text,/undefined|\[object Object\]/);
  for(const value of [NaN,Infinity,-Infinity,-1,true,'0',{}]) {
    const invalid=await refresh({modelCalls:[{model:'Invalid numbers',latencyMs:value,cost:value,quality:value}]});
    assert.match(invalid,/Latency: Unknown.*Cost: Unknown.*Quality: Unknown/);
  }
  const recovered=await refresh({modelCalls:[{model:'Recovered example',latencyMs:12,cost:0.01,quality:1}]});
  assert.match(recovered,/Recovered example/);assert.doesNotMatch(recovered,/Invalid numbers|coverage.*Unknown/i);
  for(const spendExample of [undefined,null,[],false,'bad',{}]) {
    await refresh({spendExample});
    assert.match(get('spend-example').textContent,/Settled: Unknown.*Open reservations: Unknown.*Budget: Unknown/);
    assert.doesNotMatch(get('spend-example').textContent,/undefined|\[object Object\]/);
  }
  for(const value of [NaN,Infinity,-Infinity,-1,true,'0',{}]) {
    await refresh({spendExample:{settledUsd:value,reservedOpenUsd:value,budgetUsd:value}});
    assert.match(get('spend-example').textContent,/Settled: Unknown.*Open reservations: Unknown.*Budget: Unknown/);
  }
  await refresh({spendExample:{month:'Synthetic month',settledUsd:0,reservedOpenUsd:0,budgetUsd:0,source:'Synthetic'}});
  assert.match(get('spend-example').textContent,/Synthetic month.*Settled: \$0.00.*Open reservations: \$0.00.*Budget: \$0.00/);
  await refresh({spendExample:{month:'Recovered month',settledUsd:1.25,reservedOpenUsd:2,budgetUsd:10,source:'Synthetic'}});
  assert.match(get('spend-example').textContent,/Recovered month.*\$1.25.*\$2.00.*\$10.00/);
  assert.doesNotMatch(get('spend-example').textContent,/Synthetic month/);
  for(const hubFeeds of [undefined,null,{},[null,[]],[]]) {
    await refresh({hubFeeds});
    assert.match(get('hub-banner').textContent,/unknown/i);
    assert.match(get('ffxi-feeds').textContent,/Unknown/);
  }
  const live={game:'FFXI',view:'roster',status:'Live response',note:'Synthetic reported status',at:'fixture-time'};
  await refresh({hubFeeds:[live,null]});
  assert.match(get('hub-banner').textContent,/incomplete/i);
  assert.doesNotMatch(get('hub-banner').textContent,/Hub reads available/);
  assert.match(get('hub-feeds').textContent,/FFXI.*Live response/);
  assert.match(get('ffxi-feeds').textContent,/coverage.*Unknown/i);
  await refresh({hubFeeds:[{}]});
  assert.doesNotMatch(get('hub-feeds').textContent,/undefined|\[object Object\]/);
  await refresh({hubFeeds:[live]});
  assert.match(get('hub-banner').textContent,/Hub reads available/);
  assert.doesNotMatch(get('hub-feeds').textContent,/incomplete/i);
  console.log('PASS: partial model/spend/feed metadata, zero values and recovery via offline overview refresh. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
