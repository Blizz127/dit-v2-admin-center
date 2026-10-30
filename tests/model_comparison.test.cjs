// Grouping is descriptive loaded data, never benchmark execution or a model choice.
const assert=require('node:assert/strict');
const {get,refresh,requestCount}=require('./overview_snapshot_harness.cjs');
(async()=>{
 const row={model:'Model A',purpose:'conversation',source:'Synthetic run A',latencyMs:0,cost:0,quality:0};
 await refresh({modelCalls:[row,{...row,latencyMs:20,cost:null,quality:null},
   {...row,model:'Model B',latencyMs:12}, {...row,source:'Synthetic run B',latencyMs:8},
   {...row,purpose:'planning',latencyMs:null}, {...row,model:'',latencyMs:1}, null]});
 assert.equal(get('model-comparison').children.length,5,'Four exact groups and one missing-identity warning');
 let text=get('model-comparison').textContent;
 assert.match(text,/2 loaded samples · Mean supplied latency: 10 ms \(2\/2 supplied\).*Cost supplied: 1\/2 · Quality supplied: 1\/2/);
 assert.match(text,/Model B.*12 ms/);
 assert.match(text,/planning.*Unknown \(0\/1 supplied\)/);
 assert.match(text,/Unattributed examples.*1 rows excluded/);
 assert.match(get('model-call-coverage').textContent,/Unknown total/);
 const before=requestCount();
 get('model-call-availability').value='complete';get('model-call-availability').listeners.change();
 assert.match(get('model-comparison').textContent,/Mean supplied latency: 0 ms \(1\/1 supplied\)/);
 assert.doesNotMatch(get('model-comparison').textContent,/planning/);
 assert.equal(requestCount(),before);
 await refresh({modelCalls:null});assert.match(get('model-comparison').textContent,/Comparison unavailable.*Unknown/);
 assert.doesNotMatch(get('model-comparison').textContent,/Model A/);
 get('model-call-availability').value='';
 await refresh({modelCalls:[]});assert.match(get('model-comparison').textContent,/No comparable loaded groups/);
 await refresh({modelCalls:[{...row,latencyMs:Number.MAX_VALUE},{...row,latencyMs:Number.MAX_VALUE}]});
 assert.doesNotMatch(get('model-comparison').textContent,/Infinity|NaN/);
 assert.match(get('model-comparison').textContent,/2\/2 supplied/);
 console.log('PASS: exact group boundaries, missing identity/numbers, zero, filter, overflow and recovery. Simulated DOM only.');
})().catch(e=>{console.error(e);process.exitCode=1;});
