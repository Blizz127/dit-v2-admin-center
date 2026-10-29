const form = document.querySelector('#login');
const error = document.querySelector('#error');
const workspace = document.querySelector('#workspace');
let currentSnapshot = null;
let loadedSource = null;
let sourceLoading = false;
let requestVersion = 0;
let traceVersion = 0;
let healthVersion = 0;
let interactionVersion = 0;
let sessionVersion = 0;
let selectedBotId = null;
let assignmentBotId = null;
let assignmentPage = 0;
let assignmentPages = 0;
const assignmentPageSize = 10;
let correlationFilter = '';
let bridgePending = false;
let selectedLearningId = null;
let token = sessionStorage.getItem('dit-admin-token') || '';
function panelSessionCurrent(requestToken, session) {
  return !workspace.hidden && token === requestToken && sessionVersion === session;
}
function resetPanelSession() {
  sessionVersion++;
  currentSnapshot = null; loadedSource = null;
  selectedBotId = null; selectedLearningId = null;
  assignmentBotId = null; assignmentPage = 0; assignmentPages = 0;
  assignmentNavigation('Select a bot to view loaded assignment examples.');
  for (const [id, prompt] of [['bot-inspector', 'Select a bot to inspect.'],
                             ['learning-inspector', 'Select a learning need for details.']]) {
    const panel = document.getElementById(id);
    panel.replaceChildren(); panel.textContent = prompt;
  }
  for (const id of ['interaction-status', 'hub-health', 'hub-trace', 'bridge-status', 'ffxi-focus-bridge']) {
    const panel = document.getElementById(id);
    panel.replaceChildren(); panel.textContent = 'Not requested in this session.';
  }
}
function item(parent, title, detail, meta) {
  const row = document.createElement('div'); row.className = 'row';
  const heading = document.createElement('strong'); heading.textContent = title;
  const text = document.createElement('p'); text.textContent = detail;
  const small = document.createElement('small'); small.textContent = meta || '';
  row.append(heading, text, small); parent.append(row);
}
function renderInteraction(data, source) {
  const panel = document.querySelector('#interaction-status');
  panel.replaceChildren();
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('unavailable');
  const switches = data.switches && typeof data.switches === 'object' && !Array.isArray(data.switches) ? data.switches : {};
  const rows = observationRows(data.bots, panel);
  const count = Array.isArray(data.bots) && rows.length === data.bots.length ? rows.length : 'Unknown count of';
  const flag = value => value === true ? 'On' : value === false ? 'Off' : 'Unknown';
  item(panel, source, routingText(data.coverage), `Fetched: ${routingText(data.fetchedAt, 'unknown')} · This view cannot change switches or send orders`);
  item(panel, 'Reported interaction switches', `Contract: ${flag(switches.contract)} · Natural orders: ${flag(switches.naturalOrders)} · Self claims: ${flag(switches.selfClaims)}`, 'Reported values only; no model-routing or game controls are connected here');
  item(panel, 'Coverage', `${count} returned FFXI actors · Truncated: ${data.truncated === true ? 'Yes' : data.truncated === false ? 'No' : 'Unknown'}`, `Hub freshness threshold: ${metricNumber(data.freshForSeconds) ? data.freshForSeconds + ' s' : 'unknown'} · Freshness is reported at fetch time and may be stale now`);
  if (switches.contract !== true) {
    item(panel, 'Current bot state unavailable', switches.contract === false ? 'The contract is reported off; no current bot inventory is inferred.' : 'Contract collection state is unknown.', 'An empty view does not establish healthy or absent bots');
    return;
  }
  if (!rows.length) item(panel, 'No FFXI actor records returned', 'Coverage is unknown.', 'No outcome or absence is inferred');
  const freshness = value => value === true ? 'Reported fresh' : value === false ? 'Reported stale' : 'Unknown';
  rows.forEach(b => item(panel, routingText(b.actorKey),
    `Reconciled view: ${freshness(b.fresh)} · Activity: ${b.fresh === true ? routingText(b.activity) : 'Unknown'} · Raw snapshot: ${freshness(b.snapshotFresh)}`,
    `Scope: ${routingText(b.caller)} / ${routingText(b.serverInstanceId)} · Raw state source: ${routingText(b.source, 'unknown')} · Snapshot observed: ${routingText(b.observedAt, 'unknown')} · Hub-reported snapshot age: ${metricNumber(b.ageSeconds) ? b.ageSeconds + ' s' : 'unknown'} · No roster identity join or delivery inference`));
}
async function loadInteraction() {
  if (!token || workspace.hidden) return;
  const requestToken = token, session = sessionVersion;
  const id = ++interactionVersion;
  const panel = document.querySelector('#interaction-status');
  panel.replaceChildren();
  if (document.querySelector('#data-source').value !== 'hub' || sourceLoading || loadedSource !== 'hub') {
    panel.textContent = 'Load the selected hub source successfully before requesting this read-only check. Synthetic preview is available separately.';
    return;
  }
  panel.textContent = 'Checking candidate FFXI interaction view…';
  try {
    const response = await fetch('/api/interaction', {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    if (id !== interactionVersion || !panelSessionCurrent(requestToken, session)) return;
    renderInteraction(data, 'Hub interaction response · candidate contract, deployed revision unverified');
  } catch (_) {
    if (id === interactionVersion && panelSessionCurrent(requestToken, session)) { panel.replaceChildren(); panel.textContent = 'Interaction view unavailable; the hub may be unconfigured or may not implement this candidate endpoint. Switches and bot state remain unknown.'; }
  }
}
function previewInteraction() {
  interactionVersion++;
  renderInteraction({switches: {contract: true, naturalOrders: false, selfClaims: false},
    coverage: 'Synthetic illustration only. No hub read, provider call, switch change or game action.',
    fetchedAt: null, freshForSeconds: 30, truncated: false, bots: [
      {actorKey: 'Example current view', caller: 'fixture-adapter', serverInstanceId: 'fixture-server', fresh: true, snapshotFresh: false,
       activity: 'waiting', source: 'native snapshot', observedAt: '2026-01-01T00:00:00Z', ageSeconds: 45},
      {actorKey: 'Example stale view', caller: 'fixture-adapter', serverInstanceId: 'fixture-server', fresh: false, snapshotFresh: false,
       activity: null, source: 'native snapshot', observedAt: '2026-01-01T00:00:00Z', ageSeconds: 45}
    ]}, 'Synthetic interaction preview · not live');
}
async function loadHubHealth() {
  if (!token || workspace.hidden) return;
  const requestToken = token, session = sessionVersion;
  const id = ++healthVersion;
  const panel = document.querySelector('#hub-health');
  panel.replaceChildren();
  if (document.querySelector('#data-source').value !== 'hub') { panel.textContent = 'Select configured hub data before requesting this read-only check.'; return; }
  if (sourceLoading || loadedSource !== 'hub') { panel.textContent = 'Load the selected hub source successfully before requesting this read-only check.'; return; }
  panel.textContent = 'Checking hub services…';
  try {
    const response = await fetch('/api/hub-health', {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    if (id !== healthVersion || !panelSessionCurrent(requestToken, session)) return;
    panel.replaceChildren();
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('unavailable');
    const rows = observationRows(data.services, panel);
    item(panel, 'Hub service health', routingText(data.coverage), `${routingText(data.source)} · Fetched: ${routingText(data.fetchedAt)} · Snapshot may be stale`);
    if (!rows.length) item(panel, 'No matching service records', 'Coverage is unknown.', 'Empty data does not establish healthy services.');
    rows.forEach(s => item(panel, `${routingText(s.game)} · ${routingText(s.label)}`, routingText(s.state), `Observed: ${routingText(s.observedAt, 'unknown')} · Service state is not bot presence`));
  } catch (_) { if (id === healthVersion && panelSessionCurrent(requestToken, session)) panel.textContent = 'Hub service health unavailable; current state is unknown.'; }
}
async function loadBridge() {
  if (bridgePending || !token || workspace.hidden) return;
  bridgePending = true;
  const requestToken = token, session = sessionVersion;
  const panel = document.querySelector('#bridge-status');
  try {
    const response = await fetch('/api/bridge-status', {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const received = await response.json();
    if (!panelSessionCurrent(requestToken, session)) return;
    if (!received || typeof received !== 'object' || Array.isArray(received)) throw new Error('unavailable');
    const data = Object.fromEntries(['unit', 'substate', 'result', 'marker', 'markerReason', 'source', 'observedAt']
      .map(key => [key, routingText(received[key], 'unknown')]));
    panel.replaceChildren();
    item(panel, `Unit: ${data.unit} · ${data.substate}`, `Result: ${data.result} · Fault marker: ${data.marker} · Classification: ${data.markerReason || 'unknown'}`, `${data.source} · Observed: ${data.observedAt || 'unknown'} · Marker absence does not prove delivery`);
    const focus = document.querySelector('#ffxi-focus-bridge');
    focus.replaceChildren();
    item(focus, `Bridge: ${data.unit} · ${data.substate}`, `Fault marker: ${data.marker} · Classification: ${data.markerReason || 'unknown'}`, `${data.source} · Observed: ${data.observedAt || 'unknown'} · Not proof of delivery`);
  } catch (_) {
    if (!panelSessionCurrent(requestToken, session)) return;
    panel.replaceChildren();
    panel.textContent = 'Bridge status unknown; read-only observation unavailable.';
    const focus = document.querySelector('#ffxi-focus-bridge');
    focus.replaceChildren();
    focus.textContent = 'Bridge observation unknown; delivery remains unverified.';
  }
  finally { bridgePending = false; }
}
function observationRows(value, panel) {
  const rows = Array.isArray(value) ? value.filter(row => row && typeof row === 'object' && !Array.isArray(row)) : [];
  if (!Array.isArray(value) || rows.length !== value.length || !value.length)
    item(panel, 'Observation coverage', 'Unknown', 'Missing, empty or malformed records do not establish current state. Usable supplied rows follow.');
  return rows;
}
function renderCoordinatorPanels() {
  const panel = id => { const target = document.getElementById(id); target.replaceChildren(); return target; };
  const leads = panel('leads');
  observationRows(currentSnapshot.leads, leads).forEach(l => item(leads,
    `${routingText(l.name)} · ${routingText(l.scope)}`, routingText(l.status),
    `${routingText(l.source)} · Observed: ${routingText(l.observedAt)}`));
  const summary = panel('lead-summary'), monitoring = panel('lead-monitoring');
  const monitors = observationRows(currentSnapshot.leadMonitoring, summary);
  observationRows(currentSnapshot.leadMonitoring, monitoring);
  monitors.forEach(m => {
    item(summary, routingText(m.lead), `Stall: ${routingText(m.stall)} · Lead quota: ${routingText(m.quota)}`,
      `${routingText(m.stallReason, 'No watcher data')} · ${routingText(m.quotaReason, 'No per-lead quota data')} · Shared provider pool: ${routingText(m.poolCapacity)} (${routingText(m.poolReason)})`);
    item(monitoring, routingText(m.lead), `Stall: ${routingText(m.stall)} · Quota: ${routingText(m.quota)}`,
      `Provider: ${routingText(m.provider)} · ${routingText(m.binding, 'Current lead binding unverified')} · Binding observed: ${routingText(m.bindingObservedAt)} · Session activity: ${routingText(m.sessionActivity)} (not proof of work or a stall) · ${routingText(m.stallReason)} · ${routingText(m.quotaReason)} · Provider pool: ${routingText(m.poolCapacity)} (${routingText(m.poolReason)})`);
  });
  const activity = panel('lead-activity');
  observationRows(currentSnapshot.leadActivity, activity).forEach(a => item(activity, routingText(a.lead),
    `Task: ${routingText(a.taskStatus)} · ${routingText(a.taskSummary)}`,
    `Task updated: ${routingText(a.taskUpdatedAt)} · ${routingText(a.taskSource)} · Checkout HEAD commit: ${routingText(a.commitAt)} · ${routingText(a.commitSource)}`));
  const nudges = panel('nudge-history');
  observationRows(currentSnapshot.nudgeHistory, nudges).forEach(lead => {
    item(nudges, routingText(lead.lead), routingText(lead.coverage), 'Read-only coordinator metadata');
    const group = nudges.lastElementChild;
    observationRows(lead.nudges, group).forEach(n => {
      const signal = n.resumeSignal;
      const heuristic = signal && typeof signal === 'object' && !Array.isArray(signal)
        && metricNumber(signal.seconds) && typeof signal.label === 'string' && signal.label.trim()
        ? `${signal.label}: ${signal.seconds} s at ${routingText(signal.observedAt)}` : 'Tool activity heuristic: Unknown';
      item(group, `Nudge · ${routingText(n.messageStatus)}`,
        `Created: ${routingText(n.createdAt)} · Delivered: ${routingText(n.deliveredAt)} · Reply: ${routingText(n.repliedAt)}`,
        `Time to reply: ${metricNumber(n.replySeconds) ? n.replySeconds + ' s' : 'Unknown'} · Time to resume: unknown · ${heuristic} · ${routingText(n.source)}`);
    });
  });
  const markers = panel('session-markers');
  observationRows(currentSnapshot.sessionMarkers, markers).forEach(report => {
    item(markers, routingText(report.lead), routingText(report.coverage), 'Heuristic; no rollout text is displayed');
    observationRows(report.markers, markers).forEach(m => item(markers, routingText(m.kind), routingText(m.observedAt),
      `${routingText(m.source)} · Historical; current state unknown`));
  });
}
function renderQuotaHistory() {
  const panel = document.querySelector('#quota-history');
  const window = document.querySelector('#quota-window').value;
  panel.replaceChildren();
  const records = observationRows(currentSnapshot.quotaHistory, panel).filter(q => !window || q.window === window);
  if (!records.length) item(panel, 'No matching observations', 'Quota history for this filter is unknown.', 'No account refresh is performed.');
  records.forEach(q => item(panel, `Account ${routingText(q.account)} · ${routingText(q.window)}`,
    `Remaining: ${metricNumber(q.remainingPercent) && q.remainingPercent <= 100 ? q.remainingPercent + '%' : 'Unknown'} at observation`,
    `Observed: ${routingText(q.observedAt)} · Cached Codex state; may be stale`));
}
function renderLeadTimeline() {
  const panel = document.querySelector('#lead-timeline');
  const filter = document.querySelector('#timeline-kind').value;
  const kinds = {watcher: ['Watcher alert', 'Watcher classification'], task: ['Task status'], session: ['Session activity'], commit: ['Checkout commit']};
  panel.replaceChildren();
  observationRows(currentSnapshot.leadTimeline, panel).forEach(t => {
    item(panel, routingText(t.lead), routingText(t.coverage), `${routingText(t.watchCoverage)} · ${routingText(t.commitCoverage)}`);
    const group = panel.lastElementChild;
    const events = observationRows(t.events, group).filter(e => !filter || (kinds[filter] || []).includes(e.kind));
    if (!events.length) item(group, 'No matching evidence', 'This filter has no records in the available history.', 'Current activity remains unknown.');
    events.forEach(e => item(group, `${routingText(e.kind)}: ${routingText(e.status)}`, routingText(e.at), routingText(e.source)));
  });
}
function recordsForId(rows, id) {
  if (!Array.isArray(rows) || typeof id !== 'string' || !id.trim()) return [];
  return rows.filter(row => row && typeof row === 'object' && !Array.isArray(row) && row.id === id);
}
function uniqueRecord(rows, id) {
  const matches = recordsForId(rows, id);
  return matches.length === 1 ? matches[0] : null;
}
function renderIssueCoverage() {
  const panel = document.querySelector('#issue-coverage');
  panel.replaceChildren();
  const groups = new Map();
  currentSnapshot.issues.forEach(issue => {
    const scope = typeof issue.scope === 'string' && issue.scope ? issue.scope : 'Unknown';
    groups.set(scope, (groups.get(scope) || 0) + 1);
  });
  if (!groups.size) { item(panel, 'No loaded issue records', 'Coverage is unknown.', 'An empty list does not establish health.'); return; }
  for (const [scope, count] of groups) item(panel, scope, `${count} loaded issue records`, 'Not a complete incident count; check each source and timestamp.');
}
function renderIssues() {
  const panel = document.querySelector('#issues');
  const scope = document.querySelector('#issue-scope').value;
  const status = document.querySelector('#issue-status').value;
  const selectedOnly = document.querySelector('#issue-selected-bot').checked;
  const selectedExists = selectedBotId !== null && Boolean(uniqueRecord(currentSnapshot.bots, selectedBotId));
  const query = (document.querySelector('#issue-search').value || '').trim().toLowerCase();
  panel.replaceChildren();
  const records = currentSnapshot.issues.filter(i => (!scope || i.scope === scope) && (!status || i.status === status) && (!selectedOnly || (selectedExists && i.botId === selectedBotId)) && (!query || `${i.title} ${i.detail}`.toLowerCase().includes(query)));
  document.querySelector('#issue-count').textContent = `Showing ${records.length} of ${currentSnapshot.issues.length} loaded issue records; coverage may be incomplete.`;
  if (!records.length) item(panel, 'No matching issues', selectedOnly && !selectedExists ? 'Select a bot in the loaded roster to use this filter.' : 'No matching records in the loaded data.', 'This does not establish a healthy state.');
  records.forEach(i => {
    item(panel, i.title, i.detail, `${i.scope} · ${i.status} · ${i.source} · ${i.timeLabel || 'Updated'}: ${i.updatedAt || 'unknown'}`);
    if (i.bridgeObservation) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = 'View current bridge observation';
      button.addEventListener('click', () => document.querySelector('#bridge-status').scrollIntoView({behavior: 'smooth', block: 'nearest'}));
      panel.lastElementChild.append(button);
    }
    if (i.ownerAttention) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = 'View owner decision summary';
      button.addEventListener('click', () => document.querySelector('#owner-attention').scrollIntoView({behavior: 'smooth', block: 'nearest'}));
      panel.lastElementChild.append(button);
    }
    if (i.suggestedFix) {
      const fix = document.createElement('p');
      fix.textContent = `Suggested verification: ${i.suggestedFix}`;
      panel.lastElementChild.append(fix);
    }
    if (i.botId && uniqueRecord(currentSnapshot.bots, i.botId)) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = `Inspect bot for: ${i.title}`;
      button.addEventListener('click', () => {
        inspectBot(i.botId);
        document.querySelector('#bot-inspector').scrollIntoView({behavior: 'smooth', block: 'nearest'});
      });
      panel.lastElementChild.append(button);
    }
    if (i.learningId && currentSnapshot.learning.some(l => l.id === i.learningId)) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = `Inspect learning need: ${i.title}`;
      button.addEventListener('click', () => {
        inspectLearning(i.learningId);
        document.querySelector('#learning-inspector').scrollIntoView({behavior: 'smooth', block: 'nearest'});
      });
      panel.lastElementChild.append(button);
    }
  });
}
function inspectLearning(id) {
  selectedLearningId = id;
  updateLearningCount(filteredLearning());
  const panel = document.querySelector('#learning-inspector');
  panel.replaceChildren();
  const need = currentSnapshot.learning.find(l => l.id === id);
  renderLearningEvidence(need);
  if (!need) { panel.textContent = 'Selected learning need is no longer in this snapshot.'; return; }
  item(panel, `Learning detail · ${need.game} · ${need.topic}`, `Status: ${need.status} · Phase: ${need.phase || 'Not reported'} · Reason: ${need.reason || 'Not reported'} · Escalation: ${need.escalation || 'Not reported'} · Retry at: ${need.retryAt || 'Not reported'}`,
    `Evidence: ${need.evidence} · Model answer reported: ${need.hasModelAnswer === true ? 'Yes' : need.hasModelAnswer === false ? 'No' : 'Unknown'} (not outcome evidence or permission to call a model) · Datasets: ${need.datasets} · Policy verification: ${need.policy} · Updated: ${need.updatedAt || 'unknown'} · ${need.source}`);
  const issues = currentSnapshot.issues.filter(i => i.learningId === need.id);
  if (!issues.length) item(panel, 'Related issues', 'No matching issue records in this view.', 'This does not establish a resolved learning gap.');
  issues.forEach(i => item(panel, `Related issue · ${i.title}`, `${i.status} · ${i.detail}`, `${i.source} · ${i.timeLabel || 'Updated'}: ${i.updatedAt || 'unknown'}`));
}
function mapLearningEvidence(need, review = null) {
  const omitted = need.evidence === 'Not included';
  const reason = omitted ? 'Light task response omits evidence.'
    : need.evidence === 'Present' ? 'Task evidence is reported present, but no structured game assessment is supplied.'
      : 'No structured game-evidence assessment is supplied.';
  const scoped = review && review.kind === 'synthetic' && review.game === 'FFXI'
    && need.game === 'FFXI' && typeof need.id === 'string' && review.learningId === need.id
    && Array.isArray(review.assessments);
  return ['identity', 'navigation', 'party', 'memory', 'policy'].map(criterion => {
    const rows = scoped ? review.assessments.filter(row => row && row.criterion === criterion) : [];
    const row = rows.length === 1 ? rows[0] : null;
    const valid = row && ['supported', 'missing', 'conflicting'].includes(row.state)
      && typeof row.source === 'string' && row.source.trim()
      && typeof row.observedAt === 'string' && Number.isFinite(Date.parse(row.observedAt))
      && typeof row.evidence === 'string' && row.evidence.trim();
    return valid
      ? {state: `${row.state} (synthetic)`, reason: row.evidence, provenance: `${row.source} · Observed: ${row.observedAt}`}
      : {state: 'Unknown', reason: review ? 'Synthetic assessment absent, ambiguous or invalid for this scope.' : reason,
        provenance: 'No verified game outcome inferred.'};
  });
}
function renderLearningEvidence(need, review = null) {
  const panel = document.querySelector('#learning-evidence');
  panel.replaceChildren();
  if (!need) {
    item(panel, 'No learning record selected', 'Select a loaded FFXI need to review evidence requirements.', 'No evidence assessment is available.');
    return;
  }
  if (need.game !== 'FFXI') {
    item(panel, 'FFXI checklist does not apply', 'This record needs its own game-specific evidence review.', 'FFXI evidence is not transferred to other games.');
    return;
  }
  item(panel, `${review ? 'Synthetic mapping preview' : 'Evidence review'} · ${need.topic}`,
    review ? 'Synthetic examples only · Not an assessment of the selected task or any bot.' : 'Assessment: Unknown · No structured game-evidence assessment is connected.',
    `Selected record: ${need.source || 'Unknown source'} · Updated: ${need.updatedAt || 'unknown'} · Task status is not a game outcome.`);
  const requirements = [
    ['Native identity', 'Verified native bot and realm, source and observation time; explicit roster mapping.'],
    ['Navigation and missions', 'Starting state, objective, native result and subsequent observation of progress.'],
    ['Party and job behavior', 'Defined game scenario with observed results, failures and safe fallback.'],
    ['Grounded memory', 'Underlying verified fact, scope, source, time and evaluated recall.'],
    ['Policy improvement', 'Dataset provenance, policy version, validation, adoption and measured game outcomes.'],
  ];
  const assessments = mapLearningEvidence(need, review);
  requirements.forEach(([title, required], index) => {
    const assessment = assessments[index];
    item(panel, title, `Evidence state: ${assessment.state}`,
      `${assessment.reason} · ${assessment.provenance} · Required for review: ${required}`);
  });
}
function previewLearningEvidence() {
  const need = {id: 'synthetic-review', game: 'FFXI', topic: 'Offline evidence mapping', source: 'Synthetic local example'};
  renderLearningEvidence(need, {kind: 'synthetic', game: 'FFXI', learningId: need.id, assessments: [
    {criterion: 'identity', state: 'supported', source: 'Synthetic identity fixture', observedAt: '2026-01-01T12:00:00Z', evidence: 'Example contains an explicit scoped identity mapping.'},
    {criterion: 'navigation', state: 'missing', source: 'Synthetic navigation fixture', observedAt: '2026-01-01T12:00:00Z', evidence: 'Example has an accepted request but no subsequent position observation.'},
    {criterion: 'party', state: 'conflicting', source: 'Synthetic party fixture', observedAt: '2026-01-01T12:00:00Z', evidence: 'Example observations disagree on the scenario outcome.'},
  ]});
}
function renderLearningArtifacts() {
  const panel = document.querySelector('#learning-artifacts');
  const game = document.querySelector('#learning-game').value;
  panel.replaceChildren();
  const rows = observationRows(currentSnapshot.learningArtifacts, panel).filter(a => !game || a.game === game);
  if (!rows.length) item(panel, 'No artifact examples', 'No matching synthetic records.', 'This does not establish real artifact coverage.');
  rows.forEach(a => item(panel, `${routingText(a.game)} · ${routingText(a.kind)} · ${routingText(a.name)}`, `Validation: ${routingText(a.validation)} · Adoption: ${routingText(a.adoption)} · Demonstrated outcome: ${routingText(a.outcome)}`, `Version: ${routingText(a.version, 'unknown')} · ${routingText(a.source)} · Observed: ${routingText(a.observedAt, 'unknown')}`));
}
function renderLearningPlan() {
  const panel = document.querySelector('#learning-plan');
  const game = document.querySelector('#learning-game').value;
  panel.replaceChildren();
  const rows = observationRows(currentSnapshot.learningPlan, panel).filter(p => !game || p.game === game);
  if (!rows.length) item(panel, 'No planning topics', 'No topics for this filter.', 'This does not establish coverage.');
  rows.forEach(p => item(panel, `${routingText(p.game)} · ${routingText(p.topic)}`, routingText(p.next), `Evidence: ${routingText(p.evidence)} · Datasets: ${routingText(p.datasets)} · Policy: ${routingText(p.policy)} · ${routingText(p.source)}`));
}
function renderLearningCoverage() {
  const panel = document.querySelector('#learning-coverage');
  panel.replaceChildren();
  for (const game of ['FFXI', 'SWTOR']) {
    const rows = currentSnapshot.learning.filter(l => l.game === game);
    const verifiedTasks = rows.filter(l => l.status === 'verified').length;
    item(panel, `${game} · loaded learning records`, `${rows.length} loaded · ${verifiedTasks} marked as verified tasks`, 'Loaded records may be incomplete; task verification does not establish verified datasets, policies, adoption or game outcomes. Check individual sources.');
  }
}
function filteredLearning() {
  const game = document.querySelector('#learning-game').value;
  const status = document.querySelector('#learning-status').value;
  const attention = document.querySelector('#learning-attention').checked;
  const attentionStatuses = new Set(['Needs evidence', 'Needs inventory', 'unverified', 'failed', 'canceled', 'cancelled']);
  const query = (document.querySelector('#learning-search').value || '').trim().toLowerCase();
  return currentSnapshot.learning.filter(l => (!game || l.game === game) && (!status || l.status === status) && (!attention || attentionStatuses.has(l.status)) && (!query || `${l.topic} ${l.reason || ''}`.toLowerCase().includes(query)));
}
function updateLearningCount(records) {
  const selectedMissing = selectedLearningId !== null && !currentSnapshot.learning.some(l => l.id === selectedLearningId);
  const selectedHidden = selectedLearningId !== null && !selectedMissing && !records.some(l => l.id === selectedLearningId);
  document.querySelector('#learning-count').textContent = `Showing ${records.length} of ${currentSnapshot.learning.length} loaded learning records; coverage may be incomplete.${selectedMissing ? ' Selected need is no longer in the loaded data.' : selectedHidden ? ' Selected need is outside this filtered list; its inspector remains selected.' : ''}`;
}
function renderLearning() {
  const panel = document.querySelector('#learning');
  panel.replaceChildren();
  const records = filteredLearning();
  updateLearningCount(records);
  if (!records.length) item(panel, 'No matching learning entries', 'No matching records in the loaded data.', 'Coverage is unknown.');
  records.forEach(l => {
    item(panel, `${l.game} · ${l.topic}`, l.status, `Evidence: ${l.evidence} · Datasets: ${l.datasets} · Policy verification: ${l.policy} · Updated: ${l.updatedAt || 'unknown'} · ${l.source}`);
    if (l.id) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = `Inspect ${l.topic}`; button.addEventListener('click', () => inspectLearning(l.id));
      panel.lastElementChild.append(button);
    }
  });
  if (selectedLearningId !== null) inspectLearning(selectedLearningId);
  else renderLearningEvidence(null);
}
async function loadHubTrace(correlation) {
  if (!token || workspace.hidden) return;
  const requestToken = token, session = sessionVersion;
  const id = ++traceVersion;
  const panel = document.querySelector('#hub-trace');
  panel.replaceChildren();
  if (!/^[A-Za-z0-9_.:-]{1,128}$/.test(correlation)) { panel.textContent = 'Enter a correlation ID using letters, numbers, dot, dash, underscore or colon.'; return; }
  const game = document.querySelector('#trace-game').value;
  if (!['ffxi', 'swtor'].includes(game)) { panel.textContent = 'Choose a supported game.'; return; }
  panel.textContent = 'Loading read-only trace…';
  try {
    const response = await fetch(`/api/trace?gameId=${encodeURIComponent(game)}&correlationId=${encodeURIComponent(correlation)}`, {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    if (id !== traceVersion || !panelSessionCurrent(requestToken, session)) return;
    panel.replaceChildren();
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('unavailable');
    const rows = observationRows(data.records, panel);
    const complete = Array.isArray(data.records) && rows.length === data.records.length;
    item(panel, `Hub trace · ${game.toUpperCase()} · ${correlation}`, `${routingText(data.coverage)} · ${complete ? rows.length : 'Unknown count of'} returned ${rows.length === 1 ? 'record' : 'records'}`, `Fetched: ${routingText(data.fetchedAt)} · Deployed revision unverified · Bounded lookup, not proof of outcome`);
    if (!rows.length) item(panel, 'No matching trace records', 'No matching records in the bounded trace window.', 'This does not prove an action did or did not occur.');
    rows.forEach(r => item(panel, `${routingText(r.kind)} · ${routingText(r.type)}`, `Disposition: ${routingText(r.disposition)} · Classification: ${routingText(r.classification)} · Final: ${typeof r.isFinal === 'boolean' ? r.isFinal : 'Unknown'}`, `Occurred: ${routingText(r.occurredAt, 'unknown')} · Raw envelope body omitted`));
  } catch (_) { if (id === traceVersion && panelSessionCurrent(requestToken, session)) panel.textContent = 'Hub trace unavailable; no delivery or outcome can be inferred.'; }
}
function renderLedger() {
  const panel = document.querySelector('#ledger');
  panel.replaceChildren();
  const records = currentSnapshot.ledger.filter(e => !correlationFilter || e.correlationId === correlationFilter);
  document.querySelector('#ledger-filter').textContent = correlationFilter
    ? `Synthetic ledger filter applied: ${correlationFilter}. Game selection applies to hub trace only.`
    : 'Synthetic ledger: all loaded examples. Game selection applies to hub trace only.';
  if (!records.length) item(panel, 'No matching evidence', 'No records in this mock snapshot.', 'This is not proof that an action did or did not occur.');
  records.forEach(e => item(panel, `${e.bot} · ${e.request}`, `Result: ${e.result} · Verification: ${e.verification}`, `Correlation: ${e.correlationId}`));
}
function renderBotCoverage() {
  const panel = document.querySelector('#bot-coverage');
  panel.replaceChildren();
  for (const game of ['FFXI', 'SWTOR']) {
    const rows = currentSnapshot.bots.filter(b => b.game === game);
    const unknown = rows.filter(b => !b.status || b.status.toLowerCase() === 'unknown').length;
    item(panel, `${game} · loaded roster`, `${rows.length} records · ${unknown} with unknown status`, 'Loaded records may be incomplete; registration does not establish online presence. Check each source.');
  }
}
function filteredBots() {
  const game = document.querySelector('#bot-game').value;
  const query = (document.querySelector('#bot-search').value || '').trim().toLowerCase();
  return currentSnapshot.bots.filter(b => (!game || b.game === game) && (!query || b.name.toLowerCase().includes(query)));
}
function updateBotCount(bots) {
  const selectedMissing = selectedBotId !== null && !Boolean(uniqueRecord(currentSnapshot.bots, selectedBotId));
  const selectedAmbiguous = recordsForId(currentSnapshot.bots, selectedBotId).length > 1;
  const selectedHidden = selectedBotId !== null && !selectedMissing && !bots.some(b => b.id === selectedBotId);
  document.querySelector('#bot-count').textContent = `Showing ${bots.length} of ${currentSnapshot.bots.length} loaded roster records; coverage and presence may be unknown.${selectedAmbiguous ? ' Selected bot identity is ambiguous; scoped inspection is unavailable.' : selectedMissing ? ' Selected bot is no longer in the loaded data.' : selectedHidden ? ' Selected bot is outside this filtered roster; its inspector remains selected.' : ''}`;
}
function renderBots() {
  const panel = document.querySelector('#bots');
  const bots = filteredBots();
  panel.replaceChildren();
  updateBotCount(bots);
  if (!bots.length) item(panel, 'No matching roster records', 'No matches in the loaded data.', 'This does not establish that a bot is offline.');
  else bots.forEach(botItem);
}
function renderSafety() {
  const panel = document.querySelector('#safety-records');
  panel.replaceChildren();
  const rows = currentSnapshot.safetyRecords;
  if (!Array.isArray(rows) || rows.some(r => !r || typeof r !== 'object' || Array.isArray(r))) {
    item(panel, 'Safety example coverage unknown', 'No usable safety example list was supplied.', 'Actual gate and kill-switch states remain unknown.'); return;
  }
  const selectedExists = selectedBotId !== null && Boolean(uniqueRecord(currentSnapshot.bots, selectedBotId));
  const scoped = rows.filter(r => r.botId === null || (typeof r.botId === 'string' && r.botId.trim()));
  if (scoped.length !== rows.length) item(panel, 'Safety example scope unknown', 'Unscoped examples are not attributed to this bot or the network.', 'Actual gate and kill-switch states remain unknown.');
  const records = scoped.filter(r => r.botId === null || (selectedExists && r.botId === selectedBotId));
  if (!records.length) item(panel, 'No safety examples', 'Actual gate and kill-switch states are unknown.', 'No operational controls connected');
  records.forEach(r => item(panel, routingText(r.scope, 'Scope label unknown'), `Example gate: ${routingText(r.gate)} · Example kill switch: ${routingText(r.killSwitch)}`, `${routingText(r.source, 'Source unknown')} · Observed: ${routingText(r.observedAt, 'unknown')} · Actual state unknown`));
}
function renderReplySource() {
  const panel = document.querySelector('#reply-source');
  panel.replaceChildren();
  if (!selectedBotId) { item(panel, 'No bot selected', 'Select a bot to inspect reply examples.', 'No live reply data is connected.'); return; }
  const bot = uniqueRecord(currentSnapshot.bots, selectedBotId);
  if (!Array.isArray(currentSnapshot.replyEvents) || currentSnapshot.replyEvents.some(r => !r || typeof r !== 'object' || Array.isArray(r))) {
    item(panel, 'Reply evidence coverage unknown', 'No usable reply example list was supplied.', 'Source, fallback and delivery remain unknown.'); return;
  }
  const rows = currentSnapshot.replyEvents.filter(r => r.botId === selectedBotId);
  if (!bot || !rows.length) { item(panel, 'No matching reply evidence', 'Source, fallback and delivery are unknown.', 'Absence of records does not prove no reply occurred.'); return; }
  rows.forEach(r => item(panel, `${bot.name} · ${routingText(r.wordingOrigin, 'Unknown source')}`, `Generation: ${routingText(r.generationStatus)} · Fallback: ${routingText(r.fallbackPolicy)} · Reason: ${routingText(r.fallbackReason, 'Not reported')}`, `Delivery: ${routingText(r.delivery)} · Verification: ${routingText(r.verification)} · Correlation: ${routingText(r.correlationId, 'unknown')} · ${routingText(r.source, 'Source unknown')} · Observed: ${routingText(r.observedAt, 'unknown')}`));
}
function renderOwnerAttention(data) {
  const panel = document.querySelector('#owner-attention');
  panel.replaceChildren();
  if (!data || !Array.isArray(data.items) || data.items.some(row => !row || typeof row !== 'object' || Array.isArray(row))) {
    item(panel, 'Owner-decision coverage unknown', 'No usable decision list was supplied in this snapshot.',
      'Missing data does not establish that no decisions are pending.');
    return;
  }
  item(panel, 'Coverage', routingText(data.coverage), 'Coordinator task board · Read only');
  if (!data.items.length) item(panel, 'No records listed', 'Other owner decisions may be tracked elsewhere.', 'Not a complete decision inventory');
  data.items.forEach(a => item(panel, routingText(a.title, 'Decision title unknown'), routingText(a.project, 'Project unknown'),
    `Created: ${routingText(a.createdAt, 'unknown')} · Expires: ${routingText(a.expiresAt, 'unknown')} · Coordinator approval record`));
}
function renderAudit() {
  const panel = document.querySelector('#audit');
  panel.replaceChildren();
  if (!Array.isArray(currentSnapshot.audit) || currentSnapshot.audit.some(row => !row || typeof row !== 'object' || Array.isArray(row))) {
    document.querySelector('#audit-count').textContent = 'Loaded audit example count unknown; no live audit source is connected.';
    item(panel, 'Audit example coverage unknown', 'No usable audit example list was supplied in this snapshot.',
      'Missing data does not establish whether real admin actions occurred.');
    return;
  }
  const query = (document.querySelector('#audit-search').value || '').trim().toLowerCase();
  const rows = currentSnapshot.audit.filter(a => !query || [a.actor, a.action, a.scope, a.result]
    .some(value => typeof value === 'string' && value.toLowerCase().includes(query)));
  document.querySelector('#audit-count').textContent = `Showing ${rows.length} of ${currentSnapshot.audit.length} loaded audit examples; no live audit source is connected.`;
  if (!rows.length) item(panel, currentSnapshot.audit.length ? 'No matching audit examples' : 'No audit examples loaded',
    'This view does not establish whether real admin actions occurred.', 'Read-only examples; no live audit source is connected.');
  rows.forEach(a => item(panel, `${routingText(a.action, 'Action unknown')} · ${routingText(a.scope, 'Scope unknown')}`,
    routingText(a.result), `${routingText(a.actor, 'Actor unknown')} · ${routingText(a.at, 'unknown time')} · ${routingText(a.source, 'Source unknown')}`));
}
function assignmentNavigation(message) {
  document.querySelector('#assignment-count').textContent = message;
  document.querySelector('#assignment-prev').setAttribute('aria-disabled', String(assignmentPage <= 0 || assignmentPages === 0));
  document.querySelector('#assignment-next').setAttribute('aria-disabled', String(assignmentPage + 1 >= assignmentPages));
}
function changeAssignmentPage(delta) {
  const next = assignmentPage + delta;
  if (!currentSnapshot || next < 0 || next >= assignmentPages) return;
  assignmentPage = next;
  renderAssignments();
}
function renderAssignments() {
  const panel = document.querySelector('#assignment-history');
  panel.replaceChildren();
  if (assignmentBotId !== selectedBotId) { assignmentPage = 0; assignmentBotId = selectedBotId; }
  assignmentPages = 0;
  assignmentNavigation('Assignment example count unknown.');
  if (!selectedBotId) { assignmentPage = 0; assignmentNavigation('Select a bot to view loaded assignment examples.'); item(panel, 'No bot selected', 'Select a bot to view synthetic assignment examples.', 'Real assignment history is unavailable.'); return; }
  const bot = uniqueRecord(currentSnapshot.bots, selectedBotId);
  if (!Array.isArray(currentSnapshot.assignmentHistory) || currentSnapshot.assignmentHistory.some(a => !a || typeof a !== 'object' || Array.isArray(a))) {
    assignmentPage = 0; assignmentNavigation('Assignment example count unknown.');
    item(panel, 'Assignment example coverage unknown', 'No usable assignment example list was supplied.', 'Real assignment history is unavailable; no model changes are applied.'); return;
  }
  const rows = currentSnapshot.assignmentHistory.filter(a => a.botId === selectedBotId);
  if (!bot || !rows.length) { assignmentPage = 0; assignmentNavigation(bot ? '0 loaded assignment examples for this bot.' : 'Selected bot is no longer in the loaded roster.'); item(panel, 'No matching examples', 'No synthetic assignment history is available for this bot.', 'This does not prove no real assignment exists.'); return; }
  assignmentPages = Math.ceil(rows.length / assignmentPageSize);
  assignmentPage = Math.min(assignmentPage, assignmentPages - 1);
  const start = assignmentPage * assignmentPageSize;
  assignmentNavigation(`Page ${assignmentPage + 1} of ${assignmentPages} · Showing ${start + 1}–${Math.min(start + assignmentPageSize, rows.length)} of ${rows.length} loaded examples. Not a complete live history.`);
  rows.slice(start, start + assignmentPageSize).forEach(a => item(panel, `${bot.name} · ${routingText(a.purpose)}`, `Requested: ${routingText(a.requested)} · Effective: ${routingText(a.effective)}`, `Version: ${routingText(a.version)} · Recorded: ${routingText(a.at, 'unknown')} · ${routingText(a.source)}`));
}
function rosterDetails(bot) {
  return `Status: ${routingText(bot.status)} · Character: ${routingText(bot.character)} · Level: ${routingText(bot.level)} · Body kind: ${routingText(bot.bodyKind)}`;
}
function inspectBot(id) {
  selectedBotId = id;
  updateBotCount(filteredBots());
  renderSafety();
  if (document.querySelector('#issue-selected-bot').checked) renderIssues();
  renderAssignments();
  renderReplySource();
  const panel = document.querySelector('#bot-inspector');
  panel.replaceChildren();
  const bot = uniqueRecord(currentSnapshot.bots, id);
  if (!bot) { panel.textContent = recordsForId(currentSnapshot.bots, id).length > 1
    ? 'Selected bot identity is ambiguous; no scoped details or evidence are attributed.'
    : 'Selected bot is no longer in this snapshot.'; return; }
  item(panel, `${bot.name} · ${bot.game}`, rosterDetails(bot), `${bot.source} · Observed: ${bot.observedAt || 'unknown'}`);
  if (['FFXI', 'SWTOR'].includes(bot.game)) {
    const button = document.createElement('button'); button.type = 'button';
    button.textContent = `View ${bot.game} game learning (not bot-specific)`;
    button.addEventListener('click', () => showGameLearning(bot.game));
    panel.lastElementChild.append(button);
  }
  const issuesButton = document.createElement('button'); issuesButton.type = 'button';
  issuesButton.textContent = 'View explicitly linked bot issues';
  issuesButton.addEventListener('click', () => {
    for (const id of ['issue-scope', 'issue-status', 'issue-search']) document.getElementById(id).value = '';
    document.querySelector('#issue-selected-bot').checked = true;
    renderIssues(); document.querySelector('#issues').scrollIntoView({behavior: 'smooth', block: 'nearest'});
  });
  panel.lastElementChild.append(issuesButton);
  item(panel, 'Reported personality summary', routingText(bot.personalitySummary), `${bot.source} · Roster metadata, not proof of behavior`);
  const detailRows = Array.isArray(currentSnapshot.botDetails) ? currentSnapshot.botDetails : [];
  const matches = detailRows.filter(d => d && typeof d === 'object' && !Array.isArray(d) && d.botId === bot.id);
  const details = matches.length === 1 ? matches[0] : null;
  if (!details) item(panel, 'Goals and memory', 'Unknown', matches.length > 1
    ? 'Multiple detail records match this bot ID; no record was selected.'
    : 'No usable bot detail record in this view; missing data does not establish absence.');
  else {
    const meta = `${routingText(details.source, 'Source unknown')} · Observed: ${routingText(details.observedAt, 'unknown')}`;
    for (const [key, title] of [['goals', 'Goals'], ['memories', 'Memory']]) {
      const rows = details[key];
      const usable = Array.isArray(rows) ? rows.filter(row => row && typeof row === 'object' && !Array.isArray(row)) : [];
      if (!usable.length || usable.length !== rows.length) item(panel, title, 'Unknown', `${meta} · Missing or incomplete list does not establish absence.`);
      usable.forEach(row => key === 'goals'
        ? item(panel, `Goal · ${routingText(row.text)}`, `Status: ${routingText(row.status)} · Evidence: ${routingText(row.evidence)}`, meta)
        : item(panel, `Memory · ${routingText(row.text)}`, `Grounding: ${routingText(row.grounding)}`, meta));
    }
  }
  const events = currentSnapshot.ledger.filter(e => e.botId === bot.id);
  if (!events.length) item(panel, 'Evidence', 'No matching synthetic records', 'Absence of records does not prove inactivity.');
  events.forEach(e => {
    item(panel, e.request, `Result: ${e.result} · Verification: ${e.verification}`, `Correlation: ${e.correlationId}`);
    if (typeof e.correlationId === 'string' && e.correlationId) {
      const button = document.createElement('button'); button.type = 'button'; button.textContent = 'View example episode in ledger';
      button.addEventListener('click', () => {
        correlationFilter = e.correlationId;
        document.querySelector('#correlation').value = e.correlationId;
        if (['FFXI', 'SWTOR'].includes(bot.game)) document.querySelector('#trace-game').value = bot.game.toLowerCase();
        traceVersion++; document.querySelector('#hub-trace').replaceChildren();
        renderLedger(); document.querySelector('#ledger').scrollIntoView({behavior: 'smooth', block: 'nearest'});
      });
      panel.lastElementChild.append(button);
    }
  });
  const issues = currentSnapshot.issues.filter(i => i.botId === bot.id);
  if (!issues.length) item(panel, 'Bot-linked issues', 'No matching records in this view.', 'This does not establish a healthy state.');
  issues.forEach(i => item(panel, `Issue · ${i.title}`, `${i.status} · ${i.detail}`, `${i.source} · Updated: ${i.updatedAt || 'unknown'}`));
}
function routingText(value, fallback = 'Unknown') {
  return typeof value === 'string' && value.trim() ? value : fallback;
}
function metricNumber(value) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0;
}
function renderModelCalls() {
  const panel = document.querySelector('#model-calls');
  panel.replaceChildren();
  const calls = currentSnapshot.modelCalls;
  if (!Array.isArray(calls)) {
    item(panel, 'Model call coverage', 'Unknown', 'No usable model-call list in this snapshot.');
    return;
  }
  if (!calls.length) item(panel, 'No model call examples', 'No rows supplied.', 'This does not establish zero usage or cost.');
  const rows = calls.filter(row => row && typeof row === 'object' && !Array.isArray(row));
  if (rows.length !== calls.length) item(panel, 'Model call coverage', 'Unknown for omitted malformed rows', 'Valid supplied examples are shown below; coverage is incomplete.');
  rows.forEach(c => item(panel, `${routingText(c.model)} · ${routingText(c.purpose)}`,
    `Latency: ${metricNumber(c.latencyMs) ? c.latencyMs + ' ms' : 'Unknown'} · Cost: ${metricNumber(c.cost) ? c.cost : 'Unknown'} · Quality: ${metricNumber(c.quality) ? c.quality : 'Unknown'}`,
    `${routingText(c.source, 'Source unknown')} · Observed: ${routingText(c.observedAt)}`));
}
function renderSpendExample() {
  const panel = document.querySelector('#spend-example');
  panel.replaceChildren();
  const candidate = currentSnapshot.spendExample;
  const spend = candidate && typeof candidate === 'object' && !Array.isArray(candidate) ? candidate : {};
  const usd = value => metricNumber(value) ? `$${value.toFixed(2)}` : 'Unknown';
  item(panel, `Example month: ${routingText(spend.month)}`,
    `Settled: ${usd(spend.settledUsd)} · Open reservations: ${usd(spend.reservedOpenUsd)} · Budget: ${usd(spend.budgetUsd)}`,
    `${routingText(spend.source, 'Source unknown')} · ${routingText(spend.attribution, 'Attribution unknown')} · Observed: ${routingText(spend.fetchedAt)} · Separate ledgers are not reconciled.`);
}
function botItem(bot) {
  const parent = document.querySelector('#bots');
  item(parent, `${bot.name} · ${bot.game}`, rosterDetails(bot), `${bot.source} · Observed: ${bot.observedAt || 'unknown'}`);
  const row = parent.lastElementChild;
  const inspect = document.createElement('button');
  inspect.type = 'button';
  const identified = Boolean(uniqueRecord(currentSnapshot.bots, bot.id));
  inspect.disabled = !identified;
  inspect.textContent = identified ? `Inspect ${bot.name}` : 'Inspect unavailable: missing or ambiguous identity';
  inspect.addEventListener('click', () => inspectBot(bot.id));
  row.append(inspect);
  const routingPanel = document.createElement('details');
  const summary = document.createElement('summary');
  summary.textContent = 'Model routing (read-only)';
  routingPanel.append(summary);
  const details = document.createElement('p');
  details.className = 'routing';
  const routing = bot.routing && typeof bot.routing === 'object' && !Array.isArray(bot.routing) ? bot.routing : {};
  details.textContent = `Requested model: ${routingText(routing.requested)} · Effective model: ${routingText(routing.effective)}`;
  const routingMeta = document.createElement('p');
  routingMeta.className = 'routing';
  routingMeta.textContent = `Purpose: ${routingText(routing.purpose)} · Version: ${routingText(routing.version)} · Reported availability: ${routingText(routing.availability)} · Reason: ${routingText(routing.reason, 'Not reported')} · Source: ${routingText(routing.source)} · Observed: ${routingText(routing.observedAt, 'unknown')} · Freshness: Unknown`;
  const scope = document.createElement('p');
  scope.className = 'routing';
  scope.textContent = bot.id.startsWith('live:') ? 'The hub roster does not provide an implemented per-bot routing policy or verified routing identity.' : 'Game, realm and native bot identity must be verified before routing is available.';
  const purposeLabel = document.createElement('label');
  purposeLabel.textContent = 'Purpose';
  const purpose = document.createElement('select');
  purpose.disabled = true;
  purpose.setAttribute('aria-label', `Purpose for ${bot.name}`);
  const purposeOption = document.createElement('option');
  purposeOption.textContent = 'Unavailable';
  purpose.append(purposeOption);
  purposeLabel.append(purpose);
  const label = document.createElement('label');
  label.textContent = `Model for ${bot.name}`;
  const select = document.createElement('select');
  select.disabled = true;
  select.setAttribute('aria-label', `Model for ${bot.name}`);
  const option = document.createElement('option');
  option.textContent = 'Unavailable';
  select.append(option);
  const note = document.createElement('small');
  note.textContent = 'The approved design needs a compatible hub implementation and separate authorization for model changes.';
  label.append(select);
  routingPanel.append(details, routingMeta, scope, purposeLabel, label, note);
  row.append(routingPanel);
}
async function load() {
  const requestId = ++requestVersion;
  const requestToken = token, session = sessionVersion, wasVisible = !workspace.hidden;
  const current = () => requestId === requestVersion && token === requestToken && session === sessionVersion && (!wasVisible || !workspace.hidden);
  sourceLoading = true;
  error.textContent = '';
  document.querySelector('#hub-banner').textContent = currentSnapshot && loadedSource
    ? `Loading selected data source… Showing previous ${loadedSource} request snapshot from ${currentSnapshot.generatedAt || 'unknown time'} until loading finishes.`
    : 'Loading selected data source…';
  let unauthorized = false, rendering = false;
  try {
    const source = document.querySelector('#data-source').value === 'hub' ? 'hub' : 'mock';
    const response = await fetch(`/api/overview?source=${source}`, {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!current()) return;
    if (!response.ok) { unauthorized = response.status === 401; throw new Error(unauthorized ? 'Token was not accepted.' : 'Could not load the workspace.'); }
    const data = await response.json();
    if (!current()) return;
    rendering = true;
    for (const id of ['bots', 'leads', 'issues', 'ledger', 'learning', 'lead-monitoring', 'audit', 'service-health', 'lead-timeline', 'quota-history', 'session-markers', 'model-calls', 'owner-attention', 'assignment-history', 'nudge-history', 'lead-activity', 'hub-feeds', 'lead-summary', 'reply-source', 'learning-coverage', 'issue-coverage', 'bot-coverage', 'learning-plan', 'learning-evidence', 'game-status', 'spend-example', 'learning-artifacts', 'safety-records', 'ffxi-focus', 'ffxi-feeds']) document.getElementById(id).replaceChildren();
    currentSnapshot = data;
    if (data.ffxiFocus) {
      const f = data.ffxiFocus, target = document.querySelector('#ffxi-focus');
      item(target, 'Closest documented slice', routingText(f.closest), routingText(f.source, 'Source unknown'));
      item(target, 'What to look for', routingText(f.whatToLookFor), 'Readiness must be confirmed by the owning lead');
      item(target, 'How to toggle', routingText(f.toggle), 'Read only');
      item(target, 'Not yet verified', routingText(f.unverified), 'A bridge observation does not establish delivery');
    } else item(document.querySelector('#ffxi-focus'), 'FFXI readiness unknown',
      'No readiness summary was supplied in this snapshot.', 'Confirm readiness with the owning lead; feed availability does not establish game behavior.');
    renderOwnerAttention(data.ownerAttention);
    const supplied = data.hubFeeds;
    const feeds = Array.isArray(supplied) ? supplied.filter(f => f && typeof f === 'object' && !Array.isArray(f)) : [];
    const incomplete = !Array.isArray(supplied) || feeds.length !== supplied.length
      || feeds.some(f => ['game', 'view', 'status'].some(key => typeof f[key] !== 'string' || !f[key].trim()));
    const banner = document.querySelector('#hub-banner');
    if (incomplete) banner.textContent = 'Hub coverage unknown or incomplete. Check source labels for the supplied rows.';
    else if (feeds.some(f => f.status === 'Not configured')) banner.textContent = 'Hub not configured. Bot and learning views use synthetic fallback.';
    else if (feeds.some(f => f.status === 'Mock selected')) banner.textContent = 'Synthetic examples selected. No hub read was attempted.';
    else if (feeds.some(f => f.status === 'Invalid configuration')) banner.textContent = 'Hub configuration invalid. Bot and learning views use synthetic fallback.';
    else if (feeds.some(f => f.status === 'Unavailable')) banner.textContent = 'Hub data is partially or fully unavailable. Check each feed for synthetic fallback.';
    else if (feeds.length && feeds.every(f => f.status === 'Live response')) banner.textContent = 'Hub reads available. Coverage and deployed revision remain unverified.';
    else banner.textContent = 'Hub status unknown. Check source labels for each view.';
    feeds.forEach(f => item(document.querySelector('#hub-feeds'), `${routingText(f.game)} · ${routingText(f.view)}`, routingText(f.status), `${routingText(f.note)} · Fetched: ${routingText(f.at)}`));
    if (incomplete || !feeds.length) item(document.querySelector('#hub-feeds'), 'Feed coverage', 'Unknown', 'Missing or incomplete feed metadata does not establish availability.');
    const ffxiFeeds = feeds.filter(f => f.game === 'FFXI' || f.game === 'All');
    if (incomplete || !ffxiFeeds.length) item(document.querySelector('#ffxi-feeds'), 'FFXI feed coverage', 'Unknown', 'Missing or incomplete feed metadata; supplied rows do not establish complete FFXI coverage');
    ffxiFeeds.forEach(f => item(document.querySelector('#ffxi-feeds'), `${routingText(f.game)} · ${routingText(f.view)}`, routingText(f.status), `${routingText(f.note)} · Fetched: ${routingText(f.at)} · Not proof of game presence or delivery`));
    renderBotCoverage();
    renderBots();
    if (selectedBotId !== null) inspectBot(selectedBotId);
    else { renderAssignments(); renderReplySource(); renderSafety(); }
    const gamePanel = document.querySelector('#game-status'), servicePanel = document.querySelector('#service-health');
    observationRows(data.gameStatus, gamePanel).forEach(s => item(gamePanel, routingText(s.game),
      `XP rate: ${metricNumber(s.xpRate) ? s.xpRate + '×' : 'Unknown'} · Server liveness: ${routingText(s.liveness)}`,
      `${routingText(s.source)} · Checked: ${routingText(s.checkedAt)} · Freshness unknown`));
    observationRows(data.serviceHealth, servicePanel).forEach(h => item(servicePanel,
      `${routingText(h.label)} · ${routingText(h.game)}`, `${routingText(h.status)} · ${routingText(h.detail)}`,
      `${routingText(h.source)} · Observed: ${routingText(h.observedAt)} · May be stale`));
    renderCoordinatorPanels();
    renderLeadTimeline();
    renderQuotaHistory();
    renderSpendExample();
    renderModelCalls();
    renderAudit();
    renderIssueCoverage();
    renderIssues();
    renderLedger();
    renderLearningCoverage();
    renderLearningPlan();
    renderLearningArtifacts();
    renderLearning();
    document.querySelector('#updated').textContent = `Snapshot generated ${data.generatedAt} · Sources are labeled per view; lead task state comes from the coordinator board.`;
    loadedSource = source; sourceLoading = false;
    sessionStorage.setItem('dit-admin-token', token); workspace.hidden = false; form.hidden = true; loadBridge();
  } catch (e) {
    if (!current()) return;
    sourceLoading = false;
    if (currentSnapshot && loadedSource && !unauthorized && !rendering) {
      document.querySelector('#hub-banner').textContent = `Refresh failed. Showing previous ${loadedSource} request snapshot from ${currentSnapshot.generatedAt || 'unknown time'}; selected source may not match. Check each feed's source.`;
      return;
    }
    workspace.hidden = true; form.hidden = false; sessionStorage.removeItem('dit-admin-token'); resetPanelSession();
    error.textContent = unauthorized ? 'Token was not accepted.' : 'Could not load the workspace.';
  }
}
form.addEventListener('submit', e => { e.preventDefault(); resetPanelSession(); token = document.querySelector('#token').value; document.querySelector('#token').value = ''; load(); });
document.querySelector('#refresh').addEventListener('click', load);
document.querySelector('#assignment-prev').addEventListener('click', () => changeAssignmentPage(-1));
document.querySelector('#assignment-next').addEventListener('click', () => changeAssignmentPage(1));
document.querySelector('#audit-search').addEventListener('input', () => { if (currentSnapshot) renderAudit(); });
document.querySelector('#audit-reset').addEventListener('click', () => {
  document.querySelector('#audit-search').value = '';
  if (currentSnapshot) renderAudit();
});
document.querySelector('#bridge-refresh').addEventListener('click', loadBridge);
document.querySelector('#hub-health-refresh').addEventListener('click', loadHubHealth);
document.querySelector('#interaction-refresh').addEventListener('click', loadInteraction);
document.querySelector('#interaction-preview').addEventListener('click', previewInteraction);
if (typeof setInterval === 'function') setInterval(() => { if (document.visibilityState !== 'hidden') loadBridge(); }, 15000);
document.querySelector('#data-source').addEventListener('change', () => { traceVersion++; healthVersion++; interactionVersion++; document.querySelector('#interaction-status').replaceChildren(); document.querySelector('#interaction-status').textContent = 'Not requested.'; document.querySelector('#hub-trace').replaceChildren(); document.querySelector('#hub-health').textContent = 'Not requested.'; return load(); });
document.querySelector('#quota-window').addEventListener('change', () => { if (currentSnapshot) renderQuotaHistory(); });
document.querySelector('#timeline-kind').addEventListener('change', () => { if (currentSnapshot) renderLeadTimeline(); });
document.querySelector('#show-routing').addEventListener('click', () => {
  document.querySelector('#bots').querySelectorAll('details').forEach(panel => { panel.open = true; });
});
document.querySelector('#hide-routing').addEventListener('click', () => {
  document.querySelector('#bots').querySelectorAll('details').forEach(panel => { panel.open = false; });
});
document.querySelector('#clear-bot').addEventListener('click', () => {
  selectedBotId = null;
  if (currentSnapshot) updateBotCount(filteredBots());
  const panel = document.querySelector('#bot-inspector');
  panel.replaceChildren(); panel.textContent = 'No bot selected.';
  if (currentSnapshot) { renderAssignments(); renderReplySource(); renderSafety(); if (document.querySelector('#issue-selected-bot').checked) renderIssues(); }
});
document.querySelector('#ffxi-evidence').addEventListener('click', () => {
  document.querySelector('#trace-game').value = 'ffxi';
  document.querySelector('#correlation').value = '';
  correlationFilter = ''; traceVersion++;
  document.querySelector('#hub-trace').replaceChildren();
  if (currentSnapshot) renderLedger();
  document.querySelector('#trace-search').scrollIntoView({behavior: 'smooth', block: 'nearest'});
});
document.querySelector('#ffxi-bots').addEventListener('click', () => {
  document.querySelector('#bot-search').value = '';
  document.querySelector('#bot-game').value = 'FFXI';
  if (currentSnapshot) renderBots();
  document.querySelector('#bots').scrollIntoView({behavior: 'smooth', block: 'nearest'});
});
document.querySelector('#bot-game').addEventListener('change', () => { if (currentSnapshot) renderBots(); });
document.querySelector('#bot-search').addEventListener('input', () => { if (currentSnapshot) renderBots(); });
document.querySelector('#bot-reset').addEventListener('click', () => {
  document.querySelector('#bot-game').value = '';
  document.querySelector('#bot-search').value = '';
  if (currentSnapshot) renderBots();
});
document.querySelector('#ffxi-issues').addEventListener('click', () => {
  for (const id of ['issue-status', 'issue-search']) document.getElementById(id).value = '';
  document.querySelector('#issue-selected-bot').checked = false;
  document.querySelector('#issue-scope').value = 'FFXI';
  if (currentSnapshot) renderIssues();
  document.querySelector('#issues').scrollIntoView({behavior: 'smooth', block: 'nearest'});
});
document.querySelector('#issue-scope').addEventListener('change', () => { if (currentSnapshot) renderIssues(); });
document.querySelector('#issue-status').addEventListener('change', () => { if (currentSnapshot) renderIssues(); });
document.querySelector('#issue-selected-bot').addEventListener('change', () => { if (currentSnapshot) renderIssues(); });
document.querySelector('#issue-search').addEventListener('input', () => { if (currentSnapshot) renderIssues(); });
document.querySelector('#issue-reset').addEventListener('click', () => {
  for (const id of ['issue-scope', 'issue-status', 'issue-search']) document.getElementById(id).value = '';
  document.querySelector('#issue-selected-bot').checked = false;
  if (currentSnapshot) renderIssues();
});
function showGameLearning(game) {
  for (const id of ['learning-status', 'learning-search']) document.getElementById(id).value = '';
  document.querySelector('#learning-attention').checked = false;
  document.querySelector('#learning-game').value = game;
  if (currentSnapshot) { renderLearningPlan(); renderLearningArtifacts(); renderLearning(); }
  document.querySelector('#learning').scrollIntoView({behavior: 'smooth', block: 'nearest'});
}
document.querySelector('#ffxi-learning').addEventListener('click', () => showGameLearning('FFXI'));
document.querySelector('#clear-learning').addEventListener('click', () => {
  selectedLearningId = null;
  const panel = document.querySelector('#learning-inspector');
  panel.replaceChildren(); panel.textContent = 'Select a learning need for details.';
  renderLearningEvidence(null);
  if (currentSnapshot) updateLearningCount(filteredLearning());
});
document.querySelector('#learning-evidence-preview').addEventListener('click', previewLearningEvidence);
document.querySelector('#learning-evidence-selected').addEventListener('click', () => {
  renderLearningEvidence(currentSnapshot?.learning.find(need => need.id === selectedLearningId));
});
document.querySelector('#learning-game').addEventListener('change', () => { if (currentSnapshot) { renderLearningPlan(); renderLearningArtifacts(); renderLearning(); } });
document.querySelector('#learning-status').addEventListener('change', () => { if (currentSnapshot) renderLearning(); });
document.querySelector('#learning-attention').addEventListener('change', () => { if (currentSnapshot) renderLearning(); });
document.querySelector('#learning-search').addEventListener('input', () => { if (currentSnapshot) renderLearning(); });
document.querySelector('#learning-reset').addEventListener('click', () => {
  for (const id of ['learning-game', 'learning-status', 'learning-search']) document.getElementById(id).value = '';
  document.querySelector('#learning-attention').checked = false;
  if (currentSnapshot) { renderLearningPlan(); renderLearningArtifacts(); renderLearning(); }
});
for (const id of ['trace-game', 'correlation']) {
  document.getElementById(id).addEventListener(id === 'correlation' ? 'input' : 'change', () => {
    traceVersion++; document.querySelector('#hub-trace').replaceChildren();
  });
}
document.querySelector('#trace-search').addEventListener('submit', e => {
  e.preventDefault(); correlationFilter = document.querySelector('#correlation').value.trim();
  if (currentSnapshot) renderLedger();
  if (document.querySelector('#data-source').value === 'hub') {
    if (sourceLoading || loadedSource !== 'hub') {
      traceVersion++; document.querySelector('#hub-trace').replaceChildren();
      document.querySelector('#hub-trace').textContent = 'Load the selected hub source successfully before requesting a hub trace.';
    } else loadHubTrace(correlationFilter);
  }
});
document.querySelector('#trace-clear').addEventListener('click', () => {
  correlationFilter = ''; document.querySelector('#correlation').value = ''; traceVersion++; document.querySelector('#hub-trace').replaceChildren();
  if (currentSnapshot) renderLedger();
});
if (token) load();
