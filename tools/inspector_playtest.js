// Embedded by build_inspector_playtest.py around the unchanged application source.
const requests = [];
const unexpected = [];
// Observe real object-URL/Blob creation without fetching through the network.
const gapBlobs = new Map();
const URL = {
  createObjectURL(blob) { const url = globalThis.URL.createObjectURL(blob); gapBlobs.set(url, blob); return url; },
  revokeObjectURL(url) { gapBlobs.delete(url); globalThis.URL.revokeObjectURL(url); },
};
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
  const readinessFilter = document.getElementById('wake-readiness-filter');
  const readinessRows = [...document.querySelectorAll('#wake-game-matrix tr[data-game]')];
  const visibleReadiness = () => readinessRows.filter(row => !row.hidden);
  const readinessRequests = requests.length;
  check(readinessRows.length === 12 && visibleReadiness().length === 12,
    'Readiness matrix starts with twelve mapped rows, not live health claims');
  readinessFilter.value = 'held';
  readinessFilter.dispatchEvent(new Event('change', {bubbles: true}));
  check(visibleReadiness().map(row => row.dataset.game).join(',') === 'war,marvel-heroes',
    'Readiness held filter preserves the two explicit row holds');
  check(textOf('wake-readiness-count').includes('Showing 2 of 12 mapped games'),
    'Readiness count describes filtered mapped rows');
  readinessFilter.value = 'reported';
  readinessFilter.dispatchEvent(new Event('change', {bubbles: true}));
  check(visibleReadiness().length === 0 && !document.getElementById('wake-filter-empty').hidden,
    'No receipt yields an explicit empty reported-readback filter');
  readinessFilter.value = 'all';
  readinessFilter.dispatchEvent(new Event('change', {bubbles: true}));
  check(visibleReadiness().length === 12 && requests.length === readinessRequests,
    'Readiness filters restore all rows without requesting data');
  check(textOf('model-comparison').includes('Example model A') && textOf('model-comparison').includes('120 ms (2/2 supplied)') && textOf('model-comparison').includes('Example model B'), 'Loaded synthetic models compare without selecting or running a provider');
  const issueRequests = requests.length;
  check(textOf('issues').includes('Native browser verification') && textOf('issues').includes('NOT RUN'), 'Document-fed issues keep native verification unconfirmed');
  document.getElementById('issue-status').value = 'Verification pending';
  document.getElementById('issue-status').dispatchEvent(new Event('change', {bubbles: true}));
  check(textOf('issue-count').includes('Showing 1 of 6'), 'Issue status filter selects the documented verification gap');
  document.getElementById('issue-reset').click();
  check(textOf('issue-count').includes('Showing 6 of 6') && requests.length === issueRequests, 'Issue reset restores document gaps without a fetch');
  const auditRequests = requests.length;
  const auditScope = document.getElementById('routing-audit-scope');
  const auditOutcome = document.getElementById('routing-audit-outcome');
  check(textOf('routing-audit-count').includes('Showing 3 of 3'), 'Audit starts with three synthetic examples');
  auditScope.value = 'bot';
  auditScope.dispatchEvent(new Event('change', {bubbles: true}));
  check(textOf('routing-audit-count').includes('Showing 2 of 3'), 'Audit scope selects two per-bot examples');
  auditOutcome.value = 'rejected';
  auditOutcome.dispatchEvent(new Event('change', {bubbles: true}));
  check(textOf('routing-audit-count').includes('Showing 1 of 3') && textOf('routing-audit').includes('Simulated rejection: stale version'), 'Audit outcome intersects scope without guessing effective model');
  auditScope.value = 'all';
  auditScope.dispatchEvent(new Event('change', {bubbles: true}));
  check(textOf('routing-audit-count').includes('Showing 0 of 3') && textOf('routing-audit').includes('No matching model-switch examples'), 'Audit empty intersection is explicit');
  document.getElementById('routing-audit-reset').click();
  check(auditScope.value === '' && auditOutcome.value === '' && textOf('routing-audit-count').includes('Showing 3 of 3') && textOf('routing-audit').includes('Effective model: Unknown') && requests.length === auditRequests, 'Audit reset restores examples locally; effective models remain Unknown');
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
  const originalLearning = structuredClone(fixture.learning);
  fixture.learning = null;
  await load();
  check(!workspace.hidden && textOf('learning-count').includes('Showing 0 of Unknown'), 'Unavailable learning collection keeps the workspace open with Unknown total');
  check(textOf('data-coverage').includes('Learning needs · Unavailable collection'), 'Coverage overview identifies the unavailable learning collection');
  fixture.learning = [null, originalLearning[0]];
  await load();
  check(!workspace.hidden && textOf('learning-count').includes('Showing 1 of Unknown'), 'Partial learning collection preserves usable records');
  fixture.learning = originalLearning;
  await load();
  fixture.modelCalls = [
    {model: 'Synthetic zero fields', purpose: 'Fixture only', latencyMs: 0, cost: 0, quality: 0, source: 'Offline fixture'},
    {model: 'Synthetic partial fields', purpose: 'Fixture only', latencyMs: 12, cost: null, quality: null, source: 'Offline fixture'}
  ];
  await load();
  check(textOf('model-call-coverage').includes('Latency 2/2') && textOf('model-call-coverage').includes('Cost 1/2'), 'Metric coverage preserves zero values and identifies missing fields');
  check(textOf('model-comparison').includes('Mean supplied latency: 0 ms') && textOf('model-comparison').includes('Cost supplied: 0/1'), 'Comparison preserves zero latency and unknown cost coverage');
  check(textOf('data-coverage').includes('Rows with unknown numeric fields: 1'), 'Coverage overview reports numeric-field gaps without inferring quality');
  const availability = document.getElementById('model-call-availability');
  const beforeMetricFilter = requests.length;
  availability.value = 'incomplete'; availability.dispatchEvent(new Event('change'));
  check(textOf('model-calls').includes('Synthetic partial fields') && !textOf('model-calls').includes('Synthetic zero fields'), 'Incomplete metric filter displays only missing-field examples');
  availability.value = ''; availability.dispatchEvent(new Event('change'));
  check(textOf('model-call-coverage').includes('Showing 2 of 2') && requests.length === beforeMetricFilter, 'Restoring metric examples makes no request');
  // Only synthetic records are changed here; the application remains read-only.
  fixture.bots = [{id: 'offline-inspector-bot', name: 'Synthetic inspector bot', game: 'FFXI', source: 'Offline fixture', status: 'Unknown'}];
  const botExamples = {
    botDetails: [{botId: 'offline-inspector-bot', source: 'Offline fixture', goals: [{text: 'Fixture goal'}], memories: [{text: 'Fixture memory'}]}],
    safetyRecords: [{botId: null, scope: 'Fixture network safety', source: 'Offline fixture'}, {botId: 'offline-inspector-bot', scope: 'Fixture bot safety', source: 'Offline fixture'}],
    replyEvents: [
      {botId: 'offline-inspector-bot', correlationId: 'Party-1', wordingOrigin: 'Synthetic model wording', generationStatus: 'generated', fallbackReason: 'Fixture reply reason', source: 'Offline fixture'},
      {botId: 'offline-inspector-bot', correlationId: 'Party-10', wordingOrigin: 'Synthetic canned fallback', delivery: 'queued', source: 'Offline fixture'}
    ],
    assignmentHistory: [{botId: 'offline-inspector-bot', requested: 'Fixture requested model', source: 'Offline fixture'}],
    ledger: [
      {botId: 'offline-inspector-bot', bot: 'Synthetic inspector bot', correlationId: 'Party-1', request: 'Synthetic party greeting', result: 'pending', verification: 'Unknown'},
      {botId: 'other-fixture-bot', bot: 'OTHER_BOT', correlationId: 'Party-1', request: 'OTHER_BOT_EVIDENCE'},
      {bot: 'Unscoped fixture', correlationId: 'Party-1', request: 'UNSCOPED_EVIDENCE'}
    ],
  };
  Object.assign(fixture, structuredClone(botExamples));
  await load();
  const inspectButton = [...document.querySelectorAll('#bots button')].find(b => b.textContent === 'Inspect Synthetic inspector bot');
  check(!!inspectButton, 'Synthetic bot inspection button is rendered');
  const beforeBotSelection = requests.length;
  inspectButton.click();
  check(textOf('bot-inspector').includes('Fixture memory'), 'Bot detail fixture is selectable');
  check(requests.length === beforeBotSelection, 'Bot inspection makes no request');
  const draftGoals = document.getElementById('bot-draft-goals');
  const draftPersonality = document.getElementById('bot-draft-personality');
  const draftForm = document.getElementById('bot-draft-form');
  draftGoals.value = 'Example goal: report observations without claiming progress';
  draftPersonality.value = 'Example personality: patient';
  draftForm.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));
  check(textOf('bot-draft-result').includes('offline-inspector-bot') && textOf('bot-draft-result').includes('Example goal:'), 'Local draft preview stays scoped to the selected synthetic bot');
  check(textOf('bot-draft-result').includes('Current loaded text') && textOf('bot-draft-result').includes('Fixture goal') && textOf('bot-draft-result').includes('Proposed text differs'), 'Draft review shows reported goals beside proposed local text');
  check(textOf('bot-draft-result').includes('Comparison unavailable: current value Unknown'), 'Missing personality baseline stays Unknown in draft review');
  check(textOf('bot-draft-status').includes('Not saved, applied, verified or sent') && requests.length === beforeBotSelection, 'Draft preview performs no request or command');
  draftGoals.value = 'Fixture goal'; draftPersonality.value = '';
  draftForm.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));
  check(textOf('bot-draft-result').includes('Matches loaded text') && textOf('bot-draft-result').includes('No change proposed'), 'Unchanged text and blank proposal have distinct review states');
  draftGoals.value = 'x'.repeat(1001);
  draftForm.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));
  check(textOf('bot-draft-result') === '' && draftGoals.getAttribute('aria-invalid') === 'true', 'Invalid draft removes the previous preview');
  document.getElementById('bot-draft-cancel').click();
  check(draftGoals.value === '' && draftPersonality.value === '', 'Discard removes local draft text');
  draftGoals.value = 'Must not survive refresh';
  const originalBots = structuredClone(fixture.bots);
  fixture.bots = null;
  await load();
  check(!workspace.hidden && textOf('bot-count').includes('Showing 0 of Unknown') && !textOf('bot-inspector').includes('Fixture memory'), 'Unavailable roster keeps workspace open and clears scoped detail');
  check(draftGoals.value === '' && document.getElementById('bot-draft-fields').disabled, 'Unavailable roster refresh clears and disables the local draft');
  check(textOf('data-coverage').includes('Bot roster · Unavailable collection'), 'Coverage overview identifies the unavailable roster');
  fixture.bots = [null, originalBots[0]];
  await load();
  check(textOf('bot-count').includes('Showing 1 of Unknown') && textOf('bot-inspector').includes('Fixture memory'), 'Partial roster recovers unique selected bot details');
  fixture.bots = originalBots;
  await load();
  const gapRoster = [...originalBots,
    {id: 'duplicate-fixture', name: 'Repeated FFXI fixture', game: 'FFXI'},
    {id: 'duplicate-fixture', name: 'Repeated SWTOR fixture', game: 'SWTOR'},
    {name: 'Missing ID fixture', game: 'FFXI'}];
  fixture.bots = gapRoster;
  await load();
  const identityFilter = document.getElementById('bot-identity');
  const beforeIdentityFilter = requests.length;
  identityFilter.value = 'unavailable'; identityFilter.dispatchEvent(new Event('change'));
  document.getElementById('bot-game').value = 'FFXI'; document.getElementById('bot-game').dispatchEvent(new Event('change'));
  check(textOf('bot-count').includes('Showing 2 of 4') && [...document.querySelectorAll('#bots button')].every(button => button.disabled), 'Game filter does not make a repeated loaded ID inspectable');
  document.getElementById('bot-reset').click();
  check(identityFilter.value === '' && requests.length === beforeIdentityFilter, 'Clear roster filters resets identity triage without requests');
  document.getElementById('bot-game').value = 'FFXI'; document.getElementById('bot-game').dispatchEvent(new Event('change'));
  document.querySelector('#roster-gaps button').click();
  check(textOf('roster-gap-detail').includes('game (differs)') && textOf('roster-gap-detail').includes('Repeated SWTOR fixture'), 'Ambiguity table includes the candidate hidden by the game filter');
  const exportLink = document.querySelector('#roster-gap-detail a');
  const exportBlob = gapBlobs.get(exportLink.getAttribute('href'));
  check(exportLink.getAttribute('href').startsWith('blob:') && exportBlob?.type === 'application/json;charset=utf-8', 'Export uses a local JSON Blob');
  const exportedGap = JSON.parse(await exportBlob.text());
  check(exportedGap.candidates.length === 2 && exportedGap.selectedSnapshotRow === 2 && exportedGap.differingFields.includes('game'), 'Local JSON export retains all candidate rows and differences');
  check(document.querySelector('#roster-gap-detail textarea').value === JSON.stringify(exportedGap, null, 2), 'Copy field and downloadable JSON agree');
  const oldGapLink = document.querySelector('#roster-gap-detail button');
  oldGapLink.click();
  check(textOf('bot-count').includes('Showing 1 of 4') && textOf('bot-count').includes('Pinned snapshot row: 2'), 'Gap detail targets the exact snapshot roster row');
  check(textOf('roster-gap-detail').includes('Repeated loaded ID: 2 rows') && [...document.querySelectorAll('#bots button')].every(button => button.disabled), 'Gap detail does not make repeated identity inspectable');
  check(requests.length === beforeIdentityFilter, 'Gap details and exact-row navigation make no requests');
  fixture.bots = originalBots;
  await load();
  oldGapLink.click();
  check(!textOf('bot-count').includes('Pinned snapshot row') && textOf('roster-gap-detail').includes('Select a loaded roster gap'), 'Snapshot refresh invalidates old gap links');
  document.getElementById('bot-reset').click();
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
  const replyFilter = document.getElementById('reply-correlation');
  const beforeReplyFilter = requests.length;
  replyFilter.value = 'Party-1';
  replyFilter.dispatchEvent(new Event('input'));
  check(textOf('reply-count').includes('Showing 1 of 2') && !textOf('reply-source').includes('Party-10'), 'Exact reply correlation filter excludes prefix matches');
  check(textOf('reply-source').includes('Generation: generated') && textOf('reply-source').includes('Delivery: Unknown'), 'Generated wording does not establish delivery');
  document.querySelector('#reply-source button').click();
  check(textOf('ledger-filter').includes('Pinned bot ID: offline-inspector-bot') && textOf('ledger-count').includes('Showing 1 of 3'), 'Reply shortcut counts only matching scoped ledger evidence');
  check(textOf('ledger').includes('Result: pending') && textOf('ledger').includes('Verification: Unknown') && !textOf('ledger').includes('OTHER_BOT_EVIDENCE') && !textOf('ledger').includes('UNSCOPED_EVIDENCE'), 'Shared correlation cannot attribute other-bot or unscoped evidence');
  document.getElementById('reply-reset').click();
  check(textOf('reply-count').includes('Showing 2 of 2') && requests.length === beforeReplyFilter, 'Clearing the reply filter restores examples without a request');
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
  // Leave fictional gaps visible for manual inspection after the scripted checks.
  fixture.bots = gapRoster;
  document.getElementById('bot-reset').click();
  await load();
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
  // Scripted inspection navigates through several panels. Start the owner's review
  // at the dashboard instead of leaving the viewport at the last test action.
  document.getElementById('main-content').scrollIntoView({block: 'start', behavior: 'instant'});
  markWorkspaceSection('overview');
} catch (error) {
  document.querySelector('#harness-status').textContent = 'FAIL — ' + error.message;
  document.documentElement.dataset.playtest = 'failed';
}
