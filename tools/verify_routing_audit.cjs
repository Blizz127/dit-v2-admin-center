// Candidate native workflow; called only inside the isolated synthetic runner.
const assert = require('node:assert/strict');
async function verifyRoutingAudit({evaluate, press, waitFor}) {
  const focus = id => evaluate(`document.getElementById('${id}').focus(); true`);
  const active = id => waitFor(`document.activeElement.id === '${id}'`);
  const count = n => waitFor(`document.getElementById('routing-audit-count').textContent.includes('Showing ${n} of 3')`);
  // Establish the starting selection with native activation, not a DOM click.
  await focus('routing-audit-reset');
  await press('Enter');
  await count(3);
  await focus('routing-audit-scope');
  await press('Home');
  await press('ArrowDown');
  await count(2);
  await press('Tab');
  await active('routing-audit-outcome');
  await press('Home');
  await press('ArrowDown');
  await press('ArrowDown');
  await count(1);
  assert.match(await evaluate("document.getElementById('routing-audit').textContent"), /Simulated rejection: stale version/);
  await press('Tab', true);
  await active('routing-audit-scope');
  await press('Home');
  await press('ArrowDown');
  await press('ArrowDown');
  await count(0);
  assert.match(await evaluate("document.getElementById('routing-audit').textContent"), /No matching model-switch examples/);
  await press('Tab');
  await active('routing-audit-outcome');
  await press('Tab');
  await active('routing-audit-reset');
  await press('Enter');
  await count(3);
  await active('routing-audit-reset');
  assert.equal(await evaluate("document.getElementById('routing-audit-scope').value"), '');
  assert.equal(await evaluate("document.getElementById('routing-audit-outcome').value"), '');
  assert.match(await evaluate("document.getElementById('routing-audit').textContent"), /Effective model: Unknown/);
  return {status:'passed', counts:[3,2,1,0,3], traversal:'Tab/Shift+Tab',
    selection:'Home/ArrowDown', reset:'Enter', focusRetained:true,
    limitations:'Synthetic examples only; does not verify model switching, live audit or visual appearance'};
}
module.exports = {verifyRoutingAudit};
