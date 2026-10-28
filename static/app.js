const form = document.querySelector('#login');
const error = document.querySelector('#error');
const workspace = document.querySelector('#workspace');
let token = sessionStorage.getItem('dit-admin-token') || '';
function item(parent, title, detail, meta) {
  const row = document.createElement('div'); row.className = 'row';
  const heading = document.createElement('strong'); heading.textContent = title;
  const text = document.createElement('p'); text.textContent = detail;
  const small = document.createElement('small'); small.textContent = meta || '';
  row.append(heading, text, small); parent.append(row);
}
function botItem(bot) {
  const parent = document.querySelector('#bots');
  item(parent, `${bot.name} · ${bot.game}`, bot.status, `${bot.source} · Observed: ${bot.observedAt || 'unknown'}`);
  const row = parent.lastElementChild;
  const details = document.createElement('p');
  details.className = 'routing';
  details.textContent = 'Requested model: Unknown · Effective model: Unknown';
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
  row.append(details, label, note);
}
async function load() {
  error.textContent = '';
  try {
    const response = await fetch('/api/overview', {headers: {Authorization: `Bearer ${token}`}, cache: 'no-store'});
    if (!response.ok) throw new Error(response.status === 401 ? 'Token was not accepted.' : 'Could not load the workspace.');
    const data = await response.json();
    for (const id of ['bots', 'leads', 'issues', 'ledger', 'learning', 'lead-monitoring']) document.getElementById(id).replaceChildren();
    data.bots.forEach(botItem);
    data.leads.forEach(l => item(document.querySelector('#leads'), `${l.name} · ${l.scope}`, l.status, `${l.source} · Observed: ${l.observedAt || 'unknown'}`));
    data.leadMonitoring.forEach(m => item(document.querySelector('#lead-monitoring'), m.lead, `Stall: ${m.stall} · Quota: ${m.quota}`, `${m.stallReason} · ${m.quotaReason}`));
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
