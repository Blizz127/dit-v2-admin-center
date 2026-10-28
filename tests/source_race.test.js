const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor() { this.children = []; this.listeners = {}; this.textContent = ''; }
  append(...items) { this.children.push(...items); }
  replaceChildren() { this.children = []; }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  setAttribute() {}
  get lastElementChild() { return this.children.at(-1); }
}
const elements = new Map();
const get = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
const document = {querySelector: s => get(s.slice(1)), getElementById: get, createElement: () => new Element()};
const pending = [];
const fetch = url => url === '/api/bridge-status' ? Promise.resolve({ok: true, json: async () => ({unit: 'unknown', substate: 'unknown', result: 'unknown', marker: 'unknown', source: 'Fixture', observedAt: null})}) : new Promise(resolve => pending.push({url, resolve}));
const snapshot = status => ({generatedAt: 'test', hubFeeds: [{game: 'All', view: 'hub', status, note: '', at: null}], ownerAttention: {coverage: '', items: []}, bots: [], leads: [], leadActivity: [], leadMonitoring: [], leadTimeline: [], nudgeHistory: [], sessionMarkers: [], quotaHistory: [], spendExample: {month: null, settledUsd: null, reservedOpenUsd: null, budgetUsd: null, source: 'Synthetic', attribution: 'Unknown', fetchedAt: null}, modelCalls: [], botDetails: [], replyEvents: [], assignmentHistory: [], audit: [], gameStatus: [], serviceHealth: [], issues: [], ledger: [], learningPlan: [], learning: []});
const ctx = {document, fetch, sessionStorage: {getItem: () => 'test', setItem() {}, removeItem() {}}};
vm.runInNewContext(fs.readFileSync('static/app.js', 'utf8'), ctx);
(async () => {
  assert.equal(pending[0].url, '/api/overview?source=mock');
  get('data-source').value = 'hub';
  const newer = get('data-source').listeners.change();
  assert.equal(pending[1].url, '/api/overview?source=hub');
  pending[1].resolve({ok: true, json: async () => snapshot('Live response')});
  await newer;
  assert.match(get('hub-banner').textContent, /Hub reads available/);
  pending[0].resolve({ok: true, json: async () => snapshot('Not configured')});
  await new Promise(resolve => setImmediate(resolve));
  assert.match(get('hub-banner').textContent, /Hub reads available/);
  get('trace-game').value = 'ffxi';
  get('correlation').value = 'original';
  get('trace-search').listeners.submit({preventDefault() {}});
  assert.match(pending[2].url, /correlationId=original/);
  get('correlation').value = 'different';
  get('correlation').listeners.input();
  pending[2].resolve({ok: true, json: async () => ({coverage: 'stub', fetchedAt: 'time', records: []})});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(get('hub-trace').children.length, 0);
  console.log('Out-of-order source and trace responses remain isolated.');
})().catch(error => { console.error(error); process.exitCode = 1; });
