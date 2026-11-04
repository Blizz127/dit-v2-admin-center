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
let rosterRecordIndex = null;
let rosterGapDownloadUrl = null;
let replyBotId = null;
let assignmentBotId = null;
let assignmentPage = 0;
let assignmentPages = 0;
const assignmentPageSize = 10;
let correlationFilter = '';
let ledgerBotId = null;
let bridgePending = false;
let selectedLearningId = null;
let token = sessionStorage.getItem('dit-admin-token') || '';
let selectedWorkspaceSection = null;
function markWorkspaceSection(section) {
  selectedWorkspaceSection = workspaceSections.includes(section) ? section : null;
  for (const key of workspaceSections) document.getElementById('nav-' + key).setAttribute('aria-current',
    key === selectedWorkspaceSection ? 'location' : 'false');
}
function markWorkspaceTarget(id, target) {
  const section = id.startsWith('view-') ? id : target?.closest?.('.workspace-section')?.id;
  markWorkspaceSection(section?.replace(/^view-/, '') || null);
}
function focusWorkspaceTarget(id, scroll = true) {
  const target = document.getElementById(id);
  if (!target) return;
  markWorkspaceTarget(id, target);
  // Programmatic destinations are not additional Tab stops. Native links and
  // buttons retain their normal Tab/Enter/Space behavior; no key trap is added.
  target.setAttribute('tabindex', '-1');
  target.focus?.({preventScroll: true});
  if (scroll) target.scrollIntoView({behavior: 'auto', block: 'start'});
}
const workspaceSections = ['overview', 'roster', 'ffxi', 'learning', 'evidence', 'operations', 'models', 'notes'];
globalThis.addEventListener?.('hashchange', () => {
  if (workspace.hidden) return;
  const id = globalThis.location.hash.slice(1);
  markWorkspaceTarget(id, document.getElementById(id));
});
for (const section of workspaceSections) {
  document.getElementById('nav-' + section).addEventListener('click', event => {
    if (workspace.hidden || event.defaultPrevented || event.button > 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    // Let the anchor perform native fragment navigation and history updates.
    focusWorkspaceTarget('view-' + section, false);
  });
}
function panelSessionCurrent(requestToken, session) {
  return !workspace.hidden && token === requestToken && sessionVersion === session;
}
function renderOperationSources(data) {
  const panel = document.getElementById('operation-sources');
  panel.replaceChildren();
  const rows = data?.schema === 'dit-admin-operation-sources-v1' && Array.isArray(data.rows) ? data.rows : [];
  for (const id of ['wake-8450', 'ashes', 'lotro', 'wake-preparation']) {
    const matches = rows.filter(row => row && row.id === id);
    const row = matches.length === 1 ? matches[0] : null;
    const fields = ['title', 'state', 'reported', 'missing', 'reference', 'sha256'];
    if (!row || !fields.every(key => typeof row[key] === 'string' && row[key].length <= 500)) {
      item(panel, id, 'Source coverage unknown', 'No acceptance claim');
      continue;
    }
    item(panel, `${row.title} · ${row.state}`, `Dated report: ${row.reported} Missing evidence: ${row.missing}`,
      `${row.reference} · Reviewed SHA-256 ${row.sha256} · Current health unknown`);
  }
}
let wakeVerificationView = null;
document.getElementById('wake-readiness-filter').addEventListener('change', () => renderWakeVerification(wakeVerificationView));
function renderWakeVerification(data) {
  wakeVerificationView = data;
  const games = ['wow-vanilla', 'wow-forever', 'firefall', 'eden', 'blacklight', 'tabula-rasa', 'ffxi', 'war', 'enb', 'planetside', 'marvel-heroes', 'rose'];
  let rows = data?.schema === 'dit-admin-wake-readback-v1' && Array.isArray(data.rows) ? data.rows : [];
  const summary = document.getElementById('wake-cutover-status');
  summary.textContent = 'Cutover receipt unavailable. Current route and authenticated sign-in remain unknown.';
  const cutover = data?.schema === 'dit-admin-wake-readback-v1' ? data.cutover : null;
  const validId = value => typeof value === 'string' && /^[A-Za-z0-9._-]{1,96}$/.test(value);
  if (cutover?.destination === 'banshee:8450' && validId(cutover.id) && validId(cutover.receipt)
      && typeof cutover.completedAt === 'string' && Number.isFinite(Date.parse(cutover.completedAt))) {
    summary.textContent = `Cutover completed (reported) · ${cutover.completedAt} · ${cutover.receipt}. Destination: banshee:8450. Check each game below; current route, sign-in and lifecycle safety are not certified.`;
  } else {
    rows = [];
  }
  const filterControl = document.getElementById('wake-readiness-filter');
  const filter = ['all', 'unverified', 'held', 'reported'].includes(filterControl.value) ? filterControl.value : 'all';
  filterControl.value = filter;
  const counts = {unverified: 0, held: 0, reported: 0};
  let shown = 0;
  for (const game of games) {
    const cell = document.getElementById('wake-acceptance-' + game);
    const matches = rows.filter(row => row && row.game === game);
    let category = ['war', 'marvel-heroes'].includes(game) ? 'held' : 'unverified';
    cell.textContent = category === 'held' ? 'Held — readback cannot lift hold' : 'Unverified';
    if (category !== 'held' && matches.length === 1) {
      const row = matches[0];
      if (row.status === 'Verified readback (reported)' && typeof row.observedAt === 'string'
          && Number.isFinite(Date.parse(row.observedAt)) && typeof row.receipt === 'string'
          && /^[A-Za-z0-9._-]{1,96}$/.test(row.receipt)) {
        category = 'reported';
        cell.textContent = `${row.status} · ${row.observedAt} · ${row.receipt}. Current health unknown.`;
      }
    }
    counts[category]++;
    const visible = filter === 'all' || filter === category;
    document.getElementById('wake-row-' + game).hidden = !visible;
    if (visible) shown++;
  }
  document.getElementById('wake-readiness-count').textContent = `Showing ${shown} of ${games.length} mapped games · ${counts.reported} reported ready readbacks · ${counts.unverified} unverified · ${counts.held} retained holds. Counts describe these rows, not live health or all game restrictions.`;
  document.getElementById('wake-filter-empty').hidden = shown !== 0;
}
function resetPanelSession() {
  renderPresenceExamples(null);
  document.getElementById('wake-readiness-filter').value = 'all';
  renderWakeVerification(null);
  renderOperationSources(null);
  markWorkspaceSection(null);
  sessionVersion++;
  currentSnapshot = null; loadedSource = null;
  resetBotDraft();
  selectedBotId = null; selectedLearningId = null;
  replyBotId = null;
  document.querySelector('#reply-correlation').value = '';
  document.querySelector('#reply-count').textContent = 'Select a bot to view reply examples.';
  document.querySelector('#model-call-availability').value = '';
  document.querySelector('#model-call-coverage').textContent = 'Metric coverage unknown.';
  document.querySelector('#data-coverage').replaceChildren();
  document.querySelector('#bot-identity').value = '';
  clearRosterGapSelection();
  document.querySelector('#roster-gaps').replaceChildren();
  ledgerBotId = null; correlationFilter = '';
  document.querySelector('#correlation').value = '';
  document.querySelector('#ledger').replaceChildren();
  document.querySelector('#ledger-filter').textContent = 'No ledger snapshot loaded in this session.';
  document.querySelector('#ledger-count').textContent = 'Ledger example count unknown.';
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
  const scopeKey = row => ['caller', 'serverInstanceId', 'actorKey'].every(key => typeof row[key] === 'string' && row[key].trim())
    ? JSON.stringify([row.caller, row.serverInstanceId, row.actorKey]) : null;
  const counts = new Map();
  rows.forEach(row => { const key = scopeKey(row); if (key !== null) counts.set(key, (counts.get(key) || 0) + 1); });
  rows.forEach(b => {
    const key = scopeKey(b), identified = key !== null && counts.get(key) === 1;
    const scopeNote = key === null ? 'Actor scope unverified; activity withheld'
      : !identified ? 'Actor scope ambiguous in this response; activity withheld' : 'Supplied actor scope only; native identity remains unverified';
    item(panel, routingText(b.actorKey),
      `Reconciled view: ${freshness(b.fresh)} · Activity: ${identified && b.fresh === true ? routingText(b.activity) : 'Unknown'} · Raw snapshot: ${freshness(b.snapshotFresh)}`,
      `Scope: ${routingText(b.caller)} / ${routingText(b.serverInstanceId)} · ${scopeNote} · Raw state source: ${routingText(b.source, 'unknown')} · Snapshot observed: ${routingText(b.observedAt, 'unknown')} · Hub-reported snapshot age: ${metricNumber(b.ageSeconds) ? b.ageSeconds + ' s' : 'unknown'} · No roster identity join or delivery inference`);
  });
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
  observationRows(currentSnapshot.issues, panel).forEach(issue => {
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
  const rows = observationRows(currentSnapshot.issues, panel);
  const count = Array.isArray(currentSnapshot.issues) && rows.length === currentSnapshot.issues.length ? rows.length : 'Unknown';
  const records = rows.filter(i => (!scope || i.scope === scope) && (!status || i.status === status) && (!selectedOnly || (selectedExists && i.botId === selectedBotId)) && (!query || `${routingText(i.title)} ${routingText(i.detail)}`.toLowerCase().includes(query)));
  document.querySelector('#issue-count').textContent = `Showing ${records.length} of ${count} loaded issue records; coverage may be incomplete.`;
  if (!records.length) item(panel, 'No matching issues', selectedOnly && !selectedExists ? 'Select a bot in the loaded roster to use this filter.' : 'No matching records in the loaded data.', 'This does not establish a healthy state.');
  records.forEach(i => {
    item(panel, routingText(i.title), routingText(i.detail), `${routingText(i.scope)} · ${routingText(i.status)} · ${routingText(i.source)} · ${routingText(i.timeLabel, 'Updated')}: ${routingText(i.updatedAt, 'unknown')}`);
    if (i.bridgeObservation === true) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = 'View current bridge observation';
      button.addEventListener('click', () => focusWorkspaceTarget('bridge-status'));
      panel.lastElementChild.append(button);
    }
    if (i.ownerAttention === true) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = 'View owner decision summary';
      button.addEventListener('click', () => focusWorkspaceTarget('owner-attention'));
      panel.lastElementChild.append(button);
    }
    if (typeof i.suggestedFix === 'string' && i.suggestedFix.trim()) {
      const fix = document.createElement('p');
      fix.textContent = `Suggested verification: ${i.suggestedFix}`;
      panel.lastElementChild.append(fix);
    }
    if (i.botId && uniqueRecord(currentSnapshot.bots, i.botId)) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = `Inspect bot for: ${routingText(i.title)}`;
      button.addEventListener('click', () => {
        inspectBot(i.botId);
        focusWorkspaceTarget('bot-inspector');
      });
      panel.lastElementChild.append(button);
    }
    if (i.learningId && uniqueRecord(currentSnapshot.learning, i.learningId)) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = `Inspect learning need: ${routingText(i.title)}`;
      button.addEventListener('click', () => {
        inspectLearning(i.learningId);
        focusWorkspaceTarget('learning-inspector');
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
  const need = uniqueRecord(currentSnapshot.learning, id);
  renderLearningEvidence(need);
  if (!need) { panel.textContent = recordsForId(currentSnapshot.learning, id).length > 1
    ? 'Selected learning identity is ambiguous; no task details or evidence are attributed.'
    : 'Selected learning need is no longer in this snapshot.'; return; }
  item(panel, `Learning detail · ${routingText(need.game)} · ${routingText(need.topic)}`, `Status: ${routingText(need.status)} · Phase: ${routingText(need.phase, 'Not reported')} · Reason: ${routingText(need.reason, 'Not reported')} · Escalation: ${routingText(need.escalation, 'Not reported')} · Retry at: ${routingText(need.retryAt, 'Not reported')}`,
    `Evidence: ${routingText(need.evidence)} · Model answer reported: ${need.hasModelAnswer === true ? 'Yes' : need.hasModelAnswer === false ? 'No' : 'Unknown'} (not outcome evidence or permission to call a model) · Datasets: ${routingText(need.datasets)} · Policy verification: ${routingText(need.policy)} · Updated: ${routingText(need.updatedAt, 'unknown')} · ${routingText(need.source)}`);
  const issues = observationRows(currentSnapshot.issues, panel).filter(i => i.learningId === need.id);
  if (!issues.length) item(panel, 'Related issues', 'No matching issue records in this view.', 'This does not establish a resolved learning gap.');
  issues.forEach(i => item(panel, `Related issue · ${routingText(i.title)}`, `${routingText(i.status)} · ${routingText(i.detail)}`, `${routingText(i.source)} · ${routingText(i.timeLabel, 'Updated')}: ${routingText(i.updatedAt, 'unknown')}`));
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
  item(panel, `${review ? 'Synthetic mapping preview' : 'Evidence review'} · ${routingText(need.topic)}`,
    review ? 'Synthetic examples only · Not an assessment of the selected task or any bot.' : 'Assessment: Unknown · No structured game-evidence assessment is connected.',
    `Selected record: ${routingText(need.source, 'Unknown source')} · Updated: ${routingText(need.updatedAt, 'unknown')} · Task status is not a game outcome.`);
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
  const all = observationRows(currentSnapshot.learning, panel);
  const complete = Array.isArray(currentSnapshot.learning) && all.length === currentSnapshot.learning.length;
  for (const game of ['FFXI', 'SWTOR']) {
    const rows = all.filter(l => l.game === game);
    const verifiedTasks = rows.filter(l => l.status === 'verified').length;
    item(panel, `${game} · loaded learning records`, `${rows.length} ${complete ? 'loaded' : 'usable loaded; total Unknown'} · ${verifiedTasks} marked as verified tasks`, 'Loaded records may be incomplete; task verification does not establish verified datasets, policies, adoption or game outcomes. Check individual sources.');
  }
}
function usableLearningRows() {
  return Array.isArray(currentSnapshot.learning) ? currentSnapshot.learning.filter(l => l && typeof l === 'object' && !Array.isArray(l)) : [];
}
function filteredLearning() {
  const game = document.querySelector('#learning-game').value;
  const status = document.querySelector('#learning-status').value;
  const attention = document.querySelector('#learning-attention').checked;
  const attentionStatuses = new Set(['Needs evidence', 'Needs inventory', 'unverified', 'failed', 'canceled', 'cancelled']);
  const query = (document.querySelector('#learning-search').value || '').trim().toLowerCase();
  return usableLearningRows().filter(l => (!game || l.game === game) && (!status || l.status === status) && (!attention || attentionStatuses.has(l.status)) && (!query || `${l.topic} ${l.reason || ''}`.toLowerCase().includes(query)));
}
function updateLearningCount(records) {
  const selectedMissing = selectedLearningId !== null && !Boolean(uniqueRecord(currentSnapshot.learning, selectedLearningId));
  const selectedAmbiguous = recordsForId(currentSnapshot.learning, selectedLearningId).length > 1;
  const selectedHidden = selectedLearningId !== null && !selectedMissing && !records.some(l => l.id === selectedLearningId);
  const supplied = currentSnapshot.learning;
  const total = Array.isArray(supplied) && usableLearningRows().length === supplied.length ? supplied.length : 'Unknown total';
  document.querySelector('#learning-count').textContent = `Showing ${records.length} of ${total} loaded learning records; coverage may be incomplete.${selectedAmbiguous ? ' Selected learning identity is ambiguous; scoped inspection is unavailable.' : selectedMissing ? ' Selected need is no longer in the loaded data.' : selectedHidden ? ' Selected need is outside this filtered list; its inspector remains selected.' : ''}`;
}
function renderLearning() {
  const panel = document.querySelector('#learning');
  panel.replaceChildren();
  observationRows(currentSnapshot.learning, panel);
  const records = filteredLearning();
  updateLearningCount(records);
  if (!records.length) item(panel, 'No matching learning entries', 'No matching records in the loaded data.', 'Coverage is unknown.');
  records.forEach(l => {
    item(panel, `${routingText(l.game)} · ${routingText(l.topic)}`, routingText(l.status), `Evidence: ${routingText(l.evidence)} · Datasets: ${routingText(l.datasets)} · Policy verification: ${routingText(l.policy)} · Updated: ${routingText(l.updatedAt, 'unknown')} · ${routingText(l.source)}`);
    if (l.id) {
      const button = document.createElement('button'); button.type = 'button';
      const identified = Boolean(uniqueRecord(currentSnapshot.learning, l.id));
      button.disabled = !identified;
      button.textContent = identified ? `Inspect ${routingText(l.topic)}` : 'Inspect unavailable: missing or ambiguous identity'; button.addEventListener('click', () => { inspectLearning(l.id); focusWorkspaceTarget('learning-inspector'); });
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
  const count = document.querySelector('#ledger-count');
  count.textContent = 'Ledger example count unknown.';
  document.querySelector('#ledger-filter').textContent = correlationFilter
    ? `Synthetic ledger filter applied: ${correlationFilter}.${ledgerBotId !== null ? ' Pinned bot ID: ' + ledgerBotId + '.' : ''} Game selection applies to hub trace only.`
    : 'Synthetic ledger: all loaded examples. Game selection applies to hub trace only.';
  if (ledgerBotId !== null && !uniqueRecord(currentSnapshot.bots, ledgerBotId)) {
    item(panel, 'Pinned bot identity unavailable or ambiguous', 'Scoped evidence is Unknown.', 'No first record or unscoped correlation match is selected.');
    return;
  }
  const supplied = currentSnapshot.ledger;
  const rows = observationRows(supplied, panel);
  const complete = Array.isArray(supplied) && rows.length === supplied.length;
  const records = rows.filter(e => (!correlationFilter || e.correlationId === correlationFilter)
    && (ledgerBotId === null || e.botId === ledgerBotId));
  count.textContent = `Showing ${records.length} of ${complete ? rows.length : 'Unknown total'} loaded ledger examples${ledgerBotId !== null ? ' with bot scope applied' : ''}. Actual evidence coverage is unknown.`;
  if (!records.length) item(panel, 'No matching evidence', 'No records in this mock snapshot.', 'This is not proof that an action did or did not occur.');
  records.forEach(e => item(panel, `${routingText(e.bot)} · ${routingText(e.request)}`, `Result: ${routingText(e.result)} · Verification: ${routingText(e.verification)}`, `Correlation: ${routingText(e.correlationId)}`));
}
function renderBotCoverage() {
  const panel = document.querySelector('#bot-coverage');
  panel.replaceChildren();
  const all = observationRows(currentSnapshot.bots, panel);
  const complete = Array.isArray(currentSnapshot.bots) && all.length === currentSnapshot.bots.length;
  for (const game of ['FFXI', 'SWTOR']) {
    const rows = all.filter(b => b.game === game);
    const unknown = rows.filter(b => routingText(b.status).trim().toLowerCase() === 'unknown').length;
    item(panel, `${game} · loaded roster`, `${rows.length} ${complete ? 'records' : 'usable records; total Unknown'} · ${unknown} with unknown status`, 'Loaded records may be incomplete; registration does not establish online presence. Check each source.');
  }
}
function usableBotRows() {
  return Array.isArray(currentSnapshot.bots) ? currentSnapshot.bots.filter(b => b && typeof b === 'object' && !Array.isArray(b)) : [];
}
function releaseRosterGapDownload() {
  if (rosterGapDownloadUrl !== null) {
    URL.revokeObjectURL(rosterGapDownloadUrl);
    rosterGapDownloadUrl = null;
  }
}
function clearRosterGapSelection() {
  releaseRosterGapDownload();
  rosterRecordIndex = null;
  document.querySelector('#roster-gap-detail').replaceChildren();
  document.querySelector('#roster-gap-detail').textContent = 'Select a loaded roster gap for record details.';
}
const rosterGapFields = ['id', 'name', 'game', 'status', 'character', 'level', 'bodyKind', 'source', 'observedAt'];
function rosterGapReport(snapshot, selectedIndex) {
  const selected = snapshot.bots[selectedIndex];
  const hasId = typeof selected.id === 'string' && selected.id.trim();
  const candidates = snapshot.bots.flatMap((bot, index) => {
    if (!bot || typeof bot !== 'object' || Array.isArray(bot) || (hasId ? bot.id !== selected.id : index !== selectedIndex)) return [];
    const fields = Object.fromEntries(rosterGapFields.map(key => [key,
      typeof bot[key] === 'string' && bot[key].trim() ? bot[key]
        : key === 'level' && Number.isSafeInteger(bot[key]) && bot[key] >= 0 ? bot[key] : null]));
    return [{snapshotRow: index + 1, fields}];
  });
  return {
    schema: 'dit-admin-roster-gap-report-v1',
    snapshotGeneratedAt: typeof snapshot.generatedAt === 'string' && snapshot.generatedAt.trim() ? snapshot.generatedAt : null,
    selectedSnapshotRow: selectedIndex + 1,
    reason: candidates.length > 1 ? 'repeated_loaded_id' : 'missing_usable_loaded_id',
    differingFields: rosterGapFields.filter(key => new Set(candidates.map(row => row.fields[key])).size > 1),
    candidates,
    limits: ['Loaded snapshot only; row numbers are not persistent entity IDs.',
      'Only allowlisted reported fields are included; missing or malformed values are null (Unknown).',
      'No identity resolution, freshness verification, evidence joins or model changes.',
      'Snapshot timestamp is reported metadata, not authenticated provenance.'],
  };
}
function appendRosterGapComparison(detail, report) {
  releaseRosterGapDownload();
  const differences = report.differingFields.length ? report.differingFields.join(', ') : 'None among the included fields';
  item(detail, 'Candidate comparison', `Differing fields: ${differences}`,
    'Every row with the same exact loaded ID is included, even if hidden by roster filters. A missing ID is compared only with its selected row.');
  const region = document.createElement('div'); region.className = 'gap-comparison';
  region.setAttribute('role', 'region'); region.setAttribute('aria-label', 'Roster gap candidate comparison'); region.setAttribute('tabindex', '0');
  const table = document.createElement('table');
  table.setAttribute('style', `--gap-columns: ${report.candidates.length + 1}`);
  const caption = document.createElement('caption'); caption.textContent = 'Reported fields by snapshot row; Unknown does not resolve identity'; table.append(caption);
  const head = document.createElement('thead'), headings = document.createElement('tr');
  for (const label of ['Field', ...report.candidates.map(row => `Snapshot row ${row.snapshotRow}`)]) {
    const th = document.createElement('th'); th.setAttribute('scope', 'col'); th.textContent = label; headings.append(th);
  }
  head.append(headings); table.append(head);
  const body = document.createElement('tbody');
  for (const key of rosterGapFields) {
    const row = document.createElement('tr'), label = document.createElement('th'); label.setAttribute('scope', 'row');
    label.textContent = key + (report.differingFields.includes(key) ? ' (differs)' : ''); row.append(label);
    for (const candidate of report.candidates) {
      const cell = document.createElement('td'); cell.textContent = candidate.fields[key] ?? 'Unknown (missing or malformed)'; row.append(cell);
    }
    body.append(row);
  }
  table.append(body); region.append(table); detail.append(region);
  const json = JSON.stringify(report, null, 2);
  try {
    const blob = new Blob([json], {type: 'application/json;charset=utf-8'});
    rosterGapDownloadUrl = URL.createObjectURL(blob);
    const link = document.createElement('a'); link.textContent = 'Download gap report JSON';
    link.setAttribute('href', rosterGapDownloadUrl);
    link.setAttribute('download', `roster-gap-row-${report.selectedSnapshotRow}.json`); detail.append(link);
  } catch {
    const notice = document.createElement('p');
    notice.textContent = 'Download unavailable in this environment. Copy the report JSON below.';
    detail.append(notice);
  }
  const copy = document.createElement('textarea'); copy.readOnly = true; copy.rows = 8; copy.value = json;
  copy.setAttribute('aria-label', 'Gap report JSON for local copy'); detail.append(copy);
}
function renderRosterGaps() {
  const panel = document.querySelector('#roster-gaps');
  panel.replaceChildren();
  const snapshot = currentSnapshot;
  if (!Array.isArray(snapshot.bots)) {
    item(panel, 'Roster gaps unknown', 'No usable roster collection.', 'No entity or row is inferred.'); return;
  }
  let gaps = 0;
  snapshot.bots.forEach((bot, index) => {
    if (!bot || typeof bot !== 'object' || Array.isArray(bot)) {
      item(panel, `Snapshot row ${index + 1} · Unusable record`, 'Entity details unavailable.', 'No matching roster row can be displayed.');
      gaps++; return;
    }
    if (uniqueRecord(snapshot.bots, bot.id)) return;
    gaps++;
    const matches = recordsForId(snapshot.bots, bot.id).length;
    const reason = matches > 1 ? `Repeated loaded ID: ${matches} rows` : 'Missing usable loaded ID';
    item(panel, `Snapshot row ${index + 1} · ${routingText(bot.name)}`, reason,
      `${routingText(bot.game)} · ${routingText(bot.source, 'Source unknown')}`);
    const button = document.createElement('button'); button.type = 'button';
    button.textContent = `Review gap in snapshot row ${index + 1}`;
    button.addEventListener('click', () => {
      if (currentSnapshot !== snapshot) return;
      const detail = document.querySelector('#roster-gap-detail'); detail.replaceChildren();
      item(detail, `Snapshot row ${index + 1} · ${routingText(bot.name)}`, `${reason} · Reported ID: ${routingText(bot.id)}`,
        `Game: ${routingText(bot.game)} · Source: ${routingText(bot.source, 'Source unknown')} · Observed: ${routingText(bot.observedAt)} · This row is not a verified native identity; no goals, replies or other evidence are joined.`);
      const show = document.createElement('button'); show.type = 'button'; show.textContent = 'Show matching roster row';
      show.addEventListener('click', () => {
        if (currentSnapshot !== snapshot) return;
        rosterRecordIndex = index;
        document.querySelector('#bot-game').value = '';
        document.querySelector('#bot-search').value = '';
        document.querySelector('#bot-identity').value = 'unavailable';
        renderBots(); focusWorkspaceTarget('bots');
      });
      detail.append(show);
      appendRosterGapComparison(detail, rosterGapReport(snapshot, index));
      focusWorkspaceTarget('roster-gap-detail');
    });
    panel.lastElementChild.append(button);
  });
  if (!gaps) item(panel, 'No loaded roster identity gaps', 'Every supplied record has a unique nonblank ID, or the list is empty.', 'This does not verify native identity, presence or complete roster coverage.');
}
function filteredBots() {
  const game = document.querySelector('#bot-game').value;
  const identity = document.querySelector('#bot-identity').value;
  const query = (document.querySelector('#bot-search').value || '').trim().toLowerCase();
  return (Array.isArray(currentSnapshot.bots) ? currentSnapshot.bots : []).filter((b, index) => b && typeof b === 'object' && !Array.isArray(b)
    && (!game || b.game === game)
    && (rosterRecordIndex === null || rosterRecordIndex === index)
    && (!identity || (identity === 'unique' ? Boolean(uniqueRecord(currentSnapshot.bots, b.id)) : !uniqueRecord(currentSnapshot.bots, b.id)))
    && (!query || routingText(b.name, '').toLowerCase().includes(query)));
}
function updateBotCount(bots) {
  const selectedMissing = selectedBotId !== null && !Boolean(uniqueRecord(currentSnapshot.bots, selectedBotId));
  const selectedAmbiguous = recordsForId(currentSnapshot.bots, selectedBotId).length > 1;
  const selectedHidden = selectedBotId !== null && !selectedMissing && !bots.some(b => b.id === selectedBotId);
  const supplied = currentSnapshot.bots;
  const total = Array.isArray(supplied) && usableBotRows().length === supplied.length ? supplied.length : 'Unknown total';
  document.querySelector('#bot-count').textContent = `Showing ${bots.length} of ${total} loaded roster records; coverage and presence may be unknown.${rosterRecordIndex !== null ? ' Pinned snapshot row: ' + (rosterRecordIndex + 1) + '.' : ''}${selectedAmbiguous ? ' Selected bot identity is ambiguous; scoped inspection is unavailable.' : selectedMissing ? ' Selected bot is no longer in the loaded data.' : selectedHidden ? ' Selected bot is outside this filtered roster; its inspector remains selected.' : ''}`;
}
function renderPresenceExamples(data) {
  const panel = document.getElementById('presence-examples'); panel.replaceChildren();
  const rows = data?.kind === 'synthetic' && Array.isArray(data.rows) && data.rows.length <= 8 ? data.rows : null;
  if (!rows) { item(panel, 'Presence review examples unavailable', 'Live presence: Unknown', 'No authoritative presence source is connected by this review.'); return; }
  const usable = rows.filter(row => row && typeof row === 'object' && !Array.isArray(row)
    && ['scenario', 'supplied', 'missing'].every(key => typeof row[key] === 'string' && row[key].trim() && row[key].length <= 500));
  if (usable.length !== rows.length) item(panel, 'Example coverage Unknown', 'Malformed review cases were omitted.', 'This does not change any roster or live-presence state.');
  if (!usable.length) item(panel, 'No usable presence review examples', 'Live presence: Unknown', 'An empty example list is not an empty game or bot roster.');
  usable.forEach(row => item(panel, row.scenario, `Fictional supplied information: ${row.supplied}`,
    `Still needed: ${row.missing} · Live presence: Unknown · Synthetic review only; not attached to a selected bot.`));
}
function renderBots() {
  const panel = document.querySelector('#bots');
  const bots = filteredBots();
  panel.replaceChildren();
  observationRows(currentSnapshot.bots, panel);
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
function showBotLedgerExample(bot, correlationId) {
  correlationFilter = correlationId;
  ledgerBotId = bot.id;
  document.querySelector('#correlation').value = correlationId;
  if (['FFXI', 'SWTOR'].includes(bot.game)) document.querySelector('#trace-game').value = bot.game.toLowerCase();
  traceVersion++; document.querySelector('#hub-trace').replaceChildren();
  renderLedger(); focusWorkspaceTarget('ledger');
}
function renderReplySource() {
  const panel = document.querySelector('#reply-source');
  panel.replaceChildren();
  if (replyBotId !== selectedBotId) {
    replyBotId = selectedBotId;
    document.querySelector('#reply-correlation').value = '';
  }
  const count = document.querySelector('#reply-count');
  count.textContent = 'Reply example count unknown.';
  if (!selectedBotId) { item(panel, 'No bot selected', 'Select a bot to inspect reply examples.', 'No live reply data is connected.'); return; }
  const bot = uniqueRecord(currentSnapshot.bots, selectedBotId);
  if (!bot) { item(panel, 'No matching reply evidence', 'Selected bot identity is missing or ambiguous.', 'No scoped reply evidence is attributed.'); return; }
  const supplied = currentSnapshot.replyEvents;
  const usable = Array.isArray(supplied) ? supplied.filter(r => r && typeof r === 'object' && !Array.isArray(r)
    && typeof r.botId === 'string' && r.botId.trim()) : [];
  const complete = Array.isArray(supplied) && usable.length === supplied.length;
  if (!complete) item(panel, 'Reply evidence coverage unknown', 'Missing, malformed or unscoped examples are withheld.', 'Usable scoped examples remain visible; source, fallback and delivery are not inferred.');
  const rows = usable.filter(r => r.botId === selectedBotId);
  const correlation = document.querySelector('#reply-correlation').value.trim();
  const filtered = rows.filter(r => !correlation || r.correlationId === correlation);
  count.textContent = `Showing ${filtered.length} of ${complete ? rows.length : 'Unknown total'} loaded examples for this bot; actual reply coverage is unknown.`;
  if (!filtered.length) item(panel, correlation ? 'No matching correlation' : 'No matching reply evidence',
    correlation ? 'No usable loaded example matches this exact correlation ID for the selected bot.' : 'No usable loaded reply example matches the selected bot.',
    'This does not prove no reply occurred. Source, fallback and delivery remain unknown.');
  filtered.forEach(r => {
    item(panel, `${routingText(bot.name)} · ${routingText(r.wordingOrigin, 'Unknown source')}`, `Generation: ${routingText(r.generationStatus)} · Fallback: ${routingText(r.fallbackPolicy)} · Reason: ${routingText(r.fallbackReason, 'Not reported')}`, `Delivery: ${routingText(r.delivery)} · Verification: ${routingText(r.verification)} · Correlation: ${routingText(r.correlationId, 'unknown')} · ${routingText(r.source, 'Source unknown')} · Observed: ${routingText(r.observedAt, 'unknown')}`);
    if (typeof r.correlationId === 'string' && r.correlationId.trim()) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = 'Find loaded ledger evidence';
      button.addEventListener('click', () => showBotLedgerExample(bot, r.correlationId));
      panel.lastElementChild.append(button);
    }
  });
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
  if (!Array.isArray(currentSnapshot.audit)) {
    document.querySelector('#audit-count').textContent = 'Loaded audit example count unknown; no live audit source is connected.';
    item(panel, 'Audit example coverage unknown', 'No usable audit example list was supplied in this snapshot.',
      'Missing data does not establish whether real admin actions occurred.');
    return;
  }
  const supplied = currentSnapshot.audit;
  const usable = supplied.filter(row => row && typeof row === 'object' && !Array.isArray(row));
  const partial = usable.length !== supplied.length;
  if (partial) item(panel, 'Audit example coverage unknown', 'Malformed rows were omitted; usable examples are retained.',
    'The loaded total is Unknown. Missing data does not establish whether real admin actions occurred.');
  const query = (document.querySelector('#audit-search').value || '').trim().toLowerCase();
  const rows = usable.filter(a => !query || [a.actor, a.action, a.scope, a.result]
    .some(value => typeof value === 'string' && value.toLowerCase().includes(query)));
  document.querySelector('#audit-count').textContent = `Showing ${rows.length} of ${partial ? 'Unknown total' : supplied.length} loaded audit examples; no live audit source is connected.`;
  if (!rows.length) item(panel, usable.length ? 'No matching audit examples' : partial ? 'No usable audit examples' : 'No audit examples loaded',
    'This view does not establish whether real admin actions occurred.', 'Read-only examples; no live audit source is connected.');
  rows.forEach(a => item(panel, `${routingText(a.action, 'Action unknown')} · ${routingText(a.scope, 'Scope unknown')}`,
    routingText(a.result), `${routingText(a.actor, 'Actor unknown')} · ${routingText(a.at, 'unknown time')} · ${routingText(a.source, 'Source unknown')}`));
}
function renderRoutingAudit() {
  const panel = document.querySelector('#routing-audit');
  panel.replaceChildren();
  const supplied = currentSnapshot.routingAudit;
  const rows = observationRows(supplied, panel);
  const filter = document.querySelector('#routing-audit-scope').value;
  const outcomeFilter = document.querySelector('#routing-audit-outcome').value;
  const outcome = row => ['applied', 'rejected'].includes(row.outcome) ? row.outcome : 'unknown';
  const outcomeLabels = {applied: 'Simulated application', rejected: 'Simulated rejection', unknown: 'Unknown'};
  const selected = rows.filter(row => (!filter || row.scopeKind === filter)
    && (!outcomeFilter || outcome(row) === outcomeFilter));
  const count = Array.isArray(supplied) && supplied.length === rows.length ? rows.length : 'Unknown';
  document.querySelector('#routing-audit-count').textContent = `Showing ${selected.length} of ${count} loaded synthetic events; actual audit coverage is unknown.`;
  if (!selected.length) item(panel, 'No matching model-switch examples', 'No real audit conclusion is available.', 'No model switching is connected.');
  const version = value => Number.isSafeInteger(value) && value >= 0 ? value : 'Unknown';
  selected.forEach(row => {
    const scopeLabel = row.scopeKind === 'bot' ? 'Per-bot example' : row.scopeKind === 'all' ? 'All-bots example (fixed target set)' : 'Unknown scope example';
    item(panel, scopeLabel, `Actor: ${routingText(row.actor)} · Reason: ${routingText(row.reason)} · Example outcome: ${outcomeLabels[outcome(row)]} · Attempted model: ${routingText(row.attemptedModel)} · Result: ${routingText(row.result)}`,
      `Version: ${version(row.beforeVersion)} → ${version(row.afterVersion)} · Expected version: ${version(row.expectedVersion)} · Recorded: ${routingText(row.at)} · ${routingText(row.source, 'Source unknown')}`);
    const group = panel.lastElementChild;
    const changes = observationRows(row.changes, group);
    if (!['bot', 'all'].includes(row.scopeKind) || (row.scopeKind === 'bot'
        && (!Array.isArray(row.changes) || row.changes.length !== 1))) {
      item(group, 'Event target scope unknown or inconsistent', 'Requested changes withheld.',
        'A per-bot example requires exactly one target; unknown scope is not an all-bots request.');
      return;
    }
    const key = change => {
      const scope = change.scope;
      return scope && ['game', 'realm', 'native_bot', 'purpose'].every(field => typeof scope[field] === 'string' && scope[field].trim())
        ? JSON.stringify([scope.game, scope.realm, scope.native_bot, scope.purpose]) : null;
    };
    const counts = new Map();
    changes.forEach(change => { const identity = key(change); if (identity !== null) counts.set(identity, (counts.get(identity) || 0) + 1); });
    changes.forEach(change => {
      const identity = key(change);
      if (identity === null || counts.get(identity) !== 1) {
        item(group, 'Target scope unknown or ambiguous', 'Requested change withheld.', 'No first target or roster identity is inferred.');
        return;
      }
      const scope = change.scope;
      item(group, `${scope.game} / ${scope.realm} / ${scope.native_bot} · ${scope.purpose}`,
        `Requested: ${routingText(change.beforeRequested)} → ${routingText(change.afterRequested)}`,
        'Effective model: Unknown · Fictional target only; no roster mapping or provider call.');
    });
  });
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
  if (!Array.isArray(currentSnapshot.assignmentHistory)) {
    assignmentPage = 0; assignmentNavigation('Assignment example count unknown.');
    item(panel, 'Assignment example coverage unknown', 'No usable assignment example list was supplied.', 'Real assignment history is unavailable; no model changes are applied.'); return;
  }
  const supplied = currentSnapshot.assignmentHistory;
  const usable = supplied.filter(a => a && typeof a === 'object' && !Array.isArray(a) && typeof a.botId === 'string' && a.botId.trim());
  const partial = usable.length !== supplied.length;
  if (partial) item(panel, 'Assignment example coverage unknown', 'Malformed or unscoped rows were omitted; usable scoped examples remain visible.', 'Loaded total Unknown; real assignment history is unavailable and no model changes are applied.');
  const rows = usable.filter(a => a.botId === selectedBotId);
  const coverage = partial ? ' Usable scoped rows only; loaded total Unknown.' : '';
  if (!bot || !rows.length) { assignmentPage = 0; assignmentNavigation(bot ? `0 ${partial ? 'usable' : 'loaded'} assignment examples for this bot.${coverage}` : recordsForId(currentSnapshot.bots, selectedBotId).length > 1 ? 'Selected bot identity is ambiguous in the loaded roster.' : 'Selected bot is no longer in the loaded roster.'); item(panel, 'No matching examples', 'No synthetic assignment history is available for this bot.', 'This does not prove no real assignment exists.'); return; }
  assignmentPages = Math.ceil(rows.length / assignmentPageSize);
  assignmentPage = Math.min(assignmentPage, assignmentPages - 1);
  const start = assignmentPage * assignmentPageSize;
  assignmentNavigation(`Page ${assignmentPage + 1} of ${assignmentPages} · Showing ${start + 1}–${Math.min(start + assignmentPageSize, rows.length)} of ${rows.length} loaded examples.${coverage} Not a complete live history.`);
  rows.slice(start, start + assignmentPageSize).forEach(a => item(panel, `${routingText(bot.name)} · ${routingText(a.purpose)}`, `Requested: ${routingText(a.requested)} · Effective: ${routingText(a.effective)}`, `Version: ${routingText(a.version)} · Recorded: ${routingText(a.at, 'unknown')} · ${routingText(a.source)}`));
}
function rosterDetails(bot) {
  return `Status: ${routingText(bot.status)} · Character: ${routingText(bot.character)} · Level: ${routingText(bot.level)} · Body kind: ${routingText(bot.bodyKind)}`;
}
function draftBot() {
  return currentSnapshot && !sourceLoading && loadedSource === 'mock'
    ? uniqueRecord(currentSnapshot.bots, selectedBotId) : null;
}
function resetBotDraft() {
  for (const id of ['bot-draft-goals', 'bot-draft-personality']) {
    document.getElementById(id).value = '';
    document.getElementById(id).setAttribute('aria-invalid', 'false');
  }
  document.getElementById('bot-draft-result').replaceChildren();
  const bot = draftBot();
  document.getElementById('bot-draft-fields').disabled = !bot;
  document.getElementById('bot-draft-status').textContent = bot
    ? `Local draft for ${bot.id} · ${routingText(bot.game)}. Nothing is saved or applied.`
    : 'Select a unique mock bot to prepare a local draft. Hub data and ambiguous identities are unavailable for drafting.';
}
function draftBaseline(bot) {
  const text = value => typeof value === 'string' && value.trim() && value.length <= 4000;
  const matches = Array.isArray(currentSnapshot.botDetails) ? currentSnapshot.botDetails.filter(
    row => row && typeof row === 'object' && !Array.isArray(row) && row.botId === bot.id) : [];
  const details = matches.length === 1 ? matches[0] : null;
  const goals = details?.goals;
  const goalsKnown = Array.isArray(goals) && goals.length <= 20 && goals.every(
    goal => goal && typeof goal === 'object' && !Array.isArray(goal) && text(goal.text))
    && goals.map(goal => goal.text.trim()).join('\n').length <= 4000;
  return {
    'bot-draft-goals': {known: goalsKnown, value: goalsKnown ? goals.map(goal => goal.text.trim()).join('\n') : '',
      source: details?.source, observedAt: details?.observedAt,
      reason: matches.length > 1 ? 'Multiple detail records match this bot ID.' : 'Goal list missing, partial or beyond review bounds.'},
    'bot-draft-personality': {known: Boolean(text(bot.personalitySummary)), value: text(bot.personalitySummary) ? bot.personalitySummary.trim() : '',
      source: bot.source, observedAt: bot.observedAt, reason: 'Reported personality summary missing or beyond review bounds.'},
  };
}
function renderDraftReview(panel, label, baseline, proposed) {
  const row = document.createElement('section'); row.className = 'draft-review';
  row.setAttribute('aria-label', label + ' review');
  const title = document.createElement('h4'); title.textContent = label;
  const state = document.createElement('p');
  state.textContent = !proposed ? 'No change proposed' : !baseline.known ? 'Comparison unavailable: current value Unknown'
    : proposed === baseline.value ? 'Matches loaded text' : 'Proposed text differs';
  const columns = document.createElement('div'); columns.className = 'draft-review-columns';
  for (const [heading, value] of [
    ['Current loaded text', baseline.known ? baseline.value || 'Empty supplied goal list' : 'Unknown · ' + baseline.reason],
    ['Proposed local text', proposed || 'No change proposed; current value is not cleared'],
  ]) {
    const column = document.createElement('div');
    const h = document.createElement('h5'); h.textContent = heading;
    const content = document.createElement('p'); content.className = 'draft-review-text'; content.textContent = value;
    column.append(h, content); columns.append(column);
  }
  const provenance = document.createElement('small');
  provenance.textContent = `${routingText(baseline.source, 'Source unknown')} · Observed: ${routingText(baseline.observedAt)} · Text comparison only; no verified behavior or saved change.`;
  row.append(title, state, columns, provenance); panel.append(row);
}
function previewBotDraft(event) {
  event.preventDefault();
  const panel = document.getElementById('bot-draft-result');
  panel.replaceChildren();
  const bot = draftBot();
  if (!bot) { resetBotDraft(); return; }
  const fields = [['bot-draft-goals', 'Proposed goals', 1000], ['bot-draft-personality', 'Proposed personality', 500]];
  let invalid = null;
  for (const [id, , limit] of fields) {
    const value = document.getElementById(id).value;
    const bad = value.length > limit || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(value);
    document.getElementById(id).setAttribute('aria-invalid', String(bad));
    if (bad && invalid === null) invalid = id;
  }
  const status = document.getElementById('bot-draft-status');
  if (invalid) {
    status.textContent = 'Draft not previewed: remove control characters and stay within each field limit.';
    document.getElementById(invalid).focus?.();
    return;
  }
  if (!fields.some(([id]) => document.getElementById(id).value.trim())) {
    status.textContent = 'Enter at least one proposed goal or personality change. Blank fields do not clear existing data.';
    document.getElementById('bot-draft-goals').focus?.();
    return;
  }
  item(panel, `Local draft · ${bot.id} · ${routingText(bot.game)}`, `Selected record: ${routingText(bot.name)}`,
    `${routingText(bot.source, 'Source unknown')} · Snapshot: ${routingText(currentSnapshot.generatedAt)} · Native identity remains unverified.`);
  const baseline = draftBaseline(bot);
  for (const [id, label] of fields) renderDraftReview(panel, label, baseline[id], document.getElementById(id).value.trim());
  status.textContent = 'Preview ready. Not saved, applied, verified or sent; no bot or model command was issued.';
}
function inspectBot(id) {
  selectedBotId = id;
  resetBotDraft();
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
  item(panel, `${routingText(bot.name)} · ${routingText(bot.game)}`, rosterDetails(bot), `${routingText(bot.source, 'Source unknown')} · Observed: ${routingText(bot.observedAt, 'unknown')}`);
  if (['FFXI', 'SWTOR'].includes(bot.game)) {
    const button = document.createElement('button'); button.type = 'button';
    button.textContent = `View ${routingText(bot.game)} game learning (not bot-specific)`;
    button.addEventListener('click', () => showGameLearning(bot.game));
    panel.lastElementChild.append(button);
  }
  const issuesButton = document.createElement('button'); issuesButton.type = 'button';
  issuesButton.textContent = 'View explicitly linked bot issues';
  issuesButton.addEventListener('click', () => {
    for (const id of ['issue-scope', 'issue-status', 'issue-search']) document.getElementById(id).value = '';
    document.querySelector('#issue-selected-bot').checked = true;
    renderIssues(); focusWorkspaceTarget('issues');
  });
  panel.lastElementChild.append(issuesButton);
  item(panel, 'Reported personality summary', routingText(bot.personalitySummary), `${routingText(bot.source, 'Source unknown')} · Roster metadata, not proof of behavior`);
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
  const events = observationRows(currentSnapshot.ledger, panel).filter(e => e.botId === bot.id);
  if (!events.length) item(panel, 'Evidence', 'No matching synthetic records', 'Absence of records does not prove inactivity.');
  events.forEach(e => {
    item(panel, routingText(e.request), `Result: ${routingText(e.result)} · Verification: ${routingText(e.verification)}`, `Correlation: ${routingText(e.correlationId)}`);
    if (typeof e.correlationId === 'string' && e.correlationId.trim()) {
      const button = document.createElement('button'); button.type = 'button'; button.textContent = 'View example episode in ledger';
      button.addEventListener('click', () => showBotLedgerExample(bot, e.correlationId));
      panel.lastElementChild.append(button);
    }
  });
  const issues = observationRows(currentSnapshot.issues, panel).filter(i => i.botId === bot.id);
  if (!issues.length) item(panel, 'Bot-linked issues', 'No matching records in this view.', 'This does not establish a healthy state.');
  issues.forEach(i => item(panel, `Issue · ${routingText(i.title)}`, `${routingText(i.status)} · ${routingText(i.detail)}`, `${routingText(i.source)} · Updated: ${routingText(i.updatedAt, 'unknown')}`));
}
function routingText(value, fallback = 'Unknown') {
  return typeof value === 'string' && value.trim() ? value : fallback;
}
function metricNumber(value) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0;
}
function renderDataCoverage() {
  const panel = document.querySelector('#data-coverage');
  panel.replaceChildren();
  for (const [key, label, target] of [['bots', 'Bot roster', 'bots'], ['learning', 'Learning needs', 'learning'], ['modelCalls', 'Model call metrics', 'model-calls']]) {
    const supplied = currentSnapshot[key];
    const rows = Array.isArray(supplied) ? supplied.filter(row => row && typeof row === 'object' && !Array.isArray(row)) : [];
    const state = !Array.isArray(supplied) ? 'Unavailable collection' : !supplied.length ? 'Empty loaded collection'
      : supplied.length !== rows.length ? 'Partial collection' : 'Loaded collection';
    const total = Array.isArray(supplied) && rows.length === supplied.length ? rows.length : 'Unknown';
    let detail = `Usable rows: ${rows.length} · Loaded total: ${total}`;
    if (key === 'modelCalls') {
      const missing = rows.filter(row => !['latencyMs', 'cost', 'quality'].every(field => metricNumber(row[field]))).length;
      detail += ` · Rows with unknown numeric fields: ${missing}`;
    } else {
      const unusable = rows.filter(row => typeof row.id !== 'string' || !row.id.trim()).length;
      const counts = new Map();
      rows.forEach(row => { if (typeof row.id === 'string' && row.id.trim()) counts.set(row.id, (counts.get(row.id) || 0) + 1); });
      const ambiguous = rows.filter(row => counts.get(row.id) > 1).length;
      detail += ` · Rows without usable IDs: ${unusable} · Rows with repeated IDs: ${ambiguous}`;
    }
    item(panel, `${label} · ${state}`, detail, 'Loaded snapshot only; these counts do not establish live coverage, freshness or game outcomes. Detail filters remain unchanged.');
    const button = document.createElement('button'); button.type = 'button';
    button.textContent = `Review ${label.toLowerCase()}`;
    button.addEventListener('click', () => focusWorkspaceTarget(target));
    panel.lastElementChild.append(button);
  }
}
function renderModelComparison(rows) {
  const panel = document.getElementById('model-comparison');
  panel.replaceChildren();
  if (rows === null) {
    item(panel, 'Comparison unavailable', 'Model-call coverage is Unknown.', 'No benchmark or zero-usage conclusion can be drawn.');
    return;
  }
  const groups = new Map();
  let unidentified = 0;
  for (const row of rows) {
    const identity = [row.model, row.purpose, row.source];
    if (!identity.every(value => typeof value === 'string' && value.trim())) { unidentified++; continue; }
    const key = JSON.stringify(identity);
    if (!groups.has(key)) groups.set(key, {identity, rows: []});
    groups.get(key).rows.push(row);
  }
  if (!groups.size) item(panel, 'No comparable loaded groups', rows.length
    ? 'No complete model/purpose/source identities in this selection.'
    : 'No supplied rows in this selection. Check the numeric-availability filter or refresh the snapshot.',
    'This does not establish zero usage.');
  if (unidentified) item(panel, 'Unattributed examples', `${unidentified} rows excluded from grouping.`, 'Missing model, purpose or source is not a shared identity.');
  for (const {identity: [model, purpose, source], rows: samples} of groups.values()) {
    const latencies = samples.filter(row => metricNumber(row.latencyMs)).map(row => row.latencyMs);
    // Nonnegative finite samples keep each difference and running mean bounded.
    // Summing value/count can still round above MAX_VALUE for three equal maxima.
    const mean = latencies.length ? latencies.reduce((average, value, index) => average + (value - average) / (index + 1), 0) : null;
    const meanText = metricNumber(mean) ? `${Number(mean.toFixed(3))} ms` : 'Unknown';
    item(panel, `${model} · ${purpose}`,
      `${samples.length} loaded samples · Mean supplied latency: ${meanText} (${latencies.length}/${samples.length} supplied)`,
      `${source} · Cost supplied: ${samples.filter(row => metricNumber(row.cost)).length}/${samples.length} · Quality supplied: ${samples.filter(row => metricNumber(row.quality)).length}/${samples.length} · No common quality scale or settled-spend claim.`);
    const details = document.createElement('details');
    const summary = document.createElement('summary'); summary.textContent = `Review ${samples.length} supplied rows`;
    const region = document.createElement('div'); region.className = 'model-samples';
    region.setAttribute('role', 'region'); region.setAttribute('aria-label', `Samples for ${model} · ${purpose} · ${source}`);
    region.setAttribute('tabindex', '0');
    const table = document.createElement('table');
    const caption = document.createElement('caption');
    caption.textContent = `Loaded rows · ${model} · ${purpose} · ${source}. Observation times are supplied labels, not verified freshness.`;
    const head = document.createElement('thead'); const headings = document.createElement('tr');
    for (const label of ['Row in group', 'Observed', 'Latency (ms)', 'Cost', 'Quality']) {
      const cell = document.createElement('th'); cell.setAttribute('scope', 'col'); cell.textContent = label; headings.append(cell);
    }
    head.append(headings); const body = document.createElement('tbody');
    samples.forEach((sample, index) => {
      const row = document.createElement('tr');
      const number = document.createElement('th'); number.setAttribute('scope', 'row'); number.textContent = String(index + 1); row.append(number);
      for (const value of [routingText(sample.observedAt), ...['latencyMs', 'cost', 'quality'].map(key => metricNumber(sample[key]) ? String(sample[key]) : 'Unknown')]) {
        const cell = document.createElement('td'); cell.textContent = value; row.append(cell);
      }
      body.append(row);
    });
    table.append(caption, head, body); region.append(table); details.append(summary, region); panel.lastElementChild.append(details);
  }
}
function renderModelCalls() {
  const panel = document.querySelector('#model-calls');
  panel.replaceChildren();
  const coverage = document.querySelector('#model-call-coverage');
  coverage.textContent = 'Metric coverage unknown.';
  const calls = currentSnapshot.modelCalls;
  if (!Array.isArray(calls)) {
    renderModelComparison(null);
    item(panel, 'Model call coverage', 'Unknown', 'No usable model-call list in this snapshot.');
    return;
  }
  for (const [key, label, note] of [['evaluatorSnapshot', 'Evaluator snapshot', 'Offline file import; not live hub data or a bake-off.'],
                                    ['bakeoffRun', 'Bake-off run', 'Offline recorded run; proposal shape, not live hub data.']]) {
    const snapshot = currentSnapshot[key];
    if (!snapshot || typeof snapshot !== 'object' || Array.isArray(snapshot)) continue;
    const omissions = key === 'bakeoffRun' && metricNumber(snapshot.omittedDuplicate) && metricNumber(snapshot.omittedHashMismatch)
      ? ` · Duplicate attempts withheld: ${snapshot.omittedDuplicate} · Hash mismatch withheld: ${snapshot.omittedHashMismatch}` : '';
    item(panel, `${label}: ${routingText(snapshot.status)}`,
      `Imported: ${metricNumber(snapshot.records) ? snapshot.records : 'Unknown'} · Omitted: ${metricNumber(snapshot.omitted) ? snapshot.omitted : 'Unknown'}${omissions}`,
      `${routingText(snapshot.reason, 'Reason unknown')} · ${note}`);
  }
  if (!calls.length) item(panel, 'No model call examples', 'No rows supplied.', 'This does not establish zero usage or cost.');
  const rows = calls.filter(row => row && typeof row === 'object' && !Array.isArray(row));
  if (rows.length !== calls.length) item(panel, 'Model call coverage', 'Unknown for omitted malformed rows', 'Valid supplied examples are shown below; coverage is incomplete.');
  const fields = [['latencyMs', 'Latency'], ['cost', 'Cost'], ['quality', 'Quality']];
  const complete = row => fields.every(([key]) => metricNumber(row[key]));
  const filter = document.querySelector('#model-call-availability').value;
  const selected = rows.filter(row => !filter || (filter === 'complete' ? complete(row) : !complete(row)));
  renderModelComparison(selected);
  coverage.textContent = `Showing ${selected.length} of ${rows.length === calls.length ? rows.length : 'Unknown total'} loaded examples. Numeric fields supplied among ${rows.length} usable rows: `
    + fields.map(([key, label]) => `${label} ${rows.filter(row => metricNumber(row[key])).length}/${rows.length}`).join(' · ')
    + '. Counts describe supplied fields only, not verified usage, settled spend or model quality.';
  if (rows.length && !selected.length) item(panel, 'No examples match metric availability', 'Change the local filter to see other loaded rows.', 'Missing measurements are not zero usage.');
  selected.forEach(c => item(panel, `${routingText(c.model)} · ${routingText(c.purpose)}`,
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
  item(parent, `${routingText(bot.name)} · ${routingText(bot.game)}`, rosterDetails(bot), `${routingText(bot.source, 'Source unknown')} · Observed: ${routingText(bot.observedAt, 'unknown')}`);
  const row = parent.lastElementChild;
  const inspect = document.createElement('button');
  inspect.type = 'button';
  const identified = Boolean(uniqueRecord(currentSnapshot.bots, bot.id));
  inspect.disabled = !identified;
  inspect.textContent = identified ? `Inspect ${routingText(bot.name)}` : 'Inspect unavailable: missing or ambiguous identity';
  inspect.addEventListener('click', () => { inspectBot(bot.id); focusWorkspaceTarget('bot-inspector'); });
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
  scope.textContent = typeof bot.id === 'string' && bot.id.startsWith('live:') ? 'The hub roster does not provide an implemented per-bot routing policy or verified routing identity.' : 'Game, realm and native bot identity must be verified before routing is available.';
  const purposeLabel = document.createElement('label');
  purposeLabel.textContent = 'Purpose';
  const purpose = document.createElement('select');
  purpose.disabled = true;
  purpose.setAttribute('aria-label', `Purpose for ${routingText(bot.name)}`);
  const purposeOption = document.createElement('option');
  purposeOption.textContent = 'Unavailable';
  purpose.append(purposeOption);
  purposeLabel.append(purpose);
  const label = document.createElement('label');
  label.textContent = `Model for ${routingText(bot.name)}`;
  const select = document.createElement('select');
  select.disabled = true;
  select.setAttribute('aria-label', `Model for ${routingText(bot.name)}`);
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
  resetBotDraft();
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
    for (const id of ['bots', 'leads', 'issues', 'ledger', 'learning', 'lead-monitoring', 'audit', 'service-health', 'lead-timeline', 'quota-history', 'session-markers', 'model-calls', 'model-comparison', 'owner-attention', 'assignment-history', 'nudge-history', 'lead-activity', 'hub-feeds', 'lead-summary', 'reply-source', 'learning-coverage', 'issue-coverage', 'bot-coverage', 'learning-plan', 'learning-evidence', 'game-status', 'spend-example', 'learning-artifacts', 'safety-records', 'ffxi-focus', 'ffxi-feeds']) document.getElementById(id).replaceChildren();
    if (ledgerBotId !== null && loadedSource && loadedSource !== source) {
      ledgerBotId = null; correlationFilter = ''; document.querySelector('#correlation').value = '';
    }
    currentSnapshot = data;
    clearRosterGapSelection();
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
    else if (feeds.some(f => f.status === 'Exported snapshot')) banner.textContent = feeds.every(f => f.status === 'Exported snapshot')
      ? 'Exported hub snapshot loaded. Data is as of its export time, not live; coverage and hub revision remain unverified.'
      : 'Some views come from an exported hub snapshot as of its export time, not live; other views use synthetic fallback. Check each feed.';
    else if (feeds.some(f => f.status === 'Unavailable')) banner.textContent = 'Hub data is partially or fully unavailable. Check each feed for synthetic fallback.';
    else if (feeds.length && feeds.every(f => f.status === 'Live response')) banner.textContent = 'Hub reads available. Coverage and deployed revision remain unverified.';
    else banner.textContent = 'Hub status unknown. Check source labels for each view.';
    feeds.forEach(f => item(document.querySelector('#hub-feeds'), `${routingText(f.game)} · ${routingText(f.view)}`, routingText(f.status), `${routingText(f.note)} · Fetched: ${routingText(f.at)}`));
    if (incomplete || !feeds.length) item(document.querySelector('#hub-feeds'), 'Feed coverage', 'Unknown', 'Missing or incomplete feed metadata does not establish availability.');
    const ffxiFeeds = feeds.filter(f => f.game === 'FFXI' || f.game === 'All');
    if (incomplete || !ffxiFeeds.length) item(document.querySelector('#ffxi-feeds'), 'FFXI feed coverage', 'Unknown', 'Missing or incomplete feed metadata; supplied rows do not establish complete FFXI coverage');
    ffxiFeeds.forEach(f => item(document.querySelector('#ffxi-feeds'), `${routingText(f.game)} · ${routingText(f.view)}`, routingText(f.status), `${routingText(f.note)} · Fetched: ${routingText(f.at)} · Not proof of game presence or delivery`));
    renderBotCoverage();
    renderPresenceExamples(data.presenceExamples);
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
    renderWakeVerification(data.wakeVerification);
    renderOperationSources(data.operationSources);
    renderCoordinatorPanels();
    renderLeadTimeline();
    renderQuotaHistory();
    renderSpendExample();
    renderModelCalls();
    renderAudit();
    renderRoutingAudit();
    renderIssueCoverage();
    renderIssues();
    renderLedger();
    renderLearningCoverage();
    renderLearningPlan();
    renderLearningArtifacts();
    renderLearning();
    renderDataCoverage();
    renderRosterGaps();
    document.querySelector('#updated').textContent = `Snapshot generated ${data.generatedAt} · Sources are labeled per view; lead task state comes from the coordinator board.`;
    loadedSource = source; sourceLoading = false;
    resetBotDraft();
    sessionStorage.setItem('dit-admin-token', token); workspace.hidden = false; form.hidden = true; loadBridge();
    if (selectedWorkspaceSection === null) {
      const id = globalThis.location?.hash?.slice(1);
      if (id) markWorkspaceTarget(id, document.getElementById(id));
      else markWorkspaceSection('overview');
    }
  } catch (e) {
    if (!current()) return;
    renderWakeVerification(null);
    renderOperationSources(null);
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
document.querySelector('#model-call-availability').addEventListener('change', () => { if (currentSnapshot) renderModelCalls(); });
document.querySelector('#reply-correlation').addEventListener('input', () => { if (currentSnapshot) renderReplySource(); });
document.querySelector('#reply-reset').addEventListener('click', () => {
  document.querySelector('#reply-correlation').value = '';
  if (currentSnapshot) renderReplySource();
});
document.querySelector('#assignment-prev').addEventListener('click', () => changeAssignmentPage(-1));
document.querySelector('#assignment-next').addEventListener('click', () => changeAssignmentPage(1));
document.querySelector('#audit-search').addEventListener('input', () => { if (currentSnapshot) renderAudit(); });
document.querySelector('#routing-audit-scope').addEventListener('change', () => { if (currentSnapshot) renderRoutingAudit(); });
document.querySelector('#routing-audit-outcome').addEventListener('change', () => { if (currentSnapshot) renderRoutingAudit(); });
document.querySelector('#routing-audit-reset').addEventListener('click', () => {
  document.querySelector('#routing-audit-scope').value = '';
  document.querySelector('#routing-audit-outcome').value = '';
  if (currentSnapshot) renderRoutingAudit();
});
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
document.getElementById('bot-draft-form').addEventListener('submit', previewBotDraft);
document.getElementById('bot-draft-cancel').addEventListener('click', resetBotDraft);
for (const id of ['bot-draft-goals', 'bot-draft-personality']) {
  document.getElementById(id).addEventListener('input', () => {
    if (!draftBot()) { resetBotDraft(); return; }
    document.getElementById('bot-draft-result').replaceChildren();
    document.getElementById(id).setAttribute('aria-invalid', 'false');
    document.getElementById('bot-draft-status').textContent = 'Draft changed. Preview again to review; nothing is saved or applied.';
  });
}
document.querySelector('#clear-bot').addEventListener('click', () => {
  selectedBotId = null;
  resetBotDraft();
  if (currentSnapshot) updateBotCount(filteredBots());
  const panel = document.querySelector('#bot-inspector');
  panel.replaceChildren(); panel.textContent = 'No bot selected.';
  if (currentSnapshot) { renderAssignments(); renderReplySource(); renderSafety(); if (document.querySelector('#issue-selected-bot').checked) renderIssues(); }
});
document.querySelector('#ffxi-evidence').addEventListener('click', () => {
  document.querySelector('#trace-game').value = 'ffxi';
  document.querySelector('#correlation').value = '';
  correlationFilter = ''; ledgerBotId = null; traceVersion++;
  document.querySelector('#hub-trace').replaceChildren();
  if (currentSnapshot) renderLedger();
  focusWorkspaceTarget('trace-search');
});
document.querySelector('#ffxi-bots').addEventListener('click', () => {
  rosterRecordIndex = null;
  document.querySelector('#bot-search').value = '';
  document.querySelector('#bot-identity').value = '';
  document.querySelector('#bot-game').value = 'FFXI';
  if (currentSnapshot) renderBots();
  focusWorkspaceTarget('bots');
});
document.querySelector('#bot-game').addEventListener('change', () => { rosterRecordIndex = null; if (currentSnapshot) renderBots(); });
document.querySelector('#bot-identity').addEventListener('change', () => { rosterRecordIndex = null; if (currentSnapshot) renderBots(); });
document.querySelector('#bot-search').addEventListener('input', () => { rosterRecordIndex = null; if (currentSnapshot) renderBots(); });
document.querySelector('#bot-reset').addEventListener('click', () => {
  rosterRecordIndex = null;
  document.querySelector('#bot-game').value = '';
  document.querySelector('#bot-search').value = '';
  document.querySelector('#bot-identity').value = '';
  if (currentSnapshot) renderBots();
});
document.querySelector('#ffxi-issues').addEventListener('click', () => {
  for (const id of ['issue-status', 'issue-search']) document.getElementById(id).value = '';
  document.querySelector('#issue-selected-bot').checked = false;
  document.querySelector('#issue-scope').value = 'FFXI';
  if (currentSnapshot) renderIssues();
  focusWorkspaceTarget('issues');
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
  focusWorkspaceTarget('learning');
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
  renderLearningEvidence(uniqueRecord(currentSnapshot?.learning, selectedLearningId));
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
  e.preventDefault(); ledgerBotId = null; correlationFilter = document.querySelector('#correlation').value.trim();
  if (currentSnapshot) renderLedger();
  if (document.querySelector('#data-source').value === 'hub') {
    if (sourceLoading || loadedSource !== 'hub') {
      traceVersion++; document.querySelector('#hub-trace').replaceChildren();
      document.querySelector('#hub-trace').textContent = 'Load the selected hub source successfully before requesting a hub trace.';
    } else loadHubTrace(correlationFilter);
  }
});
document.querySelector('#trace-clear').addEventListener('click', () => {
  correlationFilter = ''; ledgerBotId = null; document.querySelector('#correlation').value = ''; traceVersion++; document.querySelector('#hub-trace').replaceChildren();
  if (currentSnapshot) renderLedger();
});
if (token) load();
document.getElementById('back-to-roster').addEventListener('click', () => focusWorkspaceTarget('bots'));
