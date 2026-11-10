"""vanilla_botlog: the cmangos-classic playerbot event CSV. Offline, strict, never echoes a bad row."""
import csv
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
RELEASE_J = FIXTURE.parent / 'vanilla-bot_events-release-j-20261109T2127Z.csv'
RELEASE_J_SHA256 = '3e2e82b583feac2a854085acbc037bbdc6dcf755bfff4af53fcb3f6a0ce7d673'
RELEASE_K = FIXTURE.parent / 'vanilla-bot_events-release-k-20261109T2219Z.csv'
RELEASE_K_SHA256 = '1fcc50b793dae1ff83acf8f87bad2cb57c98203086f805c44cdb59f6417c93c6'


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

    def assert_no_continuity_metadata_or_rejected_content(self, result):
        self.assertNotIn('REJECTED_OWNER_DATA', json.dumps(result))
        def check(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertNotIn('segment', key.lower(), 'internal continuity markers must not be projected')
                    check(child)
            elif isinstance(value, (list, tuple)):
                for child in value:
                    check(child)
        check(result)

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
        self.assertEqual((coverage['stalledSharePct'], coverage['longestStall']), (36.6, 562))
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

    def test_release_j_run_shows_the_one_spot_loop_fixed(self):
        # cmangos-classic export after the fix (playerbots b893cfe9, release-20261109j), 21:27:48Z-22:00:48Z, copied
        # byte for byte (CRLF line ends; field 8 already blank on the 115 group and guild rows).
        raw = RELEASE_J.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), RELEASE_J_SHA256)
        bots, coverage = vanilla.read(str(RELEASE_J))
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['bots']), (4149, 0, 449))
        self.assertEqual((coverage['pulls'], coverage['kills'], coverage['stalledBots'], coverage['stalledPulls'],
                          coverage['stalledSharePct'], coverage['longestStall'], coverage['hearthStuck']),
                         (1524, 1093, 2, 72, 4.7, 37, 89))
        # The two runs left are other mechanisms: a burst of pull rows from one spot, and a bot that keeps walking.
        self.assertEqual([(bot['name'], bot['stall']['pulls'], bot['stall']['target'], bot['stall']['positions'])
                          for bot in bots[:2]],
                         [('Uywen', 37, 'Crag Boar', 6), ('Ohny', 35, 'Burning Blade Apprentice', 35)])
        self.assertIsNone(bots[2]['stall'])
        # The bots stuck before the fix are free in this run.
        rows = [vanilla._row(line.rstrip(b'\r')) for line in raw.split(b'\n') if line]
        tohsha = [row for row in rows if row['name'] == 'Tohsha']
        self.assertEqual((sum(row['action'] == vanilla.PULL for row in tohsha),
                          sum(row['action'] == vanilla.KILL for row in tohsha)), (34, 25))

    def test_release_k_export_keeps_only_one_qualifying_run(self):
        raw = RELEASE_K.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), RELEASE_K_SHA256)
        social = {'AcceptInvitationAction', 'LeaveGroupAction', 'GuildAcceptAction',
                  'GuildLeaveAction', 'AcceptQuestShareAction'}
        redacted = [fields for fields in csv.reader(raw.decode('ascii').splitlines()) if fields[2] in social]
        self.assertEqual(len(redacted), 120)
        self.assertTrue(all(fields[7] == '' for fields in redacted))
        bots, coverage = vanilla.read(str(RELEASE_K))
        self.assertEqual((coverage['status'], coverage['records'], coverage['omitted'], coverage['bots']),
                         ('Loaded', 4261, 0, 473))
        self.assertEqual((coverage['from'], coverage['to']), ('2026-11-09T22:20:20Z', '2026-11-09T22:52:28Z'))
        self.assertEqual((coverage['pulls'], coverage['kills'], coverage['stalledBots'], coverage['stalledPulls'],
                          coverage['stalledSharePct'], coverage['longestStall'], coverage['hearthStuck']),
                         (1617, 1264, 1, 14, 0.9, 14, 90))
        self.assertEqual((bots[0]['name'], bots[0]['stall']['target'], bots[0]['stall']['pulls'],
                          bots[0]['stall']['positions'], bots[0]['stall']['seconds']),
                         ('Chardan', 'Defias Thug', 14, 12, 507))
        self.assertTrue(all(bot['stall'] is None for bot in bots[1:]))

    def test_release_j_comparison_uses_the_release_k_duration(self):
        # First J timestamp 21:27:48 + K's 1928 seconds, with an inclusive endpoint.
        cutoff = b'2026-11-09 21:59:56+00'
        window = [line for line in RELEASE_J.read_bytes().splitlines(keepends=True)
                  if line.partition(b',')[0] <= cutoff]
        _, coverage = vanilla.read(self.write(*window))
        self.assertEqual((coverage['records'], coverage['bots'], coverage['pulls'], coverage['kills']),
                         (3988, 443, 1458, 1050))
        self.assertEqual((coverage['stalledBots'], coverage['stalledPulls'], coverage['stalledSharePct'],
                          coverage['longestStall']), (2, 62, 4.3, 37))
        self.assertEqual(round(coverage['pulls'] / coverage['kills'], 2), 1.39)

    def test_a_loot_row_ends_a_run_like_a_kill(self):
        rows = [row(stamp=f'2026-11-09 19:00:{i:02d}', info1='Crag Boar') for i in range(8)]
        rows.append(row(stamp='2026-11-09 19:00:10', action='StoreLootAction', info1='Chunk of Boar Meat', info2='769'))
        rows += [row(stamp=f'2026-11-09 19:00:{i:02d}', info1='Crag Boar') for i in range(20, 28)]
        bot = vanilla.read(self.write(*rows))[0][0]
        self.assertEqual((bot['pulls'], bot['kills'], bot['stall']), (16, 0, None))  # two runs of 8, not one of 16

    def test_unknown_targets_do_not_create_or_join_stalls(self):
        rows = [row(stamp=f'2026-11-09 19:00:{i:02d}') for i in range(6)]
        rows += [row(stamp=f'2026-11-09 19:00:{i:02d}', info1='') for i in range(6, 18)]
        rows += [row(stamp=f'2026-11-09 19:00:{i:02d}') for i in range(18, 24)]
        rows += [row(stamp=f'2026-11-09 19:00:{i:02d}', info1='<invalid>') for i in range(24, 36)]
        bots, coverage = vanilla.read(self.write(*rows))
        self.assertEqual((bots[0]['pulls'], bots[0]['stall'], coverage['stalledBots'], coverage['stalledPulls']),
                         (36, None, 0, 0))

    def test_malformed_row_prevents_joining_two_short_pull_runs(self):
        before = [row(stamp=f'2026-11-09 19:00:{i:02d}') for i in range(6)]
        after = [row(stamp=f'2026-11-09 19:00:{i:02d}') for i in range(10, 16)]
        result = vanilla.read(self.write(*before, b'REJECTED_OWNER_DATA,invalid,row\n', *after))
        bots, coverage = result
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['pulls']), (12, 1, 12))
        self.assertEqual((bots[0]['pulls'], bots[0]['counts']['AttackAnything'], len(bots[0]['events'])), (12, 12, 12))
        self.assertIsNone(bots[0]['stall'])
        self.assertEqual((coverage['stalledBots'], coverage['stalledPulls'], coverage['longestStall']), (0, 0, 0))
        self.assert_no_continuity_metadata_or_rejected_content(result)

    def test_malformed_row_keeps_separate_genuine_pull_runs_and_their_totals(self):
        before = [row(stamp=f'2026-11-09 19:00:{i:02d}') for i in range(12)]
        after = [row(stamp=f'2026-11-09 19:00:{i:02d}') for i in range(20, 32)]
        result = vanilla.read(self.write(*before, b'REJECTED_OWNER_DATA,invalid,row\n', *after))
        bots, coverage = result
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['pulls']), (24, 1, 24))
        self.assertEqual((bots[0]['stall']['pulls'], bots[0]['stalledPulls'], len(bots[0]['events'])), (12, 24, 24))
        self.assertEqual((coverage['stalledBots'], coverage['stalledPulls'], coverage['longestStall']), (1, 24, 12))
        self.assert_no_continuity_metadata_or_rejected_content(result)

    def test_omitted_row_with_unusable_identity_breaks_continuity_for_every_bot(self):
        names = ('Estellene', 'Otherbot')
        before = [row(stamp=f'2026-11-09 19:00:{i:02d}', name=name) for i in range(6) for name in names]
        after = [row(stamp=f'2026-11-09 19:00:{i:02d}', name=name) for i in range(10, 16) for name in names]
        unknown_bot = row(stamp='2026-11-09 19:00:08', name='Bad Name', info1='REJECTED_OWNER_DATA')
        result = vanilla.read(self.write(*before, unknown_bot, *after))
        bots, coverage = result
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['bots']), (24, 1, 2))
        self.assertEqual({bot['name']: bot['pulls'] for bot in bots}, {name: 12 for name in names})
        self.assertTrue(all(bot['stall'] is None and len(bot['events']) == 12 for bot in bots))
        self.assertEqual((coverage['stalledBots'], coverage['stalledPulls']), (0, 0))
        self.assert_no_continuity_metadata_or_rejected_content(result)

    def test_timestamp_sorting_does_not_rejoin_runs_across_an_omitted_row(self):
        for first, second in ((range(20, 26), range(6)), (range(0, 12, 2), range(1, 12, 2))):
            with self.subTest(first=list(first), second=list(second)):
                before = [row(stamp=f'2026-11-09 19:00:{i:02d}') for i in first]
                after = [row(stamp=f'2026-11-09 19:00:{i:02d}') for i in second]
                result = vanilla.read(self.write(*before, b'REJECTED_OWNER_DATA,invalid,row\n', *after))
                bots, coverage = result
                self.assertEqual((coverage['records'], coverage['omitted'], coverage['pulls']), (12, 1, 12))
                self.assertIsNone(bots[0]['stall'])
                self.assertEqual((coverage['stalledBots'], coverage['stalledPulls']), (0, 0))
                self.assert_no_continuity_metadata_or_rejected_content(result)

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
        self.assertEqual((bots, coverage['status'], coverage['records'], coverage['omitted']), ([], 'Loaded', 0, 0))


if __name__ == '__main__':
    unittest.main()
