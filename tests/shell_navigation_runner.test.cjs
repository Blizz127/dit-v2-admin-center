// Fabricated browser protocol state only: never a trusted/native key pass.
const assert=require('node:assert/strict');
const {verifyShellNavigation,verifyCoverageGeometry}=require('../tools/verify_shell_navigation.cjs');
const sections=['overview','roster','ffxi','learning','evidence','operations','models','notes'];
const cards=width=>[0,1,2].map(i=>({left:width===390?18:300+i*300,right:width===390?372:580+i*300,
  top:width===390?i*114:0,bottom:width===390?i*114+100:100,width:width===390?354:280,height:100}));
function fixture(failure){
  let width,active,hash='';const keys=[],widths=[];
  return {keys,widths,api:{
    command:async(method,args)=>{assert.equal(method,'Emulation.setDeviceMetricsOverride');width=args.width;widths.push(width);},
    evaluate:async expression=>{
      assert.doesNotMatch(expression,/\.click\(|dispatchEvent/);
      if(expression==='document.activeElement.id')return active;
      if(expression.includes('#data-coverage'))return failure==='cards'?[]:cards(width);
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
  assert.deepEqual(result.coverage,[{width:1280,cards:3,layout:'columns'},{width:390,cards:3,layout:'stacked'}]);
  for(const failure of ['order','activation','overflow','cards'])await assert.rejects(()=>verifyShellNavigation(fixture(failure).api));
  for(const mutate of [c=>c.pop(),c=>c[1].width=NaN,c=>c[1].left=-20,c=>c[1].right=500,
    c=>{c[1].top=50;c[1].bottom=150;},c=>{c[1].height=0;c[1].bottom=c[1].top;}]){
    const invalid=cards(390);mutate(invalid);assert.throws(()=>verifyCoverageGeometry(invalid,390));
  }
  assert.throws(()=>verifyCoverageGeometry(cards(390),1280),'Stacked cards cannot pass the desktop contract');
  console.log('PASS: fabricated shell protocol and coverage geometry/refusal contracts. Native browser NOT RUN.');
})().catch(error=>{console.error(error);process.exitCode=1;});
