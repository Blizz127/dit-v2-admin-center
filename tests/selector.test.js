// Exercise the browser rendering with synthetic data and a minimal DOM.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.attributes = {}; this.textContent = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren() { this.children = []; }
  addEventListener() {}
  setAttribute(name, value) { this.attributes[name] = value; }
  get lastElementChild() { return this.children.at(-1); }
}
const elements = new Map();
const get = id => { if (!elements.has(id)) elements.set(id, new Element('div')); return elements.get(id); };
const document = {querySelector: selector => get(selector.slice(1)), getElementById: get, createElement: tag => new Element(tag)};
const data = {generatedAt: 'test', bots: [{name: 'Example', game: 'FFXI', status: 'Unknown', source: 'Fixture', observedAt: null}], leads: [], leadMonitoring: [], issues: [], ledger: [], learning: []};
const context = {document, sessionStorage: {getItem: () => 'test', setItem() {}, removeItem() {}}, fetch: async () => ({ok: true, json: async () => data})};
vm.runInNewContext(fs.readFileSync('static/app.js', 'utf8'), context);
setImmediate(() => {
  const row = get('bots').children[0];
  const label = row.children.find(child => child.tag === 'label');
  const selector = label.children[0];
  assert.equal(selector.tag, 'select');
  assert.equal(selector.disabled, true);
  assert.equal(selector.children.length, 1);
  assert.equal(selector.children[0].textContent, 'Unavailable');
  assert.match(row.children.find(child => child.className === 'routing').textContent, /Requested model: Unknown · Effective model: Unknown/);
  assert.match(row.children.at(-1).textContent, /hub contract and owner authorization/);
  console.log('Disabled selector contract passed.');
});
