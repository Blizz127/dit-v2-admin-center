// Component behavior in actual app; synthetic snapshots, no DOM library or live reads.
const assert=require('node:assert/strict');
const {get,refresh,snapshot}=require('./overview_snapshot_harness.cjs');
(async()=>{
 await refresh({});
 let text=get('routing-audit').textContent;
 assert.match(text,/Per-bot example.*All-bots example/);
 assert.match(text,/Version: 0 → 1/);assert.match(text,/Version: 1 → 2/);
 assert.match(text,/fixture-a.*Requested: fixture-model-one → fixture-model-two/);
 assert.match(text,/fixture-b.*Requested: Unknown → fixture-model-two/);
 assert.match(text,/Effective model: Unknown/);
 assert.match(text,/Attempted model: fixture-model-one.*Simulated rejection: stale version.*Version: 2 → 2.*Expected version: 1.*Requested: fixture-model-two → fixture-model-two/);
 get('routing-audit-scope').value='bot';get('routing-audit-scope').listeners.change();
 assert.match(get('routing-audit-count').textContent,/Showing 2 of 3/);
 assert.doesNotMatch(get('routing-audit').textContent,/All-bots example|fixture-b/);
 get('routing-audit-scope').value='all';get('routing-audit-scope').listeners.change();
 assert.match(get('routing-audit').textContent,/All-bots example.*fixture-a.*fixture-b/);
 get('routing-audit-scope').value='';get('routing-audit-scope').listeners.change();
 for(const routingAudit of [undefined,null,{},[null,[],false]]){
   await refresh({routingAudit});assert.match(get('routing-audit-count').textContent,/of Unknown/);
   assert.doesNotMatch(get('routing-audit').textContent,/fixture-model/);
 }
 await refresh({routingAudit:[]});assert.match(get('routing-audit-count').textContent,/Showing 0 of 0/);
 const row=structuredClone(snapshot.routingAudit[1]);
 row.changes.push(structuredClone(row.changes[0]));row.changes.push({scope:{native_bot:'NO_SCOPE'},afterRequested:'DO_NOT_ATTRIBUTE'});
 row.changes[1].effective='DO_NOT_PROMOTE';
 await refresh({routingAudit:[null,row,{}]});text=get('routing-audit').textContent;
 assert.match(text,/Target scope unknown or ambiguous/);assert.match(text,/fixture-b/);
 assert.doesNotMatch(text,/fixture-a|DO_NOT_ATTRIBUTE|DO_NOT_PROMOTE|undefined|\[object Object\]/);
 for(const scopeKind of ['bot','unexpected',null]){
   const invalid={...snapshot.routingAudit[1],scopeKind};
   await refresh({routingAudit:[invalid]});
   assert.match(get('routing-audit').textContent,/Event target scope unknown or inconsistent/);
   assert.doesNotMatch(get('routing-audit').textContent,/Requested: .*→/);
 }
 await refresh({});assert.match(get('routing-audit-count').textContent,/Showing 3 of 3/);
 console.log('PASS: read-only routing audit scopes, before/after requests, version zero, missing/mixed records, target ambiguity and recovery. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
