// Synthetic inventory only: no datasets, policy files or live learning tasks read.
const assert = require('node:assert/strict');
const {get, refresh} = require('./overview_snapshot_harness.cjs');
(async()=>{
 for(const [field,panel] of [['learningPlan','learning-plan'],['learningArtifacts','learning-artifacts']]){
   for(const value of [undefined,null,{},[],[null,[],false],[{}]]){
     await refresh({[field]:value});
     assert.match(get(panel).textContent,/unknown|does not establish/i);
     assert.doesNotMatch(get(panel).textContent,/undefined|\[object Object\]/);
   }
 }
 const learningPlan=[null,{game:'FFXI',topic:'Synthetic navigation',next:'Review observations'},
   {game:'SWTOR',topic:'Synthetic other game',next:'No transfer'}];
 const learningArtifacts=[null,{game:'FFXI',name:'Synthetic policy',kind:'policy',validation:'Reported',adoption:null,outcome:null},
   {game:'SWTOR',name:'Other policy',kind:'policy'}];
 await refresh({learningPlan,learningArtifacts});
 assert.match(get('learning-plan').textContent,/coverage.*Unknown.*Synthetic navigation/);
 assert.match(get('learning-artifacts').textContent,/Synthetic policy.*Validation: Reported.*Adoption: Unknown.*Demonstrated outcome: Unknown/);
 get('learning-game').value='FFXI';get('learning-game').listeners.change();
 assert.match(get('learning-plan').textContent,/Synthetic navigation/);assert.doesNotMatch(get('learning-plan').textContent,/Synthetic other game/);
 assert.match(get('learning-artifacts').textContent,/Synthetic policy/);assert.doesNotMatch(get('learning-artifacts').textContent,/Other policy/);
 // Missing/malformed records remain a coverage warning even when a game filter hides them.
 assert.match(get('learning-artifacts').textContent,/coverage.*Unknown/);
 await refresh({learningPlan:[],learningArtifacts:[]});
 assert.doesNotMatch(get('learning-plan').textContent,/Synthetic navigation/);
 assert.doesNotMatch(get('learning-artifacts').textContent,/Synthetic policy/);
 await refresh({learningPlan:[{game:'FFXI',topic:'Recovered plan'}],learningArtifacts:[{game:'FFXI',name:'Recovered artifact'}]});
 assert.match(get('learning-plan').textContent,/Recovered plan/);
 assert.match(get('learning-artifacts').textContent,/Recovered artifact/);
 console.log('PASS: missing/mixed/partial learning inventory, scope filtering and recovery. Simulated DOM only.');
})().catch(error=>{console.error(error);process.exitCode=1;});
