// Bot activity sources and baseline conformance panels: synthetic data, minimal fake DOM, no browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const htmlWrites = []; // Every string written as markup. The app must never write any, so this stays empty.
class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.attributes = {}; this.textContent = ''; this.listeners = {}; this.value = ''; }
  set innerHTML(html) { htmlWrites.push(String(html)); }
  get innerHTML() { return ''; }
  set outerHTML(html) { htmlWrites.push(String(html)); }
  insertAdjacentHTML(where, html) { htmlWrites.push(String(html)); }
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
const sectionsOf = () => get('bot-activity-sources').children.filter(child => child.className === 'bot-source');

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
const WOW_NOTE = 'Exported WoW Forever bot log (70450 predecessor Bots format); not live, not DIT bots, not PlayerbotV2.';
const wowSource = {id: 'wow-70450-export', label: 'WoW Forever (70450 predecessor export)', note: WOW_NOTE, bots,
  coverage: {status: 'Loaded', records: 17, omitted: 2, reason: 'Exported copy read.'}};
const snapshot = {generatedAt: 'test', hubFeeds: [], botActivity: {coverage: {status: 'Loaded', records: 17, omitted: 2, reason: 'Exported copy read.'}, bots}, baselineConformance: conformance};

const context = vm.createContext({document, TextDecoder, sessionStorage: {getItem: () => 'test', setItem() {}, removeItem() {}},
  fetch: async url => ({ok: true, json: async () => url.startsWith('/api/overview') ? snapshot : {}})});
vm.runInContext(fs.readFileSync('static/app.js', 'utf8'), context);
const setSnapshot = value => { context.__snap = value; vm.runInContext('currentSnapshot = __snap', context); };
const render = () => { context.renderBotActivity(); context.renderBaselineConformance(); };
const coverage = () => get('bot-activity-coverage').textContent;
const panel = () => get('bot-activity');

// FFXI and bot_event rows in the shapes the server source adapters return (synthetic).
const ffxiBots = [{actorId: 'fumika', name: 'Fumika', charId: 5001, zoneId: 240, lastEventAt: '2026-11-09T04:00:00Z', doing: 'party owner_left_zone',
  counts: {ok: 109, refused: 9, defend: 0, tripStart: 2}, events: [
    {ts: '2026-11-09T04:00:00Z', type: 'act', rule: 'follow', apl: 'follow', op: 'move', result: 'refused', reason: 'too_far', detail: '<img src=x onerror=alert(1)>', repeated: 3},
    {ts: '2026-11-09T03:59:00Z', type: 'party', rule: null, apl: null, op: null, result: null, reason: 'owner_left_zone', detail: null, repeated: 1}],
  refusals: [{ts: '2026-11-09T04:00:00Z', type: 'act', rule: 'follow', op: 'move', result: 'refused', reason: 'too_far', detail: null, repeated: 3}],
  deaths: [{ts: '2026-11-09T03:58:00Z', type: 'dead', rule: null, reason: 'killed', detail: 'Slain by a crab'}]}];
const ditBots = [{game: 'swtor', actorId: '2001', lastEventAt: '2026-11-09T05:00:00Z', level: 12, area: 'Coruscant', doing: 'Accept mission',
  counts: {decision: 2, advice: 1, death: 1}, events: [
    {ts: '2026-11-09T05:00:00Z', type: 'advice', severity: 1, reason: 'choice', summary: null, action: 'accept', result: 'applied'}],
  deaths: [{ts: '2026-11-09T04:50:00Z', killer: 'Gundark', recentDecisions: [{action: 'attack', reason: 'pull'}, {action: null, reason: null}]}],
  advice: [{ts: '2026-11-09T05:00:00Z', kind: 'mission', chosen: 'accept', outcome: 'applied', reason: 'ok'}]},
  {game: 'ffxi-forever', actorId: '2002', lastEventAt: null, level: null, area: null, doing: '<script>alert(2)</script>', counts: {}, events: [],
    deaths: [], advice: 'not a list', chat: {voiced: 3, dropped: 2, byReason: {NO_LISTENER: 2, STALE: 0}}, name: 'Kade',
    feel: {cadence: {action: 'rotation_pick', gaps: 20, modalGapS: 1.5, modalCount: 18, modalShare: 0.9, metronomic: true}, sync: null,
      schedule: {intervals: 4, modalIntervalS: 3456, modalCount: 3, modalShare: 0.75, fixed: true}}}];
