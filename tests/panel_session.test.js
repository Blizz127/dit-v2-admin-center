// Session-boundary audit of every async app view, using only deferred fixture promises.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor() { this.children = []; this.listeners = {}; this.text = ''; this.hidden = false; this.value = ''; }
  append(...items) { this.children.push(...items); }
  replaceChildren() { this.children = []; this.text = ''; }
  set textContent(value) { this.children = []; this.text = value; }
  get textContent() { return this.text + this.children.map(c => c.textContent).join(' '); }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  setAttribute() {}
  get lastElementChild() { return this.children.at(-1); }
}
const overview = () => ({...Object.fromEntries(['bots','leads','leadActivity','leadMonitoring','leadTimeline','nudgeHistory','sessionMarkers','quotaHistory','modelCalls','safetyRecords','botDetails','replyEvents','assignmentHistory','audit','gameStatus','serviceHealth','issues','ledger','learningArtifacts','learningPlan','learning','hubFeeds'].map(key => [key, []])),
  generatedAt: 'fixture-time', ownerAttention: {coverage: 'Fixture', items: []}, spendExample: {source: 'Fixture'}});
const views = [
  {name: 'interaction', call: c => c.loadInteraction(), panel: 'interaction-status', data: {switches: {contract: false}, bots: [], coverage: 'Fixture'}},
  {name: 'health', call: c => c.loadHubHealth(), panel: 'hub-health', data: {services: [], coverage: 'Fixture'}},
  {name: 'trace', call: c => c.loadHubTrace('fixture'), panel: 'hub-trace', data: {records: [], coverage: 'Fixture'}},
  {name: 'bridge', call: c => c.loadBridge(), panel: 'bridge-status', data: {unit: 'active', substate: 'running', marker: 'absent', source: 'Fixture'}},
  {name: 'overview', call: c => c.load(), panel: 'hub-banner', data: overview()},
];
const source = fs.readFileSync('static/app.js', 'utf8');
function environment() {
  const elements = new Map(), pending = [], storage = [];
  const get = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
  const context = {document: {querySelector: s => get(s.slice(1)), getElementById: get, createElement: () => new Element()},
    sessionStorage: {getItem: () => '', setItem: (...args) => storage.push(['set', ...args]), removeItem: (...args) => storage.push(['remove', ...args])},
    fetch: (url, options) => new Promise((resolve, reject) => pending.push({url, options, resolve, reject}))};
  vm.runInNewContext(source, context);
  vm.runInNewContext("token = 'synthetic-original'; loadedSource = 'hub';", context);
  get('data-source').value = 'hub'; get('trace-game').value = 'ffxi';
  return {context, get, pending, storage};
}
(async () => {
  const failures = [];
  let cases = 0;
  for (const view of views) {
    if (view.name !== 'overview') {
      for (const guard of ['hidden', 'no-token']) {
        const {context, get, pending} = environment();
        if (guard === 'hidden') get('workspace').hidden = true;
        else vm.runInNewContext("token = ''", context);
        await view.call(context);
        assert.equal(pending.length, 0, view.name + ': ' + guard + ' starts no request');
      }
    }
    for (const boundary of ['hidden', 'token-change', 'same-token-login']) {
      for (const outcome of ['success', 'denied', 'rejected', 'delayed-json']) {
        const {context, get, pending, storage} = environment();
        const operation = view.call(context);
        assert.equal(pending.length, 1);
        assert.equal(pending[0].options.headers.Authorization, 'Bearer synthetic-original');
        let finishJson;
        if (outcome === 'delayed-json') {
          pending[0].resolve({ok: true, json: () => new Promise(resolve => { finishJson = resolve; })});
          await new Promise(resolve => setImmediate(resolve));
        }
        if (boundary === 'hidden') get('workspace').hidden = true;
        if (boundary === 'token-change') vm.runInNewContext("token = 'synthetic-new'", context);
        if (boundary === 'same-token-login') {
          get('workspace').hidden = true;
          get('token').value = 'synthetic-original';
          get('login').listeners.submit({preventDefault() {}});
          get('workspace').hidden = false;
        }
        get(view.panel).textContent = 'SESSION_BOUNDARY';
        get('error').textContent = 'CURRENT_ERROR';
        const writesBefore = storage.length;
        if (outcome === 'success') pending[0].resolve({ok: true, json: async () => view.data});
        if (outcome === 'denied') pending[0].resolve({ok: false, status: 401});
        if (outcome === 'rejected') pending[0].reject(new Error('fixture failure'));
        if (outcome === 'delayed-json') finishJson(view.data);
        await operation;
        cases++;
        if (get(view.panel).textContent !== 'SESSION_BOUNDARY' || get('error').textContent !== 'CURRENT_ERROR' || storage.length !== writesBefore)
          failures.push(`${view.name}/${boundary}/${outcome}`);
      }
    }
    // A current response must still render; the session guard must not suppress normal operation.
    const {context, get, pending} = environment();
    if (view.name === 'overview') get('workspace').hidden = true; // Initial login is intentionally hidden.
    const operation = view.call(context);
    pending[0].resolve({ok: true, json: async () => view.data});
    await operation;
    assert.ok(get(view.panel).textContent.length > 0, view.name + ': normal rendering');
    assert.equal(get('error').textContent, '', view.name + ': no rendering error');
    if (view.name === 'overview') assert.equal(get('workspace').hidden, false, 'Initial login opens workspace');
  }
  assert.deepEqual(failures, [], 'Late responses changed current-session state');
  console.log(`${cases} deferred-response session cases and five current-response paths passed offline.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
