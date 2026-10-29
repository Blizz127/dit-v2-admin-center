// Actual app and shipped template IDs, synthetic responses, no browser or listener.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const template = JSON.parse(execFileSync('python3', ['tests/inspector_runtime_fixture.py', '--template'], {encoding: 'utf8', timeout: 5000}));
const fixture = JSON.parse(execFileSync('python3', ['-c', 'import json; from tools.build_inspector_playtest import snapshot; print(json.dumps(snapshot()))'], {encoding: 'utf8', timeout: 5000}));
fixture.bots = [{id: 'fixture-bot', name: 'OLD_BOT_DETAIL', game: 'FFXI', source: 'Synthetic fixture', status: 'Unknown'}];
fixture.learning[0].topic = 'OLD_LEARNING_DETAIL';
class Element {
  constructor(spec = {}) { this.children = []; this.listeners = {}; this.text = ''; this.hidden = Object.hasOwn(spec.attrs || {}, 'hidden'); this.value = spec.value || ''; }
  append(...items) { this.children.push(...items); }
  replaceChildren() { this.children = []; this.text = ''; }
  set textContent(value) { this.children = []; this.text = String(value); }
  get textContent() { return this.text + this.children.map(c => c.textContent).join(' '); }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  setAttribute() {}
  get lastElementChild() { return this.children.at(-1); }
}
const elements = new Map(Object.entries(template).map(([id, spec]) => [id, new Element(spec)]));
const get = id => { assert.ok(elements.has(id), 'Unknown template ID ' + id); return elements.get(id); };
const storage = new Map();
let outcome = 'good';
const ctx = {document: {querySelector: s => get(s.slice(1)), getElementById: get, createElement: () => new Element()},
  sessionStorage: {getItem: k => storage.get(k), setItem: (k, v) => storage.set(k, v), removeItem: k => storage.delete(k)},
  fetch: async path => {
    if (path === '/api/bridge-status') return {ok: true, json: async () => ({unit: 'unknown', source: 'Synthetic'})};
    assert.equal(path, '/api/overview?source=mock');
    if (outcome === 'transport') throw new Error('OMIT_PRIVATE_TRANSPORT');
    if (outcome === '401' || outcome === '503') return {ok: false, status: Number(outcome)};
    return {ok: true, json: async () => {
      if (outcome === 'json') throw new Error('OMIT_PRIVATE_JSON');
      if (outcome === 'malformed') return {ownerAttention: {coverage: 'Partial', items: []}};
      const data = JSON.parse(JSON.stringify(fixture));
      if (outcome === 'empty') { data.bots = []; data.learning = []; }
      if (outcome === 'changed') {
        data.bots[0].name = 'NEW_BOT_DETAIL';
        data.learning[0].topic = 'NEW_LEARNING_DETAIL';
        data.learning[0].status = 'failed';
      }
      return data;
    }};
  }};
vm.runInNewContext(fs.readFileSync('static/app.js', 'utf8'), ctx);
const settle = () => new Promise(resolve => setImmediate(resolve));
async function login(mode = 'good') {
  outcome = mode; get('token').value = 'synthetic-token';
  get('login').listeners.submit({preventDefault() {}}); await settle();
}
function select() {
  ctx.inspectBot('fixture-bot'); ctx.inspectLearning(fixture.learning[0].id);
  assert.match(get('bot-inspector').textContent, /OLD_BOT_DETAIL/);
  assert.match(get('learning-inspector').textContent, /OLD_LEARNING_DETAIL/);
}
(async () => {
  await login(); select();
  for (const failure of ['503', 'transport', 'json']) {
    outcome = failure; await get('refresh').listeners.click();
    assert.equal(get('workspace').hidden, false);
    assert.match(get('hub-banner').textContent, /Refresh failed.*previous mock request snapshot/);
    assert.match(get('bot-inspector').textContent, /OLD_BOT_DETAIL/);
    assert.match(get('learning-inspector').textContent, /OLD_LEARNING_DETAIL/);
    assert.doesNotMatch(get('hub-banner').textContent, /OMIT_PRIVATE/);
  }
  for (const failure of ['401', 'malformed']) {
    await login(); select();
    outcome = failure; await get('refresh').listeners.click();
    assert.equal(get('workspace').hidden, true);
    assert.equal(get('login').hidden, false);
    assert.equal(storage.size, 0);
    assert.doesNotMatch(get('bot-inspector').textContent, /OLD_BOT_DETAIL/);
    assert.doesNotMatch(get('learning-inspector').textContent, /OLD_LEARNING_DETAIL/);
    assert.equal(vm.runInNewContext('selectedBotId === null && selectedLearningId === null && currentSnapshot === null', ctx), true);
    assert.equal(get('error').textContent, failure === '401' ? 'Token was not accepted.' : 'Could not load the workspace.');
    await login('empty');
    assert.equal(get('workspace').hidden, false);
    assert.doesNotMatch(get('bot-inspector').textContent, /OLD_BOT_DETAIL/);
    assert.doesNotMatch(get('learning-inspector').textContent, /OLD_LEARNING_DETAIL/);
  }
  await login(); select();
  const filters = {'bot-game': 'FFXI', 'bot-search': 'OLD', 'learning-game': 'FFXI',
    'learning-search': 'OLD', 'learning-status': 'verified'};
  for (const [id, value] of Object.entries(filters)) get(id).value = value;
  get('bot-search').listeners.input(); get('learning-search').listeners.input();
  assert.match(get('bot-count').textContent, /Showing 1 of 1/);
  assert.match(get('learning-count').textContent, /Showing 1 of 4/);
  outcome = 'changed'; await get('refresh').listeners.click();
  for (const [id, value] of Object.entries(filters)) assert.equal(get(id).value, value, 'Preserve filter ' + id);
  assert.match(get('bot-count').textContent, /Showing 0 of 1.*Selected bot is outside this filtered roster/);
  assert.match(get('learning-count').textContent, /Showing 0 of 4.*Selected need is outside this filtered list/);
  assert.match(get('bot-inspector').textContent, /NEW_BOT_DETAIL/);
  assert.doesNotMatch(get('bot-inspector').textContent, /OLD_BOT_DETAIL/);
  assert.match(get('learning-inspector').textContent, /NEW_LEARNING_DETAIL.*Status: failed/);
  assert.doesNotMatch(get('learning-inspector').textContent, /OLD_LEARNING_DETAIL/);
  outcome = 'empty'; await get('refresh').listeners.click();
  assert.match(get('bot-count').textContent, /Selected bot is no longer in the loaded data/);
  assert.match(get('learning-count').textContent, /Selected need is no longer in the loaded data/);
  assert.equal(get('bot-inspector').textContent, 'Selected bot is no longer in this snapshot.');
  assert.equal(get('learning-inspector').textContent, 'Selected learning need is no longer in this snapshot.');
  assert.match(get('learning-evidence').textContent, /No learning record selected/);
  for (const [id, value] of Object.entries(filters)) assert.equal(get(id).value, value);
  get('clear-bot').listeners.click(); get('clear-learning').listeners.click();
  assert.doesNotMatch(get('bot-count').textContent, /Selected bot/);
  assert.doesNotMatch(get('learning-count').textContent, /Selected need/);
  console.log('Overview state checks passed: failure/session recovery plus filter persistence, updated selected records, missing selections and explicit clear. Simulated DOM only.');
})().catch(error => { console.error(error); process.exitCode = 1; });
