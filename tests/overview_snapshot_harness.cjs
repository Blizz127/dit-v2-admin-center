// Real overview refresh code, synthetic responses and a minimal DOM; no listener/browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
// These helpers parse local fixtures, not a latency-sensitive application path.
// Keep them bounded while allowing startup on the shared, contended host.
const python = (...args) => execFileSync('python3', args, {encoding:'utf8',timeout:30000});
const artifactPath = process.env.DIT_TEST_ARTIFACT;
const application = fs.readFileSync('static/app.js','utf8');
if (artifactPath) assert.ok(fs.readFileSync(artifactPath, 'utf8').includes(application), 'Artifact does not embed the current application source');
const template = JSON.parse(python('tests/inspector_runtime_fixture.py','--template', ...(artifactPath ? [artifactPath] : [])));
const snapshot = JSON.parse(python('-c','import json; from tools.build_inspector_playtest import snapshot; print(json.dumps(snapshot()))'));
class Element {
  constructor(spec={}) { this.attributes={...spec.attrs}; this.children=[];this.listeners={};this.text='';this.value=spec.value||'';this.hidden=Object.hasOwn(spec.attrs||{},'hidden'); }
  append(...items){this.children.push(...items);}
  replaceChildren(){this.children=[];this.text='';}
  set textContent(value){this.children=[];this.text=String(value);}
  get textContent(){return this.text+this.children.map(c=>c.textContent).join(' ');}
  addEventListener(name,fn){this.listeners[name]=fn;}
  setAttribute(key,value){this.attributes[key]=String(value);}
  scrollIntoView(){}
  get lastElementChild(){return this.children.at(-1);}
}
const elements=new Map(Object.entries(template).map(([id,spec])=>[id,new Element(spec)]));
const get=id=>{assert.ok(elements.has(id),'Missing template ID '+id);return elements.get(id);};
for(const [id,spec] of Object.entries(template)) {
  get(id).id=id;
  get(id).closest=selector=>{assert.equal(selector,'.workspace-section');return spec.section?get(spec.section):null;};
}
let data=snapshot;
let requestCount=0;
const storage=new Map();
const globalEvents={};
const context={Blob,URL,location:{hash:''},addEventListener:(type,fn)=>{globalEvents[type]=fn;},document:{querySelector:s=>get(s.slice(1)),getElementById:get,createElement:()=>new Element()},
  sessionStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
  fetch:async(path, options)=>{
    requestCount++;
    assert.equal(options.method||'GET','GET');
    if(path==='/api/bridge-status')return {ok:true,json:async()=>({unit:'Unknown',source:'Synthetic'})};
    assert.equal(path,'/api/overview?source=mock');return {ok:true,json:async()=>data};
  }};
vm.createContext(context);vm.runInContext(application,context);
async function refresh(changes){
  data={...snapshot,...changes};
  vm.runInContext("token = 'synthetic-test-token'",context);
  await get('refresh').listeners.click();
  assert.equal(get('workspace').hidden,false,'Partial telemetry must not close the workspace');
  return get('model-calls').textContent;
}

module.exports = {get, refresh, snapshot, context, globalEvents, requestCount:()=>requestCount};
