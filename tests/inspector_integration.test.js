// Browser-free integration: candidate fixture -> Python projection -> real HTTP
// handler bytes -> actual app.js -> strict, template-backed simulated DOM.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const python = (...args) => execFileSync('python3', ['tests/inspector_runtime_fixture.py', ...args], {encoding: 'utf8', timeout: 5000});
const template = JSON.parse(python('--template'));
class Element {
  constructor(tag, attrs = {}, value = '') { this.tag = tag; this.attributes = attrs; this.value = value; this.hidden = Object.hasOwn(attrs, 'hidden'); this.children = []; this.listeners = {}; this.text = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren() { this.children = []; this.text = ''; }
  set textContent(value) { this.children = []; this.text = String(value); }
  get textContent() { return this.text + this.children.map(c => c.textContent).join(' '); }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  setAttribute(name, value) { this.attributes[name] = value; }
  querySelectorAll(tag) { return this.children.flatMap(child => [...(child.tag === tag ? [child] : []), ...child.querySelectorAll(tag)]); }
  scrollIntoView() {}
  get lastElementChild() { return this.children.at(-1); }
}
const elements = new Map(Object.entries(template).map(([id, spec]) => [id, new Element(spec.tag, spec.attrs, spec.value)]));
const get = id => { assert.ok(elements.has(id), 'Selector missing from shipped HTML: ' + id); return elements.get(id); };
const requests = [], storage = new Map();
let scenario = 'trace-pending';
const context = {
  document: {querySelector: selector => { assert.match(selector, /^#[\w-]+$/); return get(selector.slice(1)); }, getElementById: get, createElement: tag => new Element(tag)},
  sessionStorage: {getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key)},
  fetch: async (path, options) => {
    assert.equal(options.method || 'GET', 'GET');
    const auth = options.headers.Authorization;
    assert.ok(auth.startsWith('Bearer '));
    const result = JSON.parse(execFileSync('python3', ['tests/inspector_runtime_fixture.py'], {
      input: JSON.stringify({path, token: auth.slice(7), scenario}), encoding: 'utf8', timeout: 5000,
    }));
    requests.push({path, status: result.status, traceCalls: result.traceCalls});
    assert.equal(result.headers['Cache-Control'], 'no-store');
    assert.equal(Number(result.headers['Content-Length']), Buffer.byteLength(result.body));
    assert.ok(!result.body.includes('OMIT_RAW_ANSWER_AND_PLAYER_DATA'));
    assert.ok(!result.body.includes('OMIT_RAW_TRACE_BODY'));
    assert.ok(!result.body.includes('OMIT_PRIVATE_READ_FAILURE'));
    return {ok: result.status === 200, status: result.status, json: async () => JSON.parse(result.body)};
  },
};
vm.runInNewContext(fs.readFileSync('static/app.js', 'utf8'), context);
const flush = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  assert.equal(get('workspace').hidden, true, 'Honor actual template initial visibility');
  assert.equal(requests.length, 0, 'No startup read without a token');
  get('token').value = 'synthetic-wrong-token';
  get('login').listeners.submit({preventDefault() {}});
  await flush();
  assert.equal(requests[0].status, 401);
  assert.equal(get('workspace').hidden, true);
  assert.equal(get('error').textContent, 'Token was not accepted.');
  assert.equal(storage.size, 0);
  get('token').value = 'fixture-token';
  get('login').listeners.submit({preventDefault() {}});
  await flush();
  assert.equal(get('workspace').hidden, false);
  assert.equal(get('token').value, '');
  assert.equal(get('error').textContent, '');
  assert.equal(get('learning').children.length, 4);
  const expected = [['Yes','Not included'], ['No','Unknown'], ['Yes','Present'], ['Unknown','Not included']];
  get('learning').children.forEach((row, index) => {
    row.children.find(child => child.tag === 'button').listeners.click();
    const text = get('learning-inspector').textContent;
    assert.ok(text.includes('Model answer reported: ' + expected[index][0]));
    assert.ok(text.includes('Evidence: ' + expected[index][1]));
    assert.ok(text.includes('Status: verified') && text.includes('Policy verification: Unknown'));
    assert.equal((get('learning-evidence').textContent.match(/Evidence state: Unknown/g) || []).length, 5);
  });
  const count = requests.length;
  get('learning-evidence-preview').listeners.click();
  assert.match(get('learning-evidence').textContent, /Synthetic mapping preview/);
  get('learning-evidence-selected').listeners.click();
  assert.match(get('learning-evidence').textContent, /Evidence review/);
  get('clear-learning').listeners.click();
  assert.match(get('learning-evidence').textContent, /No learning record selected/);
  assert.equal(requests.length, count, 'Inspector controls do not fetch');
  assert.deepEqual(requests.map(r => r.status), [401, 200, 200]);
  get('data-source').value = 'hub';
  await get('data-source').listeners.change(); // Fixture overview only; no configured hub is contacted.
  await flush();
  get('trace-game').value = 'ffxi';
  get('correlation').value = 'fixture:correlation';
  const submit = async () => { get('trace-search').listeners.submit({preventDefault() {}}); await flush(); };
  await submit();
  assert.equal(requests.at(-1).status, 200);
  assert.equal(requests.at(-1).traceCalls, 1);
  assert.match(get('hub-trace').textContent, /Disposition: pending.*queued_for_native_delivery.*Final: false/);
  assert.match(get('hub-trace').textContent, /Fetched: fixture-trace-fetch/);
  scenario = 'trace-empty';
  await submit();
  assert.match(get('hub-trace').textContent, /No matching trace records/);
  assert.match(get('hub-trace').textContent, /does not prove an action did or did not occur/);
  assert.doesNotMatch(get('hub-trace').textContent, /queued_for_native_delivery/);
  for (const [failure, expectedStatus, calls] of [['trace-malformed', 502, 1], ['trace-unavailable', 503, 1], ['trace-unconfigured', 503, 0]]) {
    scenario = failure;
    await submit();
    assert.equal(requests.at(-1).status, expectedStatus);
    assert.equal(requests.at(-1).traceCalls, calls);
    assert.match(get('hub-trace').textContent, /Hub trace unavailable; no delivery or outcome can be inferred/);
    assert.doesNotMatch(get('hub-trace').textContent, /fixture-trace-fetch|queued_for_native_delivery|OMIT_/);
  }
  scenario = 'trace-pending';
  vm.runInNewContext("token = 'synthetic-expired-token'", context);
  await submit();
  assert.equal(requests.at(-1).status, 401);
  assert.equal(requests.at(-1).traceCalls, 0);
  assert.match(get('hub-trace').textContent, /Hub trace unavailable/);
  vm.runInNewContext("token = 'fixture-token'", context);
  const beforeInvalid = requests.length;
  get('correlation').value = 'invalid/correlation';
  await submit();
  assert.equal(requests.length, beforeInvalid);
  assert.match(get('hub-trace').textContent, /Enter a correlation ID/);
  scenario = 'trace-pending'; get('correlation').value = 'fixture:recovery';
  await submit();
  assert.match(get('hub-trace').textContent, /Final: false/);
  get('trace-clear').listeners.click();
  assert.equal(get('hub-trace').children.length, 0);
  console.log('Browser-free integration passed: inspector login/fixtures/controls and trace pending, empty, 502/503 failures, local validation, recovery and clear. No listener or DOM library.');
})().catch(error => { console.error(error); process.exitCode = 1; });
