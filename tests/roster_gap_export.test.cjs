// Local comparison/export contract in actual UI; no browser download is claimed.
const assert=require('node:assert/strict');
const {get,refresh,requestCount}=require('./overview_snapshot_harness.cjs');
const bots=[{id:'shared',name:'Same name',game:'FFXI',level:0,source:'First',token:'OMIT_SECRET',goals:['OMIT_GOAL']},
  {id:'shared',name:'Same name',game:'SWTOR',level:12,source:'Second',memory:'OMIT_MEMORY'},
  {id:'SHARED',name:'Different key',game:'FFXI'},
  {name:'No ID',game:'FFXI'}, {name:'Other missing ID',game:'SWTOR'}];
const reviews=()=>get('roster-gaps').children.flatMap(row=>row.children).filter(n=>n.textContent.startsWith('Review gap'));
const exported=()=>{
 const panel=get('roster-gap-detail');
 const link=panel.children.find(n=>n.textContent==='Download gap report JSON');
 assert.match(link.attributes.href,/^data:application\/json;charset=utf-8,/);
 const json=decodeURIComponent(link.attributes.href.split(',').slice(1).join(','));
 const copy=panel.children.find(n=>n.attributes['aria-label']==='Gap report JSON for local copy');
 assert.equal(copy.readOnly,true);assert.equal(copy.value,json);
 assert.doesNotMatch(json,/OMIT_SECRET|OMIT_GOAL|OMIT_MEMORY/);
 return {report:JSON.parse(json),link};
};
(async()=>{
 await refresh({bots});const before=requestCount();
 get('bot-game').value='FFXI';get('bot-game').listeners.change();
 reviews()[0].listeners.click();
 let {report,link}=exported();
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
 assert.ok(head.children[0].children.every(n=>n.attributes.scope==='col'));
 assert.equal(body.children.length,9);assert.ok(body.children.every(row=>row.children[0].attributes.scope==='row'));
 assert.match(get('roster-gap-detail').textContent,/Snapshot row 1.*Snapshot row 2.*game \(differs\).*FFXI.*SWTOR/);
 assert.doesNotMatch(get('roster-gap-detail').textContent,/Different key|Other missing ID/);
 reviews()[2].listeners.click();({report}=exported());
 assert.equal(report.reason,'missing_usable_loaded_id');assert.deepEqual(report.candidates.map(r=>r.snapshotRow),[4]);
 assert.deepEqual(report.differingFields,[]);assert.equal(requestCount(),before);
 await refresh({bots:[{id:'x',name:'<script>literal</script>',level:true},{id:'x',name:'<script>literal</script>',level:null}]});
 reviews()[0].listeners.click();({report}=exported());
 assert.deepEqual(report.differingFields,[]);assert.equal(report.candidates[0].fields.level,null);
 assert.equal(report.candidates[0].fields.name,'<script>literal</script>');
 await refresh({bots:[]});assert.equal(get('roster-gap-detail').children.length,0);
 console.log('PASS: all-candidate comparison, differing fields, exact-ID scope, allowlisted JSON/copy parity, unknowns and refresh. Native download unverified.');
})().catch(error=>{console.error(error);process.exitCode=1;});
