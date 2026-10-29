// Local comparison/export contract in actual UI; no browser download is claimed.
const assert=require('node:assert/strict');
const {resolveObjectURL}=require('node:buffer');
const {get,refresh,requestCount}=require('./overview_snapshot_harness.cjs');
const bots=[{id:'shared',name:'Same name',game:'FFXI',level:0,source:'First',token:'OMIT_SECRET',goals:['OMIT_GOAL']},
  {id:'shared',name:'Same name',game:'SWTOR',level:12,source:'Second',memory:'OMIT_MEMORY'},
  {id:'SHARED',name:'Different key',game:'FFXI'},
  {name:'No ID',game:'FFXI'}, {name:'Other missing ID',game:'SWTOR'}];
const reviews=()=>get('roster-gaps').children.flatMap(row=>row.children).filter(n=>n.textContent.startsWith('Review gap'));
const fields=['id','name','game','status','character','level','bodyKind','source','observedAt'];
function assertShape(report){
 assert.deepEqual(Object.keys(report).sort(),['schema','snapshotGeneratedAt','selectedSnapshotRow','reason','differingFields','candidates','limits'].sort());
 assert.equal(report.schema,'dit-admin-roster-gap-report-v1');
 assert.ok(report.snapshotGeneratedAt===null || (typeof report.snapshotGeneratedAt==='string' && report.snapshotGeneratedAt.trim()));
 assert.ok(Number.isSafeInteger(report.selectedSnapshotRow) && report.selectedSnapshotRow>0);
 assert.ok(['missing_usable_loaded_id','repeated_loaded_id'].includes(report.reason));
 assert.ok(Array.isArray(report.candidates) && report.candidates.length>0);
 assert.equal(new Set(report.candidates.map(r=>r.snapshotRow)).size,report.candidates.length);
 assert.ok(report.candidates.some(r=>r.snapshotRow===report.selectedSnapshotRow));
 for(const row of report.candidates){
  assert.deepEqual(Object.keys(row).sort(),['fields','snapshotRow']);
  assert.ok(Number.isSafeInteger(row.snapshotRow) && row.snapshotRow>0);
  assert.deepEqual(Object.keys(row.fields).sort(),[...fields].sort());
  for(const [key,value] of Object.entries(row.fields)){
   assert.ok(value===null || (typeof value==='string' && value.trim()) ||
    (key==='level' && Number.isSafeInteger(value) && value>=0),key+' has an unsupported JSON value');
  }
 }
 assert.deepEqual(report.differingFields,fields.filter(key=>new Set(report.candidates.map(r=>r.fields[key])).size>1));
 assert.ok(Array.isArray(report.limits) && report.limits.length>0 && report.limits.every(s=>typeof s==='string' && s.trim()));
}
const exported=async()=>{
 const panel=get('roster-gap-detail');
 const link=panel.children.find(n=>n.textContent==='Download gap report JSON');
 assert.match(link.attributes.href,/^blob:/);
 const blob=resolveObjectURL(link.attributes.href);
 assert.equal(blob.type,'application/json;charset=utf-8');
 const json=await blob.text();
 const copy=panel.children.find(n=>n.attributes['aria-label']==='Gap report JSON for local copy');
 assert.equal(copy.readOnly,true);assert.equal(copy.value,json);
 assert.doesNotMatch(json,/OMIT_SECRET|OMIT_GOAL|OMIT_MEMORY/);
 const report=JSON.parse(json);assertShape(report);
 return {report,link};
};
(async()=>{
 await refresh({bots});const before=requestCount();
 get('bot-game').value='FFXI';get('bot-game').listeners.change();
 reviews()[0].listeners.click();
 let {report,link}=await exported();
 assert.equal(report.schema,'dit-admin-roster-gap-report-v1');
 assert.equal(report.selectedSnapshotRow,1);assert.equal(report.reason,'repeated_loaded_id');
 assert.deepEqual(report.candidates.map(r=>r.snapshotRow),[1,2],'Include every exact-ID row despite game filter');
 assert.deepEqual(report.differingFields,['game','level','source']);
 assert.equal(report.candidates[0].fields.level,0);assert.equal(report.candidates[0].fields.status,null);
 assert.equal(link.attributes.download,'roster-gap-row-1.json');
 const region=get('roster-gap-detail').children.find(n=>n.attributes.role==='region');
 assert.equal(region.attributes.tabindex,'0');assert.equal(region.attributes['aria-label'],'Roster gap candidate comparison');
 const table=region.children[0],head=table.children[1],body=table.children[2];
 assert.equal(head.children[0].children.length,3);
 assert.equal(table.attributes.style,'--gap-columns: 3','Narrow table width follows actual candidate count');
 assert.ok(head.children[0].children.every(n=>n.attributes.scope==='col'));
 assert.equal(body.children.length,9);assert.ok(body.children.every(row=>row.children[0].attributes.scope==='row'));
 assert.match(get('roster-gap-detail').textContent,/Snapshot row 1.*Snapshot row 2.*game \(differs\).*FFXI.*SWTOR/);
 assert.doesNotMatch(get('roster-gap-detail').textContent,/Different key|Other missing ID/);
 reviews()[2].listeners.click();({report}=await exported());
 assert.equal(report.reason,'missing_usable_loaded_id');assert.deepEqual(report.candidates.map(r=>r.snapshotRow),[4]);
 assert.deepEqual(report.differingFields,[]);assert.equal(requestCount(),before);
 await refresh({bots:[{id:'x',name:'<script>literal</script>',level:true},{id:'x',name:'<script>literal</script>',level:null}]});
 reviews()[0].listeners.click();({report}=await exported());
 assert.deepEqual(report.differingFields,[]);assert.equal(report.candidates[0].fields.level,null);
 assert.equal(report.candidates[0].fields.name,'<script>literal</script>');
 await refresh({generatedAt:'   ',bots:[{id:'x',name:'Unicode 名 · %',level:Infinity,source:{token:'OMIT_SECRET'},observedAt:[]},
  {id:'x',name:'Unicode 名 · %',level:-1,status:false,character:42}]});
 reviews()[0].listeners.click();({report}=await exported());
 assert.equal(report.snapshotGeneratedAt,null,'Blank timestamp remains Unknown');
 assert.equal(report.candidates[0].fields.name,'Unicode 名 · %');
 assert.equal(report.candidates[0].fields.level,null);
 assert.equal(report.candidates[0].fields.source,null);
 assert.equal(report.candidates[0].fields.observedAt,null);
 assert.equal(report.candidates[1].fields.level,null);
 assert.equal(report.candidates[1].fields.character,null);
 await refresh({bots:[]});assert.equal(get('roster-gap-detail').children.length,0);
 console.log('PASS: strict export shape, all-candidate comparison, differing fields, exact-ID scope, JSON/copy parity, malformed values, Unicode, unknowns and refresh. Native download unverified.');
})().catch(error=>{console.error(error);process.exitCode=1;});