const ffxiSource = {id: 'ffxi-lsb', label: 'FFXI (LSB) Bots V2 log export', note: 'Exported [BOTS-V2] map-log lines; offline import (DIT_FFXI_BOTSV2_LOG); owner name masked.',
  bots: ffxiBots, coverage: {status: 'Loaded', records: 382, omitted: 0, unrecognized: 0, ignored: 0, reason: 'Real export.', from: '2026-11-09T01:12:51.704Z', to: '2026-11-09T04:23:57.203Z'}};
const ditSource = {id: 'dit-bot-event-v1', label: 'DIT bot_event v1 (SWTOR, FFXI Forever, other DIT games)', note: 'Offline import of dit.bot_event.v1 JSONL (DIT_BOT_EVENT_DIR); includes AI advice rows.',
  bots: ditBots, coverage: {status: 'Loaded', records: 2, omitted: 2, files: 1, reason: 'One file.', omittedByReason: {not_bot_event: 2, invalid_ts: 0}}};
const vanillaBots = [{game: 'wow_vanilla', actorId: 'tohsha', name: 'Tohsha', level: 11.23, lastEventAt: '2026-11-09T20:52:00Z', doing: 'AttackAnything Makrura Shellhide',
  counts: {AttackAnything: 578, XpGain: 9}, pulls: 578, kills: 9, pullsPerKill: 64.2, hearthStuck: {'combat long stuck': 3},
  stall: {target: 'Makrura Shellhide', pulls: 562, seconds: 3474, positions: 1, from: '2026-11-09T19:54:06Z', to: '2026-11-09T20:52:00Z'},
  events: [{ts: '2026-11-09T20:52:00Z', type: 'AttackAnything', detail: 'Makrura Shellhide'}], deaths: [],
  feel: {cadence: {action: 'pull', gaps: 577, modalGapS: 5, modalCount: 258, modalShare: 0.447, metronomic: false}, sync: null, schedule: null}},
  {game: 'wow_vanilla', actorId: 'bikdorl', name: 'Bikdorl', level: 8.56, lastEventAt: null, doing: null, counts: {}, pulls: 85, kills: 82, pullsPerKill: 1,
    hearthStuck: {}, stall: null, events: [], deaths: []}];
const vanillaSource = {id: 'wow-vanilla-playerbots', label: 'WoW Vanilla / Benilla playerbots (cmangos-classic event log)', note: 'Exported CSV.',
  bots: vanillaBots, coverage: {status: 'Loaded', records: 10337, omitted: 0, reason: 'One run.'}};
const multi = {...snapshot, botActivity: {bots, coverage: wowSource.coverage, sources: [wowSource, ffxiSource, ditSource, vanillaSource]}};
const sourceFor = (id, source) => ({...multi, botActivity: {...multi.botActivity, sources: [wowSource, ...[ffxiSource, ditSource].map(s => s.id === id ? source : s)]}});

