// Real Node Blob bytes and disposable-file equality; not a browser save action.
const assert=require('node:assert/strict');
const {resolveObjectURL}=require('node:buffer');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {get,refresh,context,requestCount}=require('./overview_snapshot_harness.cjs');
const {verifySavedReport}=require('../tools/verify_gap_export.cjs');
const bots=[{id:'unique',name:'Unique'},
 {id:'shared',name:'First 名',game:'FFXI'}, {id:'shared',name:'Second 名',game:'SWTOR'}];
const review=()=>get('roster-gaps').children.flatMap(r=>r.children).find(n=>n.textContent.startsWith('Review gap'));
const link=()=>get('roster-gap-detail').children.find(n=>n.attributes.download);
const copy=()=>get('roster-gap-detail').children.find(n=>n.attributes['aria-label']==='Gap report JSON for local copy').value;
(async()=>{
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'dit-blob-export-'));
 try{
  await refresh({bots});const before=requestCount();review().listeners.click();
  const first=link().attributes.href,blob=resolveObjectURL(first);
  assert.ok(blob instanceof Blob);assert.equal(blob.type,'application/json;charset=utf-8');
  assert.equal(await blob.text(),copy());
  const bytes=Buffer.from(await blob.arrayBuffer());
  fs.writeFileSync(path.join(directory,'roster-gap-row-2.json'),bytes);
  const receipt=verifySavedReport(directory,copy());
  assert.equal(receipt.savedBytes,bytes.length);assert.equal(receipt.nativeActivation,undefined);
  review().listeners.click();const second=link().attributes.href;
  assert.notEqual(first,second);assert.equal(resolveObjectURL(first),undefined,'Replaced URL revoked');
  assert.ok(resolveObjectURL(second));assert.equal(requestCount(),before);
  await refresh({bots});assert.equal(resolveObjectURL(second),undefined,'Snapshot refresh revokes URL');
  review().listeners.click();const third=link().attributes.href;
  context.resetPanelSession();assert.equal(resolveObjectURL(third),undefined,'Session reset revokes URL');
  await refresh({bots});
  context.URL={createObjectURL(){throw Error('PRIVATE_BROWSER_FAILURE');},revokeObjectURL(){}};
  review().listeners.click();
  assert.equal(link(),undefined);assert.match(get('roster-gap-detail').textContent,/Download unavailable/);
  assert.doesNotMatch(get('roster-gap-detail').textContent,/PRIVATE_BROWSER_FAILURE/);
  assert.equal(JSON.parse(copy()).selectedSnapshotRow,2,'Copy remains available if object URLs fail');
  console.log('PASS: real Blob/UTF-8/file/copy equality, URL revocation on replacement/refresh/reset, and copy fallback. Native browser download NOT RUN.');
 }finally{context.URL=URL;context.resetPanelSession();fs.rmSync(directory,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});
