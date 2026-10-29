// Fabricated browser protocol state only: never a trusted/native key pass.
const assert=require('node:assert/strict');
const {verifyShellNavigation}=require('../tools/verify_shell_navigation.cjs');
const sections=['overview','roster','ffxi','learning','evidence','operations','models','notes'];
function fixture(failure){
  let width,active,hash='';const keys=[],widths=[];
  return {keys,widths,api:{
    command:async(method,args)=>{assert.equal(method,'Emulation.setDeviceMetricsOverride');width=args.width;widths.push(width);},
    evaluate:async expression=>{
      assert.doesNotMatch(expression,/\.click\(|dispatchEvent/);
      if(expression==='document.activeElement.id')return active;
      if(expression.includes('documentWidth'))return {viewport:width,documentWidth:failure==='overflow'?width+20:width};
      const match=expression.match(/^document.getElementById\('nav-([a-z]+)'\).focus\(\); true$/);
      assert.ok(match);active='nav-'+match[1];return true;
    },
    press:async(key,shift=false)=>{
      keys.push([key,shift]);
      if(key==='Tab'){
        const index=sections.indexOf(active.slice(4));
        active='nav-'+sections[index+(shift?-1:1)];
        if(failure==='order')active='unexpected-focus';
      }else{
        assert.equal(key,'Enter');const section=active.slice(4);
        active='view-'+section;hash='#view-'+section;
        if(failure==='activation')active='nav-'+section;
      }
    },
    waitFor:async expression=>{
      const match=expression.match(/^document.activeElement.id === '(view-[a-z]+)' && location.hash === '#(view-[a-z]+)'$/);
      assert.ok(match);assert.equal(active,match[1]);assert.equal(hash,'#'+match[2]);
    },
  }};
}
(async()=>{
  const good=fixture();const result=await verifyShellNavigation(good.api);
  assert.deepEqual(good.widths,[1280,390]);assert.equal(result.sections,8);
  assert.equal(good.keys.filter(([key,shift])=>key==='Tab'&&!shift).length,14);
  assert.equal(good.keys.filter(([key,shift])=>key==='Tab'&&shift).length,14);
  assert.equal(good.keys.filter(([key])=>key==='Enter').length,16);
  for(const failure of ['order','activation','overflow'])await assert.rejects(()=>verifyShellNavigation(fixture(failure).api));
  console.log('PASS: fabricated shell protocol sequence and wrong-focus/activation/overflow refusal. Native browser NOT RUN.');
})().catch(error=>{console.error(error);process.exitCode=1;});
