"""vanilla_botlog: the cmangos-classic playerbot event CSV. Offline, strict, never echoes a bad row."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import vanilla_botlog as vanilla

FIXTURE = Path(__file__).parent / 'fixtures' / 'vanilla-botlog' / 'vanilla-bot_events-20261109T1927Z.derived.csv'
DERIVED_SHA256 = 'ad510a009cd3a44af973eaa32654552058430fe085eab90498d83ef0cbc20210'


def row(stamp='2026-11-09 19:27:40', name='Estellene', action='AttackAnythingAction', point='POINT(1670.56 -5705.33)',
        race='1', klass='9', level='12.32', info1='Rockjaw Skullthumper', info2='1115'):
    return f'{stamp}+00,{name},{action},"{point}",{race},{klass},{level},"{info1}","{info2}"\n'.encode()


class VanillaBotlogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def write(self, *rows):
        path = Path(self.temp.name) / 'events.csv'
        path.write_bytes(b''.join(rows))
        return str(path)

    def test_live_run_shows_the_stuck_re_pull_loop(self):
        # cmangos-classic export of the live run 11-09 19:27Z-20:52Z (source sha 91893354), info1 blanked on the
        # 246 group and guild rows. See the fixture README.
        raw = FIXTURE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), DERIVED_SHA256)
        bots, coverage = vanilla.read(str(FIXTURE))
        self.assertEqual((coverage['status'], coverage['records'], coverage['omitted'], coverage['bots']),
                         ('Loaded', 10337, 0, 580))
        self.assertEqual((coverage['pulls'], coverage['kills'], coverage['stalledBots'], coverage['stalledPulls'],
                          coverage['hearthStuck'], coverage['deaths']), (5028, 2236, 10, 1842, 305, 183))
        self.assertEqual((coverage['from'], coverage['to']), ('2026-11-09T19:27:40Z', '2026-11-09T20:52:04Z'))
        self.assertEqual(len(bots), vanilla.MAX_BOTS)
        worst = bots[0]  # Longest stall first.
        self.assertEqual((worst['name'], worst['pulls'], worst['kills'], worst['pullsPerKill']),
                         ('Tohsha', 578, 9, 64.2))
        self.assertEqual(worst['stall'], {'target': 'Makrura Shellhide', 'pulls': 562, 'seconds': 3474, 'positions': 1,
                                          'from': '2026-11-09T19:54:06Z', 'to': '2026-11-09T20:52:00Z'})
        self.assertEqual(worst['hearthStuck'], {'combat long stuck': 3})
        self.assertEqual([bot['name'] for bot in bots[:5]], ['Tohsha', 'Trevduz', 'Grewa', 'Galeando', 'Estellene'])
        by_name = {bot['name']: bot for bot in bots}
        self.assertEqual(by_name['Estellene']['feel']['cadence'],
                         {'action': 'pull', 'gaps': 124, 'modalGapS': 5.0, 'modalCount': 78, 'modalShare': 0.629,
                          'metronomic': True})
        self.assertTrue(all(len(bot['events']) <= vanilla.MAX_EVENTS for bot in bots))

    def test_a_kill_or_a_new_target_ends_a_run(self):
        rows = [row(stamp=f'2026-11-09 19:00:{i:02d}', info1='Makrura Shellhide') for i in range(12)]
        rows.append(row(stamp='2026-11-09 19:00:20', action='XpGainAction', info1='Makrura Shellhide', info2='29'))
        rows += [row(stamp=f'2026-11-09 19:01:{i:02d}', info1='Kolkar Drudge') for i in range(5)]
        rows += [row(stamp=f'2026-11-09 19:02:{i:02d}', info1='Kolkar Outrunner') for i in range(5)]
        bots, coverage = vanilla.read(self.write(*rows))
        bot = bots[0]
        self.assertEqual((bot['pulls'], bot['kills'], bot['pullsPerKill']), (22, 1, 22.0))
        self.assertEqual((bot['stall']['pulls'], bot['stall']['target'], bot['stall']['positions']),
                         (12, 'Makrura Shellhide', 1))
        self.assertEqual((coverage['stalledBots'], coverage['stalledPulls']), (1, 12))
        # Nine pulls then a kill is ordinary play, not a stall.
        rows = [row(stamp=f'2026-11-09 19:00:{i:02d}') for i in range(9)]
        self.assertIsNone(vanilla.read(self.write(*rows))[0][0]['stall'])

    def test_names_on_group_and_guild_actions_are_never_shown(self):
        bots, coverage = vanilla.read(self.write(
            row(action='AcceptInvitationAction', info1='Realplayer', info2='2'),
            row(stamp='2026-11-09 19:27:41', action='GuildAcceptAction', info1='Secret Guild', info2='16'),
            row(stamp='2026-11-09 19:27:42', action='UseHearthStoneAction', info1='', info2='move long stuck'),
            row(stamp='2026-11-09 19:27:43', action='UseHearthStoneAction', info1='', info2='free text here')))
        self.assertEqual((coverage['records'], coverage['omitted']), (4, 0))
        text = json.dumps(bots)
        self.assertNotIn('Realplayer', text)
        self.assertNotIn('Secret Guild', text)
        self.assertNotIn('free text here', text)
        self.assertEqual(bots[0]['hearthStuck'], {'move long stuck': 1})
        self.assertEqual([event['detail'] for event in bots[0]['events']], [None, 'move long stuck', None, None])

    def test_malformed_rows_are_omitted_and_never_echoed(self):
        good = row()
        bad = [b'not,a,row\n',
               row(stamp='2026-13-09 19:27:40'),                 # month 13
               row(name='Bad Name'), row(name='x' * 13),
               row(action='attack'), row(point='POINT(1 2 3)'), row(race='0'), row(klass='x'), row(level='0.5'),
               row(level='999'), good[:-1] + b',extra\n', b'\xff\xfe' + good, good[:-1] + b'\x07\n',
               b'x' * (vanilla.MAX_LINE + 1) + b'\n']
        bots, coverage = vanilla.read(self.write(good, *bad))
        self.assertEqual((coverage['records'], coverage['omitted']), (1, len(bad)))
        self.assertEqual(len(bots), 1)
        self.assertNotIn('Bad Name', json.dumps([bots, coverage]))
        # A game-object name that does not fit the pattern is dropped; the row still counts.
        bots, coverage = vanilla.read(self.write(row(info1='<script>alert(1)</script>')))
        self.assertEqual((coverage['records'], bots[0]['events'][0]['detail']), (1, None))

    def test_off_unavailable_and_path_rules(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(vanilla.read()[1]['status'], 'Off')
        with patch.dict(os.environ, {vanilla.ENV: self.write(row())}):
            self.assertEqual(vanilla.read()[1]['status'], 'Loaded')
        for path in ('relative.csv', str(Path(self.temp.name) / 'missing.csv'), self.temp.name, 7):
            bots, coverage = vanilla.read(path)
            self.assertEqual((bots, coverage['status'], coverage['omitted']), ([], 'Unavailable', None), path)
        link = Path(self.temp.name) / 'link.csv'
        link.symlink_to(self.write(row()))
        self.assertIn('symlink refused', vanilla.read(str(link))[1]['reason'])
        empty = Path(self.temp.name) / 'empty.csv'
        empty.write_bytes(b'')
        bots, coverage = vanilla.read(str(empty))
        self.assertEqual((bots, coverage['status'], coverage['records']), ([], 'Loaded', 0))


if __name__ == '__main__':
    unittest.main()
