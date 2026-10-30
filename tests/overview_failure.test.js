// Actual app and shipped template IDs, synthetic responses, no browser or listener.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const assignmentFixtures = require('./fixtures/assignment-pages.json');
const {execFileSync} = require('node:child_process');
const template = JSON.parse(execFileSync('python3', ['tests/inspector_runtime_fixture.py', '--template'], {encoding: 'utf8', timeout: 5000}));
const fixture = JSON.parse(execFileSync('python3', ['-c', 'import json; from tools.build_inspector_playtest import snapshot; print(json.dumps(snapshot()))'], {encoding: 'utf8', timeout: 5000}));
fixture.bots = [{id: 'fixture-bot', name: 'OLD_BOT_DETAIL', game: 'FFXI', source: 'Synthetic fixture', status: 'Unknown'}];
fixture.learning[0].topic = 'OLD_LEARNING_DETAIL';
class Element {
  constructor(spec = {}) { this.attributes = {...spec.attrs}; this.children = []; this.listeners = {}; this.text = ''; this.hidden = Object.hasOwn(spec.attrs || {}, 'hidden'); this.value = spec.value || ''; }
  append(...items) { this.children.push(...items); }
  replaceChildren() { this.children = []; this.text = ''; }
  set textContent(value) { this.children = []; this.text = String(value); }
  get textContent() { return this.text + this.children.map(c => c.textContent).join(' '); }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  focus() { ctx.document.activeElement = this; }
  get lastElementChild() { return this.children.at(-1); }
}
const elements = new Map(Object.entries(template).map(([id, spec]) => [id, new Element(spec)]));
const get = id => { assert.ok(elements.has(id), 'Unknown template ID ' + id); return elements.get(id); };
const storage = new Map();
let outcome = 'good';
let fetchCount = 0;
const ctx = {document: {querySelector: s => get(s.slice(1)), getElementById: get, createElement: () => new Element()},
  sessionStorage: {getItem: k => storage.get(k), setItem: (k, v) => storage.set(k, v), removeItem: k => storage.delete(k)},
  fetch: async path => {
    fetchCount++;
    if (path === '/api/bridge-status') return {ok: true, json: async () => ({unit: 'unknown', source: 'Synthetic'})};
    assert.ok(['/api/overview?source=mock', '/api/overview?source=hub'].includes(path));
    if (outcome === 'transport') throw new Error('OMIT_PRIVATE_TRANSPORT');
    if (outcome === '401' || outcome === '503') return {ok: false, status: Number(outcome)};
    return {ok: true, json: async () => {
      if (outcome === 'json') throw new Error('OMIT_PRIVATE_JSON');
      // Partial object snapshots now stay usable; null cannot supply a snapshot.
      if (outcome === 'malformed') return null;
      const data = JSON.parse(JSON.stringify(fixture));
      if (outcome === 'empty') { data.bots = []; data.learning = []; }
      if (outcome === 'changed') {
        data.bots[0].name = 'NEW_BOT_DETAIL';
        data.learning[0].topic = 'NEW_LEARNING_DETAIL';
        data.learning[0].status = 'failed';
      }
      if (outcome === 'ordered' || outcome === 'reordered') {
        const names = outcome === 'ordered' ? ['Zulu', 'Alpha', 'Mike'] : ['Mike', 'Zulu', 'Alpha'];
        data.bots = names.map(name => ({...fixture.bots[0], id: name, name, game: name === 'Alpha' ? 'SWTOR' : 'FFXI'}));
        data.learning = names.map(name => ({...fixture.learning[0], id: name, topic: name, game: name === 'Alpha' ? 'SWTOR' : 'FFXI'}));
      }
      if (outcome.startsWith('unavailable')) {
        data.hubFeeds = [{game: 'All', view: 'hub', status: 'Unavailable', at: null, note: 'Synthetic fallback; no current hub data'}];
        if (outcome === 'unavailable-empty') { data.bots = []; data.learning = []; }
      }
      if (outcome.startsWith('twins')) {
        data.bots = ['LEFT', 'RIGHT'].map(id => ({id, name: 'Same display name', game: 'FFXI', source: 'Synthetic', status: 'Unknown'}));
        data.botDetails = data.bots.map(b => ({botId: b.id, source: 'Synthetic', goals: [{text: b.id + '_GOAL'}], memories: [{text: b.id + '_MEMORY', grounding: 'Not verified'}]}));
        data.ledger = data.bots.map(b => ({botId: b.id, request: b.id + '_ACTION', result: 'Accepted', verification: 'Pending'}));
        data.issues = data.bots.map(b => ({botId: b.id, title: b.id + '_ISSUE', detail: 'Fixture', status: 'Open', scope: 'Bots', source: 'Synthetic'}));
        data.assignmentHistory = data.bots.map(b => ({botId: b.id, requested: b.id + '_MODEL', effective: null, source: 'Synthetic'}));
        data.replyEvents = data.bots.map(b => ({botId: b.id, fallbackReason: b.id + '_FALLBACK', source: 'Synthetic'}));
        data.safetyRecords = [{botId: null, scope: 'NETWORK_EXAMPLE', source: 'Synthetic'},
          ...data.bots.map(b => ({botId: b.id, scope: b.id + '_SAFETY', source: 'Synthetic'}))];
        if (outcome === 'twins-orphan') data.bots = data.bots.filter(b => b.id !== 'LEFT');
      }
      if (outcome === 'audit') data.audit = [
        {actor: 'Synthetic operator', action: 'AUDIT_EXAMPLE_A', scope: 'Fixture bot', result: 'Example only; no change applied', at: null, source: 'Synthetic audit fixture'},
        {actor: 'Synthetic operator', action: 'AUDIT_EXAMPLE_B', scope: 'Fixture network', result: 'Example rejected', at: 'fixture-time', source: 'Synthetic audit fixture'},
      ];
      if (outcome === 'ffxi-summary') {
        data.ffxiFocus = {closest: 'Synthetic FFXI candidate', whatToLookFor: 'Fixture speech observation',
          toggle: 'No connected toggle', unverified: 'Delivery unknown', source: 'Synthetic dated project note'};
        data.hubFeeds = [{game: 'FFXI', view: 'bots', status: 'Live response', at: 'fixture-time', note: 'Synthetic response fixture'}];
      }
      if (outcome === 'ffxi-partial') data.ffxiFocus = {closest: 'Synthetic partial note', toggle: false, source: '   '};
      if (outcome === 'ffxi-missing') data.hubFeeds = [{game: 'SWTOR', view: 'bots', status: 'Live response', at: 'fixture-time', note: 'OTHER_GAME_FEED'}];
      if (outcome === 'decisions-valid') data.ownerAttention = {coverage: 'Synthetic decision scope', items: [{title: 'DECISION_FIXTURE', project: 'Synthetic project'}]};
      if (outcome === 'decisions-missing') delete data.ownerAttention;
      if (outcome === 'decisions-null') data.ownerAttention = null;
      if (outcome === 'decisions-malformed') data.ownerAttention = {items: 'OMIT_PRIVATE_BAD_SHAPE'};
      if (outcome === 'decisions-invalid-row') data.ownerAttention = {items: [null]};
      if (outcome === 'audit-missing') delete data.audit;
      if (outcome === 'audit-null') data.audit = null;
      if (outcome === 'audit-malformed') data.audit = 'OMIT_PRIVATE_BAD_AUDIT';
      if (outcome === 'audit-invalid-row') data.audit = [{action: 'OMIT_PARTIAL_PREFIX'}, null];
      if (outcome === 'audit-partial') data.audit = [{action: 'Partial example', result: false, actor: null, at: {}, source: ' '}];
      if (outcome.startsWith('details-')) {
        data.botDetails = [{botId: 'fixture-bot', source: 'Synthetic detail fixture',
          goals: [{text: 'CURRENT_GOAL', status: 'Pending', evidence: 'Not verified'}],
          memories: [{text: 'CURRENT_MEMORY', grounding: 'Synthetic only'}]}];
        if (outcome === 'details-missing') delete data.botDetails;
        if (outcome === 'details-null') data.botDetails = null;
        if (outcome === 'details-malformed') data.botDetails = 'OMIT_BAD_DETAILS';
        if (outcome === 'details-duplicate') data.botDetails.push({...data.botDetails[0]});
        if (outcome === 'details-invalid-row') data.botDetails = [null, [], 'OMIT_BAD_ROW'];
        if (outcome === 'details-partial') data.botDetails = [{botId: 'fixture-bot', goals: null,
          memories: [null, {text: 'PARTIAL_MEMORY', grounding: false}], observedAt: {}, source: ' '}];
        if (outcome === 'details-empty') data.botDetails = [{botId: 'fixture-bot', goals: [], memories: []}];
        if (outcome === 'details-fields') data.botDetails = [{botId: 'fixture-bot', goals: [{}], memories: [{}]}];
      }
      if (outcome.startsWith('history-')) {
        data.replyEvents = [{botId: 'fixture-bot', fallbackReason: 'CURRENT_REPLY', source: 'Synthetic'}];
        data.assignmentHistory = [{botId: 'fixture-bot', requested: 'CURRENT_ASSIGNMENT', source: 'Synthetic'}];
        for (const key of ['replyEvents', 'assignmentHistory']) {
          if (outcome === 'history-missing') delete data[key];
          if (outcome === 'history-null') data[key] = null;
          if (outcome === 'history-malformed') data[key] = 'OMIT_BAD_HISTORY';
          if (outcome === 'history-invalid-row') data[key].push(null);
          if (outcome === 'history-empty') data[key] = [];
          if (outcome === 'history-partial') data[key] = [{botId: 'fixture-bot', source: {}, observedAt: false, wordingOrigin: []}];
        }
      }
      if (outcome.startsWith('safety-')) {
        data.safetyRecords = [{botId: null, scope: 'CURRENT_NETWORK_SAFETY', source: 'Synthetic'},
          {botId: 'fixture-bot', scope: 'CURRENT_BOT_SAFETY', gate: 'Off', source: 'Synthetic'}];
        if (outcome === 'safety-missing') delete data.safetyRecords;
        if (outcome === 'safety-null') data.safetyRecords = null;
        if (outcome === 'safety-malformed') data.safetyRecords = 'OMIT_BAD_SAFETY';
        if (outcome === 'safety-invalid-row') data.safetyRecords.push(null);
        if (outcome === 'safety-empty') data.safetyRecords = [];
        if (outcome === 'safety-partial') data.safetyRecords = [{botId: 'fixture-bot', gate: false, killSwitch: {}, source: [], observedAt: true}];
        if (outcome === 'safety-unscoped') data.safetyRecords.push(...[undefined, '', false, 0, {}, []].map(botId => ({botId, scope: 'OMIT_UNSCOPED'})));
      }
      if (outcome.startsWith('pages-')) {
        const mode = outcome.slice('pages-'.length);
        data.assignmentHistory = structuredClone(assignmentFixtures[mode === 'shrink' || mode === 'orphan' ? 'populated' : mode]);
        if (mode === 'shrink') data.assignmentHistory = data.assignmentHistory.slice(0, 5);
        if (mode === 'orphan') data.bots = [];
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
  get('bot-reset').listeners.click(); get('learning-reset').listeners.click();
  await login('ordered');
  const headings = id => get(id).children.map(row => row.children[0].textContent);
  assert.deepEqual(headings('bots'), ['Zulu · FFXI', 'Alpha · SWTOR', 'Mike · FFXI']);
  assert.deepEqual(headings('learning'), ['FFXI · Zulu', 'SWTOR · Alpha', 'FFXI · Mike']);
  assert.match(get('bot-count').textContent, /Showing 3 of 3/);
  assert.match(get('learning-count').textContent, /Showing 3 of 3/);
  get('bot-game').value = 'FFXI'; get('bot-game').listeners.change();
  get('learning-game').value = 'FFXI'; get('learning-game').listeners.change();
  assert.deepEqual(headings('bots'), ['Zulu · FFXI', 'Mike · FFXI']);
  assert.deepEqual(headings('learning'), ['FFXI · Zulu', 'FFXI · Mike']);
  outcome = 'reordered'; await get('refresh').listeners.click();
  assert.deepEqual(headings('bots'), ['Mike · FFXI', 'Zulu · FFXI']);
  assert.deepEqual(headings('learning'), ['FFXI · Mike', 'FFXI · Zulu']);
  get('bot-reset').listeners.click(); get('learning-reset').listeners.click();
  assert.deepEqual(headings('bots'), ['Mike · FFXI', 'Zulu · FFXI', 'Alpha · SWTOR']);
  assert.deepEqual(headings('learning'), ['FFXI · Mike', 'FFXI · Zulu', 'SWTOR · Alpha']);
  get('data-source').value = 'hub'; outcome = 'unavailable';
  await get('data-source').listeners.change(); await settle();
  assert.equal(get('workspace').hidden, false);
  assert.match(get('hub-banner').textContent, /partially or fully unavailable.*synthetic fallback/);
  assert.match(get('hub-feeds').textContent, /Unavailable.*Synthetic fallback.*Fetched: [Uu]nknown/);
  assert.match(get('bots').textContent, /Synthetic fixture/);
  outcome = 'unavailable-empty'; await get('refresh').listeners.click();
  assert.match(get('hub-banner').textContent, /partially or fully unavailable/);
  assert.match(get('bots').textContent, /No matching roster records.*does not establish that a bot is offline/);
  assert.match(get('learning').textContent, /No matching learning entries.*Coverage is unknown/);
  assert.match(get('bot-count').textContent, /Showing 0 of 0/);
  assert.match(get('learning-count').textContent, /Showing 0 of 0/);
  await login('503');
  assert.equal(get('workspace').hidden, true);
  assert.equal(get('error').textContent, 'Could not load the workspace.');
  assert.equal(storage.size, 0);
  get('data-source').value = 'mock'; await login('twins');
  get('issue-selected-bot').checked = true;
  const beforeInspection = fetchCount;
  for (const [selected, other] of [['LEFT', 'RIGHT'], ['RIGHT', 'LEFT']]) {
    ctx.inspectBot(selected);
    const detail = get('bot-inspector').textContent;
    for (const field of ['GOAL', 'MEMORY', 'ACTION', 'ISSUE']) assert.ok(detail.includes(selected + '_' + field));
    assert.ok(!detail.includes(other + '_'));
    for (const [panel, field] of [['assignment-history', 'MODEL'], ['reply-source', 'FALLBACK'], ['safety-records', 'SAFETY'], ['issues', 'ISSUE']]) {
      assert.ok(get(panel).textContent.includes(selected + '_' + field));
      assert.ok(!get(panel).textContent.includes(other + '_'));
    }
    assert.match(get('safety-records').textContent, /NETWORK_EXAMPLE/);
  }
  assert.equal(fetchCount, beforeInspection, 'Detail selection never calls a service');
  ctx.inspectBot('LEFT'); outcome = 'twins-orphan'; await get('refresh').listeners.click();
  assert.match(get('bot-inspector').textContent, /no longer in this snapshot/);
  for (const panel of ['bot-inspector', 'assignment-history', 'reply-source', 'safety-records', 'issues']) {
    assert.doesNotMatch(get(panel).textContent, /LEFT_|RIGHT_/, 'Missing selection must not display orphan details: ' + panel);
  }
  assert.match(get('safety-records').textContent, /NETWORK_EXAMPLE/);
  await login('audit');
  assert.equal(get('audit').children.length, 2);
  assert.deepEqual(headings('audit'), ['AUDIT_EXAMPLE_A · Fixture bot', 'AUDIT_EXAMPLE_B · Fixture network']);
  assert.match(get('audit').textContent, /Example only; no change applied.*unknown time.*Synthetic audit fixture/);
  const auditBefore = get('audit').textContent, callsBefore = fetchCount;
  ctx.inspectBot('fixture-bot'); get('clear-bot').listeners.click();
  assert.equal(fetchCount, callsBefore);
  assert.equal(get('audit').textContent, auditBefore, 'Read-only selections must not invent audit actions');
  for (const [query, count] of [['  audit_example_a  ', 1], ['NETWORK', 1], ['rejected', 1], ['Synthetic operator', 2], ['no such example', 0]]) {
    get('audit-search').value = query; get('audit-search').listeners.input();
    assert.match(get('audit-count').textContent, new RegExp(`Showing ${count} of 2 loaded audit examples`));
    if (!count) {
      assert.match(get('audit').textContent, /No matching audit examples/);
      assert.match(get('audit').textContent, /does not establish whether real admin actions occurred/);
    } else assert.equal(get('audit').children.length, count);
  }
  assert.equal(fetchCount, callsBefore, 'Audit filters make no request');
  get('audit-search').value = 'network'; get('audit-search').listeners.input();
  await get('refresh').listeners.click();
  assert.equal(get('audit-search').value, 'network');
  assert.match(get('audit-count').textContent, /Showing 1 of 2/);
  get('audit-reset').listeners.click();
  assert.equal(get('audit-search').value, '');
  assert.equal(get('audit').textContent, auditBefore);
  outcome = '503'; await get('refresh').listeners.click();
  assert.equal(get('audit').textContent, auditBefore);
  assert.match(get('hub-banner').textContent, /Refresh failed.*previous mock/);
  outcome = 'empty'; await get('refresh').listeners.click();
  assert.match(get('audit').textContent, /No audit examples loaded/);
  assert.match(get('audit').textContent, /does not establish whether real admin actions occurred/);
  assert.match(get('audit').textContent, /no live audit source is connected/);
  assert.doesNotMatch(get('audit').textContent, /AUDIT_EXAMPLE/);
  await login('ffxi-summary');
  assert.match(get('ffxi-focus').textContent, /Synthetic FFXI candidate.*Synthetic dated project note/);
  assert.match(get('ffxi-focus').textContent, /Readiness must be confirmed by the owning lead/);
  assert.match(get('ffxi-focus').textContent, /No connected toggle.*Delivery unknown/);
  assert.match(get('ffxi-feeds').textContent, /FFXI · bots.*Not proof of game presence or delivery/);
  outcome = 'ffxi-partial'; await get('refresh').listeners.click();
  assert.match(get('ffxi-focus').textContent, /Source unknown/);
  assert.equal(get('ffxi-focus').children[1].children[1].textContent, 'Unknown');
  assert.equal(get('ffxi-focus').children[2].children[1].textContent, 'Unknown');
  assert.equal(get('ffxi-focus').children[3].children[1].textContent, 'Unknown');
  assert.doesNotMatch(get('ffxi-focus').textContent, /undefined|null|Synthetic FFXI candidate/);
  outcome = 'ffxi-missing'; await get('refresh').listeners.click();
  assert.match(get('ffxi-focus').textContent, /FFXI readiness unknown.*No readiness summary/);
  assert.doesNotMatch(get('ffxi-focus').textContent, /Synthetic partial note/);
  assert.match(get('ffxi-feeds').textContent, /FFXI feed coverage.*Unknown.*Missing or incomplete feed metadata/);
  assert.doesNotMatch(get('ffxi-feeds').textContent, /OTHER_GAME_FEED|Live response/);
  await login('decisions-valid');
  assert.match(get('owner-attention').textContent, /Synthetic decision scope.*DECISION_FIXTURE.*Synthetic project/);
  assert.match(get('owner-attention').textContent, /Created: unknown · Expires: unknown/);
  assert.doesNotMatch(get('owner-attention').textContent, /undefined/);
  for (const failure of ['decisions-missing', 'decisions-null', 'decisions-malformed', 'decisions-invalid-row']) {
    outcome = failure; await get('refresh').listeners.click();
    assert.equal(get('workspace').hidden, false);
    assert.match(get('owner-attention').textContent, /Owner-decision coverage unknown.*No usable decision list/);
    assert.match(get('owner-attention').textContent, /does not establish that no decisions are pending/);
    assert.doesNotMatch(get('owner-attention').textContent, /DECISION_FIXTURE|OMIT_PRIVATE|No records listed/);
    assert.match(get('bots').textContent, /OLD_BOT_DETAIL/);
  }
  outcome = 'good'; await get('refresh').listeners.click();
  assert.match(get('owner-attention').textContent, /No records listed.*Not a complete decision inventory/);
  assert.doesNotMatch(get('owner-attention').textContent, /No usable decision list/);
  await login('audit');
  for (const failure of ['audit-missing', 'audit-null', 'audit-malformed']) {
    outcome = failure; await get('refresh').listeners.click();
    assert.equal(get('workspace').hidden, false);
    assert.match(get('audit-count').textContent, /count unknown/);
    assert.match(get('audit').textContent, /Audit example coverage unknown.*No usable audit example list/);
    assert.doesNotMatch(get('audit').textContent, /AUDIT_EXAMPLE|OMIT_|No audit examples loaded/);
    assert.match(get('bots').textContent, /OLD_BOT_DETAIL/);
    const beforeFilter = fetchCount;
    get('audit-search').value = 'anything'; get('audit-search').listeners.input();
    get('audit-reset').listeners.click();
    assert.equal(fetchCount, beforeFilter);
    assert.match(get('audit-count').textContent, /count unknown/);
  }
  outcome = 'audit-invalid-row'; await get('refresh').listeners.click();
  assert.match(get('audit-count').textContent, /Showing 1 of Unknown total/);
  assert.match(get('audit').textContent, /Audit example coverage unknown.*Malformed rows were omitted.*OMIT_PARTIAL_PREFIX/);
  assert.doesNotMatch(get('audit').textContent, /AUDIT_EXAMPLE|No audit examples loaded/);
  outcome = 'audit-partial'; await get('refresh').listeners.click();
  assert.match(get('audit').textContent, /Partial example · Scope unknown.*Unknown.*Actor unknown.*unknown time.*Source unknown/);
  assert.doesNotMatch(get('audit').textContent, /undefined|null|\[object Object\]/);
  assert.match(get('audit-count').textContent, /Showing 1 of 1/);
  outcome = 'empty'; await get('refresh').listeners.click();
  assert.match(get('audit-count').textContent, /Showing 0 of 0/);
  assert.match(get('audit').textContent, /No audit examples loaded/);
  await login('details-good'); ctx.inspectBot('fixture-bot');
  assert.match(get('bot-inspector').textContent, /CURRENT_GOAL.*CURRENT_MEMORY/);
  for (const mode of ['missing', 'null', 'malformed', 'duplicate', 'invalid-row']) {
    outcome = 'details-' + mode; await get('refresh').listeners.click();
    assert.equal(get('workspace').hidden, false);
    assert.match(get('bot-inspector').textContent, /Goals and memory.*Unknown/);
    assert.doesNotMatch(get('bot-inspector').textContent, /CURRENT_GOAL|CURRENT_MEMORY|OMIT_BAD/);
    if (mode === 'duplicate') assert.match(get('bot-inspector').textContent, /Multiple detail records/);
    const before = fetchCount; ctx.inspectBot('fixture-bot'); assert.equal(fetchCount, before);
  }
  outcome = 'details-partial'; await get('refresh').listeners.click();
  assert.equal(get('workspace').hidden, false);
  assert.match(get('bot-inspector').textContent, /Goals.*Unknown.*Memory.*Unknown.*PARTIAL_MEMORY.*Grounding: Unknown/);
  assert.match(get('bot-inspector').textContent, /Source unknown · Observed: unknown/);
  assert.doesNotMatch(get('bot-inspector').textContent, /undefined|null|\[object Object\]/);
  outcome = 'details-empty'; await get('refresh').listeners.click();
  assert.match(get('bot-inspector').textContent, /Goals.*Unknown.*Memory.*Unknown/);
  assert.doesNotMatch(get('bot-inspector').textContent, /PARTIAL_MEMORY/);
  outcome = 'details-fields'; await get('refresh').listeners.click();
  assert.match(get('bot-inspector').textContent, /Goal · Unknown.*Status: Unknown · Evidence: Unknown.*Memory · Unknown.*Grounding: Unknown/);
  outcome = 'details-good'; await get('refresh').listeners.click();
  assert.match(get('bot-inspector').textContent, /CURRENT_GOAL.*CURRENT_MEMORY/);
  assert.doesNotMatch(get('bot-inspector').textContent, /Multiple detail records|Missing or incomplete list/);
  await login('history-good'); ctx.inspectBot('fixture-bot');
  assert.match(get('reply-source').textContent, /CURRENT_REPLY/);
  assert.match(get('assignment-history').textContent, /CURRENT_ASSIGNMENT/);
  for (const mode of ['missing', 'null', 'malformed', 'invalid-row']) {
    outcome = 'history-' + mode; await get('refresh').listeners.click();
    assert.equal(get('workspace').hidden, false);
    assert.match(get('reply-source').textContent, /Reply evidence coverage unknown/);
    assert.match(get('assignment-history').textContent, /Assignment example coverage unknown/);
    for (const [panel, retained] of [['reply-source', /CURRENT_REPLY/], ['assignment-history', /CURRENT_ASSIGNMENT/]]) {
      if (mode === 'invalid-row') assert.match(get(panel).textContent, retained);
      else assert.doesNotMatch(get(panel).textContent, /CURRENT_REPLY|CURRENT_ASSIGNMENT/);
      assert.doesNotMatch(get(panel).textContent, /OMIT_BAD/);
    }
    const before = fetchCount; ctx.inspectBot('fixture-bot'); assert.equal(fetchCount, before);
  }
  outcome = 'history-partial'; await get('refresh').listeners.click();
  assert.match(get('reply-source').textContent, /Unknown source.*Generation: Unknown.*Delivery: Unknown.*Source unknown.*Observed: unknown/);
  assert.match(get('assignment-history').textContent, /Requested: Unknown · Effective: Unknown/);
  for (const panel of ['reply-source', 'assignment-history']) assert.doesNotMatch(get(panel).textContent, /undefined|null|\[object Object\]/);
  outcome = 'history-empty'; await get('refresh').listeners.click();
  assert.match(get('reply-source').textContent, /No matching reply evidence/);
  assert.match(get('assignment-history').textContent, /No matching examples/);
  outcome = 'history-good'; await get('refresh').listeners.click();
  assert.match(get('reply-source').textContent, /CURRENT_REPLY/);
  assert.match(get('assignment-history').textContent, /CURRENT_ASSIGNMENT/);
  await login('safety-good'); ctx.inspectBot('fixture-bot');
  assert.match(get('safety-records').textContent, /CURRENT_NETWORK_SAFETY.*CURRENT_BOT_SAFETY/);
  for (const mode of ['missing', 'null', 'malformed', 'invalid-row']) {
    outcome = 'safety-' + mode; await get('refresh').listeners.click();
    assert.equal(get('workspace').hidden, false);
    assert.match(get('safety-records').textContent, /Safety example coverage unknown.*Actual gate and kill-switch states remain unknown/);
    assert.doesNotMatch(get('safety-records').textContent, /CURRENT_|OMIT_BAD|No safety examples/);
    const before = fetchCount; ctx.inspectBot('fixture-bot'); assert.equal(fetchCount, before);
  }
  outcome = 'safety-partial'; await get('refresh').listeners.click();
  assert.match(get('safety-records').textContent, /Scope label unknown.*Example gate: Unknown · Example kill switch: Unknown.*Source unknown · Observed: unknown/);
  assert.doesNotMatch(get('safety-records').textContent, /undefined|null|\[object Object\]/);
  outcome = 'safety-unscoped'; await get('refresh').listeners.click();
  assert.match(get('safety-records').textContent, /Safety example scope unknown.*CURRENT_NETWORK_SAFETY.*CURRENT_BOT_SAFETY/);
  assert.doesNotMatch(get('safety-records').textContent, /OMIT_UNSCOPED/);
  get('clear-bot').listeners.click();
  assert.match(get('safety-records').textContent, /CURRENT_NETWORK_SAFETY/);
  assert.doesNotMatch(get('safety-records').textContent, /CURRENT_BOT_SAFETY|OMIT_UNSCOPED/);
  outcome = 'safety-empty'; await get('refresh').listeners.click();
  assert.match(get('safety-records').textContent, /No safety examples.*Actual gate and kill-switch states are unknown/);
  assert.doesNotMatch(get('safety-records').textContent, /coverage unknown|scope unknown/);
  outcome = 'safety-good'; await get('refresh').listeners.click(); ctx.inspectBot('fixture-bot');
  assert.match(get('safety-records').textContent, /CURRENT_NETWORK_SAFETY.*CURRENT_BOT_SAFETY/);
  await login('pages-populated'); ctx.inspectBot('fixture-bot');
  const pageCount = () => get('assignment-count').textContent;
  const pageRows = () => get('assignment-history').textContent;
  const previous = get('assignment-prev'), next = get('assignment-next');
  assert.match(pageCount(), /Page 1 of 3.*Showing 1–10 of 23 loaded/);
  assert.equal(get('assignment-history').children.length, 10);
  assert.match(pageRows(), /Synthetic model 01.*Synthetic model 10/);
  assert.doesNotMatch(pageRows(), /Synthetic model 11|OTHER_BOT/);
  assert.equal(previous.attributes['aria-disabled'], 'true');
  assert.equal(next.attributes['aria-disabled'], 'false');
  const beforePaging = fetchCount;
  next.focus(); next.listeners.click();
  assert.equal(ctx.document.activeElement, next);
  assert.match(pageCount(), /Page 2 of 3.*Showing 11–20/);
  assert.doesNotMatch(pageRows(), /Synthetic model 01|Synthetic model 21/);
  next.listeners.click();
  assert.match(pageCount(), /Page 3 of 3.*Showing 21–23/);
  assert.equal(get('assignment-history').children.length, 3);
  assert.equal(next.attributes['aria-disabled'], 'true');
  next.listeners.click(); assert.match(pageCount(), /Page 3 of 3/);
  assert.equal(ctx.document.activeElement, next);
  previous.focus(); previous.listeners.click(); assert.match(pageCount(), /Page 2 of 3/);
  assert.equal(ctx.document.activeElement, previous);
  previous.listeners.click(); previous.listeners.click(); assert.match(pageCount(), /Page 1 of 3/);
  assert.equal(fetchCount, beforePaging);
  // Native buttons use browser Enter/Space activation. No custom key trap or
  // positive tabindex: verify the shipped order/associations, not native keys.
  const ids = Object.keys(template);
  assert.ok(ids.indexOf('assignment-count') < ids.indexOf('assignment-prev'));
  assert.ok(ids.indexOf('assignment-prev') < ids.indexOf('assignment-next'));
  assert.ok(ids.indexOf('assignment-next') < ids.indexOf('assignment-history'));
  for (const id of ['assignment-prev', 'assignment-next']) {
    assert.equal(template[id].attrs.type, 'button');
    assert.equal(template[id].attrs['aria-controls'], 'assignment-history');
    assert.equal(template[id].attrs['aria-describedby'], 'assignment-count');
    assert.equal(template[id].attrs.tabindex, undefined);
    assert.equal(get(id).listeners.keydown, undefined);
  }
  next.listeners.click(); next.listeners.click();
  await get('refresh').listeners.click(); assert.match(pageCount(), /Page 3 of 3/);
  outcome = '503'; await get('refresh').listeners.click();
  assert.match(pageCount(), /Page 3 of 3/); assert.match(get('hub-banner').textContent, /Refresh failed/);
  outcome = 'pages-shrink'; await get('refresh').listeners.click();
  assert.match(pageCount(), /Page 1 of 1.*of 5 loaded/);
  for (const mode of ['empty', 'unavailable', 'partial']) {
    outcome = 'pages-' + mode; await get('refresh').listeners.click();
    assert.equal(get('workspace').hidden, false);
    assert.match(pageCount(), mode === 'empty' ? /0 loaded/ : mode === 'unavailable' ? /count unknown/ : /Page 1 of 1/);
    assert.equal(previous.attributes['aria-disabled'], 'true');
    assert.equal(next.attributes['aria-disabled'], 'true');
    const countBefore = pageCount(), requestsBefore = fetchCount;
    next.listeners.click(); previous.listeners.click();
    assert.equal(pageCount(), countBefore); assert.equal(fetchCount, requestsBefore);
  }
  assert.match(pageRows(), /Partial synthetic assignment.*Effective: Unknown/);
  outcome = 'pages-populated'; await get('refresh').listeners.click();
  next.listeners.click(); assert.match(pageCount(), /Page 2 of 3/);
  ctx.inspectBot('other-bot'); assert.match(pageCount(), /no longer in the loaded roster/);
  ctx.inspectBot('fixture-bot'); assert.match(pageCount(), /Page 1 of 3/);
  next.listeners.click(); get('clear-bot').listeners.click();
  assert.match(pageCount(), /Select a bot/);
  ctx.inspectBot('fixture-bot'); assert.match(pageCount(), /Page 1 of 3/);
  outcome = 'pages-orphan'; await get('refresh').listeners.click();
  assert.match(pageCount(), /no longer in the loaded roster/);
  assert.equal(next.attributes['aria-disabled'], 'true');
  await login('pages-populated'); ctx.inspectBot('fixture-bot');
  assert.match(pageCount(), /Page 1 of 3/);
  console.log('Overview/detail checks passed, including local assignment paging, scope/counts, boundary activation, stable controls, empty/error states and recovery. Native keyboard execution remains unverified. Simulated DOM only.');
})().catch(error => { console.error(error); process.exitCode = 1; });
