"""Baseline-conformance fixture loading and strict refusal; no network, no live game."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import baseline_conformance as bc

GAMES = ['WoW Forever Bots (Karrz v0.1.33, reference)', 'FFXI (LSB)', 'FFXI Forever (Rust)', 'SWTOR',
         'WotLK Forever', 'WoW Forever Bots, 70450 predecessor (src/server/game/Bots)']
PARITY = ['p-01', 'p-02', 'p-03', 'p-04', 'p-05', 'p-06', 'p-07', 'p-08', 'p-09', 'p-10', 'p-11', 'p-12']
PARITY_BEHAVIOR = ['Bound to the owner, party', 'Follow everywhere (zone lines, transports, teleports)',
                   'Every class/job with its own rotation',
                   'Party roles and helpers (tank, heals, cleanse/raise, buffs, debuffs, CC, pets)',
                   'Rest, death and recovery', 'Mounts', 'Getting bots by class and role, filling the party',
                   'Owner orders', 'Level match with the owner', 'Quests and progression', 'AI chat through DIT',
                   'AI decisions (dit.decision_advice.v1)']
UNKNOWN = {'status': 'Unknown', 'evidence': 'No documented evidence'}


class BaselineConformanceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.good = json.loads(bc.FIXTURE.read_text())

    def write(self, data, name='f.json'):
        path = self.dir / name
        path.write_text(data if isinstance(data, str) else json.dumps(data))
        return path

    def mutated(self, change):
        data = copy.deepcopy(self.good)
        change(data)
        return self.write(data)

    def test_committed_fixture_loads_and_fills_every_cell(self):
        result = bc.read()
        self.assertIsNotNone(result)
        self.assertEqual(set(result), {'source', 'asOf', 'rows', 'games'})
        self.assertEqual(result['asOf'], '2026-11-09')
        self.assertIn('docs/goals/BOTS-PARITY-GOAL-20261109.md', result['source'])
        ids = [row['id'] for row in result['rows']]
        self.assertEqual(len(ids), 35)
        self.assertEqual([game['game'] for game in result['games']], GAMES)
        for game in result['games']:
            self.assertEqual(set(game['cells']), set(ids))
        self.assertEqual([game['owner'] for game in result['games']],
                         ['trinitycore-forever', 'ffxi', 'ffxi-platform', 'swtor-preservation', 'WotLK lead',
                          'Forever server lead'])
        # WotLK and the 70450 predecessor carry no parity cells, so every parity cell renders Unknown.
        for index in (4, 5):
            cells = result['games'][index]['cells']
            self.assertTrue(all(cells[row_id] == UNKNOWN for row_id in PARITY), index)

    def test_parity_rows_come_first(self):
        rows = bc.read()['rows']
        self.assertEqual([row['id'] for row in rows[:12]], PARITY)
        self.assertEqual([row['behavior'] for row in rows[:12]], PARITY_BEHAVIOR)
        self.assertTrue(all(row['group'] == 'parity' for row in rows[:12]))
        self.assertTrue(all(row['group'] != 'parity' for row in rows[12:]))
        self.assertEqual([row['id'] for row in rows[12:]][0], 'forever-01')
        self.assertEqual(rows[-1]['id'], 'dit-07')

    def test_wow_forever_has_sixteen_known_forever_rows(self):
        result = bc.read()
        forever = [row['id'] for row in result['rows'] if row['group'] == 'forever']
        self.assertEqual(len(forever), 16)
        self.assertEqual(sum(row['group'] == 'dit' for row in result['rows']), 7)
        # The 70450 predecessor column is last and carries the documented statuses.
        cells = result['games'][5]['cells']
        self.assertEqual(cells['forever-01']['status'], 'Sim-measured')
        for row_id in forever:
            self.assertNotEqual(cells[row_id]['status'], 'Unknown', row_id)
        self.assertEqual(cells['dit-01']['status'], 'Not started')
        self.assertEqual(cells['dit-02']['status'], 'Unknown')

    def test_karrz_is_the_reference_for_parity_rows(self):
        cells = bc.read()['games'][0]['cells']
        self.assertEqual(cells['forever-01']['status'], 'Reference')
        evidence = cells['forever-01']['evidence']
        for text in ('PlayerbotV2', 'v0.1.33', '8ed3810b', '0.1.29.1', '8609da55023'):
            self.assertIn(text, evidence)
        for row_id in PARITY[:11]:
            self.assertEqual(cells[row_id]['status'], 'Reference', row_id)
            self.assertIn('Karrz', cells[row_id]['evidence'], row_id)
        self.assertEqual(cells['p-12']['status'], 'Not started')
        self.assertIn('8609da55023', evidence)
        self.assertTrue(all(c == UNKNOWN for k, c in cells.items()
                            if k not in PARITY and k != 'forever-01'))

    def test_ffxi_lsb_parity_cells(self):
        cells = bc.read()['games'][1]['cells']
        self.assertEqual([cells[row_id]['status'] for row_id in PARITY],
                         ['Verified live', 'Built', 'Partly live', 'Partly live', 'Partly live', 'Partly live',
                          'Designed', 'Built', 'Built', 'Designed', 'Built', 'Built'])
        self.assertIn('03:58:17Z', cells['p-01']['evidence'])
        self.assertIn('owned by <owner> (joined their party)', cells['p-01']['evidence'])
        self.assertIn('MP rest', cells['p-05']['evidence'])
        self.assertIn('inert', cells['p-09']['evidence'])
        self.assertIn('4c4a1093', cells['p-05']['evidence'])
        self.assertIn('ce90dc67', cells['p-06']['evidence'])
        self.assertIn('fb7b289b', cells['p-03']['evidence'])
        self.assertIn('bag_full', cells['p-03']['evidence'])
        self.assertIn('live 17:16:51Z', cells['p-08']['evidence'])
        self.assertNotIn('Blizz', bc.FIXTURE.read_text())  # the owner name is masked in the export and the tracker
        self.assertTrue(all(cells[k] == UNKNOWN for k in cells if k not in PARITY))

    def test_ffxi_forever_parity_cells_and_existing_body_cell(self):
        games = {game['game']: game['cells'] for game in bc.read()['games']}
        cells = games['FFXI Forever (Rust)']
        self.assertEqual([cells[row_id]['status'] for row_id in PARITY],
                         ['Built', 'Built', 'Built', 'Built', 'Built', 'Designed', 'Built', 'Built',
                          'Designed', 'Built', 'Designed', 'Designed'])
        self.assertIn('cohort0-r2', cells['p-07']['evidence'])
        # rc7 put the five bots in game (logins only); being in the owner's party is still unconfirmed, so Built stays.
        self.assertIn('all 5 logged in on rc7 2026-11-10 03:05:47Z', cells['p-07']['evidence'])
        self.assertIn('party with the owner not confirmed', cells['p-07']['evidence'])
        self.assertIn('not confirmed live', cells['p-01']['evidence'])
        self.assertIn('unconfirmed', cells['p-02']['evidence'])
        # /fb exists as native source packets (r11, r12) only: it must never read as a runtime or as live.
        self.assertIn('native source r11 (4a79acef) only: not in a runtime, not live', cells['p-07']['evidence'])
        self.assertIn('/fb native source through r25 (af18d38c)', cells['p-08']['evidence'])
        self.assertIn('Source packets only: no runtime kit, live build is still rc8', cells['p-08']['evidence'])
        self.assertIn('native source r14 (7f1707c8) only, not live', cells['p-04']['evidence'])
        self.assertTrue(cells['p-08']['evidence'].endswith('not live.'))
        self.assertIn('733dfb5', cells['p-02']['evidence'])
        self.assertIn('da14962', cells['p-10']['evidence'])
        self.assertIn('2026-11-10-rc8-live-09bf10c2', cells['p-01']['evidence'])
        self.assertIn('2026-11-10-rc8-live-09bf10c2', cells['p-02']['evidence'])
        self.assertIn('ffxi-platform 5e46007', cells['p-01']['evidence'])
        self.assertEqual(cells['forever-01']['status'], 'Designed')
        self.assertIn('FFXI_PLAYERBOTS_V0', cells['forever-01']['evidence'])
        self.assertEqual(cells['forever-02'], UNKNOWN)

    def test_swtor_parity_cells(self):
        cells = bc.read()['games'][3]['cells']
        self.assertEqual([cells[row_id]['status'] for row_id in PARITY],
                         ['Built'] * 5 + ['Designed', 'Designed', 'Built', 'Not applicable', 'Designed', 'Built',
                          'Designed'])
        for row_id in PARITY:
            if row_id == 'p-09':
                continue
            evidence = cells[row_id]['evidence']
            if cells[row_id]['status'] == 'Built':
                # Built from release kc/kf: live code, but no live log line yet, so never Verified live.
                self.assertRegex(evidence, r'release (kc live 11-09 10:48:48Z|kf live 11-09 14:50:07Z)', row_id)
                self.assertIn('not yet seen', evidence, row_id)
            else:
                self.assertIn('BOTS-PLAN-20261109.md', evidence, row_id)
        self.assertIn('bot-behavior', cells['p-08']['evidence'])
        # kt carries the squad human-timing patch (bot-human-r2, in the composition since c46); still not seen live.
        self.assertIn('Release kt (live 11-10 04:19:57Z) adds per-role reaction delays and press jitter', cells['p-04']['evidence'])
        self.assertIn('release kf live 11-09 14:50:07Z', cells['p-03']['evidence'])
        self.assertIn('rotations ON', cells['p-03']['evidence'])
        # kf logs rotation decisions but requests no advice, so AI decisions stay Designed.
        self.assertIn('No decision_advice.v1 request', cells['p-12']['evidence'])
        self.assertIn('bot-chat', cells['p-12']['evidence'])
        self.assertIn('bot-chat', cells['p-11']['evidence'])
        self.assertTrue(all(cells[k] == UNKNOWN for k in cells if k not in PARITY))

    def test_ffxi_and_wotlk_body_cells_are_designed(self):
        games = {game['game']: game['cells'] for game in bc.read()['games']}
        self.assertEqual(games['WotLK Forever']['forever-01']['status'], 'Designed')
        self.assertEqual(games['FFXI (LSB)']['forever-01'], UNKNOWN)
        self.assertEqual(games['FFXI Forever (Rust)']['forever-02']['status'], 'Unknown')

    def test_default_path_is_resolved_at_call_time(self):
        other = self.write(self.good, 'other.json')
        self.assertIsNotNone(bc.read(other))
        original = bc.FIXTURE
        bc.FIXTURE = self.dir / 'missing.json'
        try:
            self.assertIsNone(bc.read())
        finally:
            bc.FIXTURE = original
        self.assertIsNotNone(bc.read())

    def test_new_statuses_are_accepted(self):
        for status in ('Verified live', 'Partly live', 'Built', 'Not applicable'):
            with self.subTest(status=status):
                def edit(d, status=status): d['games'][0]['cells']['p-01'] = {'status': status, 'evidence': 'x'}
                result = bc.read(self.mutated(edit))
                self.assertIsNotNone(result)
                self.assertEqual(result['games'][0]['cells']['p-01']['status'], status)

    def test_parity_group_is_accepted_and_near_miss_statuses_are_refused(self):
        def parity_row(d): d['rows'][12]['group'] = 'parity'
        self.assertIsNotNone(bc.read(self.mutated(parity_row)))
        def near_miss(status):
            def edit(d): d['games'][0]['cells']['p-01'] = {'status': status, 'evidence': 'x'}
            return edit
        for status in ('verified live', 'Live', 'Partly-live', 'Built ', 'Verified', 'Done', '', 'N/A', 'not applicable'):
            with self.subTest(status=status):
                self.assertIsNone(bc.read(self.mutated(near_miss(status))))
        def bad_parity_group(d): d['rows'][0]['group'] = 'Parity'
        self.assertIsNone(bc.read(self.mutated(bad_parity_group)))

    def test_refusals_return_none(self):
        def bad_status(d): d['games'][0]['cells']['forever-01']['status'] = 'Done'
        def unknown_id(d): d['games'][1]['cells']['forever-99'] = {'status': 'Designed', 'evidence': 'x'}
        def dup_row(d): d['rows'][1]['id'] = d['rows'][0]['id']
        def dup_game(d): d['games'][1]['game'] = d['games'][0]['game']
        def wrong_kind(d): d['kind'] = 'other'
        def wrong_version(d): d['version'] = 2
        def bad_group(d): d['rows'][0]['group'] = 'misc'
        def empty_evidence(d): d['games'][0]['cells']['forever-01']['evidence'] = ' '
        def long_evidence(d): d['games'][0]['cells']['forever-01']['evidence'] = 'x' * 301
        def nonstring_evidence(d): d['games'][0]['cells']['forever-01']['evidence'] = 5
        def extra_cell_key(d): d['games'][0]['cells']['forever-01']['note'] = 'x'
        def no_rows(d): d['rows'] = []
        for change in (bad_status, unknown_id, dup_row, dup_game, wrong_kind, wrong_version, bad_group,
                       empty_evidence, long_evidence, nonstring_evidence, extra_cell_key, no_rows):
            with self.subTest(change=change.__name__):
                self.assertIsNone(bc.read(self.mutated(change)))

    def test_maximum_length_evidence_is_accepted(self):
        def edit(d): d['games'][0]['cells']['forever-01']['evidence'] = 'x' * 300
        self.assertIsNotNone(bc.read(self.mutated(edit)))

    def test_unreadable_input_returns_none(self):
        self.assertIsNone(bc.read(self.write('not json {')))
        self.assertIsNone(bc.read(self.write('[]')))
        self.assertIsNone(bc.read(self.write('{"kind": "baseline-conformance", "kind": "x"}')))
        self.assertIsNone(bc.read(self.write(b'\xff\xfe'.decode('latin-1'))))
        self.assertIsNone(bc.read(self.write('[' * 100000)))
        self.assertIsNone(bc.read(self.dir / 'absent.json'))
        self.assertIsNone(bc.read(self.dir))
        big = dict(self.good, padding='x' * (bc.LIMIT + 1))
        self.assertIsNone(bc.read(self.write(big, 'big.json')))

    def test_symlink_is_refused(self):
        target = self.write(self.good, 'target.json')
        link = self.dir / 'link.json'
        link.symlink_to(target)
        self.assertIsNotNone(bc.read(target))
        self.assertIsNone(bc.read(link))


if __name__ == '__main__':
    unittest.main()
