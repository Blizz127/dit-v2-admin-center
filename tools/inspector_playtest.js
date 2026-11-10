// Embedded by build_inspector_playtest.py around the unchanged application source.
const requests = [];
const unexpected = [];
const previewProgress = installPreviewProgress({document});
document.getElementById('harness-status').textContent = 'RUNNING — local synthetic checks. Native verification has NOT RUN.';
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
  document.getElementById('harness-checks').append(row);
  previewProgress.record(name);
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
  await settle(() => !document.getElementById('workspace').hidden);
  check(document.getElementById('error').textContent === '', 'Actual application loaded the projected fixture');
  const activityList = document.querySelector('#bot-activity details');
  check(activityList && activityList.children.length === 1 && activityList.firstElementChild.tagName === 'SUMMARY',
    'Closed bot activity list shows its summary without building its event body');
  activityList.open = true;
  await settle(() => activityList.children.length === 2);
  const activityBody = activityList.lastElementChild;
  check(activityBody.textContent.length > 0, 'Opening bot activity populates its local event body');
  activityList.open = false;
  await new Promise(resolve => setTimeout(resolve, 0));
  activityList.open = true;
  await new Promise(resolve => setTimeout(resolve, 0));
  check(activityList.children.length === 2 && activityList.lastElementChild === activityBody,
    'Reopening bot activity retains the same body without duplicate entries');
  const activityFixture = fixture.botActivity, baselineFixture = fixture.baselineConformance;
  const activityCoverage = textOf('bot-activity-coverage');
  const baselineText = textOf('baseline-conformance');
  check(activityCoverage.includes(`Observed event range: ${activityFixture.coverage.from} to ${activityFixture.coverage.to} (UTC; offline export)`),
    'Legacy Forever coverage shows retained event bounds separately from its export timestamp');
  check(document.querySelectorAll('#bot-activity-sources .bot-source').length === 3 && baselineText.includes('Bots parity'),
    'Startup renders all additional bot sources and the supplied parity evidence');
  const vanillaExport = activityFixture.sources.find(source => source.id === 'wow-vanilla-playerbots');
  const vanillaPanel = [...document.querySelectorAll('#bot-activity-sources .bot-source')]
    .find(section => section.querySelector('h4').textContent === vanillaExport.label);
  check(vanillaPanel.textContent.includes(`Observed event range: ${vanillaExport.coverage.from} to ${vanillaExport.coverage.to} (UTC; offline export)`),
    'Imported Vanilla event range is visible as offline evidence in its own source panel');
  // The following scenarios mutate unrelated roster/inspector fields. Keep their
  // snapshots small instead of rebuilding the same imported exports 30 times.
  // Full imported data is checked above and restored for the final owner view.
  fixture.botActivity = null;
  fixture.baselineConformance = null;
  check(document.querySelectorAll('#presence-examples .row').length === 3 && textOf('presence-examples').includes('Live presence: Unknown') && textOf('presence-examples').includes('Different native identity'), 'Presence review loads three synthetic cases without claiming live presence');
  const originalPresenceExamples = structuredClone(fixture.presenceExamples);
  fixture.presenceExamples = {kind:'live', rows:originalPresenceExamples.rows};
  await load();
  check(textOf('presence-examples').includes('examples unavailable') && !textOf('presence-examples').includes('Roster status only'), 'Presence review refuses a non-synthetic envelope and clears previous cases');
  fixture.presenceExamples = structuredClone(originalPresenceExamples);
  fixture.presenceExamples.rows[0].scenario = '<img src="https://offline.invalid/never">';
  fixture.presenceExamples.rows.push(null);
  await load();
  check(textOf('presence-examples').includes('Example coverage Unknown') && textOf('presence-examples').includes('<img') && document.querySelectorAll('#presence-examples img').length === 0, 'Partial presence examples retain usable text while omitting malformed rows');
  fixture.presenceExamples = originalPresenceExamples;
  await load();
  check(document.querySelectorAll('#presence-examples .row').length === 3 && !textOf('presence-examples').includes('Example coverage Unknown'), 'Presence examples recover from the current snapshot only');
  const sectionOrder = ['overview', 'roster', 'ffxi', 'learning', 'evidence', 'operations', 'models', 'notes'];
  const sectionLinks = [...document.querySelectorAll('.workspace-nav a')];
  const sectionRequests = requests.length;
  check(sectionLinks.map(link => link.id).join(',') === sectionOrder.map(key => 'nav-' + key).join(',') && sectionLinks.every(link => link.tabIndex === 0), 'Sidebar DOM Tab candidates follow all eight sections without positive tabindex');
  for (const link of sectionLinks) {
    link.focus();
    check(document.activeElement === link, `Sidebar programmatic focus reaches ${link.id}`);
    link.click(); // DOM activation only; native Enter is checked by the separate browser runner.
    const target = document.querySelector(link.getAttribute('href'));
    await settle(() => document.activeElement === target);
    check(target.tabIndex === -1 && link.getAttribute('aria-current') === 'location' && sectionLinks.filter(item => item.getAttribute('aria-current') === 'location').length === 1, `Sidebar DOM activation focuses ${target.id} and selects only its link`);
  }
  check(requests.length === sectionRequests, 'Sidebar DOM navigation does not fetch data');
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
  const comparisonRequests = requests.length;
  const sampleGroups = [...document.querySelectorAll('#model-comparison details')];
  check(sampleGroups.length === 2 && sampleGroups.every(group => !group.open), 'Each exact model group has a collapsed sample review');
  sampleGroups[0].querySelector('summary').click();
  check(sampleGroups[0].open, 'DOM summary activation opens the sample review; native keyboard is separate');
  const sampleRows = [...sampleGroups[0].querySelectorAll('tbody tr')];
  check(sampleRows.length === 2 && sampleRows[0].textContent.includes('2026-01-01T12:00:00Z') && [...sampleRows[0].querySelectorAll('td')].map(cell => cell.textContent).join('|') === '2026-01-01T12:00:00Z|0|0|Unknown', 'Sample review preserves supplied time, zero latency/cost and Unknown quality');
  check(sampleGroups[0].querySelectorAll('th[scope="col"]').length === 5 && sampleGroups[0].querySelectorAll('th[scope="row"]').length === 2 && sampleGroups[0].querySelector('.model-samples').tabIndex === 0, 'Sample table has scoped headers and a focusable scroll region');
  document.getElementById('model-call-availability').value = 'complete';
  document.getElementById('model-call-availability').dispatchEvent(new Event('change', {bubbles:true}));
  check(document.querySelectorAll('#model-comparison details').length === 0 && textOf('model-comparison').includes('No supplied rows in this selection') && !textOf('model-comparison').includes('No complete model/purpose/source identities'), 'Empty metric selection removes sample groups without claiming missing identities');
  document.getElementById('model-call-availability').value = '';
  document.getElementById('model-call-availability').dispatchEvent(new Event('change', {bubbles:true}));
  check(document.querySelectorAll('#model-comparison tbody tr').length === 3 && requests.length === comparisonRequests, 'Reset restores only loaded sample rows without a request');
  const originalModelCalls = structuredClone(fixture.modelCalls);
  const sampleText = '<img src="https://offline.invalid/forbidden" onerror="throw 1">';
  fixture.modelCalls = [{model:'Text fixture', purpose:'Review', source:sampleText, observedAt:sampleText, latencyMs:null}];
  await load();
  check(textOf('model-comparison').includes(sampleText) && document.querySelectorAll('#model-comparison img, #model-comparison script').length === 0, 'Sample provenance and observation labels remain text, not markup or resources');
  fixture.modelCalls = null;
  await load();
  check(document.querySelectorAll('#model-comparison tbody tr').length === 0 && textOf('model-comparison').includes('Comparison unavailable'), 'Unavailable refresh removes old sample rows and exposes Unknown coverage');
  fixture.modelCalls = originalModelCalls;
  await load();
  check(document.querySelectorAll('#model-comparison tbody tr').length === 3 && !textOf('model-comparison').includes(sampleText), 'Recovery restores only the new snapshot sample rows');
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
  const originalAudit = structuredClone(fixture.audit);
  fixture.audit = [{actor:'Synthetic operator', action:'Fixture retained action', scope:'Example only', result:'Not applied'}, null, 'WITHHELD_MALFORMED_AUDIT'];
  await load();
  check(textOf('audit').includes('Fixture retained action') && textOf('audit').includes('Malformed rows were omitted') && textOf('audit-count').includes('Showing 1 of Unknown total') && !textOf('audit').includes('WITHHELD_MALFORMED_AUDIT'), 'Partial audit retains usable examples with Unknown total and omits malformed payloads');
  const partialAuditRequests = requests.length;
  document.getElementById('audit-search').value = 'not in fixture';
  document.getElementById('audit-search').dispatchEvent(new Event('input', {bubbles:true}));
  check(textOf('audit-count').includes('Showing 0 of Unknown total') && textOf('audit').includes('No matching audit examples') && textOf('audit').includes('coverage unknown'), 'Audit search keeps partial coverage visible even with no matches');
  document.getElementById('audit-reset').click();
  check(textOf('audit').includes('Fixture retained action') && requests.length === partialAuditRequests, 'Audit reset restores usable partial rows without a request');
  fixture.audit = [null, []];
  await load();
  check(textOf('audit').includes('No usable audit examples') && textOf('audit-count').includes('Showing 0 of Unknown total') && !textOf('audit').includes('Fixture retained action'), 'All-malformed audit is Unknown, not a known empty log');
  fixture.audit = null;
  await load();
  check(textOf('audit-count').includes('count unknown') && !textOf('audit').includes('Fixture retained action'), 'Unavailable audit refresh clears retained examples');
  fixture.audit = originalAudit;
  await load();
  check(!textOf('audit').includes('Malformed rows were omitted') && !textOf('audit-count').includes('Unknown total'), 'Complete audit recovery removes the partial warning');
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
  document.getElementById('learning-evidence').closest('details').open = true;
  document.getElementById('learning-evidence-preview').click();
  check(textOf('learning-evidence').includes('Synthetic mapping preview'), 'Preview clearly labeled synthetic');
  check(['supported (synthetic)', 'missing (synthetic)', 'conflicting (synthetic)'].every(s => textOf('learning-evidence').includes(s)), 'Preview displays three distinct synthetic states');
  document.getElementById('learning-evidence-selected').click();
  check(textOf('learning-evidence').includes('Evidence review') && !textOf('learning-evidence').includes('Synthetic mapping preview'), 'Restore returns to the selected fixture task');
  document.getElementById('clear-learning').click();
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
  const draftPreview = document.getElementById('bot-draft-preview');
  document.getElementById('bot-draft-section').open = true;
  const draftOrder = ['bot-draft-goals', 'bot-draft-personality', 'bot-draft-preview', 'bot-draft-cancel'];
  const draftStops = [...draftForm.querySelectorAll('textarea,button,input,select')].filter(node => !node.matches(':disabled') && node.tabIndex >= 0);
  check(JSON.stringify(draftStops.map(node => node.id)) === JSON.stringify(draftOrder) && draftStops.every(node => node.tabIndex === 0), 'Draft DOM Tab-order candidates follow field/preview/discard order without positive tabindex');
  for (const shiftKey of [false, true]) {
    for (const id of shiftKey ? [...draftOrder].reverse() : draftOrder) {
      const node = document.getElementById(id); node.focus();
      const event = new KeyboardEvent('keydown', {key:'Tab', shiftKey, bubbles:true, cancelable:true});
      node.dispatchEvent(event);
      check(document.activeElement === node && !event.defaultPrevented && !event.isTrusted,
        `Draft ${shiftKey ? 'reverse' : 'forward'} programmatic focus ${id}; untrusted Tab is not native navigation`);
    }
  }
  check(draftGoals.labels.length === 1 && draftPersonality.labels.length === 1 && draftGoals.getAttribute('aria-describedby').includes('bot-draft-status'), 'Draft fields have associated labels and validation status');
  draftGoals.value = 'Example goal: report observations without claiming progress';
  draftPersonality.value = 'Example personality: patient';
  draftPreview.focus();
  draftForm.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));
  check(document.activeElement === draftPreview, 'Successful draft review preserves its preview-button DOM focus');
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
  check(document.activeElement === draftGoals, 'Invalid goals receive DOM focus for correction');
  draftGoals.value = 'Fixture goal'; draftPersonality.value = 'x'.repeat(501);
  draftForm.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));
  check(document.activeElement === draftPersonality && draftPersonality.getAttribute('aria-invalid') === 'true', 'Invalid personality receives DOM focus for correction');
  document.getElementById('bot-draft-cancel').click();
  check(draftGoals.value === '' && draftPersonality.value === '', 'Discard removes local draft text');
  draftForm.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));
  check(document.activeElement === draftGoals && textOf('bot-draft-result') === '', 'Empty draft returns DOM focus to goals without a review');
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
  check(exportLink.getAttribute('download') === 'roster-gap-row-2.json', 'Gap download filename identifies the selected snapshot row without a path');
  const blobBytes = new Uint8Array(await exportBlob.arrayBuffer());
  const copyField = document.querySelector('#roster-gap-detail textarea');
  const copyBytes = new Uint8Array(await new Blob([copyField.value]).arrayBuffer());
  check(copyField.readOnly && blobBytes.length > 0 && blobBytes.length === copyBytes.length && blobBytes.every((byte, index) => byte === copyBytes[index]), 'Gap Blob bytes equal the read-only JSON copy field; no file save claimed');
  const previousExportUrl = exportLink.getAttribute('href');
  check(exportBlob.size <= 256 * 1024, 'Gap Blob is within the local JSON report limit');
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
  check(!gapBlobs.has(previousExportUrl), 'Refreshing the snapshot revokes the previous gap Blob URL');
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
  const completeAssignments = structuredClone(fixture.assignmentHistory);
  fixture.assignmentHistory.push(null, {botId:' ', requested:'WITHHELD_UNSCOPED_ASSIGNMENT'});
  await load();
  check(textOf('assignment-count').includes('Page 1 of 3') && textOf('assignment-count').includes('loaded total Unknown') && textOf('assignment-history').includes('Malformed or unscoped') && !textOf('assignment-history').includes('WITHHELD_UNSCOPED_ASSIGNMENT') && !textOf('assignment-history').includes('OTHER_BOT'), 'Partial assignments retain only exact-bot scoped rows with Unknown total');
  const partialPagingRequests = requests.length;
  nextAssignment.click();
  check(textOf('assignment-count').includes('Showing 11–20 of 23') && textOf('assignment-history').includes('coverage unknown') && requests.length === partialPagingRequests, 'Partial assignment paging keeps its warning and makes no request');
  const assignmentBots = structuredClone(fixture.bots);
  fixture.bots.push({...fixture.bots[0]});
  await load();
  check(textOf('assignment-count').includes('identity is ambiguous') && !textOf('assignment-history').includes('Synthetic model'), 'Duplicate selected bot IDs withhold assignment rows despite usable history');
  fixture.bots = assignmentBots;
  fixture.assignmentHistory = [null, {botId:'', requested:'WITHHELD_UNSCOPED_ASSIGNMENT'}];
  await load();
  check(textOf('assignment-count').includes('0 usable assignment examples') && textOf('assignment-count').includes('loaded total Unknown') && nextAssignment.getAttribute('aria-disabled') === 'true' && previousAssignment.getAttribute('aria-disabled') === 'true', 'All-unusable assignments clear old pages without claiming a complete empty history');
  fixture.assignmentHistory = completeAssignments;
  await load();
  check(textOf('assignment-count').includes('Page 1 of 3') && !textOf('assignment-history').includes('coverage unknown') && !textOf('assignment-count').includes('loaded total Unknown'), 'Complete assignment recovery restores pages and clears the partial warning');
  document.getElementById('data-source').value = 'hub';
  document.getElementById('data-source').dispatchEvent(new Event('change'));
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
  fixture.botActivity = activityFixture;
  fixture.baselineConformance = baselineFixture;
  document.getElementById('bot-reset').click();
  await load();
  check(textOf('bot-activity-coverage') === activityCoverage && textOf('baseline-conformance') === baselineText
    && document.querySelectorAll('#bot-activity-sources .bot-source').length === 3,
    'Final preview restores the full bot exports and parity evidence after inspector scenarios');
  const paritySample = document.getElementById('parity-sample');
  const paritySampleNote = document.getElementById('parity-sample-note');
  paritySample.addEventListener('change', () => {
    const partialSource = paritySample.value === 'partial' ? parityPartialReadinessSource
      : paritySample.value === 'partial-ffxi' ? parityPartialFfxiReadinessSource : null;
    const readiness = paritySample.value === 'readiness' || partialSource !== null;
    const activity = structuredClone(activityFixture);
    if (readiness) activity.sources = activity.sources.map(source =>
      structuredClone(source.id === partialSource?.id ? partialSource
        : parityReadinessSources.find(sample => sample.id === source.id) || source));
    fixture.botActivity = activity;
    currentSnapshot.botActivity = structuredClone(activity);
    renderBotActivity();
    paritySampleNote.textContent = partialSource
      ? `Synthetic incomplete ${partialSource.id === 'ffxi-lsb' ? 'FFXI' : 'SWTOR'} import; not live evidence. Other source data and parity tracker evidence are unchanged from complete readiness.`
      : readiness
      ? 'Synthetic FFXI post-H1 and SWTOR writer samples; not live evidence. Parity tracker evidence is unchanged.'
      : 'Recorded export snapshots and schema examples restored. Check each source label; nothing here is live.';
  });
  paritySample.disabled = false;
  const parityRequests = requests.length;
  paritySample.value = 'readiness';
  paritySample.dispatchEvent(new Event('change', {bubbles: true}));
  const readinessPanels = [...document.querySelectorAll('#bot-activity-sources .bot-source')];
  check(readinessPanels.slice(0, 2).every((panel, index) =>
    panel.textContent.includes(parityReadinessSources[index].label)
    && panel.textContent.includes(`Imported log rows: ${parityReadinessSources[index].coverage.records}`)
    && panel.textContent.includes('Synthetic readiness sample; not live evidence.')),
    'Readiness selector renders separately labeled FFXI and SWTOR fixtures through the real activity view');
  check(readinessPanels[0].textContent.includes('Human-feel signals:')
    && readinessPanels[1].textContent.includes('rotation_pick affliction')
    && readinessPanels[1].textContent.includes('NO_LISTENER 1')
    && readinessPanels[1].textContent.includes('NOT_AI 1'),
    'Readiness view exposes FFXI timing measurements and SWTOR rotation/chat-drop samples');
  const lossRow = [...readinessPanels[1].querySelectorAll('.row')]
    .find(row => row.firstElementChild.textContent === 'bot_events · swtor');
  const lossEvents = lossRow.querySelector('details');
  lossEvents.open = true;
  await settle(() => lossEvents.children.length === 2);
  check(readinessPanels[1].textContent.includes('Omitted malformed: 0')
    && readinessPanels[1].textContent.includes('Producer-reported log loss: 1 LOG_DROPPED rows.')
    && lossEvents.textContent.includes('Producer-reported dropped rows: 27 (this report; not summed)'),
    'SWTOR producer-reported log loss stays visible and separate from reader omissions');
  check(textOf('baseline-conformance') === baselineText
    && textOf('parity-sample-note').includes('not live evidence'),
    'Synthetic readiness samples do not promote or replace parity evidence');
  const completeReadiness = structuredClone(currentSnapshot.botActivity);
  paritySample.value = 'partial';
  paritySample.dispatchEvent(new Event('change', {bubbles: true}));
  const partialPanel = [...document.querySelectorAll('#bot-activity-sources .bot-source')][1];
  check(partialPanel.textContent.includes(parityPartialReadinessSource.label)
    && partialPanel.textContent.includes('Synthetic incomplete readiness sample; not live evidence.')
    && partialPanel.textContent.includes('Imported log rows: 16')
    && partialPanel.textContent.includes('Omitted malformed: 1')
    && partialPanel.textContent.includes('Omitted by reason: invalid_json 1')
    && partialPanel.textContent.includes('rotation_pick affliction')
    && !partialPanel.textContent.includes('OMITTED_SYNTHETIC_ROW'),
    'Incomplete SWTOR sample keeps valid events and exposes one rejected row without rendering malformed content');
  const partialLossRow = [...partialPanel.querySelectorAll('.row')]
    .find(row => row.firstElementChild.textContent === 'bot_events · swtor');
  const partialLossEvents = partialLossRow.querySelector('details');
  partialLossEvents.open = true;
  await settle(() => partialLossEvents.children.length === 2);
  check(partialPanel.textContent.includes('Producer-reported log loss: 1 LOG_DROPPED rows.')
    && partialLossEvents.textContent.includes('Producer-reported dropped rows: 27 (this report; not summed)'),
    'One malformed reader omission is separate from the producer report of 27 dropped rows');
  check(currentSnapshot.botActivity.sources.every((source, index) => source.id === parityPartialReadinessSource.id
      || JSON.stringify(source) === JSON.stringify(completeReadiness.sources[index]))
    && textOf('baseline-conformance') === baselineText && requests.length === parityRequests,
    'Incomplete SWTOR selection leaves FFXI, WoW, Vanilla and parity evidence unchanged without requests');
  paritySample.value = 'readiness';
  paritySample.dispatchEvent(new Event('change', {bubbles: true}));
  const recoveredPanel = [...document.querySelectorAll('#bot-activity-sources .bot-source')][1];
  check(JSON.stringify(currentSnapshot.botActivity) === JSON.stringify(completeReadiness)
    && recoveredPanel.textContent.includes('Omitted malformed: 0')
    && !recoveredPanel.textContent.includes('invalid_json')
    && recoveredPanel.textContent.includes('Producer-reported log loss: 1 LOG_DROPPED rows.')
    && requests.length === parityRequests,
    'Complete readiness recovery removes the reader omission while preserving valid events and producer loss');
  paritySample.value = 'partial-ffxi';
  paritySample.dispatchEvent(new Event('change', {bubbles: true}));
  const partialFfxiPanel = [...document.querySelectorAll('#bot-activity-sources .bot-source')][0];
  check(partialFfxiPanel.textContent.includes(parityPartialFfxiReadinessSource.label)
    && partialFfxiPanel.textContent.includes('Synthetic incomplete readiness sample; not live evidence.')
    && partialFfxiPanel.textContent.includes('Imported log rows: 52')
    && partialFfxiPanel.textContent.includes('Omitted malformed: 1')
    && partialFfxiPanel.textContent.includes('Unrecognized lines: 1')
    && partialFfxiPanel.textContent.includes('Ignored lines: 1')
    && !partialFfxiPanel.textContent.includes('synthetic_unknown')
    && !partialFfxiPanel.textContent.includes('synthetic unrelated fixture line'),
    'Incomplete FFXI sample separates malformed, unrecognized and unrelated lines without displaying them as events');
  const completeFfxi = completeReadiness.sources.find(source => source.id === 'ffxi-lsb');
  const partialFfxi = currentSnapshot.botActivity.sources.find(source => source.id === 'ffxi-lsb');
  check(JSON.stringify(partialFfxi.bots) === JSON.stringify(completeFfxi.bots)
    && partialFfxiPanel.textContent.includes('readya') && partialFfxiPanel.textContent.includes('readyb')
    && partialFfxiPanel.textContent.includes(`Observed event range: ${completeFfxi.coverage.from} to ${completeFfxi.coverage.to}`),
    'Skipped FFXI lines preserve valid bots, timing measurements and accepted event bounds');
  check(currentSnapshot.botActivity.sources.every((source, index) => source.id === 'ffxi-lsb'
      || JSON.stringify(source) === JSON.stringify(completeReadiness.sources[index]))
    && textOf('baseline-conformance') === baselineText && requests.length === parityRequests,
    'Incomplete FFXI selection leaves SWTOR, WoW, Vanilla and parity evidence unchanged without requests');
  paritySample.value = 'readiness';
  paritySample.dispatchEvent(new Event('change', {bubbles: true}));
  const recoveredFfxiPanel = [...document.querySelectorAll('#bot-activity-sources .bot-source')][0];
  check(JSON.stringify(currentSnapshot.botActivity) === JSON.stringify(completeReadiness)
    && recoveredFfxiPanel.textContent.includes('Omitted malformed: 0')
    && recoveredFfxiPanel.textContent.includes('Unrecognized lines: 0')
    && recoveredFfxiPanel.textContent.includes('Ignored lines: 0')
    && requests.length === parityRequests,
    'Complete FFXI readiness recovery clears all three skipped-line counts and restores the exact source data');
  paritySample.value = 'exports';
  paritySample.dispatchEvent(new Event('change', {bubbles: true}));
  check(JSON.stringify(currentSnapshot.botActivity) === JSON.stringify(activityFixture)
    && textOf('baseline-conformance') === baselineText && requests.length === parityRequests,
    'Switching back restores the exact prior imports without requests or parity changes');
  installAssignmentKeyboardCheck({document,
    prepare: async () => {
      fixture.assignmentHistory = assignmentFixtures.populated.map(row => ({...row, botId: row.botId === 'fixture-bot' ? 'offline-inspector-bot' : row.botId}));
      document.getElementById('data-source').value = 'mock';
      await load(); await settle(() => !sourceLoading && !bridgePending);
      document.getElementById('clear-bot').click();
      inspectBot('offline-inspector-bot');
    },
    page: () => assignmentPages === 3 ? assignmentPage + 1 : null,
    requests: () => requests.length,
  });
  const keyboardStart = document.getElementById('keyboard-start');
  keyboardStart.focus();
  for (const key of ['Tab', 'Enter', ' ', 'Escape']) {
    for (const type of ['keydown', 'keyup']) {
      const event = new KeyboardEvent(type, {key, bubbles:true, cancelable:true});
      keyboardStart.dispatchEvent(event);
      check(!event.isTrusted && document.documentElement.dataset.keyboardPlaytest === 'not-run',
        `Untrusted ${type} ${key === ' ' ? 'Space' : key} cannot produce native keyboard evidence`);
    }
  }
  const beforeProgressLinks = requests.length;
  for (const location of ['overview', 'assignment']) {
    document.getElementById('preview-progress-log-' + location).click();
    check(document.getElementById('harness-results').open && document.activeElement.id === 'harness-status'
      && requests.length === beforeProgressLinks, `Preview ${location} diagnostics open and focus the check log without a request`);
    document.getElementById('harness-results').open = false;
  }
  // Scripted inspection navigates through several panels. Start the owner's review
  // with matching focus, section cue and fragment, without adding a history entry.
  history.replaceState(null, '', '#view-overview');
  focusWorkspaceTarget('view-overview');
  check(location.hash === '#view-overview' && document.activeElement.id === 'view-overview'
    && document.getElementById('nav-overview').getAttribute('aria-current') === 'location',
    'Preview landing fragment, DOM focus and selected section agree on Overview');
  if (!previewProgress.finish()) throw new Error('Local preview check limit reached; reload to retry.');
  document.getElementById('harness-status').textContent = 'PASS — automatic DOM checks completed with synthetic data. Native keyboard check is separate and has NOT RUN.';
  document.documentElement.dataset.playtest = 'passed';
} catch (error) {
  previewProgress.fail();
  document.getElementById('harness-status').textContent = 'FAIL — ' + error.message;
  document.documentElement.dataset.playtest = 'failed';
}
