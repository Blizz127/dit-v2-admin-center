// Protocol fixtures only: fake PNG headers are NOT rendered screenshots.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {views, validateLayout, captureComparisons} = require('../tools/capture_comparisons.cjs');
function layout(view) {
  return {open:true,rows:4,columns:5,modelUnknowns:4,panelLeft:10,panelRight:view.width-10,tableTop:100,tableBottom:700,
    regionLeft:12,regionRight:view.width-12,clientWidth:view.width-24,scrollWidth:1400,
    scrollLeft:view.right?1400-(view.width-24):0};
}
async function main() {
  for (const view of views) {
    validateLayout(layout(view),view);
    for(const patch of [{open:false},{rows:3},{modelUnknowns:3},{panelRight:view.width+2},{clientWidth:NaN},{tableTop:-2},{tableBottom:view.height+2}])
      assert.throws(()=>validateLayout({...layout(view),...patch},view));
  }
  assert.throws(()=>validateLayout({...layout(views[2]),scrollLeft:0},views[2]));
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'dit-capture-test-'));
  let current=0, calls=[];
  const command=async(method,params)=>{
    calls.push(method);
    if(method==='Emulation.setDeviceMetricsOverride') return {};
    const view=views[current];
    if(method==='Runtime.evaluate') return {result:{value:layout(view)}};
    assert.equal(method,'Page.captureScreenshot');
    assert.equal(params.captureBeyondViewport,false);
    const fake=Buffer.alloc(24); Buffer.from('89504e470d0a1a0a','hex').copy(fake);
    fake.writeUInt32BE(view.width,16);fake.writeUInt32BE(view.height,20);current++;
    return {data:fake.toString('base64')};
  };
  try {
    const result=await captureComparisons(command,directory);
    assert.equal(result.status,'captured');assert.equal(result.captures.length,3);
    assert.equal(calls.length,9);
    assert.deepEqual(fs.readdirSync(directory).sort(),views.map(v=>v.name+'.png').sort());
    current=0;await assert.rejects(captureComparisons(command,directory),/EEXIST/);
    await assert.rejects(captureComparisons(async(method)=>method==='Runtime.evaluate'?{exceptionDetails:{}}:{},directory),/render failed/);
    await assert.rejects(captureComparisons(async(method)=>method==='Runtime.evaluate'?{result:{value:layout(views[0])}}:{data:''},directory),/Screenshot/);
  } finally {fs.rmSync(directory,{recursive:true,force:true});}
  console.log('PASS: capture protocol fixtures (no browser execution or screenshots)');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
