// No coordinator ledger, account files, listener or live process probes.
const assert = require('node:assert/strict');
const {get, refresh} = require('./overview_snapshot_harness.cjs');
const panels={leads:'leads',leadMonitoring:'lead-monitoring',leadActivity:'lead-activity',
  leadTimeline:'lead-timeline',nudgeHistory:'nudge-history',sessionMarkers:'session-markers',quotaHistory:'quota-history',
  gameStatus:'game-status',serviceHealth:'service-health'};
(async()=>{
  for(const [field,panel] of Object.entries(panels)) {
    for(const value of [undefined,null,{},[],[null,[],false], [{}]]) {
      await refresh({[field]:value});
      assert.match(get(panel).textContent,/unknown/i,field);
      assert.doesNotMatch(get(panel).textContent,/undefined|\[object Object\]/,field);
    }
  }
  const mixed={
    leads:[null,{name:'Synthetic lead',scope:'FFXI',status:'Reported status'}],
    leadMonitoring:[null,{lead:'Synthetic lead',stall:'Unknown',quota:'Unknown'}],
    leadActivity:[false,{lead:'Synthetic lead',taskStatus:'Recorded task'}],
    leadTimeline:[null,{lead:'Synthetic lead',events:[null,{kind:'Task status',status:'Recorded task',at:'fixture-time'}]}],
    nudgeHistory:[null,{lead:'Synthetic lead',nudges:[null,{messageStatus:'reported',replySeconds:0,resumeSignal:{seconds:0,label:'Tool heuristic'}}]}],
    sessionMarkers:[null,{lead:'Synthetic lead',markers:[null,{kind:'Synthetic marker'}]}],
    quotaHistory:[null,{account:'Synthetic account',window:'unified5h',remainingPercent:0}],
    gameStatus:[null,{game:'FFXI',xpRate:0,liveness:'Unknown',source:'Synthetic settings'}],
    serviceHealth:[null,{game:'FFXI',label:'Synthetic service',status:'Reported running'}]
  };
  await refresh(mixed);
  for(const panel of Object.values(panels)) {
    assert.match(get(panel).textContent,/coverage.*unknown/i);
    assert.doesNotMatch(get(panel).textContent,/undefined|\[object Object\]/);
  }
  assert.match(get('lead-summary').textContent,/coverage.*unknown/i);
  assert.match(get('lead-timeline').textContent,/Task status: Recorded task/);
  assert.match(get('nudge-history').textContent,/Time to reply: 0 s.*Tool heuristic: 0 s/);
  assert.match(get('quota-history').textContent,/Remaining: 0%/);
  assert.match(get('game-status').textContent,/XP rate: 0×.*Server liveness: Unknown/);
  assert.match(get('service-health').textContent,/Synthetic service.*Reported running/);
  for(const value of [true,'0',-1,Infinity]) {
    await refresh({gameStatus:[{game:'FFXI',xpRate:value}]});
    assert.match(get('game-status').textContent,/XP rate: Unknown.*Server liveness: Unknown/);
  }
  for(const value of [true,'0',-1,Infinity,101]) {
    await refresh({quotaHistory:[{remainingPercent:value}]});
    assert.match(get('quota-history').textContent,/Remaining: Unknown/);
  }
  await refresh({nudgeHistory:[{nudges:[{replySeconds:-1,resumeSignal:[]},{replySeconds:'0',resumeSignal:{label:'Heuristic',seconds:Infinity}}]}]});
  assert.match(get('nudge-history').textContent,/Time to reply: Unknown/);
  assert.doesNotMatch(get('nudge-history').textContent,/Infinity|undefined|\[object Object\]/);
  await refresh({leadTimeline:[{lead:'Recovered lead',events:[{kind:'Task status',status:'Recovered',at:'fixture-time',source:'Synthetic'}]}]});
  assert.match(get('lead-timeline').textContent,/Recovered/);
  assert.doesNotMatch(get('lead-timeline').textContent,/Recorded task/);
  get('timeline-kind').value='commit';get('timeline-kind').listeners.change();
  assert.match(get('lead-timeline').textContent,/No matching evidence/);
  get('timeline-kind').value='';get('timeline-kind').listeners.change();
  assert.match(get('lead-timeline').textContent,/Recovered/);
  console.log('PASS: partial coordinator lists/nested histories, mixed rows, numeric bounds, filter and recovery. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
