const form = document.getElementById('login');
const error = document.getElementById('error');
const workspace = document.getElementById('workspace');
let currentSnapshot = null;
let loadedSource = null;
let sourceLoading = false;
let requestVersion = 0;
let traceVersion = 0;
let healthVersion = 0;
let interactionVersion = 0;
let sessionVersion = 0;
let contextCaptureVersion = 0;
let deliveryCaptureVersion = 0;
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
async function readBoundedJson(response, limit = 16 * 1024 * 1024) {
  let data;
  if (response.body && typeof response.body.getReader === 'function') {
    const reader = response.body.getReader(), decoder = new TextDecoder('utf-8', {fatal: true});
    let size = 0, text = '';
    try {
      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        size += chunk.value.byteLength;
        if (size > limit) throw new Error('response too large');
        text += decoder.decode(chunk.value, {stream: true});
      }
      data = JSON.parse(text + decoder.decode());
    } catch (error) {
      try { await reader.cancel(); } catch (_) {}
      throw error;
    }
  } else {
    // A null body fails JSON parsing in a browser; test doubles supply json().
    data = await response.json();
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    const error = new Error('invalid response'); error.invalidShape = true; throw error;
  }
  const pending = [[data, 0]];
  while (pending.length) {
    const [value, depth] = pending.pop();
    if (depth > 128) throw new Error('response too deeply nested');
    if (value && typeof value === 'object') {
      for (const child of Object.values(value)) if (child && typeof child === 'object') pending.push([child, depth + 1]);
    }
  }
  return data;
}
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
  resetContextCapture();
  resetDeliveryCapture();
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
  document.getElementById('reply-correlation').value = '';
  document.getElementById('reply-count').textContent = 'Select a bot to view reply examples.';
  document.getElementById('model-call-availability').value = '';
  document.getElementById('model-call-coverage').textContent = 'Metric coverage unknown.';
  document.getElementById('data-coverage').replaceChildren();
  document.getElementById('bot-identity').value = '';
  document.getElementById('bot-activity-engine').value = '';
  document.getElementById('bot-activity-sources').replaceChildren(); botActivitySearch.clear();
  document.getElementById('bot-activity-label').textContent = ''; document.getElementById('bot-activity-note').textContent = '';
  document.getElementById('bot-activity-search').value = '';
  document.getElementById('bot-activity-coverage').textContent = 'Coverage unknown.';
  document.getElementById('bot-activity-count').textContent = '';
  document.getElementById('bot-activity').replaceChildren();
  resetBaselineConformance();
  clearRosterGapSelection();
  document.getElementById('roster-gaps').replaceChildren();
  ledgerBotId = null; correlationFilter = '';
  document.getElementById('correlation').value = '';
  document.getElementById('ledger').replaceChildren();
  document.getElementById('ledger-filter').textContent = 'No ledger snapshot loaded in this session.';
  document.getElementById('ledger-count').textContent = 'Ledger example count unknown.';
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
function resetContextCapture() {
  contextCaptureVersion++;
  const panel = document.getElementById('context-capture');
  if (panel) { panel.replaceChildren(); panel.textContent = 'Not requested in this session.'; }
  const button = document.getElementById('context-capture-load');
  if (button) button.disabled = false;
}
function renderContextCapture(data) {
  const panel = document.getElementById('context-capture');
  panel.replaceChildren();
  if (data.status === 'Not configured' && data.capture === null) { panel.textContent = 'No offline capture configured.'; return; }
  const capture = data.capture, receipt = capture?.contextReceipt, binding = capture?.statusBinding, view = binding?.View;
  const fieldNames = ['Presence', 'Location', 'Activity', 'Party', 'Job', 'Level'];
  const unbound = view === null && ['source unavailable', 'source read failed', 'source binding mismatch'].includes(binding?.State);
  if (data.status !== 'Loaded' || capture?.schema !== 'dit.context-status-integration.v1' || capture.synthetic !== true
      || !['ffxi', 'swtor'].includes(capture.game) || !['companion', 'heard', 'intent'].includes(capture.path)
      || capture.delivery !== 'not attempted' || capture.modelCall !== 'not attempted'
      || !receipt || binding?.RequestId !== receipt.RequestId
      || (!unbound && (!view || !Array.isArray(view.Fields) || view.Fields.length !== 6 || !['snapshot projected', 'snapshot unavailable'].includes(binding.State)))
      || typeof capture.systemMessage !== 'string' || typeof capture.userMessage !== 'string') throw new Error('invalid capture');
  if (!Array.isArray(capture.suppliedHistory) || capture.suppliedHistory.length > 32
      || capture.suppliedHistory.some(turn => typeof turn !== 'string' || !turn.trim() || turn.length > 512)
      || !['SuppliedHistoryTurns', 'IncludedHistoryTurns', 'OmittedHistoryTurns', 'SerializedCharacters', 'MaximumSerializedCharacters']
        .every(key => Number.isSafeInteger(receipt[key]) && receipt[key] >= 0)
      || receipt.SuppliedHistoryTurns !== capture.suppliedHistory.length
      || receipt.IncludedHistoryTurns + receipt.OmittedHistoryTurns !== receipt.SuppliedHistoryTurns) throw new Error('invalid captured coverage');
  if (!capture.systemMessage.trim() || !capture.userMessage.trim()
      || receipt.MaximumSerializedCharacters !== 24576
      || receipt.SerializedCharacters !== capture.systemMessage.length + capture.userMessage.length
      || receipt.SerializedCharacters > receipt.MaximumSerializedCharacters
      || typeof receipt.PromptSha256 !== 'string' || !/^[0-9a-f]{64}$/.test(receipt.PromptSha256)) throw new Error('invalid prompt receipt');
  const lookup = binding.Lookup;
  const scopeText = value => typeof value === 'string' && value.trim().length > 0 && value.length <= 128;
  if (lookup?.Game !== capture.game || !scopeText(lookup.ServerInstance) || !scopeText(lookup.ActorKey)) throw new Error('invalid scope');
  if (!unbound && (view.Body?.Game !== capture.game || view.Body.Instance !== lookup.ServerInstance
      || !['Realm', 'Instance', 'NativeActorId'].every(key => scopeText(view.Body[key])) || !scopeText(view.Epoch))) throw new Error('invalid body scope');
  if (unbound) {
    const approved = capture.userMessage.split('APPROVED FACTS\n')[1]?.split('\n\n')[0].split('\n').filter(line => line.startsWith('- native_status_'));
    const expected = fieldNames.map(field => `- native_status_${field.toLowerCase()}_state: unknown: ${binding.State}`);
    if (!approved || JSON.stringify(approved) !== JSON.stringify(expected)) throw new Error('unbound status has values');
  } else if (binding.State === 'snapshot unavailable' && (view.Source !== null || view.RevisionSha256 !== null
      || view.Fields.some(field => field?.State !== 'Unknown' || field.ObservedAtUtc !== null || field.ValidUntilUtc !== null))) throw new Error('invalid unavailable snapshot');
  const fields = unbound ? fieldNames.map(Field => ({Field, State:'Unknown', Value:null, Reason:binding.State})) : view.Fields;
  for (const [index, field] of fields.entries()) {
    if (!field || !['Known', 'Stale', 'Unknown'].includes(field.State) || field.Field !== fieldNames[index]
        || typeof field.Reason !== 'string' || (field.State === 'Known' ? typeof field.Value !== 'string' : field.Value !== null)) throw new Error('invalid field');
  }
  const presence = fields[0];
  if (presence.State === 'Known' && !['online', 'offline'].includes(presence.Value)) throw new Error('invalid presence');
  if ((presence.State !== 'Known' || presence.Value !== 'online') && fields.slice(1).some(field => field.State !== 'Unknown'))
    throw new Error('body status requires confirmed online presence');
  item(panel, `${capture.game.toUpperCase()} · ${capture.path} · Synthetic captured packet`,
    `${receipt.IncludedHistoryTurns} / ${receipt.SuppliedHistoryTurns} captured input turns retained; ${receipt.OmittedHistoryTurns} omitted.`,
    'No real model call or delivery attempted. Counts start at this captured input; earlier producer omissions are not measured. This packet is independent of roster selection.');
  item(panel, 'Captured prompt receipt', `${receipt.SerializedCharacters} / ${receipt.MaximumSerializedCharacters} UTF-16 characters · Token count: Unknown`,
    `Supplied prompt SHA-256: ${receipt.PromptSha256}`);
  item(panel, 'Requested bot scope', `Game ${lookup.Game} · instance ${lookup.ServerInstance} · actor key ${lookup.ActorKey}`,
    'Lookup recorded for this captured request. The native body has its own identity.');
  if (!unbound) item(panel, 'Native body in capture', `Game ${view.Body.Game} · realm ${view.Body.Realm} · instance ${view.Body.Instance} · native actor ${view.Body.NativeActorId}`,
    `Session epoch ${view.Epoch}. Captured binding only; presence and field freshness are shown separately.`);
  item(panel, 'Live native status', 'Unknown',
    'Field states describe the synthetic captured read, not the time this page was opened. No live producer evidence is supplied.');
  for (const field of fields) {
    item(panel, field.Field, `${field.State} · ${field.Value ?? 'Value withheld'}`,
      `State at captured read · ${field.Reason} · Captured observation: ${routingText(field.ObservedAtUtc, 'Unknown (not supplied)')} · Captured validity deadline: ${routingText(field.ValidUntilUtc, 'Unknown (not supplied)')}`);
  }
  if (unbound) item(panel, 'Native status unavailable', binding.State,
    `Request ${receipt.RequestId} · No native body or status revision is bound. Conversation context remains inspectable.`);
  else item(panel, 'Captured source', `${view.Source ?? 'Unavailable'} · policy ${view.FreshnessPolicyVersion} · read ${view.ReadAtUtc}`,
    `Request ${receipt.RequestId} · status revision ${view.RevisionSha256 ?? 'Unavailable'}. Artifact consistency is not producer authenticity or live health.`);
  const details = document.createElement('details'), summary = document.createElement('summary'), prompt = document.createElement('pre');
  summary.textContent = 'Exact captured prompt';
  prompt.setAttribute('tabindex', '0'); prompt.setAttribute('aria-label', 'Exact captured prompt');
  prompt.textContent = `SYSTEM\n${capture.systemMessage}\n\nUSER\n${capture.userMessage}`;
  details.append(summary, prompt); panel.append(details);
}
async function loadContextCapture() {
  if (!token || workspace.hidden) return;
  const id = ++contextCaptureVersion, requestToken = token, session = sessionVersion;
  const panel = document.getElementById('context-capture'), button = document.getElementById('context-capture-load');
  const current = () => id === contextCaptureVersion && panelSessionCurrent(requestToken, session);
  panel.replaceChildren(); panel.textContent = 'Loading configured offline capture…'; button.disabled = true;
  try {
    const response = await fetch('/api/context-capture', {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await readBoundedJson(response, 512 * 1024);
    if (current()) renderContextCapture(data);
  } catch (_) {
    if (current()) { panel.replaceChildren(); panel.textContent = 'Offline capture unavailable. Previous packet content has been cleared.'; }
  } finally { if (current()) button.disabled = false; }
}
document.getElementById('context-capture-load')?.addEventListener('click', loadContextCapture);
function resetDeliveryCapture() {
  deliveryCaptureVersion++;
  const panel = document.getElementById('delivery-capture');
  if (panel) { panel.replaceChildren(); panel.textContent = 'Not requested in this session.'; }
  const button = document.getElementById('delivery-capture-load');
  if (button) button.disabled = false;
}
function renderDeliveryCapture(data) {
  const panel = document.getElementById('delivery-capture');
  panel.replaceChildren();
  if (data?.schema !== 'dit.delivery-correlation-report.v1' || data.evidenceKind !== 'synthetic'
      || data.nativeDeliveryVerified !== false || data.deliveredInGame !== null || data.replayAuthorized !== false
      || !Array.isArray(data.records) || data.records.length > 256) throw new Error('invalid delivery evidence');
  if (['Not configured', 'Disabled'].includes(data.status) && data.records.length === 0 && data.counts === null) {
    panel.textContent = 'No offline delivery evidence configured.'; return;
  }
  const counts = data.counts;
  if (data.status !== 'Loaded' || !counts || !['ffxi', 'swtor'].includes(data.scope?.game)
      || !['realm', 'instance', 'thread', 'channel', 'actorKey', 'nativeActorId', 'epoch'].every(key => typeof data.scope[key] === 'string' && data.scope[key])
      || typeof data.coverage !== 'string' || counts.recordedAttempts !== data.records.length
      || !Number.isSafeInteger(data.rejectedReceipts) || data.rejectedReceipts < 0 || data.rejectedReceipts > 256
      || !['recordedAttempts', 'publicationMatched', 'syntheticConfirmed', 'conflicted', 'duplicateDecisionRecords', 'duplicateReceiptRecords'].every(key => Number.isSafeInteger(counts[key]) && counts[key] >= 0)) throw new Error('invalid delivery counts');
  if (counts.publicationMatched !== data.records.filter(row => row?.publication === 'Matched').length
      || counts.syntheticConfirmed !== data.records.filter(row => row?.fixtureConfirmation === 'Synthetic match').length
      || counts.conflicted !== data.records.filter(row => row?.publication === 'Conflict' || row?.fixtureConfirmation === 'Conflict').length) throw new Error('delivery counts disagree');
  item(panel, 'Synthetic delivery evidence · Actual game delivery: Unknown',
    `${counts.recordedAttempts} recorded attempts · ${counts.publicationMatched} publication matches · ${counts.syntheticConfirmed} synthetic native matches · ${counts.conflicted} conflicts.`,
    `${data.scope.game.toUpperCase()} · Independent of roster selection. ${data.coverage} No replay or native confirmation is performed.`);
  item(panel, 'Receipt evidence', `${data.rejectedReceipts} receipts rejected or unverified.`,
    'This count includes fixture receipts with no configured verifier. It does not establish failed game delivery. The Admin loader never verifies native speech.');
  item(panel, 'Captured scope', `${data.scope.realm} / ${data.scope.instance} / ${data.scope.thread} / ${data.scope.actorKey}`,
    `Fixture body ${data.scope.nativeActorId} · epoch ${data.scope.epoch} · channel ${data.scope.channel}. Scope labels do not authenticate a producer.`);
  for (const record of data.records) {
    if (!record || record.actualDelivery !== 'Unknown'
        || !['Matched', 'Uncorroborated', 'Not evidenced', 'Conflict'].includes(record.publication)
        || !['Unknown', 'Conflict', 'Synthetic match'].includes(record.fixtureConfirmation)
        || typeof record.reason !== 'string' || (record.text !== null && typeof record.text !== 'string')
        || (record.inboxSeq !== null && (!Number.isSafeInteger(record.inboxSeq) || record.inboxSeq < 0))
        || (record.publication === 'Conflict' && (record.text !== null || record.bot !== null))) throw new Error('invalid delivery record');
    const wording = record.publication === 'Conflict' ? 'Wording withheld: publication conflict' : record.text ?? 'No final text';
    item(panel, record.inboxSeq === null ? 'No publication identity' : `Inbox sequence ${record.inboxSeq}`,
      wording, `Publication: ${record.publication} · Fixture confirmation: ${record.fixtureConfirmation} · Actual delivery: Unknown. ${record.reason}`);
  }
}
async function loadDeliveryCapture() {
  if (!token || workspace.hidden) return;
  const id = ++deliveryCaptureVersion, requestToken = token, session = sessionVersion;
  const panel = document.getElementById('delivery-capture'), button = document.getElementById('delivery-capture-load');
  const current = () => id === deliveryCaptureVersion && panelSessionCurrent(requestToken, session);
  panel.replaceChildren(); panel.textContent = 'Loading configured delivery evidence…'; button.disabled = true;
  try {
    const response = await fetch('/api/delivery-capture', {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await readBoundedJson(response, 512 * 1024);
    if (current()) renderDeliveryCapture(data);
  } catch (_) {
    if (current()) { panel.replaceChildren(); panel.textContent = 'Delivery evidence unavailable. Previous content has been cleared.'; }
  } finally { if (current()) button.disabled = false; }
}
document.getElementById('delivery-capture-load')?.addEventListener('click', loadDeliveryCapture);
function renderInteraction(data, source) {
  const panel = document.getElementById('interaction-status');
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
  const panel = document.getElementById('interaction-status');
  panel.replaceChildren();
  if (document.getElementById('data-source').value !== 'hub' || sourceLoading || loadedSource !== 'hub') {
    panel.textContent = 'Load the selected hub source successfully before requesting this read-only check. Synthetic preview is available separately.';
    return;
  }
  panel.textContent = 'Checking candidate FFXI interaction view…';
  try {
    const response = await fetch('/api/interaction', {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await readBoundedJson(response);
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
  const panel = document.getElementById('hub-health');
  panel.replaceChildren();
  if (document.getElementById('data-source').value !== 'hub') { panel.textContent = 'Select configured hub data before requesting this read-only check.'; return; }
  if (sourceLoading || loadedSource !== 'hub') { panel.textContent = 'Load the selected hub source successfully before requesting this read-only check.'; return; }
  panel.textContent = 'Checking hub services…';
  try {
    const response = await fetch('/api/hub-health', {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await readBoundedJson(response);
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
  const panel = document.getElementById('bridge-status');
  try {
    const response = await fetch('/api/bridge-status', {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const received = await readBoundedJson(response);
    if (!panelSessionCurrent(requestToken, session)) return;
    if (!received || typeof received !== 'object' || Array.isArray(received)) throw new Error('unavailable');
    const data = Object.fromEntries(['unit', 'substate', 'result', 'marker', 'markerReason', 'source', 'observedAt']
      .map(key => [key, routingText(received[key], 'unknown')]));
    panel.replaceChildren();
    item(panel, `Unit: ${data.unit} · ${data.substate}`, `Result: ${data.result} · Fault marker: ${data.marker} · Classification: ${data.markerReason || 'unknown'}`, `${data.source} · Observed: ${data.observedAt || 'unknown'} · Marker absence does not prove delivery`);
    const focus = document.getElementById('ffxi-focus-bridge');
    focus.replaceChildren();
    item(focus, `Bridge: ${data.unit} · ${data.substate}`, `Fault marker: ${data.marker} · Classification: ${data.markerReason || 'unknown'}`, `${data.source} · Observed: ${data.observedAt || 'unknown'} · Not proof of delivery`);
  } catch (_) {
    if (!panelSessionCurrent(requestToken, session)) return;
    panel.replaceChildren();
    panel.textContent = 'Bridge status unknown; read-only observation unavailable.';
    const focus = document.getElementById('ffxi-focus-bridge');
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
  const panel = document.getElementById('quota-history');
  const window = document.getElementById('quota-window').value;
  panel.replaceChildren();
  const records = observationRows(currentSnapshot.quotaHistory, panel).filter(q => !window || q.window === window);
  if (!records.length) item(panel, 'No matching observations', 'Quota history for this filter is unknown.', 'No account refresh is performed.');
  records.forEach(q => item(panel, `Account ${routingText(q.account)} · ${routingText(q.window)}`,
    `Remaining: ${metricNumber(q.remainingPercent) && q.remainingPercent <= 100 ? q.remainingPercent + '%' : 'Unknown'} at observation`,
    `Observed: ${routingText(q.observedAt)} · Cached Codex state; may be stale`));
}
function renderLeadTimeline() {
  const panel = document.getElementById('lead-timeline');
  const filter = document.getElementById('timeline-kind').value;
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
  const panel = document.getElementById('issue-coverage');
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
  const panel = document.getElementById('issues');
  const scope = document.getElementById('issue-scope').value;
  const status = document.getElementById('issue-status').value;
  const selectedOnly = document.getElementById('issue-selected-bot').checked;
  const selectedExists = selectedBotId !== null && Boolean(uniqueRecord(currentSnapshot.bots, selectedBotId));
  const query = (document.getElementById('issue-search').value || '').trim().toLowerCase();
  panel.replaceChildren();
  const rows = observationRows(currentSnapshot.issues, panel);
  const count = Array.isArray(currentSnapshot.issues) && rows.length === currentSnapshot.issues.length ? rows.length : 'Unknown';
  const records = rows.filter(i => (!scope || i.scope === scope) && (!status || i.status === status) && (!selectedOnly || (selectedExists && i.botId === selectedBotId)) && (!query || `${routingText(i.title)} ${routingText(i.detail)}`.toLowerCase().includes(query)));
  document.getElementById('issue-count').textContent = `Showing ${records.length} of ${count} loaded issue records; coverage may be incomplete.`;
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
  const panel = document.getElementById('learning-inspector');
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
  const panel = document.getElementById('learning-evidence');
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
  const panel = document.getElementById('learning-artifacts');
  const game = document.getElementById('learning-game').value;
  panel.replaceChildren();
  const rows = observationRows(currentSnapshot.learningArtifacts, panel).filter(a => !game || a.game === game);
  if (!rows.length) item(panel, 'No artifact examples', 'No matching synthetic records.', 'This does not establish real artifact coverage.');
  rows.forEach(a => item(panel, `${routingText(a.game)} · ${routingText(a.kind)} · ${routingText(a.name)}`, `Validation: ${routingText(a.validation)} · Adoption: ${routingText(a.adoption)} · Demonstrated outcome: ${routingText(a.outcome)}`, `Version: ${routingText(a.version, 'unknown')} · ${routingText(a.source)} · Observed: ${routingText(a.observedAt, 'unknown')}`));
}
function renderLearningPlan() {
  const panel = document.getElementById('learning-plan');
  const game = document.getElementById('learning-game').value;
  panel.replaceChildren();
  const rows = observationRows(currentSnapshot.learningPlan, panel).filter(p => !game || p.game === game);
  if (!rows.length) item(panel, 'No planning topics', 'No topics for this filter.', 'This does not establish coverage.');
  rows.forEach(p => item(panel, `${routingText(p.game)} · ${routingText(p.topic)}`, routingText(p.next), `Evidence: ${routingText(p.evidence)} · Datasets: ${routingText(p.datasets)} · Policy: ${routingText(p.policy)} · ${routingText(p.source)}`));
}
function renderLearningCoverage() {
  const panel = document.getElementById('learning-coverage');
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
  const game = document.getElementById('learning-game').value;
  const status = document.getElementById('learning-status').value;
  const attention = document.getElementById('learning-attention').checked;
  const attentionStatuses = new Set(['Needs evidence', 'Needs inventory', 'unverified', 'failed', 'canceled', 'cancelled']);
  const query = (document.getElementById('learning-search').value || '').trim().toLowerCase();
  return usableLearningRows().filter(l => (!game || l.game === game) && (!status || l.status === status) && (!attention || attentionStatuses.has(l.status)) && (!query || `${l.topic} ${l.reason || ''}`.toLowerCase().includes(query)));
}
function updateLearningCount(records) {
  const selectedMissing = selectedLearningId !== null && !Boolean(uniqueRecord(currentSnapshot.learning, selectedLearningId));
  const selectedAmbiguous = recordsForId(currentSnapshot.learning, selectedLearningId).length > 1;
  const selectedHidden = selectedLearningId !== null && !selectedMissing && !records.some(l => l.id === selectedLearningId);
  const supplied = currentSnapshot.learning;
  const total = Array.isArray(supplied) && usableLearningRows().length === supplied.length ? supplied.length : 'Unknown total';
  document.getElementById('learning-count').textContent = `Showing ${records.length} of ${total} loaded learning records; coverage may be incomplete.${selectedAmbiguous ? ' Selected learning identity is ambiguous; scoped inspection is unavailable.' : selectedMissing ? ' Selected need is no longer in the loaded data.' : selectedHidden ? ' Selected need is outside this filtered list; its inspector remains selected.' : ''}`;
}
function renderLearning() {
  const panel = document.getElementById('learning');
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
  const panel = document.getElementById('hub-trace');
  panel.replaceChildren();
  if (!/^[A-Za-z0-9_.:-]{1,128}$/.test(correlation)) { panel.textContent = 'Enter a correlation ID using letters, numbers, dot, dash, underscore or colon.'; return; }
  const game = document.getElementById('trace-game').value;
  if (!['ffxi', 'swtor'].includes(game)) { panel.textContent = 'Choose a supported game.'; return; }
  panel.textContent = 'Loading read-only trace…';
  try {
    const response = await fetch(`/api/trace?gameId=${encodeURIComponent(game)}&correlationId=${encodeURIComponent(correlation)}`, {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await readBoundedJson(response);
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
  const panel = document.getElementById('ledger');
  panel.replaceChildren();
  const count = document.getElementById('ledger-count');
  count.textContent = 'Ledger example count unknown.';
  document.getElementById('ledger-filter').textContent = correlationFilter
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
  const panel = document.getElementById('bot-coverage');
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
  document.getElementById('roster-gap-detail').replaceChildren();
  document.getElementById('roster-gap-detail').textContent = 'Select a loaded roster gap for record details.';
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
  const panel = document.getElementById('roster-gaps');
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
      const detail = document.getElementById('roster-gap-detail'); detail.replaceChildren();
      item(detail, `Snapshot row ${index + 1} · ${routingText(bot.name)}`, `${reason} · Reported ID: ${routingText(bot.id)}`,
        `Game: ${routingText(bot.game)} · Source: ${routingText(bot.source, 'Source unknown')} · Observed: ${routingText(bot.observedAt)} · This row is not a verified native identity; no goals, replies or other evidence are joined.`);
      const show = document.createElement('button'); show.type = 'button'; show.textContent = 'Show matching roster row';
      show.addEventListener('click', () => {
        if (currentSnapshot !== snapshot) return;
        rosterRecordIndex = index;
        document.getElementById('bot-game').value = '';
        document.getElementById('bot-search').value = '';
        document.getElementById('bot-identity').value = 'unavailable';
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
  const game = document.getElementById('bot-game').value;
  const identity = document.getElementById('bot-identity').value;
  const query = (document.getElementById('bot-search').value || '').trim().toLowerCase();
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
  document.getElementById('bot-count').textContent = `Showing ${bots.length} of ${total} loaded roster records; coverage and presence may be unknown.${rosterRecordIndex !== null ? ' Pinned snapshot row: ' + (rosterRecordIndex + 1) + '.' : ''}${selectedAmbiguous ? ' Selected bot identity is ambiguous; scoped inspection is unavailable.' : selectedMissing ? ' Selected bot is no longer in the loaded data.' : selectedHidden ? ' Selected bot is outside this filtered roster; its inspector remains selected.' : ''}`;
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
  const panel = document.getElementById('bots');
  const bots = filteredBots();
  panel.replaceChildren();
  observationRows(currentSnapshot.bots, panel);
  updateBotCount(bots);
  if (!bots.length) item(panel, 'No matching roster records', 'No matches in the loaded data.', 'This does not establish that a bot is offline.');
  else bots.forEach(botItem);
}
function renderSafety() {
  const panel = document.getElementById('safety-records');
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
  document.getElementById('correlation').value = correlationId;
  if (['FFXI', 'SWTOR'].includes(bot.game)) document.getElementById('trace-game').value = bot.game.toLowerCase();
  traceVersion++; document.getElementById('hub-trace').replaceChildren();
  renderLedger(); focusWorkspaceTarget('ledger');
}
function renderReplySource() {
  const panel = document.getElementById('reply-source');
  panel.replaceChildren();
  if (replyBotId !== selectedBotId) {
    replyBotId = selectedBotId;
    document.getElementById('reply-correlation').value = '';
  }
  const count = document.getElementById('reply-count');
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
  const correlation = document.getElementById('reply-correlation').value.trim();
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
  const panel = document.getElementById('owner-attention');
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
  const panel = document.getElementById('audit');
  panel.replaceChildren();
  if (!Array.isArray(currentSnapshot.audit)) {
    document.getElementById('audit-count').textContent = 'Loaded audit example count unknown; no live audit source is connected.';
    item(panel, 'Audit example coverage unknown', 'No usable audit example list was supplied in this snapshot.',
      'Missing data does not establish whether real admin actions occurred.');
    return;
  }
  const supplied = currentSnapshot.audit;
  const usable = supplied.filter(row => row && typeof row === 'object' && !Array.isArray(row));
  const partial = usable.length !== supplied.length;
  if (partial) item(panel, 'Audit example coverage unknown', 'Malformed rows were omitted; usable examples are retained.',
    'The loaded total is Unknown. Missing data does not establish whether real admin actions occurred.');
  const query = (document.getElementById('audit-search').value || '').trim().toLowerCase();
  const rows = usable.filter(a => !query || [a.actor, a.action, a.scope, a.result]
    .some(value => typeof value === 'string' && value.toLowerCase().includes(query)));
  document.getElementById('audit-count').textContent = `Showing ${rows.length} of ${partial ? 'Unknown total' : supplied.length} loaded audit examples; no live audit source is connected.`;
  if (!rows.length) item(panel, usable.length ? 'No matching audit examples' : partial ? 'No usable audit examples' : 'No audit examples loaded',
    'This view does not establish whether real admin actions occurred.', 'Read-only examples; no live audit source is connected.');
  rows.forEach(a => item(panel, `${routingText(a.action, 'Action unknown')} · ${routingText(a.scope, 'Scope unknown')}`,
    routingText(a.result), `${routingText(a.actor, 'Actor unknown')} · ${routingText(a.at, 'unknown time')} · ${routingText(a.source, 'Source unknown')}`));
}
function renderRoutingAudit() {
  const panel = document.getElementById('routing-audit');
  panel.replaceChildren();
  const supplied = currentSnapshot.routingAudit;
  const rows = observationRows(supplied, panel);
  const filter = document.getElementById('routing-audit-scope').value;
  const outcomeFilter = document.getElementById('routing-audit-outcome').value;
  const outcome = row => ['applied', 'rejected'].includes(row.outcome) ? row.outcome : 'unknown';
  const outcomeLabels = {applied: 'Simulated application', rejected: 'Simulated rejection', unknown: 'Unknown'};
  const selected = rows.filter(row => (!filter || row.scopeKind === filter)
    && (!outcomeFilter || outcome(row) === outcomeFilter));
  const count = Array.isArray(supplied) && supplied.length === rows.length ? rows.length : 'Unknown';
  document.getElementById('routing-audit-count').textContent = `Showing ${selected.length} of ${count} loaded synthetic events; actual audit coverage is unknown.`;
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
  document.getElementById('assignment-count').textContent = message;
  document.getElementById('assignment-prev').setAttribute('aria-disabled', String(assignmentPage <= 0 || assignmentPages === 0));
  document.getElementById('assignment-next').setAttribute('aria-disabled', String(assignmentPage + 1 >= assignmentPages));
}
function changeAssignmentPage(delta) {
  const next = assignmentPage + delta;
  if (!currentSnapshot || next < 0 || next >= assignmentPages) return;
  assignmentPage = next;
  renderAssignments();
}
function renderAssignments() {
  const panel = document.getElementById('assignment-history');
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
  if (document.getElementById('issue-selected-bot').checked) renderIssues();
  renderAssignments();
  renderReplySource();
  const panel = document.getElementById('bot-inspector');
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
    document.getElementById('issue-selected-bot').checked = true;
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
  const panel = document.getElementById('data-coverage');
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
  const panel = document.getElementById('model-calls');
  panel.replaceChildren();
  const coverage = document.getElementById('model-call-coverage');
  coverage.textContent = 'Metric coverage unknown.';
  const calls = currentSnapshot.modelCalls;
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
  if (!Array.isArray(calls)) {
    renderModelComparison(null);
    item(panel, 'Model call coverage', 'Unknown', 'No usable model-call list in this snapshot; imported rows are not shown.');
    return;
  }
  if (!calls.length) item(panel, 'No model call examples', 'No rows supplied.', 'This does not establish zero usage or cost.');
  const rows = calls.filter(row => row && typeof row === 'object' && !Array.isArray(row));
  if (rows.length !== calls.length) item(panel, 'Model call coverage', 'Unknown for omitted malformed rows', 'Valid supplied examples are shown below; coverage is incomplete.');
  const fields = [['latencyMs', 'Latency'], ['cost', 'Cost'], ['quality', 'Quality']];
  const complete = row => fields.every(([key]) => metricNumber(row[key]));
  const filter = document.getElementById('model-call-availability').value;
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
const botActivityEngines = ['noncombat', 'combat', 'dead', 'Unknown'];
const botActivityWowId = 'wow-70450-export';
const botActivityVanillaId = 'wow-vanilla-playerbots';
const botActivitySourceIds = [botActivityWowId, 'ffxi-lsb', 'dit-bot-event-v1', botActivityVanillaId];
// Per-source fallbacks for a snapshot that omits a label or note. The 70450 caveat belongs to the WoW source only.
const botActivityDefaults = {
  [botActivityWowId]: {label: 'WoW Forever (70450 predecessor export)', env: 'DIT_FOREVER_BOTLOG_DIR',
    note: 'Exported WoW Forever bot log (70450 predecessor Bots format); not live, not DIT bots, not PlayerbotV2.'},
  'ffxi-lsb': {label: 'FFXI (LSB) Bots V2 log export', env: 'DIT_FFXI_BOTSV2_LOG',
    note: 'Exported [BOTS-V2] map-log lines; offline import (DIT_FFXI_BOTSV2_LOG); owner name masked.'},
  'dit-bot-event-v1': {label: 'DIT bot_event v1 (SWTOR, FFXI Forever, other DIT games)', env: 'DIT_BOT_EVENT_DIR',
    note: 'Offline import of dit.bot_event.v1 JSONL (DIT_BOT_EVENT_DIR); includes AI advice rows.'},
  [botActivityVanillaId]: {label: 'WoW Vanilla / Benilla playerbots (cmangos-classic event log)', env: 'DIT_VANILLA_BOTLOG_CSV',
    note: 'Exported cmangos-classic playerbot event CSV; offline import (DIT_VANILLA_BOTLOG_CSV); one server run, bots only.'},
};
const botActivityStatuses = ['Not configured', 'Off', 'Loaded', 'Unavailable'];
const botActivityRowLimit = 200, botActivityListLimit = 50, botActivityAlternativeLimit = 20;
const botActivitySearch = new Map(); // Local text filter per non-WoW source; kept across re-renders of that section.
function plainObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value);
}
function shown(value) {
  if (typeof value === 'string' && value.trim()) return value.slice(0, 500);
  return typeof value === 'number' && Number.isFinite(value) ? String(value) : 'Unknown';
}
function botActivityPart(value, label = '') {
  if (typeof value === 'string' && value.trim()) return label + value.trim();
  return typeof value === 'number' && Number.isFinite(value) ? label + value : '';
}
function botActivityJoin(parts) {
  return parts.filter(Boolean).join(' · ').slice(0, 1000) || 'Unknown';
}
function botActivityCounts(counts) {
  const entries = plainObject(counts) ? Object.entries(counts).filter(([, n]) => metricNumber(n) && n > 0) : [];
  return entries.length ? entries.map(([key, n]) => `${String(key).slice(0, 40)} ${n}`).join(', ') : 'Unknown';
}
function botActivityNested(list, limit, label, describe) {
  if (!Array.isArray(list) || !list.length) {
    const note = document.createElement('p');
    note.textContent = Array.isArray(list) ? `${label}: none in the export (does not mean none occurred).` : `${label}: Unknown (missing or malformed in the export).`;
    return note;
  }
  const ul = document.createElement('ul');
  list.slice(0, limit).forEach(entry => {
    const li = document.createElement('li');
    if (plainObject(entry)) {
      const {text, child} = describe(entry);
      li.textContent = text; // Set text before appending: textContent replaces existing children.
      if (child) li.append(child);
    } else li.textContent = 'Unreadable entry; Unknown';
    ul.append(li);
  });
  if (list.length > limit) {
    const more = document.createElement('li');
    more.textContent = `${list.length - limit} more entries not shown.`;
    ul.append(more);
  }
  return ul;
}
function botActivityList(parent, label, list, describe) {
  const details = document.createElement('details');
  const summary = document.createElement('summary');
  summary.textContent = `${label} (${Array.isArray(list) ? list.length : 'Unknown'})`;
  details.append(summary);
  // Event bodies can contain hundreds of rows across the loaded bots. Build only
  // the lists the reader opens, once for this snapshot's details element.
  let rendered = false;
  details.addEventListener('toggle', () => {
    if (!details.open || rendered) return;
    details.append(botActivityNested(list, botActivityListLimit, label, describe));
    rendered = true;
  });
  parent.append(details);
}
function botActivityRow(panel, bot) {
  const engine = botActivityEngines.includes(bot.engine) ? bot.engine : 'Unknown';
  const counts = plainObject(bot.counts) ? Object.entries(bot.counts).filter(([, n]) => metricNumber(n)).sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1)).slice(0, 5) : [];
  item(panel, `${routingText(bot.name, 'Unnamed')} (${bot.botGuid}) · ${engine}`,
    `Doing: ${shown(bot.doing)} · Level: ${shown(bot.level)} · Zone ID: ${shown(bot.zoneId)} · Faction: ${shown(bot.faction)}`,
    `Last event: ${shown(bot.lastEventAt)} · Top events: ${counts.length ? counts.map(([type, n]) => `${type} ${n}`).join(', ') : 'Unknown'}`);
  const row = panel.lastElementChild;
  botActivityList(row, 'Recent decisions', bot.decisions, d => ({
    text: `${shown(d.ts)} · ${shown(d.action)} via ${shown(d.trigger)} · ${shown(d.reason)} · relevance ${shown(d.relevance)} ${shown(d.band)} (effective ${shown(d.effective)}) · ${shown(d.engine)}`,
    child: botActivityNested(d.alternatives, botActivityAlternativeLimit, 'Rejected alternatives', a => ({text: `${shown(a.action)} — ${shown(a.result)} (${shown(a.relevance)})`}))}));
  botActivityList(row, 'Deaths', bot.deaths, d => ({
    text: `${shown(d.ts)} · ${shown(d.reason)} · ${shown(d.summary)} · Killer entry: ${shown(d.killerEntry)} · Killer level: ${shown(d.killerLevel)} · Level gap: ${shown(d.levelGap)}`,
    child: botActivityNested(d.recentDecisions, botActivityAlternativeLimit, 'Recent decisions before death', r => ({text: `${shown(r.msAgo)} ms before death · ${shown(r.action)} · ${shown(r.reason)}`}))}));
  botActivityList(row, 'Quests', bot.quests, q => ({text: `${shown(q.ts)} · ${shown(q.reason)} · Quest ${shown(q.questId)} · ${shown(q.summary)}`}));
}
function botActivityFfxiRow(panel, bot) {
  item(panel, `${routingText(bot.name, 'Unnamed')} (${shown(bot.actorId)})`,
    `Doing: ${shown(bot.doing)} · Zone ID: ${shown(bot.zoneId)} · Character ID: ${shown(bot.charId)}`,
    `Last event: ${shown(bot.lastEventAt)} · Counts: ${botActivityCounts(bot.counts)}`);
  const row = panel.lastElementChild;
  botActivityList(row, 'Events', bot.events, e => ({text: botActivityJoin([
    botActivityPart(e.ts), botActivityPart(e.type), botActivityPart(e.rule), botActivityPart(e.op), botActivityPart(e.result),
    botActivityPart(e.reason), botActivityPart(e.apl, 'apl '), metricNumber(e.repeated) && e.repeated > 1 ? `repeated ${e.repeated}` : '',
    botActivityPart(e.detail)])}));
  botActivityList(row, 'Refusals', bot.refusals, e => ({text: botActivityJoin([
    botActivityPart(e.ts), botActivityPart(e.rule), botActivityPart(e.op), botActivityPart(e.reason, 'reason '), botActivityPart(e.detail)])}));
  botActivityList(row, 'Deaths', bot.deaths, e => ({text: botActivityJoin([
    botActivityPart(e.ts), botActivityPart(e.type), botActivityPart(e.reason, 'reason '), botActivityPart(e.detail)])}));
  botActivityFeelNote(row, bot);
}
// Human-feel signals (human_feel.py): measurements of machine-regular timing. Missing or short data reads as not measured.
function botActivityFeel(feel) {
  if (!plainObject(feel)) return 'Human-feel signals: not measured in this snapshot.';
  const parts = [];
  const c = feel.cadence, s = feel.sync, t = feel.schedule;
  if (plainObject(c) && metricNumber(c.gaps) && metricNumber(c.modalCount) && metricNumber(c.modalGapS))
    parts.push(`${shown(c.action)}: ${c.modalCount} of ${c.gaps} gaps near ${c.modalGapS} s${c.metronomic === true ? ' (metronomic)' : ''}`);
  if (plainObject(s) && metricNumber(s.actions) && metricNumber(s.together))
    parts.push(`group actions within 1 s of a mate: ${s.together} of ${s.actions}${s.synchronized === true ? ' (synchronized)' : ''}`);
  if (plainObject(t) && metricNumber(t.intervals) && metricNumber(t.modalCount) && metricNumber(t.modalIntervalS))
    parts.push(`trip starts: ${t.modalCount} of ${t.intervals} gaps near ${t.modalIntervalS} s${t.fixed === true ? ' (fixed clock)' : ''}`);
  return `Human-feel signals: ${parts.length ? parts.join(' · ') : 'too few samples to measure.'}`;
}
// Appended after the lists, so the list positions in a row stay the same.
function botActivityFeelNote(row, bot) {
  const feel = document.createElement('p');
  feel.textContent = botActivityFeel(bot.feel);
  row.append(feel);
}
// Chat totals (BOT_BRAIN_STANDARD 6.6): lines voiced, lines dropped and why. Empty when the bot has no chat rows.
function botActivityChat(chat) {
  if (!plainObject(chat) || !metricNumber(chat.voiced) || !metricNumber(chat.dropped) || chat.voiced + chat.dropped <= 0) return '';
  const reasons = botActivityCounts(chat.byReason);
  return ` · Chat: voiced ${chat.voiced}, dropped ${chat.dropped}${chat.dropped > 0 && reasons !== 'Unknown' ? ` (${reasons})` : ''}`;
}
function botActivityLogLoss(event) {
  if (event.type !== 'error' || event.reason !== 'LOG_DROPPED') return '';
  const count = Number.isSafeInteger(event.reportedDropped) && event.reportedDropped >= 0 ? event.reportedDropped : 'Unknown';
  return `Producer-reported dropped rows: ${count} (this report; not summed)`;
}
function botActivityDitRow(panel, bot) {
  const named = botActivityPart(bot.name), place = botActivityPart(bot.areaName), spec = botActivityPart(bot.discipline, ' · Discipline: ');
  item(panel, `${named ? `${named} (${shown(bot.actorId)})` : shown(bot.actorId)} · ${shown(bot.game)}`,
    `Doing: ${shown(bot.doing)} · Level: ${shown(bot.level)} · Area: ${place || shown(bot.area)}${spec}`,
    `Last event: ${shown(bot.lastEventAt)} · Counts by type: ${botActivityCounts(bot.counts)}${botActivityChat(bot.chat)}`);
  const row = panel.lastElementChild;
  botActivityList(row, 'Events', bot.events, e => ({text: botActivityJoin([
    botActivityPart(e.ts), botActivityPart(e.type), botActivityPart(e.severity, 'severity '), botActivityPart(e.reason),
    botActivityPart(e.action, 'action '), botActivityPart(e.ability, 'ability '), botActivityPart(e.result, 'result '),
    botActivityPart(e.summary), botActivityLogLoss(e)])}));
  botActivityList(row, 'Deaths', bot.deaths, d => ({
    text: botActivityJoin([botActivityPart(d.ts), `Killer: ${routingText(d.killer, 'Unknown')}`]),
    child: botActivityNested(d.recentDecisions, botActivityAlternativeLimit, 'Recent decisions before death', r => ({text: botActivityJoin([
      botActivityPart(r.action, 'action '), botActivityPart(r.reason, 'reason ')])}))}));
  botActivityList(row, 'Advice', bot.advice, a => ({text: botActivityJoin([
    botActivityPart(a.ts), botActivityPart(a.kind), botActivityPart(a.chosen, 'chosen '), botActivityPart(a.outcome, 'outcome '),
    botActivityPart(a.reason)])}));
  botActivityFeelNote(row, bot);
}
// Vanilla playerbots: XP-gain rows are a kill signal, not a complete kill count.
function botActivityStall(stall) {
  if (!plainObject(stall) || !metricNumber(stall.pulls) || !metricNumber(stall.seconds)) return 'No run of 10+ same-target pulls was established in this export; this does not prove the bot is unstuck.';
  const spots = metricNumber(stall.positions) ? ` from ${stall.positions} position${stall.positions === 1 ? '' : 's'}` : '';
  return `Longest same-target run without recorded XP or loot: ${stall.pulls} pulls on ${shown(stall.target)} over ${Math.round(stall.seconds / 60)} min${spots} (${shown(stall.from)} to ${shown(stall.to)}).`;
}
function botActivityHearthStuck(counts) {
  if (!plainObject(counts) || Object.values(counts).some(n => !Number.isSafeInteger(n) || n < 0)) return 'Unknown';
  const text = botActivityCounts(counts);
  return text === 'Unknown' ? 'none recorded' : text;
}
function botActivityVanillaRow(panel, bot) {
  const ratio = metricNumber(bot.pullsPerKill) ? bot.pullsPerKill : 'Unknown';
  item(panel, `${routingText(bot.name, 'Unnamed')} (${shown(bot.actorId)}) · level ${shown(bot.level)}`,
    `Doing: ${shown(bot.doing)} · Pulls: ${shown(bot.pulls)} · XP-gain rows: ${shown(bot.kills)} · Pulls per XP-gain row: ${ratio} · Hearthstone escapes (stuck): ${botActivityHearthStuck(bot.hearthStuck)}`,
    `Last event: ${shown(bot.lastEventAt)} · Counts: ${botActivityCounts(bot.counts)}`);
  const row = panel.lastElementChild;
  botActivityList(row, 'Events', bot.events, e => ({text: botActivityJoin([botActivityPart(e.ts), botActivityPart(e.type), botActivityPart(e.detail)])}));
  botActivityList(row, 'Deaths', bot.deaths, e => ({text: botActivityJoin([botActivityPart(e.ts), botActivityPart(e.type)])}));
  const stall = document.createElement('p');
  stall.textContent = botActivityStall(bot.stall);
  row.append(stall);
  botActivityFeelNote(row, bot);
}
const botActivityRenderers = {[botActivityWowId]: botActivityRow, 'ffxi-lsb': botActivityFfxiRow, 'dit-bot-event-v1': botActivityDitRow,
  [botActivityVanillaId]: botActivityVanillaRow};
// The source record for id: the top-level WoW keys when the snapshot has no sources list (older snapshots).
function botActivityEntry(data, id) {
  if (!plainObject(data)) return null;
  if (!Array.isArray(data.sources)) return id === botActivityWowId ? data : null;
  return data.sources.find(entry => plainObject(entry) && entry.id === id) || null;
}
function botActivityValid(entry) {
  return plainObject(entry) && plainObject(entry.coverage) && Array.isArray(entry.bots) ? entry : null;
}
function botActivityLabel(entry, id) {
  return routingText(entry?.label, botActivityDefaults[id].label).slice(0, 200);
}
function botActivityNoteText(entry, id) {
  return routingText(entry?.note, botActivityDefaults[id].note).slice(0, 500);
}
function botActivityKey(bot, id) {
  const key = bot[id === botActivityWowId ? 'botGuid' : 'actorId'];
  return typeof key === 'string' ? key.trim() : '';
}
function botActivityEventRange(cov) {
  const unknown = 'Observed event range: Unknown';
  if (!plainObject(cov) || cov.status !== 'Loaded' || !metricNumber(cov.records) || cov.records === 0) return unknown;
  const timestamp = value => {
    if (typeof value !== 'string') return null;
    const match = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?Z$/.exec(value);
    if (!match || value.startsWith('0000-')) return null;
    const millis = Date.parse(value);
    // Date.parse may normalize an impossible calendar date; refuse that change.
    if (!Number.isFinite(millis) || new Date(millis).toISOString().slice(0, 19) !== match[1]) return null;
    // Compare at the readers' microsecond precision, beyond Date's milliseconds.
    return `${match[1]}.${(match[2] || '').padEnd(6, '0')}Z`;
  };
  const first = timestamp(cov.from), last = timestamp(cov.to);
  if (first === null || last === null || first > last) return unknown;
  return `Observed event range: ${cov.from} to ${cov.to} (UTC; offline export)`;
}
function botActivityCoverageText(cov) {
  const status = botActivityStatuses.includes(cov.status) ? cov.status : 'Unknown';
  // Import omissions can include row limits, duplicate IDs or non-event rows.
  const parts = [`Coverage: ${status}`, `Imported log rows: ${metricNumber(cov.records) ? cov.records : 'Unknown'}`,
    `Rows omitted on import: ${metricNumber(cov.omitted) ? cov.omitted : 'Unknown'}`];
  if (metricNumber(cov.files)) parts.push(`Files read: ${cov.files}`);
  if (metricNumber(cov.unrecognized)) parts.push(`Unrecognized lines: ${cov.unrecognized}`);
  if (metricNumber(cov.ignored)) parts.push(`Ignored lines: ${cov.ignored}`);
  if (plainObject(cov.omittedByReason)) {
    const reasons = Object.entries(cov.omittedByReason).filter(([, n]) => metricNumber(n) && n > 0).slice(0, 10)
      .map(([code, n]) => `${String(code).slice(0, 40)} ${n}`);
    if (reasons.length) parts.push(`Omitted by reason: ${reasons.join(', ')}`);
  }
  parts.push(botActivityEventRange(cov), routingText(cov.reason, 'Reason unknown'));
  return parts.join(' · ');
}
function botActivityStatusItem(panel, status, cov, id) {
  if (status === 'Not configured' || status === 'Off') item(panel, 'Import is off', `The ${botActivityDefaults[id].env} switch is not set, so no exported log is read.`, 'Off by default. Nothing here describes live activity.');
  else if (status === 'Unavailable') item(panel, 'Import unavailable', routingText(cov.reason, 'Reason unknown'), 'Nothing was imported; this does not mean the bots are idle.');
  else if (status !== 'Loaded') item(panel, 'Import status Unknown', 'Coverage status was not recognized.', 'No conclusion about bot activity can be drawn.');
}
// Renders one source's coverage line and rows into refs. A missing or malformed source is Unknown, never empty.
function renderBotActivityBody(refs, entry, id, engine, needle) {
  const {coverage, count, rows} = refs;
  rows.replaceChildren(); count.textContent = '';
  const source = botActivityValid(entry);
  if (!source) {
    coverage.textContent = 'Coverage: Unknown · No usable data for this source in the snapshot.';
    item(rows, 'Source coverage', 'Unknown', 'Missing or malformed data does not mean the bots are idle or that the log is empty.');
    return;
  }
  const cov = source.coverage;
  const status = botActivityStatuses.includes(cov.status) ? cov.status : 'Unknown';
  coverage.textContent = botActivityCoverageText(cov);
  botActivityStatusItem(rows, status, cov, id);
  if (status !== 'Loaded') return;
  const bots = source.bots.filter(bot => plainObject(bot) && botActivityKey(bot, id));
  const matches = bots.filter(bot => (!engine || (botActivityEngines.includes(bot.engine) ? bot.engine : 'Unknown') === engine)
    && (!needle || (typeof bot.name === 'string' && bot.name.toLowerCase().includes(needle)) || botActivityKey(bot, id).toLowerCase().includes(needle)));
  count.textContent = `Showing ${Math.min(matches.length, botActivityRowLimit)} of ${bots.length} loaded bots. Local filter only; no request is made.`;
  if (source.bots.length !== bots.length) item(rows, 'Bot coverage Unknown for omitted malformed rows', `${source.bots.length - bots.length} rows without a usable bot ID are not shown.`, 'Valid rows are shown below; coverage is incomplete.');
  if (status === 'Loaded' && !bots.length) item(rows, 'No bot activity in the export', 'The export contained no usable bot rows (does not mean bots are idle).', 'Not a claim about live activity.');
  else if (bots.length && !matches.length) item(rows, 'No bots match the local filter', 'Change the filter to see other loaded bots.', 'This does not mean a bot is idle.');
  matches.slice(0, botActivityRowLimit).forEach(bot => botActivityRenderers[id](rows, bot));
  if (matches.length > botActivityRowLimit) item(rows, 'More bots not shown', `${matches.length - botActivityRowLimit} matching bots exceed the ${botActivityRowLimit}-row display limit.`, 'Narrow the filter to see them.');
}
// One list of repeated-pull and timing patterns for QA to inspect in the loaded exports.
const botActivityGapLimit = 30;
function botActivityGapLines(data) {
  const lines = [];
  for (const id of botActivitySourceIds.slice(1)) {
    const source = botActivityValid(botActivityEntry(data, id));
    if (!source || source.coverage.status !== 'Loaded') continue;
    const label = botActivityLabel(source, id);
    for (const bot of source.bots) {
      if (!plainObject(bot) || !botActivityKey(bot, id)) continue;
      const who = `${label}: ${routingText(bot.name, shown(bot.actorId))}`;
      const feel = plainObject(bot.feel) ? bot.feel : {};
      const c = feel.cadence, s = feel.sync, t = feel.schedule, stall = bot.stall;
      if (plainObject(stall) && metricNumber(stall.pulls) && metricNumber(stall.seconds))
        lines.push(`${who} has a repeated-pull run: ${stall.pulls} pulls on ${shown(stall.target)} without recorded XP or loot over ${Math.round(stall.seconds / 60)} min.`);
      if (plainObject(c) && c.metronomic === true && metricNumber(c.modalCount) && metricNumber(c.gaps))
        lines.push(`${who} has a regular cadence: ${shown(c.action)}, ${c.modalCount} of ${c.gaps} gaps near ${shown(c.modalGapS)} s.`);
      if (plainObject(t) && t.fixed === true && metricNumber(t.modalCount) && metricNumber(t.intervals))
        lines.push(`${who} has a regular departure pattern: ${t.modalCount} of ${t.intervals} gaps between trip starts near ${shown(t.modalIntervalS)} s.`);
      if (plainObject(s) && s.synchronized === true && metricNumber(s.together) && metricNumber(s.actions))
        lines.push(`${who} moves in lockstep: ${s.together} of ${s.actions} group actions within 1 s of a party mate.`);
    }
  }
  return lines;
}
function renderBotActivityGaps(container, data) {
  const block = document.createElement('div'); block.className = 'bot-gaps';
  const heading = document.createElement('h4'); heading.textContent = 'Patterns to review in the loaded exports';
  const note = document.createElement('p'); note.className = 'muted';
  note.textContent = 'Measured from the offline exports below. Timing gaps are rounded before grouping. Kills that produce neither XP nor loot can look like repeated-pull runs. These patterns, or their absence, do not establish human-like behavior.';
  const lines = botActivityGapLines(data);
  const list = document.createElement('ul');
  lines.slice(0, botActivityGapLimit).forEach(text => { const li = document.createElement('li'); li.textContent = text.slice(0, 500); list.append(li); });
  if (lines.length > botActivityGapLimit) { const more = document.createElement('li'); more.textContent = `${lines.length - botActivityGapLimit} more not shown.`; list.append(more); }
  if (!lines.length) {
    const loaded = botActivitySourceIds.slice(1).some(id => botActivityValid(botActivityEntry(data, id))?.coverage.status === 'Loaded');
    const none = document.createElement('li');
    none.textContent = loaded ? 'None found in the loaded exports.' : 'Review patterns: Unknown; no usable loaded export for these sources.';
    list.append(none);
  }
  block.append(heading, note, list);
  container.append(block);
}
function renderBotActivityOthers(data) {
  const container = document.getElementById('bot-activity-sources');
  container.replaceChildren();
  if (Array.isArray(data?.sources)) renderBotActivityGaps(container, data);
  if (Array.isArray(data?.sources)) {
    const unknown = data.sources.filter(entry => !plainObject(entry) || !botActivitySourceIds.includes(entry.id)).length;
    if (unknown) item(container, 'Unrecognized sources not shown', `${unknown} source entries have an id this page does not render.`, 'Nothing from them is shown.');
  }
  for (const id of botActivitySourceIds.slice(1)) {
    const entry = botActivityEntry(data, id);
    const section = document.createElement('div'); section.className = 'bot-source';
    const heading = document.createElement('h4'); heading.textContent = botActivityLabel(entry, id);
    const note = document.createElement('p'); note.className = 'muted'; note.textContent = botActivityNoteText(entry, id);
    const coverage = document.createElement('p'); coverage.setAttribute('role', 'status');
    const search = document.createElement('label'), input = document.createElement('input');
    input.type = 'search'; input.setAttribute('maxlength', '128'); input.placeholder = 'Bot name or ID'; input.value = botActivitySearch.get(id) || '';
    search.textContent = 'Search bot name or ID'; search.append(input);
    const count = document.createElement('p'); count.className = 'muted'; count.setAttribute('aria-live', 'polite');
    const rows = document.createElement('div'); rows.setAttribute('aria-live', 'polite');
    section.append(heading, note, coverage, search, count, rows);
    container.append(section);
    const refs = {coverage, count, rows};
    const refresh = () => renderBotActivityBody(refs, entry, id, '', (botActivitySearch.get(id) || '').trim().toLowerCase());
    input.addEventListener('input', () => { botActivitySearch.set(id, input.value); refresh(); });
    refresh();
  }
}
function renderBotActivity() {
  const data = currentSnapshot?.botActivity;
  const wow = botActivityEntry(data, botActivityWowId);
  document.getElementById('bot-activity-label').textContent = botActivityLabel(wow, botActivityWowId);
  document.getElementById('bot-activity-note').textContent = botActivityNoteText(wow, botActivityWowId);
  const engine = botActivityEngines.includes(document.getElementById('bot-activity-engine').value) ? document.getElementById('bot-activity-engine').value : '';
  const needle = typeof document.getElementById('bot-activity-search').value === 'string' ? document.getElementById('bot-activity-search').value.trim().toLowerCase() : '';
  renderBotActivityBody({coverage: document.getElementById('bot-activity-coverage'), count: document.getElementById('bot-activity-count'),
    rows: document.getElementById('bot-activity')}, wow, botActivityWowId, engine, needle);
  renderBotActivityOthers(data);
}
const baselineStatuses = ['Reference', 'Sim-measured', 'Unit-tested', 'Designed', 'Not started', 'Not applicable', 'Verified live', 'Partly live', 'Built', 'Unknown'];
const baselineStatusClass = {'Reference': 'reference', 'Sim-measured': 'sim-measured', 'Unit-tested': 'unit-tested', 'Designed': 'designed',
  'Not started': 'not-started', 'Not applicable': 'not-applicable', 'Verified live': 'verified-live', 'Partly live': 'partly-live', 'Built': 'built', 'Unknown': 'unknown'};
const baselineGroups = [['parity', 'Bots parity (owner goal 2026-11-09)'], ['forever', 'WoW Forever operating model'], ['dit', 'DIT improvements'], [null, 'Group unknown']];
function resetBaselineConformance() {
  for (const id of ['baseline-game', 'baseline-group', 'baseline-status']) {
    document.getElementById(id).value = '';
    document.getElementById(id).disabled = true;
  }
  baselineGameOptions([]);
  document.getElementById('baseline-conformance').replaceChildren();
  document.getElementById('baseline-summary').replaceChildren();
  document.getElementById('baseline-count').textContent = 'Conformance coverage unknown.';
}
function baselineGameOptions(games) {
  const control = document.getElementById('baseline-game'), selected = control.value;
  control.replaceChildren();
  const all = document.createElement('option'); all.value = ''; all.textContent = 'All games'; control.append(all);
  const names = [...new Set(games.map(game => game.game))];
  for (const name of names) {
    const option = document.createElement('option'); option.value = name; option.textContent = name; control.append(option);
  }
  control.value = names.includes(selected) ? selected : '';
  return Boolean(selected && !names.includes(selected));
}
function baselineCell(game, row, rowIds, gameIds) {
  const cells = plainObject(game.cells) ? game.cells : {};
  const cell = Object.hasOwn(cells, row.id) && plainObject(cells[row.id]) && rowIds.get(row.id) === 1 && gameIds.get(game.game) === 1 ? cells[row.id] : null;
  const hasEvidence = cell && typeof cell.evidence === 'string' && cell.evidence.trim();
  const evidence = hasEvidence ? cell.evidence.slice(0, 500) : 'No evidence supplied';
  return {status: hasEvidence && baselineStatuses.includes(cell.status) ? cell.status : 'Unknown', evidence};
}
function baselinePlaytestScenarios(game) {
  if (!['FFXI (LSB)', 'FFXI Forever (Rust)', 'SWTOR'].includes(game)) return null;
  const swtor = game === 'SWTOR', forever = game === 'FFXI Forever (Rust)';
  return [
    {title: 'Invite and follow', rows: ['p-01', 'p-02', 'p-07'],
      step: swtor ? 'Invite the squad and cross three area boundaries, including walking and one available taxi, shuttle or ship transfer. Look for every bot to arrive within 30 seconds each time, with the squad intact.'
        : `Invite the bots and cross three zone boundaries by walking and one available ${forever ? 'era-correct transport, such as a boat' : 'teleport or transport'}. Look for every bot to arrive within 30 seconds each time, with the party intact.`,
      evidence: 'Timestamped owner and bot arrivals for all three transfers, exact bot IDs and party membership before and after.'},
    {title: 'Ten pulls and party roles', rows: ['p-03', 'p-04', 'p-05'],
      step: swtor ? 'Fight 10 appropriate pulls. Watch tank threat, healing, resource recovery between fights and abilities appropriate to each squad role, discipline and level.'
        : `Fight 10 pulls at an appropriate camp${forever ? ' in the level-appropriate West Sarutabaruta area' : ''}. Watch the tank hold hate, the healer keep the party up and rest for MP, and each bot use job- and level-appropriate abilities.`,
      evidence: 'A bounded log of all 10 pulls showing actors, abilities, targets, healing and between-pull recovery; record failures as well as successes.'},
    {title: 'Death and recovery', rows: ['p-05'],
      step: swtor ? 'Observe a bot death during normal play, then its revive and regroup with the squad. Check that it is ready before rejoining combat.'
        : 'Observe a bot death during normal play. Check that it accepts a Raise offered within 60 seconds; otherwise it releases and rejoins the party within 5 minutes, without pulling while weakened.',
      evidence: swtor ? 'Death, revive and regroup timestamps, bot identity and subsequent combat state.'
        : 'Death, Raise or release, return-to-party and weakness-state timestamps for the same bot.'},
    {title: 'Owner orders', rows: ['p-08'],
      step: 'Using only commands already available to the owner, try stay, follow, assist, attack, pull, rest, a stance, focus heal and dismiss. Check each requested action and any AI-worded acknowledgement or silence.',
      evidence: 'Correlated owner request, target bot, resulting action and native acknowledgement if any. An acknowledgement alone does not prove execution.'},
    {title: 'Mount and dismount', rows: ['p-06'],
      step: swtor ? 'During an authorized mounted journey, check that every bot uses its class mount or speeder and dismounts to fight.'
        : forever ? 'During an era-correct journey, check that every bot uses a rented chocobo and dismounts to fight.'
        : 'Mount or travel a long distance; check that every bot uses its available chocobo or mount and dismounts to fight.',
      evidence: 'Mount, movement and combat-dismount observations for each bot, with times and exact actor IDs.'},
    {title: 'Quest or mission step', rows: ['p-10'],
      step: swtor ? 'Complete one available class-story or planet-quest step with the squad present and helping.'
        : `Complete one available ${forever ? 'era-correct ' : ''}quest or mission step with the bots present and helping.`,
      evidence: 'Scoped objective and starting state, bot participation, and observed quest or mission progress after the step.'},
    {title: 'Talk and memory', rows: ['p-11'],
      step: swtor ? 'Use whisper and group chat with a bot. Check that relevant AI replies remember the last few lines in this conversation.'
        : 'Send a /tell and a party message to a bot. Check that relevant AI replies remember the last few lines in this conversation.',
      evidence: 'Exact bot and channel, scoped conversation turns and native reply observations; wording generation alone does not prove speech.'},
    {title: 'AI tactics', rows: ['p-12'],
      step: 'Only when advice is already authorized and enabled, inspect at least one applied goal, tactic or rotation advice record and its reason. Use an already-authorized advice-off session to check that bots still play correctly. Leave unavailable runs unverified; this checklist does not enable or switch advice.',
      evidence: 'Scoped advice request, chosen legal option, applied outcome and reason, plus the separate advice-off gameplay observation.'},
  ];
}
function renderBaselinePlaytest(panel, rows, game, rowIds, gameIds) {
  const scenarios = baselinePlaytestScenarios(game.game);
  if (!scenarios) {
    const note = document.createElement('p'); note.className = 'muted';
    note.textContent = 'No owner playtest checklist supplied for this game.'; panel.append(note);
    return;
  }
  const details = document.createElement('details'); details.id = 'baseline-playtest-checklist';
  const summary = document.createElement('summary'); summary.textContent = `${game.game} owner playtest checklist · 8 scenarios`;
  const note = document.createElement('p'); note.className = 'muted';
  note.textContent = 'Owner acceptance plan, 2026-11-09. Use only an existing authorized playtest session after readiness is confirmed by the game lead; preserve player and release holds. These are planned checks, not completed results. This checklist records nothing and never changes tracker statuses.';
  const list = document.createElement('ol');
  for (const scenario of scenarios) {
    const entry = document.createElement('li'), heading = document.createElement('strong'); heading.textContent = scenario.title;
    const step = document.createElement('p'); step.textContent = scenario.step;
    const evidence = document.createElement('p'); evidence.textContent = `Evidence needed: ${scenario.evidence}`;
    const mappings = document.createElement('ul'); mappings.setAttribute('aria-label', `${scenario.title}: existing parity evidence`);
    for (const id of scenario.rows) {
      const row = rows.find(candidate => candidate.group === 'parity' && candidate.id === id);
      const cell = row ? baselineCell(game, row, rowIds, gameIds) : {status: 'Unknown', evidence: 'No usable parity row supplied'};
      const line = document.createElement('li');
      const behavior = row && rowIds.get(id) === 1 ? row.behavior.slice(0, 500) : 'Behavior identity missing or ambiguous';
      line.textContent = `${id} · ${behavior} — ${cell.status}. Existing evidence: ${cell.evidence}`;
      mappings.append(line);
    }
    entry.append(heading, step, evidence, mappings); list.append(entry);
  }
  details.append(summary, note, list); panel.append(details);
}
function renderBaselineSummary(rows, games, rowIds, gameIds, incomplete) {
  const panel = document.getElementById('baseline-summary'); panel.replaceChildren();
  if (!document.getElementById('baseline-game').value) {
    panel.textContent = 'Select one game to review its supplied parity counts and owner playtest plan.';
    return;
  }
  const parity = rows.filter(row => row.group === 'parity');
  if (!parity.length || !games.length) {
    panel.textContent = 'Parity counts: Unknown. No usable parity rows for the selected game; this is not a completed goal.';
    if (games.length) renderBaselinePlaytest(panel, rows, games[0], rowIds, gameIds);
    return;
  }
  const counts = Object.fromEntries(baselineStatuses.map(status => [status, 0]));
  for (const row of parity) counts[baselineCell(games[0], row, rowIds, gameIds).status]++;
  const order = ['Verified live', 'Partly live', 'Built', 'Designed', 'Not started', 'Unknown', 'Not applicable', 'Reference', 'Sim-measured', 'Unit-tested'];
  item(panel, `${games[0].game} · supplied parity counts`, order.map(status => `${status}: ${counts[status]}`).join(' · '),
    `${parity.length} supplied parity rows before group/status filters. ${incomplete ? 'Total coverage Unknown: malformed, repeated or omitted entries. ' : ''}Counts describe documented evidence, not current behavior or goal completion.`);
  renderBaselinePlaytest(panel, rows, games[0], rowIds, gameIds);
}
function renderBaselineConformance() {
  const panel = document.getElementById('baseline-conformance');
  panel.replaceChildren();
  const data = currentSnapshot?.baselineConformance;
  if (!plainObject(data) || !Array.isArray(data.rows) || !Array.isArray(data.games)) {
    resetBaselineConformance();
    document.getElementById('baseline-summary').textContent = 'Parity counts: Unknown. No usable tracker is loaded.';
    item(panel, 'Baseline conformance', 'Unknown', 'Missing or malformed baselineConformance; no behavior is shown as present.');
    return;
  }
  const validText = value => typeof value === 'string' && value.trim() && value.length <= 500;
  const rows = data.rows.filter(row => plainObject(row) && validText(row.id) && validText(row.behavior)).slice(0, 40);
  const games = data.games.filter(g => plainObject(g) && validText(g.game)).slice(0, 20);
  // Count identities over the full supplied collections: filters and display
  // limits must never make an ambiguous identity appear unique.
  const rowIds = new Map(), gameIds = new Map();
  for (const row of data.rows) if (plainObject(row) && validText(row.id)) rowIds.set(row.id, (rowIds.get(row.id) || 0) + 1);
  for (const game of data.games) if (plainObject(game) && validText(game.game)) gameIds.set(game.game, (gameIds.get(game.game) || 0) + 1);
  const omitted = rows.length !== data.rows.length || games.length !== data.games.length;
  const repeated = [...rowIds.values(), ...gameIds.values()].some(count => count > 1);
  const incomplete = omitted || repeated;
  const selectionLost = baselineGameOptions(games);
  for (const id of ['baseline-game', 'baseline-group', 'baseline-status']) document.getElementById(id).disabled = !rows.length || !games.length;
  const groupControl = document.getElementById('baseline-group'), statusControl = document.getElementById('baseline-status');
  if (!['', 'parity', 'forever', 'dit', 'unknown'].includes(groupControl.value)) groupControl.value = '';
  if (!['', 'needs-live', ...baselineStatuses].includes(statusControl.value)) statusControl.value = '';
  const selectedGames = document.getElementById('baseline-game').value ? games.filter(game => game.game === document.getElementById('baseline-game').value) : games;
  const matchesStatus = status => !statusControl.value || (statusControl.value === 'needs-live'
    ? !['Verified live', 'Reference', 'Not applicable'].includes(status) : status === statusControl.value);
  const filteredRows = rows.filter(row => (!groupControl.value || (groupControl.value === 'unknown'
    ? !['parity', 'forever', 'dit'].includes(row.group) : row.group === groupControl.value))
    && selectedGames.some(game => matchesStatus(baselineCell(game, row, rowIds, gameIds).status)));
  item(panel, 'Baseline conformance source', routingText(data.source, 'Source unknown'),
    `${rows.length} behaviors · ${games.length} games${omitted ? ' · Malformed entries omitted; coverage incomplete' : ''}${repeated ? ' · Repeated identities; affected statuses Unknown' : ''} · Documented tracker date: ${routingText(data.asOf, 'Unknown').slice(0, 100)}; not a freshness or live check.`);
  document.getElementById('baseline-count').textContent = !rows.length || !games.length
    ? 'Conformance coverage Unknown: no usable behaviors or games. An empty table does not establish completion.'
    : `${selectionLost ? 'Previous game selection unavailable; showing all supplied games. ' : ''}Showing ${filteredRows.length} of ${rows.length} supplied behaviors across ${selectedGames.length} displayed game columns.${incomplete ? ' Total coverage Unknown.' : ''} Local filters only; no requests or status changes.`;
  renderBaselineSummary(rows, selectedGames, rowIds, gameIds, incomplete);
  if (!rows.length || !games.length) item(panel, 'No usable conformance rows or games', 'Unknown', 'An empty table does not mean no bot has these behaviors.');
  else if (!filteredRows.length) item(panel, 'No behaviors match these filters', 'No matching supplied rows', 'Clear the filters to review other documented evidence; this does not establish completion.');
  for (const [group, label] of baselineGroups) {
    const groupRows = filteredRows.filter(row => group ? row.group === group : !['parity', 'forever', 'dit'].includes(row.group));
    if (!groupRows.length || !selectedGames.length) continue;
    const region = document.createElement('div'); region.className = 'model-samples';
    region.setAttribute('role', 'region'); region.setAttribute('aria-label', label); region.setAttribute('tabindex', '0');
    const heading = document.createElement('h4'); heading.textContent = label;
    const table = document.createElement('table'), caption = document.createElement('caption');
    caption.textContent = `${label}. Status reflects the evidence cited for each cell; Unknown means not supplied.`;
    const head = document.createElement('thead'), headings = document.createElement('tr');
    for (const text of ['Behavior', ...selectedGames.map(g => `${g.game} · ${routingText(g.owner, 'Owner unknown')}`)]) {
      const cell = document.createElement('th'); cell.setAttribute('scope', 'col'); cell.textContent = text; headings.append(cell);
    }
    head.append(headings);
    const body = document.createElement('tbody');
    for (const row of groupRows) {
      const tr = document.createElement('tr'), name = document.createElement('th');
      name.setAttribute('scope', 'row'); name.textContent = row.behavior.slice(0, 500); tr.append(name);
      for (const g of selectedGames) {
        const {status, evidence} = baselineCell(g, row, rowIds, gameIds);
        const td = document.createElement('td'), strong = document.createElement('strong'), small = document.createElement('small');
        strong.className = `baseline-status baseline-${baselineStatusClass[status]}`;
        strong.textContent = status; small.textContent = evidence;
        td.setAttribute('title', evidence); td.append(strong, small); tr.append(td);
      }
      body.append(tr);
    }
    table.append(caption, head, body); region.append(heading, table); panel.append(region);
  }
}
function renderSpendExample() {
  const panel = document.getElementById('spend-example');
  panel.replaceChildren();
  const candidate = currentSnapshot.spendExample;
  const spend = candidate && typeof candidate === 'object' && !Array.isArray(candidate) ? candidate : {};
  const usd = value => metricNumber(value) ? `$${value.toFixed(2)}` : 'Unknown';
  item(panel, `Example month: ${routingText(spend.month)}`,
    `Settled: ${usd(spend.settledUsd)} · Open reservations: ${usd(spend.reservedOpenUsd)} · Budget: ${usd(spend.budgetUsd)}`,
    `${routingText(spend.source, 'Source unknown')} · ${routingText(spend.attribution, 'Attribution unknown')} · Observed: ${routingText(spend.fetchedAt)} · Separate ledgers are not reconciled.`);
}
function botItem(bot) {
  const parent = document.getElementById('bots');
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
  document.getElementById('hub-banner').textContent = currentSnapshot && loadedSource
    ? `Loading selected data source… Showing previous ${loadedSource} request snapshot from ${currentSnapshot.generatedAt || 'unknown time'} until loading finishes.`
    : 'Loading selected data source…';
  let unauthorized = false, rendering = false;
  try {
    const source = document.getElementById('data-source').value === 'hub' ? 'hub' : 'mock';
    const response = await fetch(`/api/overview?source=${source}`, {headers: {Authorization: `Bearer ${requestToken}`}, cache: 'no-store'});
    if (!current()) return;
    if (!response.ok) { unauthorized = response.status === 401; throw new Error(unauthorized ? 'Token was not accepted.' : 'Could not load the workspace.'); }
    const data = await readBoundedJson(response);
    if (!current()) return;
    rendering = true;
    for (const id of ['bots', 'leads', 'issues', 'ledger', 'learning', 'lead-monitoring', 'audit', 'service-health', 'lead-timeline', 'quota-history', 'session-markers', 'model-calls', 'model-comparison', 'bot-activity', 'baseline-conformance', 'owner-attention', 'assignment-history', 'nudge-history', 'lead-activity', 'hub-feeds', 'lead-summary', 'reply-source', 'learning-coverage', 'issue-coverage', 'bot-coverage', 'learning-plan', 'learning-evidence', 'game-status', 'spend-example', 'learning-artifacts', 'safety-records', 'ffxi-focus', 'ffxi-feeds']) document.getElementById(id).replaceChildren();
    if (ledgerBotId !== null && loadedSource && loadedSource !== source) {
      ledgerBotId = null; correlationFilter = ''; document.getElementById('correlation').value = '';
    }
    currentSnapshot = data;
    clearRosterGapSelection();
    if (data.ffxiFocus) {
      const f = data.ffxiFocus, target = document.getElementById('ffxi-focus');
      item(target, 'Closest documented slice', routingText(f.closest), routingText(f.source, 'Source unknown'));
      item(target, 'What to look for', routingText(f.whatToLookFor), 'Readiness must be confirmed by the owning lead');
      item(target, 'How to toggle', routingText(f.toggle), 'Read only');
      item(target, 'Not yet verified', routingText(f.unverified), 'A bridge observation does not establish delivery');
    } else item(document.getElementById('ffxi-focus'), 'FFXI readiness unknown',
      'No readiness summary was supplied in this snapshot.', 'Confirm readiness with the owning lead; feed availability does not establish game behavior.');
    renderOwnerAttention(data.ownerAttention);
    const supplied = data.hubFeeds;
    const feeds = Array.isArray(supplied) ? supplied.filter(f => f && typeof f === 'object' && !Array.isArray(f)) : [];
    const incomplete = !Array.isArray(supplied) || feeds.length !== supplied.length
      || feeds.some(f => ['game', 'view', 'status'].some(key => typeof f[key] !== 'string' || !f[key].trim()));
    const banner = document.getElementById('hub-banner');
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
    feeds.forEach(f => item(document.getElementById('hub-feeds'), `${routingText(f.game)} · ${routingText(f.view)}`, routingText(f.status), `${routingText(f.note)} · Fetched: ${routingText(f.at)}`));
    if (incomplete || !feeds.length) item(document.getElementById('hub-feeds'), 'Feed coverage', 'Unknown', 'Missing or incomplete feed metadata does not establish availability.');
    const ffxiFeeds = feeds.filter(f => f.game === 'FFXI' || f.game === 'All');
    if (incomplete || !ffxiFeeds.length) item(document.getElementById('ffxi-feeds'), 'FFXI feed coverage', 'Unknown', 'Missing or incomplete feed metadata; supplied rows do not establish complete FFXI coverage');
    ffxiFeeds.forEach(f => item(document.getElementById('ffxi-feeds'), `${routingText(f.game)} · ${routingText(f.view)}`, routingText(f.status), `${routingText(f.note)} · Fetched: ${routingText(f.at)} · Not proof of game presence or delivery`));
    renderBotCoverage();
    renderPresenceExamples(data.presenceExamples);
    renderBots();
    if (selectedBotId !== null) inspectBot(selectedBotId);
    else { renderAssignments(); renderReplySource(); renderSafety(); }
    const gamePanel = document.getElementById('game-status'), servicePanel = document.getElementById('service-health');
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
    renderBotActivity();
    renderBaselineConformance();
    document.getElementById('updated').textContent = `Snapshot generated ${data.generatedAt} · Sources are labeled per view; lead task state comes from the coordinator board.`;
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
    if (currentSnapshot && loadedSource && !unauthorized && !rendering && !e?.invalidShape) {
      document.getElementById('hub-banner').textContent = `Refresh failed. Showing previous ${loadedSource} request snapshot from ${currentSnapshot.generatedAt || 'unknown time'}; selected source may not match. Check each feed's source.`;
      return;
    }
    workspace.hidden = true; form.hidden = false; sessionStorage.removeItem('dit-admin-token'); resetPanelSession();
    error.textContent = unauthorized ? 'Token was not accepted.' : 'Could not load the workspace.';
  }
}
form.addEventListener('submit', e => { e.preventDefault(); resetPanelSession(); token = document.getElementById('token').value; document.getElementById('token').value = ''; load(); });
document.getElementById('refresh').addEventListener('click', load);
document.getElementById('model-call-availability').addEventListener('change', () => { if (currentSnapshot) renderModelCalls(); });
document.getElementById('bot-activity-engine').addEventListener('change', () => { if (currentSnapshot) renderBotActivity(); });
document.getElementById('bot-activity-search').addEventListener('input', () => { if (currentSnapshot) renderBotActivity(); });
for (const id of ['baseline-game', 'baseline-group', 'baseline-status']) {
  document.getElementById(id).addEventListener('change', () => { if (currentSnapshot) renderBaselineConformance(); });
}
document.getElementById('baseline-reset').addEventListener('click', () => {
  for (const id of ['baseline-game', 'baseline-group', 'baseline-status']) document.getElementById(id).value = '';
  if (currentSnapshot) renderBaselineConformance();
});
document.getElementById('reply-correlation').addEventListener('input', () => { if (currentSnapshot) renderReplySource(); });
document.getElementById('reply-reset').addEventListener('click', () => {
  document.getElementById('reply-correlation').value = '';
  if (currentSnapshot) renderReplySource();
});
document.getElementById('assignment-prev').addEventListener('click', () => changeAssignmentPage(-1));
document.getElementById('assignment-next').addEventListener('click', () => changeAssignmentPage(1));
document.getElementById('audit-search').addEventListener('input', () => { if (currentSnapshot) renderAudit(); });
document.getElementById('routing-audit-scope').addEventListener('change', () => { if (currentSnapshot) renderRoutingAudit(); });
document.getElementById('routing-audit-outcome').addEventListener('change', () => { if (currentSnapshot) renderRoutingAudit(); });
document.getElementById('routing-audit-reset').addEventListener('click', () => {
  document.getElementById('routing-audit-scope').value = '';
  document.getElementById('routing-audit-outcome').value = '';
  if (currentSnapshot) renderRoutingAudit();
});
document.getElementById('audit-reset').addEventListener('click', () => {
  document.getElementById('audit-search').value = '';
  if (currentSnapshot) renderAudit();
});
document.getElementById('bridge-refresh').addEventListener('click', loadBridge);
document.getElementById('hub-health-refresh').addEventListener('click', loadHubHealth);
document.getElementById('interaction-refresh').addEventListener('click', loadInteraction);
document.getElementById('interaction-preview').addEventListener('click', previewInteraction);
if (typeof setInterval === 'function') setInterval(() => { if (document.visibilityState !== 'hidden') loadBridge(); }, 15000);
document.getElementById('data-source').addEventListener('change', () => { traceVersion++; healthVersion++; interactionVersion++; document.getElementById('interaction-status').replaceChildren(); document.getElementById('interaction-status').textContent = 'Not requested.'; document.getElementById('hub-trace').replaceChildren(); document.getElementById('hub-health').textContent = 'Not requested.'; return load(); });
document.getElementById('quota-window').addEventListener('change', () => { if (currentSnapshot) renderQuotaHistory(); });
document.getElementById('timeline-kind').addEventListener('change', () => { if (currentSnapshot) renderLeadTimeline(); });
document.getElementById('show-routing').addEventListener('click', () => {
  document.getElementById('bots').querySelectorAll('details').forEach(panel => { panel.open = true; });
});
document.getElementById('hide-routing').addEventListener('click', () => {
  document.getElementById('bots').querySelectorAll('details').forEach(panel => { panel.open = false; });
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
document.getElementById('clear-bot').addEventListener('click', () => {
  selectedBotId = null;
  resetBotDraft();
  if (currentSnapshot) updateBotCount(filteredBots());
  const panel = document.getElementById('bot-inspector');
  panel.replaceChildren(); panel.textContent = 'No bot selected.';
  if (currentSnapshot) { renderAssignments(); renderReplySource(); renderSafety(); if (document.getElementById('issue-selected-bot').checked) renderIssues(); }
});
document.getElementById('ffxi-evidence').addEventListener('click', () => {
  document.getElementById('trace-game').value = 'ffxi';
  document.getElementById('correlation').value = '';
  correlationFilter = ''; ledgerBotId = null; traceVersion++;
  document.getElementById('hub-trace').replaceChildren();
  if (currentSnapshot) renderLedger();
  focusWorkspaceTarget('trace-search');
});
document.getElementById('ffxi-bots').addEventListener('click', () => {
  rosterRecordIndex = null;
  document.getElementById('bot-search').value = '';
  document.getElementById('bot-identity').value = '';
  document.getElementById('bot-game').value = 'FFXI';
  if (currentSnapshot) renderBots();
  focusWorkspaceTarget('bots');
});
document.getElementById('bot-game').addEventListener('change', () => { rosterRecordIndex = null; if (currentSnapshot) renderBots(); });
document.getElementById('bot-identity').addEventListener('change', () => { rosterRecordIndex = null; if (currentSnapshot) renderBots(); });
document.getElementById('bot-search').addEventListener('input', () => { rosterRecordIndex = null; if (currentSnapshot) renderBots(); });
document.getElementById('bot-reset').addEventListener('click', () => {
  rosterRecordIndex = null;
  document.getElementById('bot-game').value = '';
  document.getElementById('bot-search').value = '';
  document.getElementById('bot-identity').value = '';
  if (currentSnapshot) renderBots();
});
document.getElementById('ffxi-issues').addEventListener('click', () => {
  for (const id of ['issue-status', 'issue-search']) document.getElementById(id).value = '';
  document.getElementById('issue-selected-bot').checked = false;
  document.getElementById('issue-scope').value = 'FFXI';
  if (currentSnapshot) renderIssues();
  focusWorkspaceTarget('issues');
});
document.getElementById('issue-scope').addEventListener('change', () => { if (currentSnapshot) renderIssues(); });
document.getElementById('issue-status').addEventListener('change', () => { if (currentSnapshot) renderIssues(); });
document.getElementById('issue-selected-bot').addEventListener('change', () => { if (currentSnapshot) renderIssues(); });
document.getElementById('issue-search').addEventListener('input', () => { if (currentSnapshot) renderIssues(); });
document.getElementById('issue-reset').addEventListener('click', () => {
  for (const id of ['issue-scope', 'issue-status', 'issue-search']) document.getElementById(id).value = '';
  document.getElementById('issue-selected-bot').checked = false;
  if (currentSnapshot) renderIssues();
});
function showGameLearning(game) {
  for (const id of ['learning-status', 'learning-search']) document.getElementById(id).value = '';
  document.getElementById('learning-attention').checked = false;
  document.getElementById('learning-game').value = game;
  if (currentSnapshot) { renderLearningPlan(); renderLearningArtifacts(); renderLearning(); }
  focusWorkspaceTarget('learning');
}
document.getElementById('ffxi-learning').addEventListener('click', () => showGameLearning('FFXI'));
document.getElementById('clear-learning').addEventListener('click', () => {
  selectedLearningId = null;
  const panel = document.getElementById('learning-inspector');
  panel.replaceChildren(); panel.textContent = 'Select a learning need for details.';
  renderLearningEvidence(null);
  if (currentSnapshot) updateLearningCount(filteredLearning());
});
document.getElementById('learning-evidence-preview').addEventListener('click', previewLearningEvidence);
document.getElementById('learning-evidence-selected').addEventListener('click', () => {
  renderLearningEvidence(uniqueRecord(currentSnapshot?.learning, selectedLearningId));
});
document.getElementById('learning-game').addEventListener('change', () => { if (currentSnapshot) { renderLearningPlan(); renderLearningArtifacts(); renderLearning(); } });
document.getElementById('learning-status').addEventListener('change', () => { if (currentSnapshot) renderLearning(); });
document.getElementById('learning-attention').addEventListener('change', () => { if (currentSnapshot) renderLearning(); });
document.getElementById('learning-search').addEventListener('input', () => { if (currentSnapshot) renderLearning(); });
document.getElementById('learning-reset').addEventListener('click', () => {
  for (const id of ['learning-game', 'learning-status', 'learning-search']) document.getElementById(id).value = '';
  document.getElementById('learning-attention').checked = false;
  if (currentSnapshot) { renderLearningPlan(); renderLearningArtifacts(); renderLearning(); }
});
for (const id of ['trace-game', 'correlation']) {
  document.getElementById(id).addEventListener(id === 'correlation' ? 'input' : 'change', () => {
    traceVersion++; document.getElementById('hub-trace').replaceChildren();
  });
}
document.getElementById('trace-search').addEventListener('submit', e => {
  e.preventDefault(); ledgerBotId = null; correlationFilter = document.getElementById('correlation').value.trim();
  if (currentSnapshot) renderLedger();
  if (document.getElementById('data-source').value === 'hub') {
    if (sourceLoading || loadedSource !== 'hub') {
      traceVersion++; document.getElementById('hub-trace').replaceChildren();
      document.getElementById('hub-trace').textContent = 'Load the selected hub source successfully before requesting a hub trace.';
    } else loadHubTrace(correlationFilter);
  }
});
document.getElementById('trace-clear').addEventListener('click', () => {
  correlationFilter = ''; ledgerBotId = null; document.getElementById('correlation').value = ''; traceVersion++; document.getElementById('hub-trace').replaceChildren();
  if (currentSnapshot) renderLedger();
});
if (token) load();
document.getElementById('back-to-roster').addEventListener('click', () => focusWorkspaceTarget('bots'));
