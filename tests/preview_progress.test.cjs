// Actual jsdom views with a controlled clock; no browser timing/native claims.
const assert = require('node:assert/strict');
const {JSDOM} = require(process.env.DIT_JSDOM_MODULE || 'jsdom');
const {installPreviewProgress} = require('../tools/preview_progress.js');
function fixture() {
  const dom = new JSDOM(['overview','assignment'].map(location => `<details><summary id="preview-progress-label-${location}"></summary><p id="preview-progress-${location}"></p></details>`).join(''));
  let time = 0, tick, cancelled = 0;
  const progress = installPreviewProgress({document:dom.window.document, now:()=>time,
    schedule:callback=>{tick=callback;return 1;}, cancel:id=>{assert.equal(id,1);cancelled++;}});
  const panels = [...dom.window.document.querySelectorAll('p')];
  return {progress, panels, labels:[...dom.window.document.querySelectorAll('summary')], at(value){time=value; tick();}, cancelled:()=>cancelled, close:()=>dom.window.close()};
}
const stalled = fixture();
try {
  stalled.progress.record('<img src="https://offline.invalid/never">');
  stalled.at(4999);assert.ok(stalled.panels.every(p=>p.dataset.state==='running'));
  stalled.at(5000);
  assert.ok(stalled.panels.every(p=>p.dataset.state==='progress-timeout' && p.textContent.includes('no assertion progress') && p.textContent.includes('1 completed checks')));
  assert.equal(stalled.panels[0].textContent, stalled.panels[1].textContent);
  assert.ok(stalled.labels.every(label=>label.textContent.includes('Stalled')));
  assert.equal(stalled.panels[0].querySelector('img'), null);
  stalled.progress.record('late success');assert.equal(stalled.progress.finish(),false);
  assert.equal(stalled.progress.snapshot().checks,1);assert.equal(stalled.cancelled(),1);
} finally {stalled.close();}
const total = fixture();
try {
  for (const time of [4000,8000,9999]) {total.at(time);total.progress.record('Fixture progress');}
  total.at(10000);
  assert.ok(total.panels.every(p=>p.dataset.state==='total-timeout' && p.textContent.includes('10-second total')));
  assert.ok(total.labels.every(label=>label.textContent.includes('10-second total')));
  assert.equal(total.progress.finish(),false);assert.equal(total.cancelled(),1);
} finally {total.close();}
const good = fixture();
try {
  good.progress.record('x'.repeat(500));good.at(100);assert.equal(good.progress.finish(),true);
  assert.ok(good.panels.every(p=>p.dataset.state==='passed' && p.dataset.checks==='1' && p.textContent.includes('remain unverified')));
  assert.equal(good.progress.snapshot().lastCheck.length,240);
  good.at(20000);assert.equal(good.progress.snapshot().state,'passed');assert.equal(good.cancelled(),1);
  assert.equal(good.progress.snapshot().elapsedMs,100);assert.ok(good.labels.every(label=>label.textContent.includes('Completed')));
} finally {good.close();}
const failed = fixture();
try {
  failed.progress.fail();failed.at(12000);
  assert.ok(failed.panels.every(p=>p.dataset.state==='failed'));
  assert.equal(failed.progress.finish(),false);assert.equal(failed.cancelled(),1);
} finally {failed.close();}
console.log('PASS: actual DOM diagnostics for stall, total limit, failure and completion; terminal states, bounded text and timer cleanup. Clock is synthetic; native NOT RUN.');
