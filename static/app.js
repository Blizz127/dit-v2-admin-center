const form = document.querySelector('#login');
const error = document.querySelector('#error');
const workspace = document.querySelector('#workspace');
let currentSnapshot = null;
let selectedBotId = null;
let token = sessionStorage.getItem('dit-admin-token') || '';
function item(parent, title, detail, meta) {
  const row = document.createElement('div'); row.className = 'row';
  const heading = document.createElement('strong'); heading.textContent = title;
  const text = document.createElement('p'); text.textContent = detail;
  const small = document.createElement('small'); small.textContent = meta || '';
  row.append(heading, text, small); parent.append(row);
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
  details.textContent = 'Requested model: Unknown · Effective model: Unknown';
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
  row.append(details, scope, purposeLabel, label, note);
}
async function load() {
  error.textContent = '';
  try {
    const response = await fetch('/api/overview', {headers: {Authorization: `Bearer ${token}`}, cache: 'no-store'});
    if (!response.ok) throw new Error(response.status === 401 ? 'Token was not accepted.' : 'Could not load the workspace.');
    const data = await response.json();
    for (const id of ['bots', 'leads', 'issues', 'ledger', 'learning', 'lead-monitoring']) document.getElementById(id).replaceChildren();
    currentSnapshot = data;
    data.bots.forEach(botItem);
    if (selectedBotId !== null) inspectBot(selectedBotId);
    data.leads.forEach(l => item(document.querySelector('#leads'), `${l.name} · ${l.scope}`, l.status, `${l.source} · Observed: ${l.observedAt || 'unknown'}`));
    data.leadMonitoring.forEach(m => item(document.querySelector('#lead-monitoring'), m.lead, `Stall: ${m.stall} · Quota: ${m.quota}`, `Session activity: ${m.sessionActivity} (not proof of work or a stall) · ${m.stallReason} · ${m.quotaReason} · Provider pool: ${m.poolCapacity} (${m.poolReason})`));
    data.issues.forEach(i => item(document.querySelector('#issues'), i.title, i.detail, `${i.status} · ${i.source}`));
    data.ledger.forEach(e => item(document.querySelector('#ledger'), `${e.bot} · ${e.request}`, `Result: ${e.result} · Verification: ${e.verification}`, `Correlation: ${e.correlationId}`));
    data.learning.forEach(l => item(document.querySelector('#learning'), `${l.game} · ${l.topic}`, l.status, `Evidence: ${l.evidence} · Datasets: ${l.datasets} · Policy verification: ${l.policy} · ${l.source}`));
    document.querySelector('#updated').textContent = `Snapshot generated ${data.generatedAt} · Bot and learning data are synthetic; lead task state comes from the coordinator board.`;
    sessionStorage.setItem('dit-admin-token', token); workspace.hidden = false; form.hidden = true;
  } catch (e) { workspace.hidden = true; form.hidden = false; sessionStorage.removeItem('dit-admin-token'); error.textContent = e.message; }
}
form.addEventListener('submit', e => { e.preventDefault(); token = document.querySelector('#token').value; document.querySelector('#token').value = ''; load(); });
document.querySelector('#refresh').addEventListener('click', load);
if (token) load();
