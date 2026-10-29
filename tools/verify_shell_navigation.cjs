// Run only inside the existing disposable, network-isolated Chromium runner.
// Offline protocol tests of this module are not native keyboard evidence.
const assert = require('node:assert/strict');
const sections = ['overview','roster','ffxi','learning','evidence','operations','models','notes'];
async function verifyShellNavigation({command,evaluate,press,waitFor}) {
  for (const width of [1280,390]) {
    await command('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:false});
    await evaluate("document.getElementById('nav-overview').focus(); true");
    for (const section of sections.slice(1)) {
      await press('Tab');
      assert.equal(await evaluate('document.activeElement.id'),'nav-'+section,'Forward sidebar Tab order');
    }
    for (const section of sections.slice(0,-1).reverse()) {
      await press('Tab',true);
      assert.equal(await evaluate('document.activeElement.id'),'nav-'+section,'Reverse sidebar Tab order');
    }
    for (const section of sections) {
      // Position the start only; Enter must do the activation and target focus.
      await evaluate(`document.getElementById('nav-${section}').focus(); true`);
      await press('Enter');
      await waitFor(`document.activeElement.id === 'view-${section}' && location.hash === '#view-${section}'`);
    }
    const geometry=await evaluate('({viewport:innerWidth,documentWidth:document.documentElement.scrollWidth})');
    assert.equal(geometry.viewport,width);
    assert.ok(Number.isFinite(geometry.documentWidth) && geometry.documentWidth<=width+1,'Page-level horizontal overflow');
  }
  return {status:'passed',sections:sections.length,widths:[1280,390],traversal:'Tab/Shift+Tab',activation:'Enter',
    limitations:'Synthetic artifact only; geometry is not visual appearance or screen-reader review'};
}
module.exports={verifyShellNavigation};
