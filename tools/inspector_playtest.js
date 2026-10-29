// Embedded by build_inspector_playtest.py around the unchanged application source.
const requests = [];
const unexpected = [];
let healthResponse = {ok: true, json: async () => ({services: [], source: 'Synthetic offline health', fetchedAt: 'fixture-time', coverage: 'Fixture coverage only'})};
let bridgeResponse = {ok: true, json: async () => ({unit: 'unknown', substate: 'unknown', result: 'unknown', marker: 'unknown', source: 'Synthetic offline fixture', observedAt: null})};
const sessionStorage = {getItem: () => 'synthetic-harness-token', setItem() {}, removeItem() {}};
const setInterval = () => 0; // No polling or background observations in this harness.
const fetch = async (url, options = {}) => {
  requests.push(url);
  if (options.method && options.method !== 'GET') throw new Error('Only fixture GETs allowed');
  if (url === '/api/overview?source=mock' || url === '/api/overview?source=hub') return {ok: true, json: async () => structuredClone(fixture)};
  if (url === '/api/hub-health') return healthResponse;
  if (url === '/api/bridge-status') return bridgeResponse;
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
  check(textOf('learning-evidence').includes('No learning record selected'), 'Initial render explains the empty selection');
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
  document.querySelector('#data-source').value = 'hub';
  document.querySelector('#data-source').dispatchEvent(new Event('change'));
  await settle(() => loadedSource === 'hub' && !sourceLoading && !bridgePending);
  const healthGood = {services: [{game: 'FFXI', label: 'Synthetic bridge', state: 'running', observedAt: 'fixture-time'}],
    source: 'Synthetic offline health', fetchedAt: 'fixture-time', coverage: 'Fixture coverage only'};
  const bridgeGood = {unit: 'active', substate: 'running', result: 'success', marker: 'absent', markerReason: 'unknown',
    source: 'Synthetic offline bridge', observedAt: 'fixture-time'};
  const refresh = async (button, predicate) => { document.getElementById(button).click(); await settle(predicate); };
  for (const id of ['hub-health', 'bridge-status']) {
    const details = document.getElementById(id).closest('details');
    if (details) details.open = true;
  }
  await refresh('hub-health-refresh', () => textOf('hub-health').includes('No matching service records'));
  check(textOf('hub-health').includes('Empty data does not establish healthy services'), 'Empty health coverage is not healthy');
  for (const status of [401, 502, 503]) {
    healthResponse = {ok: true, json: async () => structuredClone(healthGood)};
    await refresh('hub-health-refresh', () => textOf('hub-health').includes('Synthetic bridge'));
    healthResponse = {ok: false, status};
    await refresh('hub-health-refresh', () => textOf('hub-health').includes('health unavailable'));
    check(!textOf('hub-health').includes('fixture-time'), 'Health ' + status + ' removes previous service records');
  }
  healthResponse = {ok: true, json: async () => structuredClone(healthGood)};
  await refresh('hub-health-refresh', () => textOf('hub-health').includes('Synthetic bridge'));
  check(textOf('hub-health').includes('Service state is not bot presence'), 'Health recovers without implying bot presence');
  for (const status of [200, 401, 503]) {
    bridgeResponse = {ok: true, json: async () => structuredClone(bridgeGood)};
    await refresh('bridge-refresh', () => !bridgePending && textOf('bridge-status').includes('active'));
    bridgeResponse = status === 200 ? {ok: true, json: async () => ({unit: 'unknown', substate: 'unknown', result: 'unknown', marker: 'unknown', markerReason: 'unknown', source: 'Synthetic unavailable observation', observedAt: null})} : {ok: false, status};
    await refresh('bridge-refresh', () => !bridgePending && textOf('bridge-status').includes('unknown'));
    check(['bridge-status', 'ffxi-focus-bridge'].every(id => !textOf(id).includes('fixture-time') && !textOf(id).includes('active')), 'Bridge ' + status + ' clears both previous observations');
  }
  bridgeResponse = {ok: true, json: async () => structuredClone(bridgeGood)};
  await refresh('bridge-refresh', () => !bridgePending && textOf('bridge-status').includes('active'));
  check(textOf('ffxi-focus-bridge').includes('Not proof of delivery'), 'Both bridge cards recover without claiming delivery');
  check(unexpected.length === 0, 'Only allowlisted in-memory fixture reads occurred');
  document.querySelector('#harness-status').textContent = 'PASS — DOM checks completed with synthetic data; runtime identity is reported by the runner.';
  document.documentElement.dataset.playtest = 'passed';
} catch (error) {
  document.querySelector('#harness-status').textContent = 'FAIL — ' + error.message;
  document.documentElement.dataset.playtest = 'failed';
}
