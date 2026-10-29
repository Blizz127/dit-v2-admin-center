// Actual async loaders with synthetic GET responses; no browser, listener or live data.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const template=JSON.parse(execFileSync('python3',['tests/inspector_runtime_fixture.py','--template'],{encoding:'utf8',timeout:5000}));
class Element {
  constructor(spec={}){this.attributes={...spec.attrs};this.value=spec.value||'';this.children=[];this.listeners={};this.hidden=false;this.text='';}
  append(...items){this.children.push(...items);} replaceChildren(){this.children=[];this.text='';}
  set textContent(value){this.children=[];this.text=String(value);} get textContent(){return this.text+this.children.map(c=>c.textContent).join(' ');}
  addEventListener(name,fn){this.listeners[name]=fn;} setAttribute(key,value){this.attributes[key]=String(value);}
  get lastElementChild(){return this.children.at(-1);}
}
const elements=new Map(Object.entries(template).map(([id,spec])=>[id,new Element(spec)]));
const get=id=>{assert.ok(elements.has(id),'Unknown template ID '+id);return elements.get(id);};
let body, expectedPath;
const context={document:{querySelector:s=>get(s.slice(1)),getElementById:get,createElement:()=>new Element()},
  sessionStorage:{getItem:()=>'',setItem(){},removeItem(){}},
  fetch:async(path,options)=>{assert.equal(path,expectedPath);assert.equal(options.method||'GET','GET');return {ok:true,json:async()=>body};}};
vm.createContext(context);vm.runInContext(fs.readFileSync('static/app.js','utf8'),context);
vm.runInContext("token='synthetic'; loadedSource='hub'",context);get('data-source').value='hub';get('trace-game').value='ffxi';
const cases=[
  {panel:'hub-health',path:'/api/hub-health',run:()=>context.loadHubHealth(),list:'services',
   good:{services:[{game:'FFXI',label:'Synthetic service',state:'running',observedAt:'fixture-time'}]},match:/Synthetic service.*running/},
  {panel:'hub-trace',path:'/api/trace?gameId=ffxi&correlationId=fixture',run:()=>context.loadHubTrace('fixture'),list:'records',
   good:{records:[{kind:'Synthetic trace',type:'reported',disposition:'pending',isFinal:false}]},match:/Synthetic trace.*Final: false/},
  {panel:'interaction-status',path:'/api/interaction',run:()=>context.loadInteraction(),list:'bots',
   good:{switches:{contract:true,naturalOrders:false,selfClaims:false},bots:[{actorKey:'Synthetic actor',caller:'fixture',serverInstanceId:'fixture',fresh:true,snapshotFresh:false,activity:'waiting'}]},match:/Synthetic actor.*Activity: waiting/}
];
(async()=>{
 for(const c of cases){
   expectedPath=c.path;
   const load=async value=>{body=value;await c.run();return get(c.panel).textContent;};
   assert.match(await load(c.good),c.match);
   for(const malformed of [null,[],false,'bad']){
     const text=await load(malformed);assert.match(text,/unavailable|unknown/i);assert.doesNotMatch(text,/undefined|\[object Object\]|Synthetic actor|Synthetic service|Synthetic trace/);
   }
   for(const value of [undefined,null,{},[null,[],false]]){
     const text=await load({...c.good,[c.list]:value});assert.match(text,/unknown/i);assert.doesNotMatch(text,/undefined|\[object Object\]/);
   }
   const mixed=await load({...c.good,[c.list]:[null,...c.good[c.list]]});
   assert.match(mixed,c.match);assert.match(mixed,/coverage.*unknown/i);
   const partial=await load({...c.good,[c.list]:[{}]});assert.match(partial,/unknown/i);assert.doesNotMatch(partial,/undefined|\[object Object\]/);
   const recovered=await load(c.good);assert.match(recovered,c.match);assert.doesNotMatch(recovered,/malformed records/);
 }
 expectedPath='/api/trace?gameId=ffxi&correlationId=fixture';body={records:[{isFinal:'true'}]};await context.loadHubTrace('fixture');assert.match(get('hub-trace').textContent,/Final: Unknown/);
 expectedPath='/api/interaction';body={switches:{contract:'true'},bots:cases[2].good.bots};await context.loadInteraction();assert.doesNotMatch(get('interaction-status').textContent,/Synthetic actor|Activity: waiting/);
 console.log('PASS: partial health/trace/interaction loaders preserve valid rows and Unknown coverage; strict flags, empty/malformed/recovery. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
