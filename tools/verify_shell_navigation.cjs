// Run only inside the existing disposable, network-isolated Chromium runner.
// Offline protocol tests of this module are not native keyboard evidence.
const assert = require('node:assert/strict');
const sections = ['overview','roster','ffxi','learning','evidence','operations','models','notes'];
function verifyCoverageGeometry(cards,width) {
  assert.equal(cards.length,3,'All three coverage cards must be rendered');
  for(const card of cards) {
    for(const key of ['left','right','top','bottom','width','height'])assert.ok(Number.isFinite(card[key]),'Invalid card geometry');
    assert.ok(card.width>0 && card.height>0 && card.left>=-1 && card.right<=width+1,'Coverage card outside horizontal viewport');
    assert.ok(Math.abs(card.right-card.left-card.width)<=1 && Math.abs(card.bottom-card.top-card.height)<=1,'Inconsistent card bounds');
  }
  for(let index=1;index<cards.length;index++) {
    const previous=cards[index-1],card=cards[index];
    if(width<=1100) {
      assert.ok(card.top>=previous.bottom && Math.abs(card.left-previous.left)<=1 && Math.abs(card.width-previous.width)<=1,'Narrow coverage cards must stack without overlap');
    } else {
      assert.ok(card.left>=previous.right && Math.abs(card.top-previous.top)<=1,'Desktop coverage cards must form one non-overlapping row');
    }
  }
  return {width,cards:cards.length,layout:width<=1100?'stacked':'columns'};
}
async function verifyShellNavigation({command,evaluate,press,waitFor}) {
  const coverage=[];
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
    const cards=await evaluate(`[...document.querySelectorAll('#data-coverage > .row')].map(node => {
      const {left,right,top,bottom,width,height}=node.getBoundingClientRect();
      return {left,right,top,bottom,width,height};
    })`);
    coverage.push(verifyCoverageGeometry(cards,width));
  }
  return {status:'passed',sections:sections.length,widths:[1280,390],traversal:'Tab/Shift+Tab',activation:'Enter',coverage,
    limitations:'Synthetic artifact only; geometry is not visual appearance or screen-reader review'};
}
module.exports={verifyShellNavigation,verifyCoverageGeometry};
