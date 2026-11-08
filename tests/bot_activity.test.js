// Forever-style bot activity and baseline conformance panels: synthetic data, minimal fake DOM, no browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.attributes = {}; this.textContent = ''; this.listeners = {}; this.value = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren() { this.children = []; }
  scrollIntoView() {}
  addEventListener(name, fn) { this.listeners[name] = fn; }
  setAttribute(name, value) { this.attributes[name] = value; }
  querySelectorAll(tag) { return this.children.flatMap(child => [...(child.tag === tag ? [child] : []), ...child.querySelectorAll(tag)]); }
  get lastElementChild() { return this.children.at(-1); }
}
const elements = new Map();
const get = id => { if (!elements.has(id)) elements.set(id, new Element('div')); return elements.get(id); };
const document = {querySelector: selector => get(selector.slice(1)), getElementById: get, createElement: tag => new Element(tag)};
const everything = el => [el.textContent, ...el.children.map(everything)].join('\n');
const titles = panel => panel.children.map(row => row.children[0].textContent);

const decision = {ts: '2026-01-01T00:00:01Z', engine: 'noncombat', trigger: 'low health', action: 'eat food', reason: 'hp below 40%',
  relevance: 60, band: 'NORMAL', effective: 61, alternatives: [
    {action: 'drink', relevance: 55, result: 'NOT_NEEDED'}, {action: 'attack nearest', relevance: 90, result: 'NO_TARGET'}, {action: 'follow', relevance: 20, result: 'LOW_RELEVANCE'}]};
const bots = [
  {botGuid: '1001', name: 'Alyra', classId: 1, raceId: 1, faction: 'Alliance', engine: 'noncombat', lastEventAt: '2026-01-01T00:00:05Z', level: 12, zoneId: 12,
    doing: 'Travelling to Goldshire', decisions: [decision],
    deaths: [{ts: '2026-01-01T00:00:09Z', reason: 'killed', summary: 'Slain by a boar', killerEntry: 299, killerLevel: 14, levelGap: 2,
      recentDecisions: [{msAgo: 1500, action: 'attack nearest', reason: 'pull'}, {msAgo: 400, action: 'flee', reason: 'low hp'}]}],
    quests: [{ts: '2026-01-01T00:00:03Z', reason: 'accept', questId: 33, summary: 'Wolves Across the Border'}],
    counts: {decision: 5, death: 1, quest: 2, stuck: 9, path_fail: 3, state_change: 4, extra: 1}},
  {botGuid: '2002', name: 'Borin', classId: 4, raceId: 2, faction: 'Horde', engine: 'combat', lastEventAt: '2026-01-01T00:00:06Z', level: 20, zoneId: 17,
    doing: 'Fighting a boar', decisions: [], deaths: [], quests: [], counts: {decision: 1}},
  {botGuid: '3003', name: null, engine: 'dead', lastEventAt: '2026-01-01T00:00:07Z', level: null, zoneId: null, doing: 'Running to corpse', decisions: [], deaths: [], quests: [], counts: {}},
];
const conformance = {source: 'docs/FOREVER-BASELINE-PROPOSAL.md', rows: [
  {id: 'engine', group: 'forever', behavior: 'One decision engine'}, {id: 'log', group: 'forever', behavior: 'The log is part of the engine'},
  {id: 'ladder', group: 'dit', behavior: 'DIT improvement ladder'}], games: [
  {game: 'WoW Forever', owner: 'forever lead', cells: {engine: {status: 'Reference', evidence: 'Bots/ engine sources'}, log: {status: 'Sim-measured', evidence: '800 bots, 3.9 h'}, ladder: {status: 'Bogus status', evidence: 'x'}}},
  {game: 'FFXI', owner: 'ffxi lead', cells: {engine: {status: 'Designed', evidence: 'FFXI_PLAYERBOTS_V0'}}},
  {game: 'SWTOR', owner: 'swtor lead'}]};
const snapshot = {generatedAt: 'test', hubFeeds: [], botActivity: {coverage: {status: 'Loaded', records: 17, omitted: 2, reason: 'Exported copy read.'}, bots}, baselineConformance: conformance};

const context = vm.createContext({document, TextDecoder, sessionStorage: {getItem: () => 'test', setItem() {}, removeItem() {}},
  fetch: async url => ({ok: true, json: async () => url.startsWith('/api/overview') ? snapshot : {}})});
