// Browser-free integration: candidate fixture -> Python projection -> real HTTP
// handler bytes -> actual app.js -> strict, template-backed simulated DOM.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const python = (...args) => execFileSync('python3', ['tests/inspector_runtime_fixture.py', ...args], {encoding: 'utf8', timeout: 5000});
const application = fs.readFileSync('static/app.js', 'utf8');
const artifactPath = process.env.DIT_TEST_ARTIFACT;
if (artifactPath) assert.ok(fs.readFileSync(artifactPath, 'utf8').includes(application),
  'Artifact does not embed the current application source');
const template = JSON.parse(python('--template', ...(artifactPath ? [artifactPath] : [])));
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
    requests.push({path, status: result.status, traceCalls: result.traceCalls, interactionCalls: result.interactionCalls, healthCalls: result.healthCalls, bridgeRunnerCalls: result.bridgeRunnerCalls});
    assert.equal(result.headers['Cache-Control'], 'no-store');
    assert.equal(Number(result.headers['Content-Length']), Buffer.byteLength(result.body));
    assert.ok(!result.body.includes('OMIT_RAW_ANSWER_AND_PLAYER_DATA'));
    assert.ok(!result.body.includes('OMIT_RAW_TRACE_BODY'));
    assert.ok(!result.body.includes('OMIT_PRIVATE_READ_FAILURE'));
    assert.ok(!result.body.includes('OMIT_PRIVATE_INTERACTION_FAILURE'));
    assert.ok(!result.body.includes('OMIT_PRIVATE_INVALID'));
    assert.ok(!result.body.includes('OMIT_PRIVATE_HEALTH_'));
    assert.ok(!result.body.includes('OMIT_PRIVATE_OTHER_SERVICE'));
    assert.ok(!result.body.includes('OMIT_PRIVATE_BRIDGE_'));
    assert.ok(!result.body.includes('FixtureRequester'));
    return {ok: result.status === 200, status: result.status, json: async () => JSON.parse(result.body)};
  },
};
vm.runInNewContext(application, context);
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
  const interaction = get('interaction-status');
  const refreshInteraction = () => get('interaction-refresh').listeners.click();
  const cases = [
    ['contract-off-empty', 0], ['contract-off-retained', 0], ['contract-on-empty', 0],
    ['fresh-snapshot', 1], ['fresh-snapshot-superseded-view', 1], ['fresh-mode-stale-snapshot', 1],
    ['stale-mode-and-snapshot', 1], ['same-actor-distinct-scopes', 3], ['limit-50-truncated', 50],
  ];
  for (const [name, count] of cases) {
    scenario = 'interaction:' + name;
    await refreshInteraction();
    assert.equal(requests.at(-1).status, 200, name);
    assert.equal(requests.at(-1).interactionCalls, 1, name);
    assert.ok(interaction.textContent.includes(`${count} returned FFXI actors`), name);
    assert.match(interaction.textContent, /deployed revision unverified/);
    if (name.startsWith('contract-off')) {
      assert.match(interaction.textContent, /contract is reported off; no current bot inventory/);
      assert.doesNotMatch(interaction.textContent, /fixture-bot/);
    }
    if (name === 'contract-on-empty') assert.match(interaction.textContent, /No FFXI actor records returned/);
    if (name === 'fresh-mode-stale-snapshot') assert.match(interaction.textContent, /Reconciled view: Reported fresh.*Activity: following.*Raw snapshot: Reported stale/);
    if (name === 'fresh-snapshot-superseded-view') assert.match(interaction.textContent, /Reconciled view: Reported stale.*Activity: Unknown.*Raw snapshot: Reported fresh/);
    if (name === 'stale-mode-and-snapshot') assert.match(interaction.textContent, /Activity: Unknown.*Raw snapshot: Reported stale/);
    if (name === 'same-actor-distinct-scopes') {
      const rows = interaction.children.slice(3);
      assert.equal(rows.length, 3);
      assert.equal(new Set(rows.map(row => row.children[0].textContent)).size, 1);
      const scopeLabels = rows.map(row => row.children[2].textContent);
      scopeLabels.forEach(label => assert.match(label,
        /^Scope: .* · Supplied actor scope only; native identity remains unverified · Raw/));
      assert.deepEqual(scopeLabels.map(label => label.match(/^Scope: (.*?) · Supplied actor scope only;/)[1]).sort(),
        ['fixture-adapter / fixture-other-server', 'fixture-adapter / fixture-server', 'fixture-other-caller / fixture-server']);
    }
    if (name === 'limit-50-truncated') assert.match(interaction.textContent, /Truncated: Yes/);
  }
  for (const [failure, status, calls] of [['interaction-malformed', 502, 1], ['interaction-unavailable', 503, 1], ['interaction-unconfigured', 503, 0]]) {
    scenario = failure;
    await refreshInteraction();
    assert.equal(requests.at(-1).status, status);
    assert.equal(requests.at(-1).interactionCalls, calls);
    assert.match(interaction.textContent, /Interaction view unavailable/);
    assert.doesNotMatch(interaction.textContent, /fixture-bot|fixture-interaction-fetch|OMIT_/);
  }
  scenario = 'interaction:fresh-snapshot';
  vm.runInNewContext("token = 'synthetic-expired-token'", context);
  await refreshInteraction();
  assert.equal(requests.at(-1).status, 401);
  assert.equal(requests.at(-1).interactionCalls, 0);
  vm.runInNewContext("token = 'fixture-token'", context);
  await refreshInteraction();
  assert.match(interaction.textContent, /Activity: idle/);
  const beforePreview = requests.length;
  get('interaction-preview').listeners.click();
  assert.match(interaction.textContent, /Synthetic interaction preview/);
  assert.equal(requests.length, beforePreview);
  const health = get('hub-health');
  const refreshHealth = () => get('hub-health-refresh').listeners.click();
  scenario = 'health-services';
  await refreshHealth();
  assert.equal(requests.at(-1).status, 200);
  assert.equal(requests.at(-1).healthCalls, 1);
  assert.equal(health.children.length, 3, 'Only the two supported game services plus heading');
  assert.match(health.textContent, /FFXI · Fixture FFXI bridge running/);
  assert.match(health.textContent, /SWTOR · Fixture SWTOR adapter Unknown/);
  assert.match(health.textContent, /Observed: 2026-01-01T12:00:00Z/);
  assert.match(health.textContent, /Fetched: fixture-health-fetch/);
  assert.match(health.textContent, /revision unverified/);
  assert.match(health.textContent, /Service state is not bot presence/);
  scenario = 'health-empty';
  await refreshHealth();
  assert.equal(requests.at(-1).status, 200);
  assert.match(health.textContent, /No matching service records.*Coverage is unknown/);
  assert.match(health.textContent, /Empty data does not establish healthy services/);
  assert.doesNotMatch(health.textContent, /Fixture FFXI bridge/);
  for (const [failure, status, calls] of [['health-malformed', 502, 1], ['health-unavailable', 503, 1], ['health-unconfigured', 503, 0]]) {
    // Seed prior service data before each failure to prove it is discarded.
    scenario = 'health-services';
    await refreshHealth();
    scenario = failure;
    await refreshHealth();
    assert.equal(requests.at(-1).status, status);
    assert.equal(requests.at(-1).healthCalls, calls);
    assert.equal(health.textContent, 'Hub service health unavailable; current state is unknown.');
  }
  scenario = 'health-services';
  await refreshHealth();
  vm.runInNewContext("token = 'synthetic-expired-token'", context);
  await refreshHealth();
  assert.equal(requests.at(-1).status, 401);
  assert.equal(requests.at(-1).healthCalls, 0);
  assert.equal(health.textContent, 'Hub service health unavailable; current state is unknown.');
  vm.runInNewContext("token = 'fixture-token'", context);
  await refreshHealth();
  assert.equal(requests.at(-1).status, 200);
  assert.match(health.textContent, /Fixture FFXI bridge running/);
  get('data-source').value = 'mock';
  await get('data-source').listeners.change();
  await flush(); // Overview starts its own bridge refresh; let that request settle.
  assert.equal(interaction.textContent, 'Not requested.');
  assert.equal(health.textContent, 'Not requested.');
  const beforeHealthGuard = requests.length;
  await refreshHealth();
  assert.equal(requests.length, beforeHealthGuard);
  assert.match(health.textContent, /Select configured hub data/);
  const bridgePanels = [get('bridge-status'), get('ffxi-focus-bridge')];
  const refreshBridge = () => get('bridge-refresh').listeners.click();
  for (const state of ['bridge-active', 'bridge-fault']) {
    scenario = state;
    await refreshBridge();
    assert.equal(requests.at(-1).status, 200);
    assert.equal(requests.at(-1).bridgeRunnerCalls, 1);
    for (const panel of bridgePanels) {
      assert.match(panel.textContent, state === 'bridge-active' ? /active · running/ : /failed · failed/);
      assert.match(panel.textContent, state === 'bridge-active' ? /Fault marker: absent/ : /Fault marker: present · Classification: delayed_delivery_failed/);
      assert.match(panel.textContent, /Observed: 2026-01-01T12:00:00Z/);
    }
  }
  for (const failure of ['bridge-empty', 'bridge-malformed', 'bridge-denied', 'bridge-timeout']) {
    scenario = 'bridge-active';
    await refreshBridge();
    scenario = failure;
    await refreshBridge();
    assert.equal(requests.at(-1).status, 200, 'Observer failures return Unknown, not an invented HTTP error');
    assert.equal(requests.at(-1).bridgeRunnerCalls, 1);
    for (const panel of bridgePanels) {
      assert.match(panel.textContent, /unknown · unknown/);
      assert.match(panel.textContent, /Fault marker: unknown/);
      assert.match(panel.textContent, /Observed: unknown/);
      assert.doesNotMatch(panel.textContent, /active|running|2026-01-01|OMIT_/);
    }
  }
  scenario = 'bridge-active';
  await refreshBridge();
  vm.runInNewContext("token = 'synthetic-expired-token'", context);
  await refreshBridge();
  assert.equal(requests.at(-1).status, 401);
  assert.equal(requests.at(-1).bridgeRunnerCalls, 0);
  bridgePanels.forEach(panel => assert.doesNotMatch(panel.textContent, /active|running|2026-01-01/));
  assert.match(bridgePanels[0].textContent, /Bridge status unknown/);
  assert.match(bridgePanels[1].textContent, /delivery remains unverified/);
  vm.runInNewContext("token = 'fixture-token'", context);
  await refreshBridge();
  bridgePanels.forEach(panel => assert.match(panel.textContent, /active · running/));
  assert.match(bridgePanels[0].textContent, /Marker absence does not prove delivery/);
  assert.match(bridgePanels[1].textContent, /Not proof of delivery/);
  console.log('Browser-free integration passed: inspector, trace, interaction, service health and bridge; empty/error/denial/recovery states through real handlers. No listener or DOM library.');
})().catch(error => { console.error(error); process.exitCode = 1; });
