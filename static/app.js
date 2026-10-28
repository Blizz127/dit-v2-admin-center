const form = document.querySelector('#login');
const error = document.querySelector('#error');
const workspace = document.querySelector('#workspace');
let currentSnapshot = null;
let selectedBotId = null;
let correlationFilter = '';
let selectedLearningId = null;
let token = sessionStorage.getItem('dit-admin-token') || '';
function item(parent, title, detail, meta) {
  const row = document.createElement('div'); row.className = 'row';
  const heading = document.createElement('strong'); heading.textContent = title;
  const text = document.createElement('p'); text.textContent = detail;
  const small = document.createElement('small'); small.textContent = meta || '';
  row.append(heading, text, small); parent.append(row);
}
function renderIssues() {
  const panel = document.querySelector('#issues');
  const scope = document.querySelector('#issue-scope').value;
  panel.replaceChildren();
  const records = currentSnapshot.issues.filter(i => !scope || i.scope === scope);
  if (!records.length) item(panel, 'No matching issues', 'No records in this mock snapshot.', 'This does not establish a healthy state.');
  records.forEach(i => {
    item(panel, i.title, i.detail, `${i.scope} · ${i.status} · ${i.source} · Updated: ${i.updatedAt || 'unknown'}`);
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
  item(panel, `Learning detail · ${need.game} · ${need.topic}`, `Status: ${need.status} · Reason: ${need.reason || 'Not reported'}`,
    `Evidence: ${need.evidence} · Datasets: ${need.datasets} · Policy verification: ${need.policy} · Updated: ${need.updatedAt || 'unknown'} · ${need.source}`);
}
function renderLearning() {
  const panel = document.querySelector('#learning');
  const game = document.querySelector('#learning-game').value;
  const status = document.querySelector('#learning-status').value;
  panel.replaceChildren();
  const records = currentSnapshot.learning.filter(l => (!game || l.game === game) && (!status || l.status === status));
  if (!records.length) item(panel, 'No matching learning entries', 'No records in this mock snapshot.', 'Coverage is unknown.');
  records.forEach(l => {
    item(panel, `${l.game} · ${l.topic}`, l.status, `Evidence: ${l.evidence} · Datasets: ${l.datasets} · Policy verification: ${l.policy} · ${l.source}`);
    if (l.id) {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = `Inspect ${l.topic}`; button.addEventListener('click', () => inspectLearning(l.id));
      panel.lastElementChild.append(button);
    }
  });
  if (selectedLearningId !== null) inspectLearning(selectedLearningId);
}
function renderLedger() {
  const panel = document.querySelector('#ledger');
  panel.replaceChildren();
  const records = currentSnapshot.ledger.filter(e => !correlationFilter || e.correlationId === correlationFilter);
  if (!records.length) item(panel, 'No matching evidence', 'No records in this mock snapshot.', 'This is not proof that an action did or did not occur.');
  records.forEach(e => item(panel, `${e.bot} · ${e.request}`, `Result: ${e.result} · Verification: ${e.verification}`, `Correlation: ${e.correlationId}`));
}
function inspectBot(id) {
  selectedBotId = id;
  const panel = document.querySelector('#bot-inspector');
  panel.replaceChildren();
  const bot = currentSnapshot.bots.find(b => b.id === id);
  if (!bot) { panel.textContent = 'Selected bot is no longer in this snapshot.'; return; }
  item(panel, `${bot.name} · ${bot.game}`, `Status: ${bot.status}`, `${bot.source} · Observed: ${bot.observedAt || 'unknown'}`);
  item(panel, 'Goals, personality and memory', 'Unknown', 'No hub connection');
  const events = currentSnapshot.ledger.filter(e => e.botId === bot.id);
  if (!events.length) item(panel, 'Evidence', 'No matching synthetic records', 'Absence of records does not prove inactivity.');
  events.forEach(e => item(panel, e.request, `Result: ${e.result} · Verification: ${e.verification}`, `Correlation: ${e.correlationId}`));
}
function botItem(bot) {
  const parent = document.querySelector('#bots');
  item(parent, `${bot.name} · ${bot.game}`, bot.status, `${bot.source} · Observed: ${bot.observedAt || 'unknown'}`);
  const row = parent.lastElementChild;
  const inspect = document.createElement('button');
  inspect.type = 'button';
  inspect.textContent = `Inspect ${bot.name}`;
  inspect.addEventListener('click', () => inspectBot(bot.id));
  row.append(inspect);
  const details = document.createElement('p');
  details.className = 'routing';
  const routing = bot.routing || {};
  details.textContent = `Requested model: ${routing.requested || 'Unknown'} · Effective model: ${routing.effective || 'Unknown'}`;
  const routingMeta = document.createElement('p');
  routingMeta.className = 'routing';
  routingMeta.textContent = `Purpose: ${routing.purpose || 'Unknown'} · Version: ${routing.version || 'Unknown'} · Availability: ${routing.availability || 'Unknown'} · Reason: ${routing.reason || 'Not reported'} · Source: ${routing.source || 'Unknown'} · Observed: ${routing.observedAt || 'unknown'}`;
  const scope = document.createElement('p');
  scope.className = 'routing';
  scope.textContent = 'Game, realm and native bot identity must be verified before routing is available.';
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
  note.textContent = 'Model selection awaits a hub contract and owner authorization.';
  label.append(select);
  row.append(details, routingMeta, scope, purposeLabel, label, note);
}
async function load() {
  error.textContent = '';
  try {
    const response = await fetch('/api/overview', {headers: {Authorization: `Bearer ${token}`}, cache: 'no-store'});
    if (!response.ok) throw new Error(response.status === 401 ? 'Token was not accepted.' : 'Could not load the workspace.');
    const data = await response.json();
    for (const id of ['bots', 'leads', 'issues', 'ledger', 'learning', 'lead-monitoring', 'audit', 'service-health']) document.getElementById(id).replaceChildren();
    currentSnapshot = data;
    data.bots.forEach(botItem);
    if (selectedBotId !== null) inspectBot(selectedBotId);
    data.serviceHealth.forEach(h => item(document.querySelector('#service-health'), `${h.label} · ${h.game}`, `${h.status} · ${h.detail}`, `${h.source} · Observed: ${h.observedAt || 'unknown'} · May be stale`));
    data.leads.forEach(l => item(document.querySelector('#leads'), `${l.name} · ${l.scope}`, l.status, `${l.source} · Observed: ${l.observedAt || 'unknown'}`));
    data.leadMonitoring.forEach(m => item(document.querySelector('#lead-monitoring'), m.lead, `Stall: ${m.stall} · Quota: ${m.quota}`, `Session activity: ${m.sessionActivity} (not proof of work or a stall) · ${m.stallReason} · ${m.quotaReason} · Provider pool: ${m.poolCapacity} (${m.poolReason})`));
    data.audit.forEach(a => item(document.querySelector('#audit'), `${a.action} · ${a.scope}`, a.result, `${a.actor} · ${a.at || 'unknown time'} · ${a.source}`));
    renderIssues();
    renderLedger();
    renderLearning();
    document.querySelector('#updated').textContent = `Snapshot generated ${data.generatedAt} · Bot and learning data are synthetic; lead task state comes from the coordinator board.`;
    sessionStorage.setItem('dit-admin-token', token); workspace.hidden = false; form.hidden = true;
  } catch (e) { workspace.hidden = true; form.hidden = false; sessionStorage.removeItem('dit-admin-token'); error.textContent = e.message; }
}
form.addEventListener('submit', e => { e.preventDefault(); token = document.querySelector('#token').value; document.querySelector('#token').value = ''; load(); });
document.querySelector('#refresh').addEventListener('click', load);
document.querySelector('#issue-scope').addEventListener('change', () => { if (currentSnapshot) renderIssues(); });
document.querySelector('#learning-game').addEventListener('change', () => { if (currentSnapshot) renderLearning(); });
document.querySelector('#learning-status').addEventListener('change', () => { if (currentSnapshot) renderLearning(); });
document.querySelector('#trace-search').addEventListener('submit', e => {
  e.preventDefault(); correlationFilter = document.querySelector('#correlation').value.trim();
  if (currentSnapshot) renderLedger();
});
document.querySelector('#trace-clear').addEventListener('click', () => {
  correlationFilter = ''; document.querySelector('#correlation').value = '';
  if (currentSnapshot) renderLedger();
});
if (token) load();
