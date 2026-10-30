// Actual app and document-fed fixture; simulated DOM, no native browser.
const assert=require('node:assert/strict');
const {get,refresh,requestCount}=require('./overview_snapshot_harness.cjs');
(async()=>{
 await refresh({});
 assert.match(get('issues').textContent,/FFXI adapter evidence gaps/);
 assert.match(get('issues').textContent,/docs\/LEARNING-AND-ISSUES.md/);
 assert.match(get('issues').textContent,/Native browser verification.*NOT RUN/);
 const before=requestCount();
 get('issue-status').value='Verification pending';get('issue-status').listeners.change();
 assert.match(get('issue-count').textContent,/Showing 1 of 6/);
 assert.doesNotMatch(get('issues').textContent,/FFXI adapter/);
 get('issue-reset').listeners.click();
 get('issue-scope').value='SWTOR';get('issue-scope').listeners.change();
 assert.match(get('issue-count').textContent,/Showing 1 of 6/);
 assert.match(get('issues').textContent,/SWTOR adapter.*Suggested verification/);
 get('issue-search').value='not-an-issue';get('issue-search').listeners.input();
 assert.match(get('issues').textContent,/does not establish a healthy state/);
 get('issue-reset').listeners.click();
 assert.match(get('issue-count').textContent,/Showing 6 of 6/);
 assert.equal(requestCount(),before);
 console.log('PASS: document-fed issue rendering, source/next step, scope/status/search/reset; simulated DOM only.');
})().catch(e=>{console.error(e);process.exitCode=1;});
