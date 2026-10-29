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
  // Only synthetic records are changed here; the application remains read-only.
  fixture.bots = [{id: 'offline-inspector-bot', name: 'Synthetic inspector bot', game: 'FFXI', source: 'Offline fixture', status: 'Unknown'}];
  const botExamples = {
    botDetails: [{botId: 'offline-inspector-bot', source: 'Offline fixture', goals: [{text: 'Fixture goal'}], memories: [{text: 'Fixture memory'}]}],
    safetyRecords: [{botId: null, scope: 'Fixture network safety', source: 'Offline fixture'}, {botId: 'offline-inspector-bot', scope: 'Fixture bot safety', source: 'Offline fixture'}],
    replyEvents: [{botId: 'offline-inspector-bot', fallbackReason: 'Fixture reply reason', source: 'Offline fixture'}],
    assignmentHistory: [{botId: 'offline-inspector-bot', requested: 'Fixture requested model', source: 'Offline fixture'}],
  };
  Object.assign(fixture, structuredClone(botExamples));
  await load();
  const inspectButton = [...document.querySelectorAll('#bots button')].find(b => b.textContent === 'Inspect Synthetic inspector bot');
  check(!!inspectButton, 'Synthetic bot inspection button is rendered');
  const beforeBotSelection = requests.length;
  inspectButton.click();
  check(textOf('bot-inspector').includes('Fixture memory'), 'Bot detail fixture is selectable');
  check(requests.length === beforeBotSelection, 'Bot inspection makes no request');
  for (const key of Object.keys(botExamples)) fixture[key] = null;
  await load();
  check(!workspace.hidden && textOf('bot-inspector').includes('Goals and memory'), 'Unavailable detail metadata keeps workspace open');
  check(textOf('safety-records').includes('Safety example coverage unknown') && !textOf('safety-records').includes('Fixture bot safety'), 'Unavailable safety list clears previous examples');
  check(textOf('reply-source').includes('Reply evidence coverage unknown') && !textOf('reply-source').includes('Fixture reply reason'), 'Unavailable reply list clears previous examples');
  check(textOf('assignment-history').includes('Assignment example coverage unknown') && !textOf('assignment-history').includes('Fixture requested model'), 'Unavailable assignment list clears previous examples');
  fixture.botDetails = [{botId: 'offline-inspector-bot', goals: null, memories: [{text: 'Partial fixture memory'}]}];
  fixture.safetyRecords = [{scope: 'Unattributed fixture safety'}, {botId: 'offline-inspector-bot', gate: false}];
  fixture.replyEvents = [{botId: 'offline-inspector-bot', source: {}}];
  fixture.assignmentHistory = [{botId: 'offline-inspector-bot'}];
  await load();
  check(textOf('bot-inspector').includes('Partial fixture memory') && textOf('bot-inspector').includes('Unknown'), 'Partial goals do not erase usable memory');
  check(textOf('safety-records').includes('Safety example scope unknown') && !textOf('safety-records').includes('Unattributed fixture safety'), 'Missing bot identity is not treated as network scope');
  check(textOf('reply-source').includes('Source unknown') && textOf('assignment-history').includes('Effective: Unknown'), 'Partial reply and assignment fields stay Unknown');
  for (const key of Object.keys(botExamples)) fixture[key] = [];
  await load();
  check(textOf('safety-records').includes('No safety examples') && textOf('reply-source').includes('No matching reply evidence') && textOf('assignment-history').includes('No matching examples'), 'Valid empty inspector lists differ from unavailable lists');
  Object.assign(fixture, structuredClone(botExamples));
  await load();
  check(textOf('bot-inspector').includes('Fixture goal') && textOf('safety-records').includes('Fixture bot safety') && textOf('reply-source').includes('Fixture reply reason') && textOf('assignment-history').includes('Fixture requested model'), 'Inspector panels recover with current synthetic examples');
  const botSelectors = [...document.querySelectorAll('#bots select')];
  check(botSelectors.length === 2 && botSelectors.every(select => select.disabled), 'Per-bot model selectors remain disabled');
  fixture.assignmentHistory = assignmentFixtures.populated.map(row => ({...row, botId: row.botId === 'fixture-bot' ? 'offline-inspector-bot' : row.botId}));
  await load();
  const previousAssignment = document.getElementById('assignment-prev');
  const nextAssignment = document.getElementById('assignment-next');
  check(textOf('assignment-count').includes('Page 1 of 3') && !textOf('assignment-history').includes('OTHER_BOT'), 'Assignment pages count only loaded examples for the selected bot');
  const beforePaging = requests.length;
  nextAssignment.focus({preventScroll: true});
  nextAssignment.click();
  check(textOf('assignment-count').includes('Showing 11–20 of 23') && document.activeElement === nextAssignment, 'Next assignment page keeps focus on its button');
  nextAssignment.click();
  check(textOf('assignment-count').includes('Showing 21–23 of 23') && nextAssignment.getAttribute('aria-disabled') === 'true', 'Last assignment page announces its boundary');
  nextAssignment.click();
  check(textOf('assignment-count').includes('Page 3 of 3') && document.activeElement === nextAssignment, 'Unavailable next page ignores activation without losing focus');
  previousAssignment.focus({preventScroll: true});
  previousAssignment.click(); previousAssignment.click(); previousAssignment.click();
  check(textOf('assignment-count').includes('Page 1 of 3') && document.activeElement === previousAssignment, 'Previous page respects its boundary and preserves focus');
  check(requests.length === beforePaging, 'Assignment paging makes no requests');
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
  installAssignmentKeyboardCheck({document,
    prepare: async () => {
      fixture.assignmentHistory = assignmentFixtures.populated.map(row => ({...row, botId: row.botId === 'fixture-bot' ? 'offline-inspector-bot' : row.botId}));
      document.querySelector('#data-source').value = 'mock';
      await load(); await settle(() => !sourceLoading && !bridgePending);
      document.querySelector('#clear-bot').click();
      inspectBot('offline-inspector-bot');
    },
    page: () => assignmentPages === 3 ? assignmentPage + 1 : null,
    requests: () => requests.length,
  });
  document.querySelector('#harness-status').textContent = 'PASS — automatic DOM checks completed with synthetic data. Native keyboard check is separate and has NOT RUN.';
  document.documentElement.dataset.playtest = 'passed';
} catch (error) {
  document.querySelector('#harness-status').textContent = 'FAIL — ' + error.message;
  document.documentElement.dataset.playtest = 'failed';
}
