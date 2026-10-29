// Fabricated protocol/file contracts only. These are NOT browser evidence.
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {verifySavedReport,verifyGapExport}=require('../tools/verify_gap_export.cjs');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'dit-export-contract-'));
const directory=path.join(root,'downloads');fs.mkdirSync(directory);
const filename=path.join(directory,'roster-gap-row-2.json');
const report={schema:'dit-admin-roster-gap-report-v1',selectedSnapshotRow:2,reason:'repeated_loaded_id',
 candidates:[{snapshotRow:2},{snapshotRow:3}],differingFields:['name','game']};
const expected=JSON.stringify(report,null,2);
(async()=>{
 try {
  assert.throws(()=>verifySavedReport(directory,expected));
  fs.writeFileSync(filename,expected);
  assert.equal(verifySavedReport(directory,expected).savedBytes,Buffer.byteLength(expected));
  assert.equal(verifySavedReport(directory,expected).nativeActivation,undefined,'Disk validation alone is not native Enter evidence');
  // The UI uses the same JSON string for its Blob and copy field. Parsed-value
  // equality alone hides encoding damage and contradictory duplicate keys.
  const unicodeExpected=JSON.stringify({...report,note:'\ufffd'});
  const damaged=Buffer.from(unicodeExpected).toString('hex').replace('efbfbd','ff');
  fs.writeFileSync(filename,Buffer.from(damaged,'hex'));
  assert.throws(()=>verifySavedReport(directory,unicodeExpected));
  fs.writeFileSync(filename,'{"selectedSnapshotRow":999,'+expected.slice(1));
  assert.throws(()=>verifySavedReport(directory,expected));
  fs.writeFileSync(filename,expected+'\n');
  assert.throws(()=>verifySavedReport(directory,expected));
  const validUnicode=JSON.stringify({...report,note:'名é'});
  fs.writeFileSync(filename,validUnicode);
  assert.equal(verifySavedReport(directory,validUnicode).savedBytes,Buffer.byteLength(validUnicode));
  fs.writeFileSync(filename,expected);
  fs.writeFileSync(path.join(directory,'partial.crdownload'),'unfinished');
  assert.throws(()=>verifySavedReport(directory,expected));fs.unlinkSync(path.join(directory,'partial.crdownload'));
  for(const bad of ['broken',JSON.stringify({...report,candidates:[{snapshotRow:2}]}),JSON.stringify({...report,extra:'Unexpected'})]){
    fs.writeFileSync(filename,bad);assert.throws(()=>verifySavedReport(directory,expected));
  }
  fs.unlinkSync(filename);fs.writeFileSync(path.join(root,'outside.json'),expected);
  fs.symlinkSync(path.join(root,'outside.json'),filename);
  assert.throws(()=>verifySavedReport(directory,expected));fs.unlinkSync(filename);
  const sent=[],expressions=[],keys=[];
  const receipt=await verifyGapExport({
    send:async(method,params)=>sent.push({method,params}),
    evaluate:async expression=>{expressions.push(expression);return expression.includes('const region')
      ? {rows:9,columns:3,width:390,scrollWidth:500,differences:['name (differs)','game (differs)'],copy:expected,href:'blob:synthetic-protocol-fixture'}:true;},
    waitFor:async expression=>assert.match(expression,/textarea/),
    press:async key=>{keys.push(key);if(keys.length===2)fs.writeFileSync(filename,expected);}
  },directory);
  assert.deepEqual(keys,['Enter','Enter']);assert.equal(sent.length,1);
  assert.deepEqual(sent[0],{method:'Browser.setDownloadBehavior',params:{behavior:'allow',downloadPath:directory}});
  assert.ok(expressions.every(expression=>!expression.includes('.click(')));
  assert.equal(receipt.table.rows,9);assert.match(receipt.sha256,/^[a-f0-9]{64}$/);
  assert.equal(receipt.nativeActivation,'Enter');
  console.log('PASS: fabricated gap-download protocol, file integrity and refusal contracts. Native browser NOT RUN.');
 } finally {fs.rmSync(root,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});
