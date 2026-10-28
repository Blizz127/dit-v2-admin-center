const form = document.querySelector('#login');
const error = document.querySelector('#error');
const workspace = document.querySelector('#workspace');
let currentSnapshot = null;
let requestVersion = 0;
let traceVersion = 0;
let healthVersion = 0;
let selectedBotId = null;
let correlationFilter = '';
let bridgePending = false;
let selectedLearningId = null;
let token = sessionStorage.getItem('dit-admin-token') || '';
function item(parent, title, detail, meta) {
  const row = document.createElement('div'); row.className = 'row';
  const heading = document.createElement('strong'); heading.textContent = title;
  const text = document.createElement('p'); text.textContent = detail;
  const small = document.createElement('small'); small.textContent = meta || '';
  row.append(heading, text, small); parent.append(row);
}
async function loadHubHealth() {
  const id = ++healthVersion;
  const panel = document.querySelector('#hub-health');
  panel.replaceChildren();
  if (document.querySelector('#data-source').value !== 'hub') { panel.textContent = 'Select configured hub data before requesting this read-only check.'; return; }
  panel.textContent = 'Checking hub services…';
  try {
    const response = await fetch('/api/hub-health', {headers: {Authorization: `Bearer ${token}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    if (id !== healthVersion) return;
    panel.replaceChildren();
    item(panel, 'Hub service health', data.coverage, `${data.source} · Fetched: ${data.fetchedAt} · Snapshot may be stale`);
    if (!data.services.length) item(panel, 'No matching service records', 'Coverage is unknown.', 'Empty data does not establish healthy services.');
    data.services.forEach(s => item(panel, `${s.game} · ${s.label}`, s.state, `Observed: ${s.observedAt || 'unknown'} · Service state is not bot presence`));
  } catch (_) { if (id === healthVersion) panel.textContent = 'Hub service health unavailable; current state is unknown.'; }
}
async function loadBridge() {
  if (bridgePending || !token || workspace.hidden) return;
  bridgePending = true;
  const panel = document.querySelector('#bridge-status');
  try {
    const response = await fetch('/api/bridge-status', {headers: {Authorization: `Bearer ${token}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    panel.replaceChildren();
    item(panel, `Unit: ${data.unit} · ${data.substate}`, `Result: ${data.result} · Fault marker: ${data.marker} · Classification: ${data.markerReason || 'unknown'}`, `${data.source} · Observed: ${data.observedAt || 'unknown'} · Marker absence does not prove delivery`);
    const focus = document.querySelector('#ffxi-focus-bridge');
    focus.replaceChildren();
    item(focus, `Bridge: ${data.unit} · ${data.substate}`, `Fault marker: ${data.marker} · Classification: ${data.markerReason || 'unknown'}`, `${data.source} · Observed: ${data.observedAt || 'unknown'} · Not proof of delivery`);
  } catch (_) {
    panel.replaceChildren();
    panel.textContent = 'Bridge status unknown; read-only observation unavailable.';
    const focus = document.querySelector('#ffxi-focus-bridge');
    focus.replaceChildren();
    focus.textContent = 'Bridge observation unknown; delivery remains unverified.';
  }
  finally { bridgePending = false; }
}
function renderQuotaHistory() {
  const panel = document.querySelector('#quota-history');
  const window = document.querySelector('#quota-window').value;
  const records = currentSnapshot.quotaHistory.filter(q => !window || q.window === window);
  panel.replaceChildren();
  if (!records.length) item(panel, 'No matching observations', 'Quota history for this filter is unknown.', 'No account refresh is performed.');
  records.forEach(q => item(panel, `Account ${q.account} · ${q.window}`, `Remaining: ${q.remainingPercent}% at observation`, `Observed: ${q.observedAt} · Cached Codex state; may be stale`));
}
function renderLeadTimeline() {
  const panel = document.querySelector('#lead-timeline');
  const filter = document.querySelector('#timeline-kind').value;
  const kinds = {watcher: ['Watcher alert', 'Watcher classification'], task: ['Task status'], session: ['Session activity'], commit: ['Checkout commit']};
  panel.replaceChildren();
  currentSnapshot.leadTimeline.forEach(t => {
    item(panel, t.lead, t.coverage, `${t.watchCoverage} · ${t.commitCoverage}`);
    const group = panel.lastElementChild;
    const events = t.events.filter(e => !filter || (kinds[filter] || []).includes(e.kind));
    if (!events.length) item(group, 'No matching evidence', 'This filter has no records in the available history.', 'Current activity remains unknown.');
    events.forEach(e => item(group, `${e.kind}: ${e.status}`, e.at, e.source));
  });
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
  const query = (document.querySelector('#issue-search').value || '').trim().toLowerCase();
  panel.replaceChildren();
  const records = currentSnapshot.issues.filter(i => (!scope || i.scope === scope) && (!status || i.status === status) && (!selectedOnly || (selectedBotId !== null && i.botId === selectedBotId)) && (!query || `${i.title} ${i.detail}`.toLowerCase().includes(query)));
  document.querySelector('#issue-count').textContent = `Showing ${records.length} of ${currentSnapshot.issues.length} loaded issue records; coverage may be incomplete.`;
  if (!records.length) item(panel, 'No matching issues', selectedOnly && selectedBotId === null ? 'Select a bot to use this filter.' : 'No matching records in the loaded data.', 'This does not establish a healthy state.');
  records.forEach(i => {
    item(panel, i.title, i.detail, `${i.scope} · ${i.status} · ${i.source} · ${i.timeLabel || 'Updated'}: ${i.updatedAt || 'unknown'}`);
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
    if (i.botId && currentSnapshot.bots.some(b => b.id === i.botId)) {
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
  const panel = document.querySelector('#learning-inspector');
  panel.replaceChildren();
  const need = currentSnapshot.learning.find(l => l.id === id);
  if (!need) { panel.textContent = 'Selected learning need is no longer in this snapshot.'; return; }
  item(panel, `Learning detail · ${need.game} · ${need.topic}`, `Status: ${need.status} · Phase: ${need.phase || 'Not reported'} · Reason: ${need.reason || 'Not reported'} · Escalation: ${need.escalation || 'Not reported'} · Retry at: ${need.retryAt || 'Not reported'}`,
    `Evidence: ${need.evidence} · Datasets: ${need.datasets} · Policy verification: ${need.policy} · Updated: ${need.updatedAt || 'unknown'} · ${need.source}`);
  const issues = currentSnapshot.issues.filter(i => i.learningId === need.id);
  if (!issues.length) item(panel, 'Related issues', 'No matching issue records in this view.', 'This does not establish a resolved learning gap.');
  issues.forEach(i => item(panel, `Related issue · ${i.title}`, `${i.status} · ${i.detail}`, `${i.source} · ${i.timeLabel || 'Updated'}: ${i.updatedAt || 'unknown'}`));
}
function renderLearningArtifacts() {
  const panel = document.querySelector('#learning-artifacts');
  const game = document.querySelector('#learning-game').value;
  const rows = currentSnapshot.learningArtifacts.filter(a => !game || a.game === game);
  panel.replaceChildren();
  if (!rows.length) item(panel, 'No artifact examples', 'No matching synthetic records.', 'This does not establish real artifact coverage.');
  rows.forEach(a => item(panel, `${a.game} · ${a.kind} · ${a.name}`, `Validation: ${a.validation} · Adoption: ${a.adoption} · Demonstrated outcome: ${a.outcome}`, `Version: ${a.version || 'unknown'} · ${a.source} · Observed: ${a.observedAt || 'unknown'}`));
}
function renderLearningPlan() {
  const panel = document.querySelector('#learning-plan');
  const game = document.querySelector('#learning-game').value;
  const rows = currentSnapshot.learningPlan.filter(p => !game || p.game === game);
  panel.replaceChildren();
  if (!rows.length) item(panel, 'No planning topics', 'No topics for this filter.', 'This does not establish coverage.');
  rows.forEach(p => item(panel, `${p.game} · ${p.topic}`, p.next, `Evidence: ${p.evidence || 'Unknown'} · Datasets: ${p.datasets || 'Unknown'} · Policy: ${p.policy || 'Unknown'} · ${p.source}`));
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
function renderLearning() {
  const panel = document.querySelector('#learning');
  const game = document.querySelector('#learning-game').value;
  const status = document.querySelector('#learning-status').value;
  const attention = document.querySelector('#learning-attention').checked;
  const attentionStatuses = new Set(['Needs evidence', 'Needs inventory', 'unverified', 'failed', 'canceled', 'cancelled']);
  const query = (document.querySelector('#learning-search').value || '').trim().toLowerCase();
  panel.replaceChildren();
  const records = currentSnapshot.learning.filter(l => (!game || l.game === game) && (!status || l.status === status) && (!attention || attentionStatuses.has(l.status)) && (!query || `${l.topic} ${l.reason || ''}`.toLowerCase().includes(query)));
  document.querySelector('#learning-count').textContent = `Showing ${records.length} of ${currentSnapshot.learning.length} loaded learning records; coverage may be incomplete.`;
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
}
async function loadHubTrace(correlation) {
  const id = ++traceVersion;
  const panel = document.querySelector('#hub-trace');
  panel.replaceChildren();
  if (!/^[A-Za-z0-9_.:-]{1,128}$/.test(correlation)) { panel.textContent = 'Enter a correlation ID using letters, numbers, dot, dash, underscore or colon.'; return; }
  const game = document.querySelector('#trace-game').value;
  if (!['ffxi', 'swtor'].includes(game)) { panel.textContent = 'Choose a supported game.'; return; }
  panel.textContent = 'Loading read-only trace…';
  try {
    const response = await fetch(`/api/trace?gameId=${encodeURIComponent(game)}&correlationId=${encodeURIComponent(correlation)}`, {headers: {Authorization: `Bearer ${token}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    if (id !== traceVersion) return;
    panel.replaceChildren();
    item(panel, `Hub trace · ${game.toUpperCase()} · ${correlation}`, data.coverage, `Fetched: ${data.fetchedAt} · Deployed revision unverified`);
    if (!data.records.length) item(panel, 'No matching trace records', 'No matching records in the bounded trace window.', 'This does not prove an action did or did not occur.');
    data.records.forEach(r => item(panel, `${r.kind || 'Unknown'} · ${r.type || 'Unknown'}`, `Disposition: ${r.disposition || 'Unknown'} · Classification: ${r.classification || 'Unknown'} · Final: ${r.isFinal == null ? 'Unknown' : r.isFinal}`, `Occurred: ${r.occurredAt || 'unknown'} · Raw envelope body omitted`));
  } catch (_) { if (id === traceVersion) panel.textContent = 'Hub trace unavailable; no delivery or outcome can be inferred.'; }
}
function renderLedger() {
  const panel = document.querySelector('#ledger');
  panel.replaceChildren();
  const records = currentSnapshot.ledger.filter(e => !correlationFilter || e.correlationId === correlationFilter);
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
function renderBots() {
  const panel = document.querySelector('#bots');
  const game = document.querySelector('#bot-game').value;
  const query = (document.querySelector('#bot-search').value || '').trim().toLowerCase();
  const bots = currentSnapshot.bots.filter(b => (!game || b.game === game) && (!query || b.name.toLowerCase().includes(query)));
  panel.replaceChildren();
  document.querySelector('#bot-count').textContent = `Showing ${bots.length} of ${currentSnapshot.bots.length} loaded roster records; coverage and presence may be unknown.`;
  if (!bots.length) item(panel, 'No matching roster records', 'No matches in the loaded data.', 'This does not establish that a bot is offline.');
  else bots.forEach(botItem);
}
function renderSafety() {
  const panel = document.querySelector('#safety-records');
  panel.replaceChildren();
  const records = currentSnapshot.safetyRecords.filter(r => r.botId == null || (selectedBotId !== null && r.botId === selectedBotId));
  if (!records.length) item(panel, 'No safety examples', 'Actual gate and kill-switch states are unknown.', 'No operational controls connected');
  records.forEach(r => item(panel, r.scope, `Example gate: ${r.gate || 'Unknown'} · Example kill switch: ${r.killSwitch || 'Unknown'}`, `${r.source} · Observed: ${r.observedAt || 'unknown'} · Actual state unknown`));
}
function renderReplySource() {
  const panel = document.querySelector('#reply-source');
  panel.replaceChildren();
  if (!selectedBotId) { item(panel, 'No bot selected', 'Select a bot to inspect reply examples.', 'No live reply data is connected.'); return; }
  const bot = currentSnapshot.bots.find(b => b.id === selectedBotId);
  const rows = currentSnapshot.replyEvents.filter(r => r.botId === selectedBotId);
  if (!bot || !rows.length) { item(panel, 'No matching reply evidence', 'Source, fallback and delivery are unknown.', 'Absence of records does not prove no reply occurred.'); return; }
  rows.forEach(r => item(panel, `${bot.name} · ${r.wordingOrigin || 'Unknown source'}`, `Generation: ${r.generationStatus || 'Unknown'} · Fallback: ${r.fallbackPolicy || 'Unknown'} · Reason: ${r.fallbackReason || 'Not reported'}`, `Delivery: ${r.delivery || 'Unknown'} · Verification: ${r.verification || 'Unknown'} · Correlation: ${r.correlationId || 'unknown'} · ${r.source} · Observed: ${r.observedAt || 'unknown'}`));
}
function renderAssignments() {
  const panel = document.querySelector('#assignment-history');
  panel.replaceChildren();
  if (!selectedBotId) { item(panel, 'No bot selected', 'Select a bot to view synthetic assignment examples.', 'Real assignment history is unavailable.'); return; }
  const bot = currentSnapshot.bots.find(b => b.id === selectedBotId);
  const rows = currentSnapshot.assignmentHistory.filter(a => a.botId === selectedBotId);
  if (!bot || !rows.length) { item(panel, 'No matching examples', 'No synthetic assignment history is available for this bot.', 'This does not prove no real assignment exists.'); return; }
  rows.forEach(a => item(panel, `${bot.name} · ${routingText(a.purpose)}`, `Requested: ${routingText(a.requested)} · Effective: ${routingText(a.effective)}`, `Version: ${routingText(a.version)} · Recorded: ${routingText(a.at, 'unknown')} · ${routingText(a.source)}`));
}
function rosterDetails(bot) {
  return `Status: ${routingText(bot.status)} · Character: ${routingText(bot.character)} · Level: ${routingText(bot.level)} · Body kind: ${routingText(bot.bodyKind)}`;
}
function inspectBot(id) {
  selectedBotId = id;
  renderSafety();
  if (document.querySelector('#issue-selected-bot').checked) renderIssues();
  renderAssignments();
  renderReplySource();
  const panel = document.querySelector('#bot-inspector');
  panel.replaceChildren();
  const bot = currentSnapshot.bots.find(b => b.id === id);
  if (!bot) { panel.textContent = 'Selected bot is no longer in this snapshot.'; return; }
  item(panel, `${bot.name} · ${bot.game}`, rosterDetails(bot), `${bot.source} · Observed: ${bot.observedAt || 'unknown'}`);
  item(panel, 'Reported personality summary', routingText(bot.personalitySummary), `${bot.source} · Roster metadata, not proof of behavior`);
  const details = currentSnapshot.botDetails.find(d => d.botId === bot.id);
  if (!details) item(panel, 'Goals and memory', 'Unknown', 'No bot detail record in this view; missing data does not establish absence.');
  else {
    const meta = `${details.source} · Observed: ${details.observedAt || 'unknown'}`;
    if (!details.goals.length) item(panel, 'Goals', 'Unknown', meta);
    details.goals.forEach(g => item(panel, `Goal · ${g.text}`, `Status: ${g.status} · Evidence: ${g.evidence}`, meta));
    if (!details.memories.length) item(panel, 'Memory', 'Unknown', meta);
    details.memories.forEach(m => item(panel, `Memory · ${m.text}`, `Grounding: ${m.grounding}`, meta));
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
function botItem(bot) {
  const parent = document.querySelector('#bots');
  item(parent, `${bot.name} · ${bot.game}`, rosterDetails(bot), `${bot.source} · Observed: ${bot.observedAt || 'unknown'}`);
  const row = parent.lastElementChild;
  const inspect = document.createElement('button');
  inspect.type = 'button';
  inspect.textContent = `Inspect ${bot.name}`;
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
  error.textContent = '';
  document.querySelector('#hub-banner').textContent = 'Loading selected data source…';
  try {
    const source = document.querySelector('#data-source').value === 'hub' ? 'hub' : 'mock';
    const response = await fetch(`/api/overview?source=${source}`, {headers: {Authorization: `Bearer ${token}`}, cache: 'no-store'});
    if (requestId !== requestVersion) return;
    if (!response.ok) throw new Error(response.status === 401 ? 'Token was not accepted.' : 'Could not load the workspace.');
    const data = await response.json();
    if (requestId !== requestVersion) return;
    for (const id of ['bots', 'leads', 'issues', 'ledger', 'learning', 'lead-monitoring', 'audit', 'service-health', 'lead-timeline', 'quota-history', 'session-markers', 'model-calls', 'owner-attention', 'assignment-history', 'nudge-history', 'lead-activity', 'hub-feeds', 'lead-summary', 'reply-source', 'learning-coverage', 'issue-coverage', 'bot-coverage', 'learning-plan', 'game-status', 'spend-example', 'learning-artifacts', 'safety-records', 'ffxi-focus']) document.getElementById(id).replaceChildren();
    currentSnapshot = data;
    if (data.ffxiFocus) {
      const f = data.ffxiFocus, target = document.querySelector('#ffxi-focus');
      item(target, 'Closest documented slice', f.closest, f.source);
      item(target, 'What to look for', f.whatToLookFor, 'Readiness must be confirmed by the owning lead');
      item(target, 'How to toggle', f.toggle, 'Read only');
      item(target, 'Not yet verified', f.unverified, 'A bridge observation does not establish delivery');
    }
    item(document.querySelector('#owner-attention'), 'Coverage', data.ownerAttention.coverage, 'Coordinator task board · Read only');
    if (!data.ownerAttention.items.length) item(document.querySelector('#owner-attention'), 'No records listed', 'Other owner decisions may be tracked elsewhere.', 'Not a complete decision inventory');
    data.ownerAttention.items.forEach(a => item(document.querySelector('#owner-attention'), a.title, a.project, `Created: ${a.createdAt} · Expires: ${a.expiresAt} · Coordinator approval record`));
    const feeds = data.hubFeeds;
    const banner = document.querySelector('#hub-banner');
    if (feeds.some(f => f.status === 'Not configured')) banner.textContent = 'Hub not configured. Bot and learning views use synthetic fallback.';
    else if (feeds.some(f => f.status === 'Mock selected')) banner.textContent = 'Synthetic examples selected. No hub read was attempted.';
    else if (feeds.some(f => f.status === 'Invalid configuration')) banner.textContent = 'Hub configuration invalid. Bot and learning views use synthetic fallback.';
    else if (feeds.some(f => f.status === 'Unavailable')) banner.textContent = 'Hub data is partially or fully unavailable. Check each feed for synthetic fallback.';
    else if (feeds.length && feeds.every(f => f.status === 'Live response')) banner.textContent = 'Hub reads available. Coverage and deployed revision remain unverified.';
    else banner.textContent = 'Hub status unknown. Check source labels for each view.';
    data.hubFeeds.forEach(f => item(document.querySelector('#hub-feeds'), `${f.game} · ${f.view}`, f.status, `${f.note} · Fetched: ${f.at || 'unknown'}`));
    renderBotCoverage();
    renderBots();
    if (selectedBotId !== null) inspectBot(selectedBotId);
    else { renderAssignments(); renderReplySource(); renderSafety(); }
    data.gameStatus.forEach(s => item(document.querySelector('#game-status'), s.game, `XP rate: ${s.xpRate == null ? 'Unknown' : s.xpRate + '×'} · Server liveness: ${s.liveness}`, `${s.source} · Checked: ${s.checkedAt || 'unknown'} · Freshness unknown`));
    data.serviceHealth.forEach(h => item(document.querySelector('#service-health'), `${h.label} · ${h.game}`, `${h.status} · ${h.detail}`, `${h.source} · Observed: ${h.observedAt || 'unknown'} · May be stale`));
    data.leads.forEach(l => item(document.querySelector('#leads'), `${l.name} · ${l.scope}`, l.status, `${l.source} · Observed: ${l.observedAt || 'unknown'}`));
    if (!data.leadMonitoring.length) item(document.querySelector('#lead-summary'), 'No lead observations', 'Stall and quota are unknown.', 'Coordinator data unavailable or empty');
    data.leadMonitoring.forEach(m => item(document.querySelector('#lead-summary'), m.lead, `Stall: ${m.stall || 'Unknown'} · Lead quota: ${m.quota || 'Unknown'}`, `${m.stallReason || 'No watcher data'} · ${m.quotaReason || 'No per-lead quota data'} · Shared provider pool: ${m.poolCapacity || 'Unknown'} (${m.poolReason || 'Unavailable'})`));
    data.leadMonitoring.forEach(m => item(document.querySelector('#lead-monitoring'), m.lead, `Stall: ${m.stall} · Quota: ${m.quota}`, `Session activity: ${m.sessionActivity} (not proof of work or a stall) · ${m.stallReason} · ${m.quotaReason} · Provider pool: ${m.poolCapacity} (${m.poolReason})`));
    data.leadActivity.forEach(a => item(document.querySelector('#lead-activity'), a.lead, `Task: ${a.taskStatus} · ${a.taskSummary}`, `Task updated: ${a.taskUpdatedAt || 'unknown'} · ${a.taskSource} · Checkout HEAD commit: ${a.commitAt || 'unknown'} · ${a.commitSource}`));
    renderLeadTimeline();
    data.nudgeHistory.forEach(lead => {
      const panel = document.querySelector('#nudge-history');
      item(panel, lead.lead, lead.coverage, 'Read-only coordinator metadata');
      const group = panel.lastElementChild;
      if (!lead.nudges.length) item(group, 'No matching records', 'Coverage may be incomplete.', 'Resume state unknown');
      lead.nudges.forEach(n => item(group, `Nudge · ${n.messageStatus}`, `Created: ${n.createdAt} · Delivered: ${n.deliveredAt || 'unknown'} · Reply: ${n.repliedAt || 'unknown'}`, `Time to reply: ${n.replySeconds == null ? 'unknown' : n.replySeconds + ' s'} · Time to resume: unknown${n.resumeSignal ? ` · ${n.resumeSignal.label}: ${n.resumeSignal.seconds} s at ${n.resumeSignal.observedAt}` : ' · Tool activity heuristic: unknown'} · ${n.source}`));
    });
    data.sessionMarkers.forEach(report => {
      item(document.querySelector('#session-markers'), report.lead, report.coverage, 'Heuristic; no rollout text is displayed');
      report.markers.forEach(m => item(document.querySelector('#session-markers'), m.kind, m.observedAt, `${m.source} · Historical; current state unknown`));
    });
    renderQuotaHistory();
    const spend = data.spendExample;
    const usd = value => typeof value === 'number' ? `$${value.toFixed(2)}` : 'Unknown';
    item(document.querySelector('#spend-example'), `Example month: ${spend.month || 'Unknown'}`, `Settled: ${usd(spend.settledUsd)} · Open reservations: ${usd(spend.reservedOpenUsd)} · Budget: ${usd(spend.budgetUsd)}`, `${spend.source} · ${spend.attribution} · Observed: ${spend.fetchedAt || 'unknown'} · Separate ledgers are not reconciled.`);
    data.modelCalls.forEach(c => item(document.querySelector('#model-calls'), `${c.model} · ${c.purpose}`, `Latency: ${typeof c.latencyMs === 'number' ? c.latencyMs + ' ms' : 'Unknown'} · Cost: ${c.cost == null ? 'Unknown' : c.cost} · Quality: ${c.quality == null ? 'Unknown' : c.quality}`, `${c.source} · Observed: ${c.observedAt || 'unknown'}`));
    data.audit.forEach(a => item(document.querySelector('#audit'), `${a.action} · ${a.scope}`, a.result, `${a.actor} · ${a.at || 'unknown time'} · ${a.source}`));
    renderIssueCoverage();
    renderIssues();
    renderLedger();
    renderLearningCoverage();
    renderLearningPlan();
    renderLearningArtifacts();
    renderLearning();
    document.querySelector('#updated').textContent = `Snapshot generated ${data.generatedAt} · Sources are labeled per view; lead task state comes from the coordinator board.`;
    sessionStorage.setItem('dit-admin-token', token); workspace.hidden = false; form.hidden = true; loadBridge();
  } catch (e) { if (requestId !== requestVersion) return; workspace.hidden = true; form.hidden = false; sessionStorage.removeItem('dit-admin-token'); error.textContent = e.message; }
}
form.addEventListener('submit', e => { e.preventDefault(); token = document.querySelector('#token').value; document.querySelector('#token').value = ''; load(); });
document.querySelector('#refresh').addEventListener('click', load);
document.querySelector('#bridge-refresh').addEventListener('click', loadBridge);
document.querySelector('#hub-health-refresh').addEventListener('click', loadHubHealth);
if (typeof setInterval === 'function') setInterval(() => { if (document.visibilityState !== 'hidden') loadBridge(); }, 15000);
document.querySelector('#data-source').addEventListener('change', () => { traceVersion++; healthVersion++; document.querySelector('#hub-trace').replaceChildren(); document.querySelector('#hub-health').textContent = 'Not requested.'; return load(); });
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
  const panel = document.querySelector('#bot-inspector');
  panel.replaceChildren(); panel.textContent = 'No bot selected.';
  if (currentSnapshot) { renderAssignments(); renderReplySource(); renderSafety(); if (document.querySelector('#issue-selected-bot').checked) renderIssues(); }
});
document.querySelector('#bot-game').addEventListener('change', () => { if (currentSnapshot) renderBots(); });
document.querySelector('#bot-search').addEventListener('input', () => { if (currentSnapshot) renderBots(); });
document.querySelector('#bot-reset').addEventListener('click', () => {
  document.querySelector('#bot-game').value = '';
  document.querySelector('#bot-search').value = '';
  if (currentSnapshot) renderBots();
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
document.querySelector('#ffxi-learning').addEventListener('click', () => {
  for (const id of ['learning-status', 'learning-search']) document.getElementById(id).value = '';
  document.querySelector('#learning-attention').checked = false;
  document.querySelector('#learning-game').value = 'FFXI';
  if (currentSnapshot) { renderLearningPlan(); renderLearningArtifacts(); renderLearning(); }
  document.querySelector('#learning').scrollIntoView({behavior: 'smooth', block: 'nearest'});
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
  if (document.querySelector('#data-source').value === 'hub') loadHubTrace(correlationFilter);
});
document.querySelector('#trace-clear').addEventListener('click', () => {
  correlationFilter = ''; document.querySelector('#correlation').value = ''; traceVersion++; document.querySelector('#hub-trace').replaceChildren();
  if (currentSnapshot) renderLedger();
});
if (token) load();
