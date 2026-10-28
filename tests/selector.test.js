// Exercise the browser rendering with synthetic data and a minimal DOM.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.attributes = {}; this.textContent = ''; this.listeners = {}; }
  append(...children) { this.children.push(...children); }
  replaceChildren() { this.children = []; }
  scrollIntoView() {}
  addEventListener(name, fn) { this.listeners[name] = fn; }
  setAttribute(name, value) { this.attributes[name] = value; }
  get lastElementChild() { return this.children.at(-1); }
}
const elements = new Map();
const get = id => { if (!elements.has(id)) elements.set(id, new Element('div')); return elements.get(id); };
const document = {querySelector: selector => get(selector.slice(1)), getElementById: get, createElement: tag => new Element(tag)};
const data = {generatedAt: 'test', bots: [{id: 'one', name: 'Example', game: 'FFXI', status: 'Unknown', source: 'Fixture', observedAt: null}, {id: 'two', name: 'Other', game: 'FFXI', status: 'Unknown', source: 'Fixture', observedAt: null, routing: {purpose: 'conversation', requested: 'Example provider / example model', effective: null, version: 'example-1', availability: 'Unavailable', reason: 'Identity unverified', source: 'Synthetic example', observedAt: '2026-01-01T00:00:00Z'}}], leads: [], leadMonitoring: [], leadTimeline: [], sessionMarkers: [{lead: 'Admin Center lead', coverage: 'Unknown', markers: []}], quotaHistory: [], modelCalls: [], audit: [], serviceHealth: [], issues: [{title: 'Bot issue', detail: 'Example', scope: 'Bots', status: 'Open', source: 'Fixture', learningId: 'need-one'}, {title: 'Network issue', detail: 'Example', scope: 'Network', status: 'Open', source: 'Fixture'}], ledger: [{botId: 'one', request: 'Observe', result: 'Accepted', verification: 'Pending', correlationId: 'one'}, {botId: 'another', request: 'Other bot action', result: 'Accepted', verification: 'Verified', correlationId: 'two'}], learning: [{id: 'need-one', game: 'FFXI', topic: 'Example FFXI', reason: 'Missing evidence', status: 'Unknown', evidence: 'Unknown', datasets: 'Unknown', policy: 'Unknown', source: 'Fixture'}, {game: 'SWTOR', topic: 'Example SWTOR', status: 'Unknown', evidence: 'Unknown', datasets: 'Unknown', policy: 'Unknown', source: 'Fixture'}]};
const context = {document, sessionStorage: {getItem: () => 'test', setItem() {}, removeItem() {}}, fetch: async () => ({ok: true, json: async () => data})};
vm.runInNewContext(fs.readFileSync('static/app.js', 'utf8'), context);
setImmediate(() => {
  const row = get('bots').children[0];
  const labels = row.children.filter(child => child.tag === 'label');
  const purpose = labels[0].children[0];
  assert.equal(purpose.disabled, true);
  assert.equal(purpose.children[0].textContent, 'Unavailable');
  const selector = labels[1].children[0];
  assert.equal(selector.tag, 'select');
  assert.equal(selector.disabled, true);
  assert.equal(selector.children.length, 1);
  assert.equal(selector.children[0].textContent, 'Unavailable');
  assert.match(row.children.find(child => child.className === 'routing').textContent, /Requested model: Unknown · Effective model: Unknown/);
  assert.match(row.children.at(-1).textContent, /hub contract and owner authorization/);
  const other = get('bots').children[1];
  const routing = other.children.filter(child => child.className === 'routing');
  assert.match(routing[0].textContent, /Requested model: Example provider \/ example model · Effective model: Unknown/);
  assert.match(routing[1].textContent, /Reported availability: Unavailable · Reason: Identity unverified/);
  assert.match(routing[1].textContent, /Synthetic example/);
  assert.match(routing[1].textContent, /Freshness: Unknown/);
  assert.ok(other.children.filter(child => child.tag === 'label').every(label => label.children[0].disabled));
  row.children.find(child => child.tag === 'button').listeners.click();
  const inspector = get('bot-inspector');
  assert.equal(inspector.children.length, 3);
  assert.equal(inspector.children[2].children[0].textContent, 'Observe');
  assert.match(inspector.children[2].children[1].textContent, /Verification: Pending/);
  assert.equal(inspector.children.some(child => child.children[0].textContent === 'Other bot action'), false);
  get('correlation').value = 'two';
  get('trace-search').listeners.submit({preventDefault() {}});
  assert.equal(get('ledger').children.length, 1);
  assert.match(get('ledger').children[0].children[0].textContent, /Other bot action/);
  get('correlation').value = 'missing';
  get('trace-search').listeners.submit({preventDefault() {}});
  assert.equal(get('ledger').children[0].children[0].textContent, 'No matching evidence');
  get('trace-clear').listeners.click();
  assert.equal(get('ledger').children.length, 2);
  get('learning-game').value = 'FFXI';
  get('learning-game').listeners.change();
  assert.equal(get('learning').children.length, 1);
  assert.match(get('learning').children[0].children[0].textContent, /FFXI/);
  get('learning-status').value = 'unverified';
  get('learning-status').listeners.change();
  assert.equal(get('learning').children[0].children[0].textContent, 'No matching learning entries');
  get('learning-status').value = '';
  get('learning-status').listeners.change();
  get('issue-scope').value = 'Bots';
  get('issue-scope').listeners.change();
  assert.equal(get('issues').children.length, 1);
  assert.equal(get('issues').children[0].children[0].textContent, 'Bot issue');
  assert.match(get('issues').children[0].children[2].textContent, /Updated: unknown/);
  get('issue-search').value = 'not found';
  get('issue-search').listeners.input();
  assert.equal(get('issues').children[0].children[0].textContent, 'No matching issues');
  get('issue-search').value = '';
  get('issue-search').listeners.input();
  get('issues').children[0].children.find(child => child.tag === 'button').listeners.click();
  const learningDetail = get('learning-inspector').children[0];
  assert.match(learningDetail.children[0].textContent, /Example FFXI/);
  assert.match(learningDetail.children[1].textContent, /Missing evidence/);
  assert.match(learningDetail.children[2].textContent, /Policy verification: Unknown/);
  console.log('Disabled selector, bot inspection and filters passed.');
});
