// Execute the actual app's bridge path with a minimal DOM and deferred fixture fetches.
// No HTTP listener, browser, account, network transport or timers are provided.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor() { this.children = []; this.listeners = {}; this.hidden = false; this.text = ''; }
  append(...items) { this.children.push(...items); }
  replaceChildren() { this.children = []; this.text = ''; }
  set textContent(value) { this.children = []; this.text = value; }
  get textContent() { return this.text + this.children.map(child => child.textContent).join(' '); }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  setAttribute() {}
  get lastElementChild() { return this.children.at(-1); }
}
const elements = new Map();
const get = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
const pending = [];
const context = {
  document: {querySelector: s => get(s.slice(1)), getElementById: get, createElement: () => new Element()},
  sessionStorage: {getItem: () => '', setItem() {}, removeItem() {}},
  fetch: (url, options) => {
    assert.equal(url, '/api/bridge-status');
    assert.equal(options.headers.Authorization, 'Bearer synthetic-view-token');
    assert.equal(options.cache, 'no-store');
    return new Promise((resolve, reject) => pending.push({resolve, reject}));
  },
};
get('workspace').hidden = true;
vm.runInNewContext(fs.readFileSync('static/app.js', 'utf8'), context);
const good = {unit: 'active', substate: 'running', result: 'success', marker: 'absent',
  markerReason: 'unknown', source: 'Synthetic observation', observedAt: '2026-01-01T12:00:00Z'};
const panels = ['bridge-status', 'ffxi-focus-bridge'];
async function success(data = good) {
  const operation = context.loadBridge();
  pending.at(-1).resolve({ok: true, json: async () => data});
  await operation;
}
(async () => {
  await context.loadBridge();
  assert.equal(pending.length, 0);
  vm.runInNewContext("token = 'synthetic-view-token'", context);
  await context.loadBridge();
  assert.equal(pending.length, 0, 'Hidden workspace must not poll');
  get('workspace').hidden = false;
  const first = context.loadBridge();
  await context.loadBridge();
  assert.equal(pending.length, 1, 'Only one bridge read may be in flight');
  pending[0].resolve({ok: true, json: async () => good});
  await first;
  panels.forEach(id => assert.match(get(id).textContent, /active.*running/));
  for (const failure of ['401', '503', 'invalid-json', 'transport-rejection']) {
    const operation = context.loadBridge();
    const request = pending.at(-1);
    if (failure === 'transport-rejection') request.reject(new Error('OMIT_PRIVATE_TRANSPORT'));
    else if (failure === 'invalid-json') request.resolve({ok: true, json: async () => { throw new Error('OMIT_PRIVATE_BODY'); }});
    else request.resolve({ok: false, status: Number(failure), json: async () => { throw new Error('Error body must not be read'); }});
    await operation;
    for (const id of panels) {
      assert.match(get(id).textContent, /unknown/i, failure);
      assert.doesNotMatch(get(id).textContent, /active|running|2026-01-01|OMIT_PRIVATE/, failure);
      assert.equal(get(id).children.length, 0, 'Old observation nodes removed');
    }
    await success();
    panels.forEach(id => assert.match(get(id).textContent, /active.*running/, 'Later read recovers'));
  }
  await success({unit: 'unknown', substate: 'unknown', result: 'unknown', marker: 'unknown',
    markerReason: 'unknown', source: 'Synthetic unavailable observation', observedAt: null});
  panels.forEach(id => {
    assert.match(get(id).textContent, /Observed: unknown/);
    assert.doesNotMatch(get(id).textContent, /active|running|2026-01-01/);
  });
  assert.match(get('ffxi-focus-bridge').textContent, /Not proof of delivery/);
  get('workspace').hidden = true;
  const count = pending.length;
  await context.loadBridge();
  assert.equal(pending.length, count);
  console.log('Bridge simulated-DOM checks passed: auth/visibility guard, single flight, 401/503/JSON/transport failures, both-card redaction and recovery.');
})().catch(error => { console.error(error); process.exitCode = 1; });
