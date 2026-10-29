// Focused partial-metadata checks using actual overview refresh and synthetic data.
const assert = require('node:assert/strict');
const {get, refresh, snapshot} = require('./overview_snapshot_harness.cjs');
(async()=>{
  for(const modelCalls of [undefined,null,{},'bad']) assert.match(await refresh({modelCalls}),/Unknown/);
  assert.match(await refresh({modelCalls:[]}),/No model call examples/);
  assert.match(await refresh({modelCalls:[null,[],false]}),/Unknown/);
  const text=await refresh({modelCalls:[null,{model:'Good example',purpose:'Synthetic',latencyMs:0,cost:0,quality:0},{}]});
  assert.match(text,/Good example.*Latency: 0 ms.*Cost: 0.*Quality: 0/);
  assert.match(text,/coverage.*Unknown/i);
  assert.doesNotMatch(text,/undefined|\[object Object\]/);
  for(const value of [NaN,Infinity,-Infinity,-1,true,'0',{}]) {
    const invalid=await refresh({modelCalls:[{model:'Invalid numbers',latencyMs:value,cost:value,quality:value}]});
    assert.match(invalid,/Latency: Unknown.*Cost: Unknown.*Quality: Unknown/);
  }
  const recovered=await refresh({modelCalls:[{model:'Recovered example',latencyMs:12,cost:0.01,quality:1}]});
  assert.match(recovered,/Recovered example/);assert.doesNotMatch(recovered,/Invalid numbers|coverage.*Unknown/i);
  for(const spendExample of [undefined,null,[],false,'bad',{}]) {
    await refresh({spendExample});
    assert.match(get('spend-example').textContent,/Settled: Unknown.*Open reservations: Unknown.*Budget: Unknown/);
    assert.doesNotMatch(get('spend-example').textContent,/undefined|\[object Object\]/);
  }
  for(const value of [NaN,Infinity,-Infinity,-1,true,'0',{}]) {
    await refresh({spendExample:{settledUsd:value,reservedOpenUsd:value,budgetUsd:value}});
    assert.match(get('spend-example').textContent,/Settled: Unknown.*Open reservations: Unknown.*Budget: Unknown/);
  }
  await refresh({spendExample:{month:'Synthetic month',settledUsd:0,reservedOpenUsd:0,budgetUsd:0,source:'Synthetic'}});
  assert.match(get('spend-example').textContent,/Synthetic month.*Settled: \$0.00.*Open reservations: \$0.00.*Budget: \$0.00/);
  await refresh({spendExample:{month:'Recovered month',settledUsd:1.25,reservedOpenUsd:2,budgetUsd:10,source:'Synthetic'}});
  assert.match(get('spend-example').textContent,/Recovered month.*\$1.25.*\$2.00.*\$10.00/);
  assert.doesNotMatch(get('spend-example').textContent,/Synthetic month/);
  for(const hubFeeds of [undefined,null,{},[null,[]],[]]) {
    await refresh({hubFeeds});
    assert.match(get('hub-banner').textContent,/unknown/i);
    assert.match(get('ffxi-feeds').textContent,/Unknown/);
  }
  const live={game:'FFXI',view:'roster',status:'Live response',note:'Synthetic reported status',at:'fixture-time'};
  await refresh({hubFeeds:[live,null]});
  assert.match(get('hub-banner').textContent,/incomplete/i);
  assert.doesNotMatch(get('hub-banner').textContent,/Hub reads available/);
  assert.match(get('hub-feeds').textContent,/FFXI.*Live response/);
  assert.match(get('ffxi-feeds').textContent,/coverage.*Unknown/i);
  await refresh({hubFeeds:[{}]});
  assert.doesNotMatch(get('hub-feeds').textContent,/undefined|\[object Object\]/);
  await refresh({hubFeeds:[live]});
  assert.match(get('hub-banner').textContent,/Hub reads available/);
  assert.doesNotMatch(get('hub-feeds').textContent,/incomplete/i);
  console.log('PASS: partial model/spend/feed metadata, zero values and recovery via offline overview refresh. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
