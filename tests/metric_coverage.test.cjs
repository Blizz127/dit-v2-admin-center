// Actual app with synthetic metrics in a minimal DOM. No provider or ledger reads.
const assert = require('node:assert/strict');
const {get,refresh,context,requestCount} = require('./overview_snapshot_harness.cjs');
const all={model:'ALL_ZERO',latencyMs:0,cost:0,quality:0};
const partial={model:'PARTIAL',latencyMs:12,cost:null,quality:null};
const filter=value=>{get('model-call-availability').value=value;get('model-call-availability').listeners.change();};
(async()=>{
  await refresh({modelCalls:[all,partial,{}]});
  assert.match(get('model-call-coverage').textContent,/Showing 3 of 3.*Latency 2\/3.*Cost 1\/3.*Quality 1\/3/);
  const before=requestCount();filter('complete');
  assert.match(get('model-call-coverage').textContent,/Showing 1 of 3.*Latency 2\/3/);
  assert.match(get('model-calls').textContent,/ALL_ZERO.*Cost: 0/);
  assert.doesNotMatch(get('model-calls').textContent,/PARTIAL/);
  filter('incomplete');assert.match(get('model-call-coverage').textContent,/Showing 2 of 3/);
  assert.doesNotMatch(get('model-calls').textContent,/ALL_ZERO/);
  assert.equal(requestCount(),before,'Filtering must not request telemetry');
  await refresh({modelCalls:[all]});assert.match(get('model-calls').textContent,/No examples match/);
  assert.match(get('model-call-coverage').textContent,/Showing 0 of 1/);
  filter('');await refresh({modelCalls:[null,all,partial]});
  assert.match(get('model-call-coverage').textContent,/Showing 2 of Unknown total.*Latency 2\/2.*Cost 1\/2/);
  for(const value of [true,'0',NaN,Infinity,-1]){
    await refresh({modelCalls:[{model:'BAD',latencyMs:value,cost:value,quality:value}]});
    assert.match(get('model-call-coverage').textContent,/Latency 0\/1.*Cost 0\/1.*Quality 0\/1/);
  }
  await refresh({modelCalls:[]});assert.match(get('model-call-coverage').textContent,/Showing 0 of 0/);
  await refresh({modelCalls:null});assert.equal(get('model-call-coverage').textContent,'Metric coverage unknown.');
  await refresh({modelCalls:[all]});assert.match(get('model-call-coverage').textContent,/Showing 1 of 1/);
  filter('complete');context.resetPanelSession();
  assert.equal(get('model-call-availability').value,'');
  assert.equal(get('model-call-coverage').textContent,'Metric coverage unknown.');
  console.log('PASS: metric field coverage, local filters, zero/invalid values, partial feeds and session reset. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
