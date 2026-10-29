// Embedded by build_inspector_playtest.py around the unchanged application source.
const requests = [];
const unexpected = [];
const sessionStorage = {getItem: () => 'synthetic-harness-token', setItem() {}, removeItem() {}};
const setInterval = () => 0; // No polling or background observations in this harness.
const fetch = async (url, options = {}) => {
  requests.push(url);
  if (options.method && options.method !== 'GET') throw new Error('Only fixture GETs allowed');
  if (url === '/api/overview?source=mock') return {ok: true, json: async () => structuredClone(fixture)};
  if (url === '/api/bridge-status') return {ok: true, json: async () => ({unit: 'unknown', substate: 'unknown', result: 'unknown', marker: 'unknown', source: 'Synthetic offline fixture', observedAt: null})};
  unexpected.push(url);
  throw new Error('No fixture for request; network forbidden');
};
// Keep guide links inside this artifact; no navigation to the running application.
document.querySelectorAll('a').forEach(a => { if (!a.getAttribute('href')?.startsWith('#')) a.href = '#harness-results'; });
const report = (name) => {
  const row = document.createElement('li'); row.textContent = 'PASS — ' + name;
  document.querySelector('#harness-checks').append(row);
};
const check = (condition, name) => { if (!condition) throw new Error(name); report(name); };
const textOf = id => document.getElementById(id).textContent;
const settle = async predicate => {
  const deadline = Date.now() + 2000;
  while (!predicate()) {
    if (Date.now() > deadline) throw new Error('Timed out waiting for inspector runtime');
    await new Promise(resolve => setTimeout(resolve, 10));
  }
};
const clickNeed = topic => {
  const button = [...document.querySelectorAll('#learning button')].find(b => b.textContent === 'Inspect ' + topic);
  if (!button) throw new Error('Missing runtime inspect button for ' + topic);
  button.click();
};
try {
/* APPLICATION */
  await settle(() => !document.querySelector('#workspace').hidden);
  check(document.querySelector('#error').textContent === '', 'Actual application loaded the projected fixture');
  const answers = ['Yes', 'No', 'Yes', 'Unknown'];
  fixture.learning.forEach((need, index) => {
    clickNeed(need.topic);
    const inspector = textOf('learning-inspector');
    check(inspector.includes('Model answer reported: ' + answers[index]), need.id + ': answer flag rendered');
    check(inspector.includes('Evidence: ' + need.evidence), need.id + ': evidence availability rendered');
    check(inspector.includes('Status: verified') && inspector.includes('Policy verification: Unknown'), need.id + ': verified task does not verify policy');
    check((textOf('learning-evidence').match(/Evidence state: Unknown/g) || []).length === 5, need.id + ': five game assessments stay Unknown');
  });
  const before = requests.length;
  document.querySelector('#learning-evidence').closest('details').open = true;
  document.querySelector('#learning-evidence-preview').click();
  check(textOf('learning-evidence').includes('Synthetic mapping preview'), 'Preview clearly labeled synthetic');
  check(['supported (synthetic)', 'missing (synthetic)', 'conflicting (synthetic)'].every(s => textOf('learning-evidence').includes(s)), 'Preview displays three distinct synthetic states');
  document.querySelector('#learning-evidence-selected').click();
  check(textOf('learning-evidence').includes('Evidence review') && !textOf('learning-evidence').includes('Synthetic mapping preview'), 'Restore returns to the selected fixture task');
  document.querySelector('#clear-learning').click();
  check(textOf('learning-evidence').includes('No learning record selected'), 'Clear removes assessment context');
  check(requests.length === before, 'Inspector, preview, restore and clear make no fetch requests');
  check(unexpected.length === 0, 'Only allowlisted in-memory fixture reads occurred');
  document.querySelector('#harness-status').textContent = 'PASS — real browser DOM checks completed with synthetic data; no network transport.';
  document.documentElement.dataset.playtest = 'passed';
} catch (error) {
  document.querySelector('#harness-status').textContent = 'FAIL — ' + error.message;
  document.documentElement.dataset.playtest = 'failed';
}
