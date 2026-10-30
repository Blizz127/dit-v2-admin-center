import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from wake_verification import GAMES, LIMIT, project, read


def receipt():
    return {'schema': 'dit-admin-wake-readback-v1',
            'cutover': {'id': 'synthetic-cutover-1', 'completed': True,
                        'destination': 'banshee:8450', 'completedAt': '2026-01-01T00:00:00Z',
                        'receipt': 'synthetic-cutover-receipt'},
            'games': [{'game': game, 'cutoverId': 'synthetic-cutover-1', 'authenticated': True,
                       'result': 'ready', 'observedAt': '2026-01-01T00:01:00Z',
                       'receipt': 'synthetic-' + game} for game in ('enb', 'wow-forever', 'war')]}


class WakeVerificationTests(unittest.TestCase):
    def rows(self, data):
        return {r['game']: r for r in project(data, datetime(2026, 1, 2, tzinfo=timezone.utc))['rows']}

    def test_exact_partial_readbacks_and_hold_preservation(self):
        rows = self.rows(receipt())
        self.assertEqual(set(rows), set(GAMES))
        self.assertEqual(rows['enb']['status'], 'Verified readback (reported)')
        self.assertEqual(rows['wow-forever']['status'], 'Verified readback (reported)')
        self.assertEqual(rows['war']['status'], 'Held')
        self.assertEqual(rows['ffxi']['status'], 'Unverified')

    def test_cutover_alone_and_mismatched_readbacks_never_verify(self):
        for changes in ({'authenticated': False}, {'authenticated': 1}, {'result': 'starting'},
                        {'result': '401'}, {'cutoverId': 'older-cutover'}, {'game': 'ENB'},
                        {'observedAt': '2025-12-31T23:59:00Z'}, {'observedAt': '2027-01-01T00:00:00Z'},
                        {'observedAt': '2026-01-01T00:01:00'}, {'receipt': 'Bearer PRIVATE'}):
            with self.subTest(changes=changes):
                data = receipt(); data['games'][0].update(changes)
                self.assertEqual(self.rows(data)['enb']['status'], 'Unverified')
        data = receipt(); data['games'] = []
        self.assertTrue(all(r['status'] in ('Unverified', 'Held') for r in self.rows(data).values()))

    def test_duplicate_game_and_new_cutover_clear_old_claims(self):
        data = receipt(); data['games'].append(copy.deepcopy(data['games'][0]))
        self.assertEqual(self.rows(data)['enb']['status'], 'Unverified')
        self.assertEqual(self.rows(data)['wow-forever']['status'], 'Verified readback (reported)')
        for change in ({'id': 'new-cutover'}, {'destination': 'ax41:8450'}, {'completed': False}):
            data = receipt(); data['cutover'].update(change)
            self.assertEqual(self.rows(data)['enb']['status'], 'Unverified')

    def test_local_file_is_bounded_strict_and_not_cached(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'receipt.json'
            for raw in (b'', b'{', b'\xff', b' ' * (LIMIT + 1), b'{"schema":0,"schema":1}', b'{"x":NaN}'):
                path.write_bytes(raw)
                self.assertTrue(all(r['status'] in ('Unverified', 'Held') for r in read(path)['rows']))
            path.write_text(json.dumps(receipt()))
            self.assertEqual(read(path)['rows'][GAMES.index('enb')]['status'], 'Verified readback (reported)')
            path.unlink()
            self.assertEqual(read(path)['rows'][GAMES.index('enb')]['status'], 'Unverified')

    def test_malformed_envelopes_remain_unknown(self):
        for data in (None, [], {}, {'cutover': []}, {'cutover': {'completedAt': False}}):
            self.assertTrue(all(r['status'] in ('Unverified', 'Held') for r in self.rows(data).values()))
