// Local parity review on the real app and template with synthetic snapshots.
// This is simulated DOM coverage, not browser rendering or native keyboard evidence.
const assert = require('node:assert/strict');
const {get, refresh, context, requestCount} = require('./overview_snapshot_harness.cjs');
const statuses = ['Verified live', 'Partly live', 'Built', 'Designed', 'Unknown', 'Not applicable', 'Reference', 'Unit-tested', 'Sim-measured', 'Not started'];
const tracker = {
  source: 'Synthetic review fixture', asOf: '2026-11-11',
  rows: [...statuses.map((status, index) => ({id: `p-${index}`, group: 'parity', behavior: `Area ${index}`})),
    {id: 'engine', group: 'forever', behavior: 'Engine'}, {id: 'advice', group: 'dit', behavior: 'Advice'}],
  games: [
    {game: 'FFXI', owner: 'ffxi lead', cells: Object.fromEntries([
      ...statuses.map((status, index) => [`p-${index}`, {status, evidence: `Evidence ${index}`}]),
      ['engine', {status: 'Built', evidence: 'Engine evidence'}], ['advice', {status: 'Designed', evidence: 'Advice evidence'}]])},
    {game: 'SWTOR', owner: 'swtor lead', cells: {'p-0': {status: 'Built', evidence: 'Independent SWTOR evidence'}}},
  ],
};
const clone = value => JSON.parse(JSON.stringify(value));
const change = (id, value) => { get(id).value = value; get(id).listeners.change(); };
const text = id => get(id).textContent;
const regions = () => get('baseline-conformance').children.slice(1);
const tableRows = () => regions().flatMap(region => region.children[1]?.children[2]?.children || []);
const labels = () => tableRows().map(row => row.children[0].textContent);
const cellStatuses = () => tableRows().flatMap(row => row.children.slice(1).map(cell => cell.children[0].textContent));
const selectFfxi = () => change('baseline-game', 'FFXI');
const reset = () => get('baseline-reset').listeners.click();
(async () => {
  await refresh({baselineConformance: tracker});
  const firstRequests = requestCount();
  assert.equal(regions().length, 3, 'the default all-game matrix retains all behavior groups');
  assert.equal(tableRows().length, 12);
  assert.equal(tableRows()[0].children.length, 3, 'behavior plus both game columns');
  assert.match(text('baseline-conformance'), /Documented tracker date: 2026-11-11; not a freshness or live check/);
  assert.match(text('baseline-summary'), /Select one game/);
  assert.equal(get('baseline-game').disabled, false);
  assert.equal(get('baseline-game').attributes['aria-describedby'], 'baseline-filter-note');
  for (const id of ['baseline-group', 'baseline-status']) assert.equal(get(id).attributes['aria-describedby'], 'baseline-filter-note');

  selectFfxi();
  assert.equal(tableRows()[0].children.length, 2);
  assert.match(text('baseline-summary'), /FFXI · supplied parity counts/);
  for (const status of statuses) assert.ok(text('baseline-summary').includes(`${status}: 1`), `separate ${status} count`);
  assert.match(text('baseline-summary'), /10 supplied parity rows before group\/status filters/);
  assert.match(text('baseline-summary'), /not current behavior or goal completion/);
  const summary = text('baseline-summary');
  change('baseline-group', 'parity');
  change('baseline-status', 'needs-live');
  assert.deepEqual(labels(), ['Area 1', 'Area 2', 'Area 3', 'Area 4', 'Area 7', 'Area 8', 'Area 9']);
  assert.ok(cellStatuses().includes('Unknown'), 'unknown evidence remains in needs-verification view');
  assert.equal(text('baseline-summary'), summary, 'filters do not shrink the parity denominator');
  assert.match(text('baseline-conformance'), /Evidence 2/);
  assert.doesNotMatch(text('baseline-conformance'), /Independent SWTOR evidence/);

  change('baseline-status', 'Built');
  assert.deepEqual(labels(), ['Area 2']);
  change('baseline-group', 'dit');
  assert.match(text('baseline-conformance'), /No behaviors match these filters/);
  assert.match(text('baseline-conformance'), /does not establish completion/);
  assert.equal(text('baseline-summary'), summary);
  reset();
  assert.equal(get('baseline-game').value, '');
  assert.equal(get('baseline-group').value, '');
  assert.equal(get('baseline-status').value, '');
  assert.equal(tableRows().length, 12);
  change('baseline-group', 'parity'); change('baseline-status', 'Built');
  assert.deepEqual(labels(), ['Area 0', 'Area 2'], 'all-game status filter matches any shown game');
  assert.deepEqual(tableRows()[0].children.slice(1).map(cell => cell.children[0].textContent), ['Verified live', 'Built'],
    'other game evidence is retained, not rewritten to the filter status');
  reset(); selectFfxi(); change('baseline-status', 'Built');
  assert.equal(requestCount(), firstRequests, 'all filters and reset are local');

  await refresh({baselineConformance: tracker});
  assert.equal(get('baseline-game').value, 'FFXI');
  assert.equal(get('baseline-status').value, 'Built');
  const missingGame = clone(tracker); missingGame.games = [missingGame.games[1]];
  await refresh({baselineConformance: missingGame});
  assert.equal(get('baseline-game').value, '');
  assert.match(text('baseline-count'), /Previous game selection unavailable/);
  assert.doesNotMatch(text('baseline-summary'), /FFXI · supplied parity counts/);
  assert.match(text('baseline-conformance'), /Independent SWTOR evidence/);

  reset(); await refresh({baselineConformance: tracker}); selectFfxi();
  const repeated = clone(tracker);
  repeated.rows.push({id: 'p-0', group: 'dit', behavior: 'Repeated identity'});
  await refresh({baselineConformance: repeated});
  assert.match(text('baseline-summary'), /Verified live: 0/);
  assert.match(text('baseline-summary'), /Unknown: 2/);
  assert.match(text('baseline-summary'), /Total coverage Unknown/);
  change('baseline-group', 'parity'); change('baseline-status', 'Unknown');
  assert.deepEqual(labels(), ['Area 0', 'Area 4'], 'group filtering cannot make repeated IDs unique');
  assert.ok(!text('baseline-conformance').includes('Evidence 0'), 'ambiguous evidence is not attributed');

  const malformedDuplicate = clone(tracker);
  malformedDuplicate.rows.push({id: 'p-0'});
  await refresh({baselineConformance: malformedDuplicate});
  assert.deepEqual(labels(), ['Area 0', 'Area 4'], 'even an omitted malformed duplicate invalidates the visible identity');
  assert.match(text('baseline-count'), /Total coverage Unknown/);
  const cappedDuplicate = clone(tracker);
  for (let index = 0; index < 35; index++) cappedDuplicate.rows.push({id: `extra-${index}`, group: 'dit', behavior: 'Extra'});
  cappedDuplicate.rows.push({id: 'p-0', group: 'dit', behavior: 'Duplicate beyond display cap'});
  await refresh({baselineConformance: cappedDuplicate});
  assert.deepEqual(labels(), ['Area 0', 'Area 4'], 'display cap cannot hide identity ambiguity');

  reset(); const repeatedGame = clone(tracker); repeatedGame.games.push(clone(repeatedGame.games[0]));
  await refresh({baselineConformance: repeatedGame}); selectFfxi();
  assert.match(text('baseline-summary'), /Verified live: 0/);
  assert.match(text('baseline-summary'), /Unknown: 10/);
  assert.match(text('baseline-summary'), /Total coverage Unknown/);
  assert.ok(cellStatuses().every(status => status === 'Unknown'), 'duplicate game identity cannot certify any column');

  const absentEvidence = clone(tracker); delete absentEvidence.games[0].cells['p-0'].evidence;
  await refresh({baselineConformance: absentEvidence});
  assert.match(text('baseline-summary'), /Verified live: 0/);
  assert.match(text('baseline-summary'), /Unknown: 2/);
  assert.match(text('baseline-conformance'), /No evidence supplied/);
  const invalidId = clone(tracker); invalidId.rows[0].id = '';
  await refresh({baselineConformance: invalidId});
  assert.match(text('baseline-summary'), /Verified live: 0/);
  assert.match(text('baseline-summary'), /Total coverage Unknown/);

  const noParity = clone(tracker); noParity.rows = noParity.rows.filter(row => row.group !== 'parity');
  await refresh({baselineConformance: noParity});
  assert.match(text('baseline-summary'), /Parity counts: Unknown/);
  assert.doesNotMatch(text('baseline-summary'), /Verified live: 0/);
  await refresh({baselineConformance: null});
  assert.match(text('baseline-summary'), /Parity counts: Unknown/);
  assert.equal(get('baseline-game').disabled, true);
  assert.equal(get('baseline-game').value, '');
  assert.equal(get('baseline-game').children.length, 1, 'unavailable data removes old game choices');
  await refresh({baselineConformance: tracker});
  assert.equal(get('baseline-game').disabled, false);
  selectFfxi(); assert.match(text('baseline-summary'), /Verified live: 1/);
  assert.doesNotMatch(text('baseline-summary'), /Total coverage Unknown/);
  await refresh({baselineConformance: {...tracker, rows: []}});
  assert.match(text('baseline-count'), /Conformance coverage Unknown/);
  assert.match(text('baseline-summary'), /Parity counts: Unknown/);
  assert.equal(get('baseline-status').disabled, true);

  // The owner's eight acceptance scenarios are scoped by exact game name and
  // remain read-only plans, with existing evidence shown beside each scenario.
  const planTracker = {
    source: 'Synthetic acceptance-plan fixture', asOf: '2026-11-11',
    rows: Array.from({length: 12}, (_, index) => ({id: `p-${String(index + 1).padStart(2, '0')}`, group: 'parity', behavior: `Parity area ${index + 1}`})),
    games: ['FFXI (LSB)', 'FFXI Forever (Rust)', 'SWTOR', 'Other game'].map(game => ({game, owner: 'Synthetic lead', cells: {
      'p-01': {status: 'Verified live', evidence: `${game} party receipt`},
      'p-02': {status: 'Partly live', evidence: `${game} transfer receipt`},
      'p-12': {status: 'Built', evidence: `${game} advice code only`},
    }})),
  };
  const planBefore = JSON.stringify(planTracker);
  await refresh({baselineConformance: planTracker});
  const planRequests = requestCount();
  const checklist = () => get('baseline-summary').children.find(child => child.id === 'baseline-playtest-checklist');
  const scenarios = () => checklist().children[2].children;
  change('baseline-game', 'FFXI (LSB)');
  assert.equal(scenarios().length, 8);
  assert.deepEqual(scenarios().map(row => row.children[0].textContent), [
    'Invite and follow', 'Ten pulls and party roles', 'Death and recovery', 'Owner orders',
    'Mount and dismount', 'Quest or mission step', 'Talk and memory', 'AI tactics',
  ]);
  assert.match(checklist().children[1].textContent, /existing authorized playtest session/);
  assert.match(checklist().children[1].textContent, /planned checks, not completed results/);
  assert.match(checklist().children[1].textContent, /records nothing and never changes tracker statuses/);
  assert.match(scenarios()[0].children[1].textContent, /three zone boundaries/);
  assert.match(scenarios()[0].children[1].textContent, /30 seconds/);
  assert.match(scenarios()[0].children[3].textContent, /p-01 · Parity area 1 — Verified live.*FFXI \(LSB\) party receipt/);
  assert.match(scenarios()[0].children[3].textContent, /p-02 · Parity area 2 — Partly live/);
  assert.match(scenarios()[1].children[1].textContent, /10 pulls/);
  assert.match(scenarios()[1].children[1].textContent, /rest for MP/);
  assert.match(scenarios()[2].children[1].textContent, /Raise offered within 60 seconds/);
  assert.match(scenarios()[2].children[1].textContent, /within 5 minutes/);
  assert.match(scenarios()[2].children[1].textContent, /without pulling while weakened/);
  assert.match(scenarios()[2].children[3].textContent, /p-05 · Parity area 5 — Unknown/);
  assert.match(scenarios()[3].children[1].textContent, /commands already available to the owner/);
  assert.match(scenarios()[6].children[1].textContent, /\/tell and a party message/);
  assert.match(scenarios()[7].children[1].textContent, /already authorized and enabled/);
  assert.match(scenarios()[7].children[1].textContent, /does not enable or switch advice/);
  assert.match(scenarios()[7].children[3].textContent, /p-12 · Parity area 12 — Built.*advice code only/);
  for (const scenario of scenarios()) assert.match(scenario.children[2].textContent, /^Evidence needed: /);
  const unfilteredPlan = checklist().textContent;
  change('baseline-group', 'dit'); change('baseline-status', 'Built');
  assert.equal(checklist().textContent, unfilteredPlan, 'view filters cannot hide checklist evidence or mark a scenario done');

  change('baseline-game', 'FFXI Forever (Rust)');
  assert.match(scenarios()[0].children[1].textContent, /era-correct transport, such as a boat/);
  assert.match(scenarios()[1].children[1].textContent, /West Sarutabaruta/);
  assert.match(scenarios()[4].children[1].textContent, /rented chocobo/);
  assert.match(scenarios()[5].children[1].textContent, /era-correct quest or mission/);
  assert.doesNotMatch(scenarios()[0].children[3].textContent, /FFXI \(LSB\) party receipt/);
  change('baseline-game', 'SWTOR');
  assert.match(scenarios()[0].children[1].textContent, /taxi, shuttle or ship/);
  assert.match(scenarios()[1].children[1].textContent, /resource recovery/);
  assert.match(scenarios()[2].children[1].textContent, /revive and regroup/);
  assert.doesNotMatch(scenarios()[2].children[1].textContent, /Raise|weakness|weakened/);
  assert.match(scenarios()[4].children[1].textContent, /mount or speeder/);
  assert.match(scenarios()[5].children[1].textContent, /class-story or planet-quest/);
  assert.match(scenarios()[6].children[1].textContent, /whisper and group chat/);
  change('baseline-game', 'Other game');
  assert.equal(checklist(), undefined);
  assert.match(text('baseline-summary'), /No owner playtest checklist supplied for this game/);
  assert.equal(requestCount(), planRequests, 'reviewing plans issues no requests');
  assert.equal(JSON.stringify(planTracker), planBefore, 'checklist leaves tracker records unchanged');

  const ambiguousPlan = clone(planTracker);
  ambiguousPlan.rows.push({id: 'p-01', group: 'parity', behavior: 'Duplicate party'});
  ambiguousPlan.rows = ambiguousPlan.rows.filter(row => row.id !== 'p-02');
  await refresh({baselineConformance: ambiguousPlan}); change('baseline-game', 'SWTOR');
  assert.match(scenarios()[0].children[3].textContent, /p-01 · Behavior identity missing or ambiguous — Unknown/);
  assert.match(scenarios()[0].children[3].textContent, /p-02 · Behavior identity missing or ambiguous — Unknown/);
  assert.doesNotMatch(scenarios()[0].children[3].textContent, /SWTOR party receipt|transfer receipt/);
  const ambiguousGamePlan = clone(planTracker); ambiguousGamePlan.games.push(clone(ambiguousGamePlan.games[2]));
  await refresh({baselineConformance: ambiguousGamePlan});
  assert.match(scenarios()[0].children[3].textContent, /p-01 · Parity area 1 — Unknown/);
  assert.doesNotMatch(scenarios()[0].children[3].textContent, /SWTOR party receipt/);
  await refresh({baselineConformance: {...planTracker, rows: []}});
  assert.equal(scenarios().length, 8, 'known plan survives absent tracker rows without inventing results');
  assert.match(scenarios()[0].children[3].textContent, /No usable parity row supplied/);
  await refresh({baselineConformance: null}); assert.equal(checklist(), undefined);
  await refresh({baselineConformance: planTracker}); change('baseline-game', 'SWTOR');
  assert.match(scenarios()[0].children[3].textContent, /SWTOR party receipt/);
  reset(); assert.equal(checklist(), undefined, 'all-games reset removes per-game plans');

  const literal = clone(tracker); literal.games[0].game = '<img src=x onerror=alert(1)>';
  literal.asOf = '<script>not a date</script>'; literal.games[0].cells['p-0'].evidence = '<img src=x onerror=alert(2)>';
  await refresh({baselineConformance: literal}); change('baseline-game', literal.games[0].game);
  assert.ok(text('baseline-summary').includes(literal.games[0].game));
  assert.ok(text('baseline-conformance').includes(literal.asOf));
  assert.ok(text('baseline-conformance').includes(literal.games[0].cells['p-0'].evidence));
  change('baseline-group', 'forged'); change('baseline-status', 'forged');
  assert.equal(get('baseline-group').value, ''); assert.equal(get('baseline-status').value, '');
  context.resetPanelSession();
  for (const id of ['baseline-game', 'baseline-group', 'baseline-status']) {
    assert.equal(get(id).value, ''); assert.equal(get(id).disabled, true);
  }
  assert.equal(text('baseline-summary'), '');
  assert.equal(text('baseline-conformance'), '');
  assert.equal(text('baseline-count'), 'Conformance coverage unknown.');
  console.log('PASS: per-game parity filters/counts, evidence preservation, ambiguous/missing input, refresh recovery, scoped owner playtest plans and session reset; local simulated DOM only.');
})().catch(error => { console.error(error); process.exitCode = 1; });