setImmediate(() => {
  // The real load path renders both panels (and resets them with the other overview panels).
  assert.equal(get('bot-activity').children.length > 0, true, 'load() should render bot activity');
  assert.equal(get('baseline-conformance').children.length > 0, true, 'load() should render conformance');

  // Loaded coverage line.
  setSnapshot(snapshot); render();
  assert.match(coverage(), /Coverage: Loaded · Imported log rows: 17 · Omitted malformed: 2 · Exported copy read\./);
  assert.equal(get('bot-activity-note').textContent, WOW_NOTE);
  assert.equal(get('bot-activity-label').textContent, 'WoW Forever (70450 predecessor export)');
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
  assert.match(coverage(), /Coverage: Loaded · Imported log rows: 0 · Omitted malformed: 0 · Empty export\./);
  assert.equal(titles(panel())[0], 'No bot activity in the export');
  assert.match(everything(panel()), /does not mean bots are idle/);
  setSnapshot({...snapshot, botActivity: {coverage: {status: 'Not configured', records: 0, omitted: 0, reason: 'Import is off.'}, bots: []}}); render();
  assert.match(coverage(), /^Coverage: Not configured · Imported log rows: 0 · Omitted malformed: 0 · Import is off\.$/);
  assert.match(everything(panel()), /DIT_FOREVER_BOTLOG_DIR/);
  setSnapshot({...snapshot, botActivity: {coverage: {status: 'Unavailable', records: 0, omitted: null, reason: 'Directory unreadable.'}, bots: []}}); render();
  assert.match(coverage(), /Coverage: Unavailable · Imported log rows: 0 · Omitted malformed: Unknown · Directory unreadable\./);
  assert.equal(titles(panel())[0], 'Import unavailable');
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
  assert.match(coverage(), /^Coverage: Unknown · Imported log rows: 1 · Omitted malformed: Unknown · Reason unknown/);

  // Baseline conformance: supplied status plus evidence, missing cell Unknown, invalid status Unknown.
  setSnapshot(snapshot); render();
  const conformancePanel = get('baseline-conformance');
  assert.equal(conformancePanel.children[0].children[0].textContent, 'Baseline conformance source');
  assert.equal(conformancePanel.children[0].children[1].textContent, 'docs/FOREVER-BASELINE-PROPOSAL.md');
  const regions = conformancePanel.children.slice(1);
  assert.equal(regions.length, 2, 'Forever and DIT groups render separately');
  const tables = regions.map(region => region.children[1]);
  assert.equal(regions[0].children[0].textContent, 'WoW Forever operating model');
  assert.match(tables[0].children[0].textContent, /WoW Forever operating model/);
  assert.match(tables[1].children[0].textContent, /DIT improvements/);
  const headers = tables[0].children[1].children[0].children.map(th => th.textContent);
  assert.deepEqual(headers, ['Behavior', 'WoW Forever · forever lead', 'FFXI · ffxi lead', 'SWTOR · swtor lead']);
  const cell = (table, rowIndex, col) => table.children[2].children[rowIndex].children[col];
  assert.equal(cell(tables[0], 0, 0).textContent, 'One decision engine');
  assert.equal(cell(tables[0], 0, 1).children[0].textContent, 'Reference');
  assert.equal(cell(tables[0], 0, 1).children[0].className, 'baseline-status baseline-reference');
  assert.equal(cell(tables[0], 0, 1).children[1].textContent, 'Bots/ engine sources');
  assert.equal(cell(tables[0], 0, 1).attributes.title, 'Bots/ engine sources');
  assert.equal(cell(tables[0], 1, 1).children[0].textContent, 'Sim-measured');
  assert.equal(cell(tables[0], 0, 2).children[0].textContent, 'Designed');
  assert.equal(cell(tables[0], 1, 2).children[0].textContent, 'Unknown', 'missing cell');
  assert.equal(cell(tables[0], 0, 3).children[0].textContent, 'Unknown', 'game without cells');
  assert.equal(cell(tables[1], 0, 1).children[0].textContent, 'Unknown', 'unrecognized status is Unknown');
  // Repeated row ids are ambiguous, so neither shows a supplied status.
  setSnapshot({...snapshot, baselineConformance: {...conformance, rows: [...conformance.rows, {id: 'engine', group: 'forever', behavior: 'Duplicate id'}]}}); render();
  assert.equal(cell(get('baseline-conformance').children[1].children[1], 0, 1).children[0].textContent, 'Unknown');

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
  assert.equal(cell(get('baseline-conformance').children[1].children[1], 0, 1).children[0].textContent, 'Unknown');

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
  assert.equal(get('bot-activity-sources').children.length, 0);
  assert.equal(get('baseline-conformance').children.length, 0);

  // Legacy snapshot without sources: WoW renders from the top-level keys; FFXI and bot_event are explicit Unknown.
  setSnapshot(snapshot); render();
  assert.equal(sectionsOf().length, 3, 'one section each for FFXI, bot_event and Vanilla playerbots even when not supplied');
  for (const section of sectionsOf()) {
    assert.match(section.children[2].textContent, /^Coverage: Unknown · No usable data for this source/);
    assert.equal(section.children[5].children[0].children[1].textContent, 'Unknown');
  }
  assert.equal(get('bot-activity-sources').children.some(child => child.className === 'row'), false, 'no unrecognized-source notice for a legacy snapshot');

  // Multi-source: one WoW block plus one section per other source, each with its own label, note and coverage line.
  setSnapshot(multi); render();
  assert.equal(get('bot-activity-label').textContent, 'WoW Forever (70450 predecessor export)');
  assert.equal(get('bot-activity-note').textContent, WOW_NOTE);
  assert.match(coverage(), /^Coverage: Loaded · Imported log rows: 17 · Omitted malformed: 2 · Exported copy read\.$/);
  assert.equal(sectionsOf().length, 3);
  const [ffxi, dit] = sectionsOf();
  assert.equal(ffxi.children[0].textContent, 'FFXI (LSB) Bots V2 log export');
  assert.equal(ffxi.children[1].textContent, ffxiSource.note);
  assert.equal(ffxi.children[1].className, 'muted');
  assert.equal(ffxi.children[2].attributes.role, 'status');
  assert.equal(ffxi.children[2].textContent, 'Coverage: Loaded · Imported log rows: 382 · Omitted malformed: 0 · Unrecognized lines: 0 · Ignored lines: 0 · Real export.');
  assert.equal(dit.children[0].textContent, 'DIT bot_event v1 (SWTOR, FFXI Forever, other DIT games)');
  assert.equal(dit.children[1].textContent, ditSource.note);
  assert.equal(dit.children[2].textContent, 'Coverage: Loaded · Imported log rows: 2 · Omitted malformed: 2 · Files read: 1 · Omitted by reason: not_bot_event 2 · One file.');
  for (const section of [ffxi, dit]) assert.ok(!section.children[1].textContent.includes('70450'), 'the 70450 caveat applies to the WoW source only');
  assert.ok(!everything(ffxi).includes('70450') && !everything(dit).includes('70450'));

  // FFXI rows: counts, latest doing, events with repeats and refusals with reasons, deaths. Markup stays text.
  assert.equal(ffxi.children[4].textContent, 'Showing 1 of 1 loaded bots. Local filter only; no request is made.');
  const fumika = ffxi.children[5].children[0];
  assert.equal(fumika.children[0].textContent, 'Fumika (fumika)');
  assert.equal(fumika.children[1].textContent, 'Doing: party owner_left_zone · Zone ID: 240 · Character ID: 5001');
  assert.equal(fumika.children[2].textContent, 'Last event: 2026-11-09T04:00:00Z · Counts: ok 109, refused 9, tripStart 2');
  const [ffxiEvents, ffxiRefusals, ffxiDeaths] = fumika.children.slice(3);
  assert.equal(ffxiEvents.children[0].textContent, 'Events (2)');
  assert.equal(ffxiEvents.children[1].children[0].textContent,
    '2026-11-09T04:00:00Z · act · follow · move · refused · too_far · apl follow · repeated 3 · <img src=x onerror=alert(1)>');
  assert.equal(ffxiEvents.children[1].children[1].textContent, '2026-11-09T03:59:00Z · party · owner_left_zone');
  assert.equal(ffxiRefusals.children[0].textContent, 'Refusals (1)');
  assert.equal(ffxiRefusals.children[1].children[0].textContent, '2026-11-09T04:00:00Z · follow · move · reason too_far');
  assert.equal(ffxiDeaths.children[0].textContent, 'Deaths (1)');
  assert.equal(ffxiDeaths.children[1].children[0].textContent, '2026-11-09T03:58:00Z · dead · reason killed · Slain by a crab');
  assert.deepEqual(htmlWrites, [], 'malicious text never becomes markup; the literal textContent checks above are the guard');

  // The FFXI search filters only the FFXI section, by name or ID, and keeps its own value.
  const ffxiSearch = ffxi.children[3].children[0];
  assert.equal(ffxiSearch.tag, 'input');
  assert.equal(ffxiSearch.attributes.maxlength, '128');
  ffxiSearch.value = 'SHADOW'; ffxiSearch.listeners.input();
  assert.equal(sectionsOf()[0].children[4].textContent, 'Showing 0 of 1 loaded bots. Local filter only; no request is made.');
  assert.equal(sectionsOf()[0].children[5].children[0].children[0].textContent, 'No bots match the local filter');
  assert.equal(sectionsOf()[1].children[4].textContent, 'Showing 2 of 2 loaded bots. Local filter only; no request is made.', 'other sections are unaffected');
  ffxiSearch.value = 'fum'; ffxiSearch.listeners.input();
  assert.equal(sectionsOf()[0].children[5].children[0].children[0].textContent, 'Fumika (fumika)');
  // A full re-render keeps the FFXI text filter value.
  render();
  assert.equal(sectionsOf()[0].children[3].children[0].value, 'fum');
  setSnapshot(multi); render();
  assert.equal(sectionsOf()[0].children[3].children[0].value, 'fum', 'the saved filter survives a re-render');
  get('bot-activity-search').value = ''; render();

  // bot_event rows: counts by type, events, deaths with recent decisions, advice with outcome; malformed rows are Unknown.
  const [d1, d2] = dit.children[5].children;
  assert.equal(d1.children[0].textContent, '2001 · swtor');
  assert.equal(d1.children[1].textContent, 'Doing: Accept mission · Level: 12 · Area: Coruscant');
  assert.equal(d1.children[2].textContent, 'Last event: 2026-11-09T05:00:00Z · Counts by type: decision 2, advice 1, death 1');
  const [ditEvents, ditDeaths, ditAdvice] = d1.children.slice(3);
  assert.equal(ditEvents.children[1].children[0].textContent, '2026-11-09T05:00:00Z · advice · severity 1 · choice · action accept · result applied');
  assert.equal(ditDeaths.children[0].textContent, 'Deaths (1)');
  assert.equal(ditDeaths.children[1].children[0].textContent, '2026-11-09T04:50:00Z · Killer: Gundark');
  assert.deepEqual(ditDeaths.children[1].children[0].children[0].children.map(li => li.textContent), ['action attack · reason pull', 'Unknown']);
  assert.equal(ditAdvice.children[1].children[0].textContent, '2026-11-09T05:00:00Z · mission · chosen accept · outcome applied · ok');
  assert.equal(d2.children[1].textContent, 'Doing: <script>alert(2)</script> · Level: Unknown · Area: Unknown');
  // Vanilla playerbots: pulls against kills, the longest run of pulls without a kill, and stuck hearthstone escapes.
  const [v1, v2] = sectionsOf()[2].children[5].children;
  assert.equal(v1.children[0].textContent, 'Tohsha (tohsha) · level 11.23');
  assert.equal(v1.children[1].textContent, 'Doing: AttackAnything Makrura Shellhide · Pulls: 578 · Kills: 9 · Pulls per kill: 64.2 · Hearthstone escapes (stuck): combat long stuck 3');
  assert.equal(v1.children[5].textContent, 'Longest run of pulls without a kill: 562 pulls on Makrura Shellhide over 58 min from 1 position (2026-11-09T19:54:06Z to 2026-11-09T20:52:00Z).');
  assert.equal(v1.children[6].textContent, 'Human-feel signals: pull: 258 of 577 gaps exactly 5 s');
  assert.equal(v2.children[1].textContent, 'Doing: Unknown · Pulls: 85 · Kills: 82 · Pulls per kill: 1 · Hearthstone escapes (stuck): none');
  assert.equal(v2.children[5].textContent, 'Longest run of pulls without a kill: under 10 pulls (not stuck).');
  // Human-feel signals: the measurement line closes each row; a snapshot without the field says so.
  assert.equal(d1.children[d1.children.length - 1].textContent, 'Human-feel signals: not measured in this snapshot.');
  assert.equal(d2.children[d2.children.length - 1].textContent,
    'Human-feel signals: rotation_pick: 18 of 20 gaps exactly 1.5 s (metronomic) · trip starts: 3 of 4 gaps exactly 3456 s (fixed clock)');
  // Names: the DIT actor key and area name are shown when present; the game id stays.
  assert.equal(d2.children[0].textContent, 'Kade (2002) · ffxi-forever');
  // Chat totals appear only for a bot with chat rows; a bot without the field (d1, an older snapshot) shows none.
  assert.equal(d2.children[2].textContent, 'Last event: Unknown · Counts by type: Unknown · Chat: voiced 3, dropped 2 (NO_LISTENER 2)');
  assert.equal(d2.children[3].children[0].textContent, 'Events (0)');
  assert.match(d2.children[3].children[1].textContent, /Events: none in the export/);
  assert.equal(d2.children[5].children[0].textContent, 'Advice (Unknown)', 'a non-list advice field is Unknown, not empty');
  assert.match(d2.children[5].children[1].textContent, /Unknown \(missing or malformed in the export\)/);

  // Source-level states: Off and Unavailable say so, and a missing or malformed source is Unknown.
  setSnapshot(sourceFor('dit-bot-event-v1', {...ditSource, coverage: {status: 'Off', records: 0, omitted: 0, reason: 'Switch unset.'}, bots: []})); render();
  assert.equal(sectionsOf()[1].children[2].textContent.startsWith('Coverage: Off · Imported log rows: 0'), true);
  assert.equal(sectionsOf()[1].children[5].children[0].children[0].textContent, 'Import is off');
  assert.match(everything(sectionsOf()[1]), /DIT_BOT_EVENT_DIR/);
  setSnapshot(sourceFor('ffxi-lsb', {...ffxiSource, coverage: {status: 'Unavailable', records: 0, omitted: null, reason: 'Log unreadable (unreadable).'}, bots: []})); render();
  assert.equal(sectionsOf()[0].children[5].children[0].children[0].textContent, 'Import unavailable');
  assert.match(sectionsOf()[0].children[5].children[0].children[1].textContent, /Log unreadable/);
  assert.equal(sectionsOf()[1].children[5].children[0].children[0].textContent, '2001 · swtor', 'the other source is unaffected');

  const malformedSources = {...snapshot, botActivity: {bots, coverage: wowSource.coverage, sources: [null, 7, wowSource,
    {id: 'ffxi-lsb', coverage: {status: 'Loaded'}, bots: 'no'}, {id: 'mystery', coverage: {status: 'Loaded'}, bots: []}]}};
  setSnapshot(malformedSources); render();
  assert.equal(get('bot-activity-label').textContent, 'WoW Forever (70450 predecessor export)', 'the WoW entry is still found among malformed entries');
  assert.match(sectionsOf()[0].children[2].textContent, /^Coverage: Unknown · No usable data for this source/, 'malformed FFXI entry is Unknown');
  assert.equal(sectionsOf()[1].children[5].children[0].children[0].textContent, 'Source coverage', 'missing DIT entry is Unknown');
  const unrecognized = get('bot-activity-sources').children.find(child => child.className === 'row');
  assert.equal(unrecognized.children[0].textContent, 'Unrecognized sources not shown');
  assert.equal(unrecognized.children[1].textContent, '3 source entries have an id this page does not render.');

  // A WoW entry without a usable coverage line is Unknown; the other sources still render.
  setSnapshot({...multi, botActivity: {...multi.botActivity, sources: [{id: 'wow-70450-export', bots: []}, ffxiSource]}}); render();
  assert.equal(get('bot-activity-label').textContent, 'WoW Forever (70450 predecessor export)');
  assert.equal(get('bot-activity-note').textContent, WOW_NOTE, 'a missing note falls back to the WoW note');
  assert.match(coverage(), /^Coverage: Unknown/);
  assert.equal(sectionsOf()[0].children[2].textContent.startsWith('Coverage: Loaded · Imported log rows: 382'), true);

  // Malformed bot entries inside a source are counted, not rendered.
  setSnapshot(sourceFor('ffxi-lsb', {...ffxiSource, bots: [null, 3, {name: 'noid'}, {actorId: '  ', name: 'blank'}, ffxiBots[0]]})); render();
  assert.equal(sectionsOf()[0].children[5].children[0].children[0].textContent, 'Bot coverage Unknown for omitted malformed rows');
  assert.equal(sectionsOf()[0].children[5].children[0].children[1].textContent, '4 rows without a usable bot ID are not shown.');
  assert.equal(sectionsOf()[0].children[4].textContent, 'Showing 1 of 1 loaded bots. Local filter only; no request is made.');

  // Parity: the parity group renders first under its heading; new statuses carry their own classes; missing cells Unknown.
  const parityConformance = {source: 'docs/goals/BOTS-PARITY-GOAL-20261109.md', rows: [
    {id: 'p-01', group: 'parity', behavior: 'Bound to the owner, party'}, {id: 'p-02', group: 'parity', behavior: 'Walks to camp'},
    {id: 'engine', group: 'forever', behavior: 'One decision engine'}, {id: 'mystery', group: 'other', behavior: 'Unclassified row'}],
  games: [
    {game: 'FFXI (LSB)', owner: 'ffxi lead', cells: {'p-01': {status: 'Verified live', evidence: '[BOTS-V2] log line'}, 'p-02': {status: 'Partly live', evidence: 'partial'},
      engine: {status: 'Built', evidence: 'port built'}, mystery: {status: 'Reference', evidence: 'x'}}},
    {game: 'SWTOR', owner: 'swtor lead', cells: {'p-01': {status: 'verified live', evidence: 'lowercase is not a status'}}}]};
  setSnapshot({...snapshot, baselineConformance: parityConformance}); render();
  const parityPanel = get('baseline-conformance');
  const groups = parityPanel.children.slice(1);
  assert.deepEqual(groups.map(region => region.children[0].textContent), ['Bots parity (owner goal 2026-11-09)', 'WoW Forever operating model', 'Group unknown'],
    'parity first, then forever, then unknown group');
  assert.equal(groups[0].attributes['aria-label'], 'Bots parity (owner goal 2026-11-09)');
  const parityTable = groups[0].children[1];
  assert.equal(parityTable.children[2].children.length, 2, 'parity rows only in the parity table');
  assert.deepEqual(parityTable.children[1].children[0].children.map(th => th.textContent), ['Behavior', 'FFXI (LSB) · ffxi lead', 'SWTOR · swtor lead']);
  const parityCell = (rowIndex, col) => parityTable.children[2].children[rowIndex].children[col].children[0];
  assert.equal(parityCell(0, 1).textContent, 'Verified live');
  assert.equal(parityCell(0, 1).className, 'baseline-status baseline-verified-live');
  assert.equal(parityCell(1, 1).textContent, 'Partly live');
  assert.equal(parityCell(1, 1).className, 'baseline-status baseline-partly-live');
  assert.equal(parityCell(0, 2).textContent, 'Unknown', 'a lowercase status is not a status');
  assert.equal(parityCell(0, 2).className, 'baseline-status baseline-unknown');
  assert.equal(parityCell(1, 2).textContent, 'Unknown', 'a missing cell is Unknown');
  assert.equal(groups[1].children[1].children[2].children[0].children[1].children[0].textContent, 'Built', 'Built uses the built class');
  assert.equal(groups[1].children[1].children[2].children[0].children[1].children[0].className, 'baseline-status baseline-built');
  assert.equal(groups[2].children[1].children[2].children[0].children[1].children[0].textContent, 'Reference');
  assert.ok(!everything(groups[2]).includes('Verified live'), 'parity rows are not repeated under Group unknown');
  assert.match(parityTable.children[0].textContent, /Status reflects the evidence cited for each cell; Unknown means not supplied\./);

  assert.deepEqual(htmlWrites, [], 'no panel in this test writes markup');
  console.log('Bot activity sources, parity and baseline conformance panels passed: coverage states, filters, escaping, malformed sources, parity statuses.');
});
