// Simulated adapter + actual application. This is NOT a native browser result.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const {verifyRoutingAudit} = require('../tools/verify_routing_audit.cjs');
const {get, refresh, context, requestCount} = require('./overview_snapshot_harness.cjs');
const ids = ['routing-audit-scope','routing-audit-outcome','routing-audit-reset'];
const options = [['','bot','all'],['','applied','rejected','unknown']];
for (const id of ids) get(id).focus = () => { context.document.activeElement = get(id); };
const evaluate = async expression => vm.runInContext(expression, context);
const waitFor = async expression => assert.equal(await evaluate(expression), true, expression);
function adapter(fault) {
  return {evaluate, waitFor, press: async (key, shift=false) => {
    const element = context.document.activeElement;
    const index = ids.indexOf(element.id);
    if (key === 'Tab') {
      if (fault === 'focus') return;
      get(ids[index + (shift ? -1 : 1)]).focus();
    } else if (key === 'Enter') {
      element.listeners.click();
      if (fault === 'reset') get(ids[0]).value = 'bot';
    } else {
      const values = options[index];
      element.value = key === 'Home' ? '' : values[values.indexOf(element.value) + 1];
      if (fault !== 'change') element.listeners.change();
    }
  }};
}
(async () => {
  await refresh({});
  // Execute the new standalone-driver block against the same actual app.
  // Only DOM events/geometry are simulated; no claim of full artifact execution.
  for (const id of ids) {
    get(id).dispatchEvent = event => get(id).listeners[event.type]();
    get(id).click = () => get(id).listeners.click();
  }
  context.Event = class {constructor(type) {this.type=type;}};
  context.textOf = id => get(id).textContent;
  context.check = (condition, message) => assert.ok(condition, message);
  context.requests = {get length() {return requestCount();}};
  const driver = fs.readFileSync('tools/inspector_playtest.js', 'utf8');
  const start = driver.indexOf('  const auditRequests =');
  const end = driver.indexOf("  check(textOf('learning-evidence')", start);
  assert.ok(start >= 0 && end > start, 'Standalone audit scenario must be present');
  vm.runInContext('{'+driver.slice(start, end)+'}', context);
  const before = requestCount();
  const receipt = await verifyRoutingAudit(adapter());
  assert.deepEqual(receipt.counts, [3,2,1,0,3]);
  assert.equal(receipt.focusRetained, true);
  assert.equal(requestCount(), before, 'Local audit selection must not request data');
  for (const fault of ['focus','change','reset']) {
    await refresh({});
    await assert.rejects(verifyRoutingAudit(adapter(fault)), undefined, fault + ' must not produce success');
  }
  console.log('PASS: audit keyboard workflow through simulated adapter; focus/change/reset failures refused. Native NOT RUN.');
})().catch(error => {console.error(error); process.exitCode=1;});
