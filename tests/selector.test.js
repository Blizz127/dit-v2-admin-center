// Exercise the browser rendering with synthetic data and a minimal DOM.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.attributes = {}; this.textContent = ''; this.listeners = {}; }
  append(...children) { this.children.push(...children); }
  replaceChildren() { this.children = []; }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  setAttribute(name, value) { this.attributes[name] = value; }
  get lastElementChild() { return this.children.at(-1); }
}
const elements = new Map();
const get = id => { if (!elements.has(id)) elements.set(id, new Element('div')); return elements.get(id); };
const document = {querySelector: selector => get(selector.slice(1)), getElementById: get, createElement: tag => new Element(tag)};
const data = {generatedAt: 'test', bots: [{id: 'one', name: 'Example', game: 'FFXI', status: 'Unknown', source: 'Fixture', observedAt: null}], leads: [], leadMonitoring: [], issues: [{title: 'Bot issue', detail: 'Example', scope: 'Bots', status: 'Open', source: 'Fixture'}, {title: 'Network issue', detail: 'Example', scope: 'Network', status: 'Open', source: 'Fixture'}], ledger: [{botId: 'one', request: 'Observe', result: 'Accepted', verification: 'Pending', correlationId: 'one'}, {botId: 'another', request: 'Other bot action', result: 'Accepted', verification: 'Verified', correlationId: 'two'}], learning: [{game: 'FFXI', topic: 'Example FFXI', status: 'Unknown', evidence: 'Unknown', datasets: 'Unknown', policy: 'Unknown', source: 'Fixture'}, {game: 'SWTOR', topic: 'Example SWTOR', status: 'Unknown', evidence: 'Unknown', datasets: 'Unknown', policy: 'Unknown', source: 'Fixture'}]};
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
  get('issue-scope').value = 'Bots';
  get('issue-scope').listeners.change();
  assert.equal(get('issues').children.length, 1);
  assert.equal(get('issues').children[0].children[0].textContent, 'Bot issue');
  console.log('Disabled selector, bot inspection and filters passed.');
});
