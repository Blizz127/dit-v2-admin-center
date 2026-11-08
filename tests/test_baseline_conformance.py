"""Baseline-conformance fixture loading and strict refusal; no network, no live game."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import baseline_conformance as bc


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
        ids = [row['id'] for row in result['rows']]
        self.assertEqual(len(ids), 23)
        self.assertEqual([game['game'] for game in result['games']],
                         ['WoW Forever (Classic 1.60)', 'FFXI', 'WotLK Forever', 'SWTOR'])
        for game in result['games']:
            self.assertEqual(set(game['cells']), set(ids))
        swtor = result['games'][3]['cells']
        self.assertTrue(all(cell == {'status': 'Unknown', 'evidence': 'No documented evidence'}
                            for cell in swtor.values()))

    def test_wow_forever_has_sixteen_known_forever_rows(self):
        result = bc.read()
        forever = [row['id'] for row in result['rows'] if row['group'] == 'forever']
        self.assertEqual(len(forever), 16)
        self.assertEqual(sum(row['group'] == 'dit' for row in result['rows']), 7)
        cells = result['games'][0]['cells']
        for row_id in forever:
            self.assertNotEqual(cells[row_id]['status'], 'Unknown', row_id)
        self.assertEqual(cells['dit-01']['status'], 'Not started')
        self.assertEqual(cells['dit-02']['status'], 'Unknown')

    def test_ffxi_and_wotlk_body_cells_are_designed(self):
        games = {game['game']: game['cells'] for game in bc.read()['games']}
        self.assertEqual(games['FFXI']['forever-01']['status'], 'Designed')
        self.assertIn('FFXI_PLAYERBOTS_V0', games['FFXI']['forever-01']['evidence'])
        self.assertEqual(games['WotLK Forever']['forever-01']['status'], 'Designed')
        self.assertEqual(games['FFXI']['forever-02']['status'], 'Unknown')

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