vm.runInContext(fs.readFileSync('static/app.js', 'utf8'), context);
const setSnapshot = value => { context.__snap = value; vm.runInContext('currentSnapshot = __snap', context); };
const render = () => { context.renderBotActivity(); context.renderBaselineConformance(); };
const coverage = () => get('bot-activity-coverage').textContent;
const panel = () => get('bot-activity');

setImmediate(() => {
  // The real load path renders both panels (and resets them with the other overview panels).
  assert.equal(get('bot-activity').children.length > 0, true, 'load() should render bot activity');
  assert.equal(get('baseline-conformance').children.length > 0, true, 'load() should render conformance');

  // Loaded coverage line.
  setSnapshot(snapshot); render();
  assert.match(coverage(), /Coverage: Loaded · Imported: 17 · Omitted malformed: 2 · Exported copy read\./);
  assert.ok(coverage().includes('Exported WoW Forever bot log; not live, not DIT bots.'));
  assert.match(get('bot-activity-count').textContent, /Showing 3 of 3 loaded bots/);

  // Bot rows: title, doing line, meta with top five counts only.
  assert.deepEqual(titles(panel()), ['Alyra (1001) · noncombat', 'Borin (2002) · combat', 'Unnamed (3003) · dead']);
  const alyra = panel().children[0];
  assert.match(alyra.children[1].textContent, /^Doing: Travelling to Goldshire · Level: 12 · Zone ID: 12/);
  assert.match(alyra.children[2].textContent, /Last event: 2026-01-01T00:00:05Z · Top events: stuck 9, decision 5, state_change 4, path_fail 3, quest 2$/);
  assert.ok(!alyra.children[2].textContent.includes('extra'), 'only the top five event counts are shown');
  assert.match(panel().children[2].children[1].textContent, /Level: Unknown · Zone ID: Unknown/);

  // Decisions: line format, alternatives in supplied order with result codes.
  const [decisions, deaths, quests] = alyra.children.slice(3);
  assert.equal(decisions.tag, 'details');
  assert.match(decisions.children[0].textContent, /Recent decisions \(1\)/);
  const decisionItem = decisions.children[1].children[0];
  assert.match(decisionItem.textContent, /eat food via low health · hp below 40% · relevance 60 NORMAL \(effective 61\)/);
  assert.deepEqual(decisionItem.children[0].children.map(li => li.textContent),
    ['drink — NOT_NEEDED (55)', 'attack nearest — NO_TARGET (90)', 'follow — LOW_RELEVANCE (20)']);
  // Deaths and quests.
  assert.match(deaths.children[1].children[0].textContent, /Slain by a boar · Killer entry: 299 · Killer level: 14 · Level gap: 2/);
  assert.deepEqual(deaths.children[1].children[0].children[0].children.map(li => li.textContent),
    ['1500 ms before death · attack nearest · pull', '400 ms before death · flee · low hp']);
  assert.match(quests.children[1].children[0].textContent, /Quest 33 · Wolves Across the Border/);
  // Empty lists say so explicitly rather than vanishing.
  const borin = panel().children[1];
  assert.equal(borin.children.length, 6, 'decisions, deaths and quests sections are always present');
  assert.equal(borin.children[3].children[0].textContent, 'Recent decisions (0)');
  assert.match(borin.children[3].children[1].textContent, /none in the export \(does not mean none occurred\)/);

  // Engine filter hides the others; search by name and by guid; both are local.
  get('bot-activity-engine').value = 'combat'; get('bot-activity-engine').listeners.change();
  assert.deepEqual(titles(panel()), ['Borin (2002) · combat']);
  assert.match(get('bot-activity-count').textContent, /Showing 1 of 3 loaded bots/);
  get('bot-activity-engine').value = 'dead'; get('bot-activity-engine').listeners.change();
  assert.deepEqual(titles(panel()), ['Unnamed (3003) · dead']);
  get('bot-activity-engine').value = '';
  get('bot-activity-search').value = 'ALY'; get('bot-activity-search').listeners.input();
  assert.deepEqual(titles(panel()), ['Alyra (1001) · noncombat']);
  get('bot-activity-search').value = '2002'; get('bot-activity-search').listeners.input();
  assert.deepEqual(titles(panel()), ['Borin (2002) · combat']);
  get('bot-activity-search').value = 'nobody'; get('bot-activity-search').listeners.input();
  assert.equal(titles(panel())[0], 'No bots match the local filter');
  get('bot-activity-search').value = ''; get('bot-activity-engine').value = '';

  // Loaded but empty; Not configured; Unavailable.
  setSnapshot({...snapshot, botActivity: {coverage: {status: 'Loaded', records: 0, omitted: 0, reason: 'Empty export.'}, bots: []}}); render();
  assert.match(coverage(), /Coverage: Loaded · Imported: 0 · Omitted malformed: 0 · Empty export\./);
  assert.equal(titles(panel())[0], 'No bot activity in the export');
  assert.match(everything(panel()), /does not mean bots are idle/);
  setSnapshot({...snapshot, botActivity: {coverage: {status: 'Not configured', records: 0, omitted: 0, reason: 'Import is off.'}, bots: []}}); render();
  assert.match(coverage(), /Coverage: Not configured · Imported: 0 · Omitted malformed: 0 · Import is off\. · Exported WoW Forever bot log/);
  assert.match(everything(panel()), /DIT_FOREVER_BOTLOG_DIR/);
  setSnapshot({...snapshot, botActivity: {coverage: {status: 'Unavailable', records: 0, omitted: null, reason: 'Directory unreadable.'}, bots: []}}); render();
  assert.match(coverage(), /Coverage: Unavailable · Imported: 0 · Omitted malformed: Unknown · Directory unreadable\./);
  assert.equal(titles(panel())[0], 'Forever bot log unavailable');
  assert.ok(!titles(panel()).includes('No bot activity in the export'));

  // Malformed bot rows are counted, not rendered; malformed fields show Unknown and never throw.
  setSnapshot({...snapshot, botActivity: {coverage: snapshot.botActivity.coverage, bots: [null, 7, {name: 'No guid'}, {botGuid: '9', engine: 'bogus', decisions: 'x', deaths: [null], quests: {}, counts: {a: -1, b: 'x'}}]}}); render();
  assert.equal(titles(panel())[0], 'Bot coverage Unknown for omitted malformed rows');
  assert.ok(titles(panel()).includes('Unnamed (9) · Unknown'));
  assert.match(get('bot-activity-count').textContent, /Showing 1 of 1 loaded bots/);
  const nine = panel().children.find(row => row.children[0].textContent === 'Unnamed (9) · Unknown');
  assert.equal(nine.children[3].children[0].textContent, 'Recent decisions (Unknown)');
  assert.match(nine.children[3].children[1].textContent, /Unknown \(missing or malformed in the export\)/);
  assert.equal(nine.children[4].children[0].textContent, 'Deaths (1)');
  assert.equal(nine.children[4].children[1].children[0].textContent, 'Unreadable entry; Unknown');
  assert.equal(nine.children[5].children[0].textContent, 'Quests (Unknown)');
  // A decision whose alternatives are malformed still renders, with Unknown rather than a silent gap.
  setSnapshot({...snapshot, botActivity: {coverage: snapshot.botActivity.coverage, bots: [{botGuid: '8', decisions: [{action: 'rest', alternatives: 'oops'}, {action: 'sit', alternatives: [null]}]}]}}); render();
  const decisionsList = panel().children[0].children[3].children[1].children;
  assert.match(decisionsList[0].children[0].textContent, /Rejected alternatives: Unknown \(missing or malformed/);
  assert.equal(decisionsList[1].children[0].children[0].textContent, 'Unreadable entry; Unknown');

  // Missing or malformed botActivity: explicit Unknown, no throw.
  for (const bad of [undefined, null, 'x', [], {}, {coverage: null, bots: []}, {coverage: {status: 'Loaded'}, bots: 'no'}]) {
    const without = {...snapshot}; if (bad === undefined) delete without.botActivity; else without.botActivity = bad;
    setSnapshot(without);
    assert.doesNotThrow(render);
    assert.match(coverage(), /^Coverage: Unknown/);
    assert.equal(titles(panel()).length, 1);
    assert.equal(panel().children[0].children[1].textContent, 'Unknown');
  }
  // An unrecognized status is Unknown, never treated as Loaded.
  setSnapshot({...snapshot, botActivity: {coverage: {status: 'Fine', records: 1}, bots: []}}); render();
  assert.match(coverage(), /^Coverage: Unknown · Imported: 1 · Omitted malformed: Unknown · Reason unknown/);

  // Baseline conformance: supplied status plus evidence, missing cell Unknown, invalid status Unknown.
  setSnapshot(snapshot); render();
  const conformancePanel = get('baseline-conformance');
  assert.equal(conformancePanel.children[0].children[0].textContent, 'Baseline conformance source');
  assert.equal(conformancePanel.children[0].children[1].textContent, 'docs/FOREVER-BASELINE-PROPOSAL.md');
  const regions = conformancePanel.children.slice(1);
  assert.equal(regions.length, 2, 'Forever and DIT groups render separately');
  const tables = regions.map(region => region.children[0]);
  assert.match(tables[0].children[0].textContent, /WoW Forever operating model/);
  assert.match(tables[1].children[0].textContent, /DIT improvements/);
  const headers = tables[0].children[1].children[0].children.map(th => th.textContent);
  assert.deepEqual(headers, ['Behavior', 'WoW Forever · forever lead', 'FFXI · ffxi lead', 'SWTOR · swtor lead']);
  const cell = (table, rowIndex, col) => table.children[2].children[rowIndex].children[col];
  assert.equal(cell(tables[0], 0, 0).textContent, 'One decision engine');
  assert.equal(cell(tables[0], 0, 1).children[0].textContent, 'Reference');
  assert.equal(cell(tables[0], 0, 1).children[1].textContent, 'Bots/ engine sources');
  assert.equal(cell(tables[0], 0, 1).attributes.title, 'Bots/ engine sources');
  assert.equal(cell(tables[0], 1, 1).children[0].textContent, 'Sim-measured');
  assert.equal(cell(tables[0], 0, 2).children[0].textContent, 'Designed');
  assert.equal(cell(tables[0], 1, 2).children[0].textContent, 'Unknown', 'missing cell');
  assert.equal(cell(tables[0], 0, 3).children[0].textContent, 'Unknown', 'game without cells');
  assert.equal(cell(tables[1], 0, 1).children[0].textContent, 'Unknown', 'unrecognized status is Unknown');
  // Repeated row ids are ambiguous, so neither shows a supplied status.
  setSnapshot({...snapshot, baselineConformance: {...conformance, rows: [...conformance.rows, {id: 'engine', group: 'forever', behavior: 'Duplicate id'}]}}); render();
  assert.equal(cell(get('baseline-conformance').children[1].children[0], 0, 1).children[0].textContent, 'Unknown');

  // Malformed or missing baselineConformance is Unknown without throwing.
  for (const bad of [undefined, null, 'x', [], {}, {rows: 'x', games: []}, {rows: [], games: {}}]) {
    const without = {...snapshot}; if (bad === undefined) delete without.baselineConformance; else without.baselineConformance = bad;
    setSnapshot(without);
    assert.doesNotThrow(render);
    assert.equal(get('baseline-conformance').children.length, 1);
    assert.equal(get('baseline-conformance').children[0].children[1].textContent, 'Unknown');
  }
  setSnapshot({...snapshot, baselineConformance: {source: 's', rows: [null, {id: 'a'}, {id: 'ok', group: 'forever', behavior: 'B'}], games: [null, {game: 'G', cells: {ok: 'str'}}]}}); render();
  assert.match(get('baseline-conformance').children[0].children[2].textContent, /1 behaviors · 1 games · Malformed entries omitted/);
  assert.equal(cell(get('baseline-conformance').children[1].children[0], 0, 1).children[0].textContent, 'Unknown');

  // Data is rendered as text only: a markup string stays a literal string.
  setSnapshot({...snapshot, botActivity: {coverage: snapshot.botActivity.coverage, bots: [{...bots[1], doing: '<img src=x onerror=alert(1)>'}]}}); render();
  assert.equal(panel().children[0].children[1].textContent.includes('<img src=x onerror=alert(1)>'), true);
  // Sign-out/session reset clears the filters, coverage text and both panels.
  get('bot-activity-engine').value = 'combat'; get('bot-activity-search').value = 'x';
  context.resetPanelSession();
  assert.equal(get('bot-activity-engine').value, '');
  assert.equal(get('bot-activity-search').value, '');
  assert.equal(get('bot-activity-coverage').textContent, 'Coverage unknown.');
  assert.equal(get('bot-activity').children.length, 0);
  assert.equal(get('baseline-conformance').children.length, 0);
  console.log('Bot activity and baseline conformance panels passed: coverage states, filters, ordering, Unknown handling.');
});
