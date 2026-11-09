"""Offline FFXI Bots V2 log import: off by default, strict lines, repeats counted, owners masked, nothing raised."""
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import stat
import tempfile
import unittest
from unittest.mock import patch

import ffxi_botsv2_log as botsv2

FIXTURE = Path(__file__).resolve().parent / 'fixtures/ffxi-botsv2'
REAL = FIXTURE / 'bots-v2-20261109.log'
SYNTHETIC = FIXTURE / 'synthetic-edge-cases.log'
REAL_SHA256 = 'b11459411b1062573eca7beb2cacb19d7031fe60e1e39b1247df54df194647bb'
REAL_LINES = 382
C28 = FIXTURE / 'bots-v2-c28-20261109.log'
C281 = FIXTURE / 'bots-v2-c281-20261109.log'
C281_SHA256 = 'a53acf46d5076eaaf1b83690237e4081825f2169ae6baeedf4e661139a0185cc'
C291 = FIXTURE / 'bots-v2-c291-20261109.log'
C291_SHA256 = '4c4a1093dedce6055e3f4e44f6cd8122cea5903cfac23b16f14e6319094b044b'
C2101 = FIXTURE / 'bots-v2-c2101-20261109.log'
C2101_SHA256 = 'ce90dc67feb82b5a46cbe6abf3608b3cd88c113ccb31f5d61e7f3dc20105234b'
J0B = FIXTURE / 'bots-v2-j0b-20261109.log'
J0B_SHA256 = '027b96d5a05459815e301cba85fb82d1f32d7cedfed2b883c9323874973b7c01'
J1234 = FIXTURE / 'bots-v2-j1234-20261109.log'
J1234_SHA256 = 'fb7b289b4e59bdbe5ab562bdcf4e770d39c8006debf5e0d74a53e5b1f9ec4cd6'
C28_SHA256 = 'be2eea13e43c196a06bef51cc580b9a4ff2bbde6ede624eb7cb608b03a1740fc'

# Expected values come from grep over REAL, not from the parser. Recipe for bot B (run with the export as FILE):
#   ok        grep "[BOTS-V2] act B " FILE | grep -c -- "-> ok "
#   refused   L = grep "[BOTS-V2] act B " FILE | grep -c -- "-> refused "; R = the repeated tails of those lines
#             (grep -o "repeated [0-9]* times" | awk sum); refused = L + R, since a tail line is 1 + N
#   defend    grep -c "[BOTS-V2] defend B " FILE
#   tripStart grep "[BOTS-V2] trip start group " FILE | grep -c "B"
#   tripEnd   grep -c "[BOTS-V2] trip end B " FILE
#   noTrip    grep -c "[BOTS-V2] no trip B " FILE
#   party     grep -c "[BOTS-V2] B: owner \\|[BOTS-V2] B owned by " FILE
#   other     grep -c "[BOTS-V2] owns B \\|[BOTS-V2] zone danger B " FILE
#   events    every bot line naming B: act, defend, owns, trip, no trip, zone danger, owner lines, trip start group
REAL_COUNTS = {
    'fumika': {'ok': 109, 'refused': 10, 'defend': 3, 'tripStart': 1, 'tripEnd': 2, 'noTrip': 1, 'stuck': 0,
               'dead': 0, 'release': 0, 'return': 0, 'weak': 0, 'rest': 0, 'mount': 0, 'advice': 0, 'party': 5, 'other': 2},
    'shadowtail': {'ok': 64, 'refused': 1, 'defend': 1, 'tripStart': 1, 'tripEnd': 2, 'noTrip': 2, 'stuck': 0,
                   'dead': 0, 'release': 0, 'return': 0, 'weak': 0, 'rest': 0, 'mount': 0, 'advice': 0, 'party': 6, 'other': 2},
    'tomoe': {'ok': 90, 'refused': 1, 'defend': 2, 'tripStart': 1, 'tripEnd': 2, 'noTrip': 1, 'stuck': 0,
              'dead': 0, 'release': 0, 'return': 0, 'weak': 0, 'rest': 0, 'mount': 0, 'advice': 0, 'party': 0, 'other': 3},
}
REAL_EVENTS = {'fumika': 127, 'shadowtail': 79, 'tomoe': 100}
REAL_REFUSALS = {'fumika': 4, 'shadowtail': 1, 'tomoe': 1}
REAL_IDS = {'fumika': (1050162, 241), 'shadowtail': (1040292, 241), 'tomoe': (1050143, 241)}
REAL_LAST = {'fumika': ('2026-11-09T04:23:21.034Z', 'party owner_left_zone'),
             'shadowtail': ('2026-11-09T04:23:21.034Z', 'party owner_left_zone'),
             'tomoe': ('2026-11-09T04:13:08.903Z', 'tripEnd home')}


def _lines(raw):
    return raw.count(b'\n')  # Every fixture ends with a newline, so this is the line count.


class FFXIBotsV2LogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, raw):
        path = self.root / name
        path.write_bytes(raw)
        return path

    def line(self, body, stamp='11/09/26 05:10:00:000'):
        return f'[{stamp}][map][lua] [BOTS-V2] {body} (lua_print:228)\n'.encode('utf-8', 'surrogateescape')

    def assertConserved(self, coverage, total):
        parts = (coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['ignored'])
        self.assertEqual(sum(parts), total, coverage)

    # Real export

    def test_real_export_is_the_verified_copy(self):
        raw = REAL.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), REAL_SHA256)
        self.assertEqual(_lines(raw), REAL_LINES)

    def test_real_export_coverage_is_exact(self):
        bots, coverage = botsv2.read(REAL)
        self.assertEqual(coverage['status'], 'Loaded')
        self.assertEqual(coverage['records'], REAL_LINES)
        self.assertEqual(coverage['omitted'], 0)
        self.assertEqual(coverage['unrecognized'], 0)
        self.assertEqual(coverage['ignored'], 0)
        self.assertEqual((coverage['budget'], coverage['system']), (69, 9))
        self.assertEqual(coverage['from'], '2026-11-09T01:12:51.704Z')
        self.assertEqual(coverage['to'], '2026-11-09T04:23:57.203Z')
        self.assertConserved(coverage, REAL_LINES)
        self.assertEqual([b['actorId'] for b in bots], ['fumika', 'shadowtail', 'tomoe'])

    def test_real_export_per_bot_counts_and_identity(self):
        bots, _ = botsv2.read(REAL)
        by_id = {b['actorId']: b for b in bots}
        for name, counts in REAL_COUNTS.items():
            with self.subTest(bot=name):
                bot = by_id[name]
                self.assertEqual(bot['game'], 'ffxi-lsb')
                self.assertEqual(bot['counts'], counts)
                self.assertEqual((bot['charId'], bot['zoneId']), REAL_IDS[name])
                self.assertEqual(len(bot['events']), REAL_EVENTS[name])
                self.assertEqual(len(bot['refusals']), REAL_REFUSALS[name])
                self.assertEqual(bot['deaths'], [])
                self.assertEqual((bot['lastEventAt'], bot['doing']), REAL_LAST[name])

    def test_real_export_repeated_refusal_counts_printed_line_plus_held(self):
        bots, _ = botsv2.read(REAL)
        fumika = next(b for b in bots if b['actorId'] == 'fumika')
        # Independent grep: 4 'refused' lines for fumika, one of them with 'repeated 6 times'.
        # The printed tail is 1 + 6 occurrences, so 3 plain + 7 = 10.
        self.assertEqual(sum(1 for line in REAL.read_text().splitlines()
                             if '[BOTS-V2] act fumika ' in line and '-> refused ' in line), 4)
        repeated = next(e for e in fumika['refusals'] if e['repeated'] == 6)
        self.assertEqual((repeated['reason'], repeated['detail']), ('ws', 'wsId=18 targetId=17264690 sc=solo'))
        self.assertEqual(fumika['counts']['refused'], 10)

    def test_event_and_refusal_caps_with_out_of_order_lines(self):
        # 250 refusals for one bot, one per second; lines 10/11 and 100/101 are written out of order.
        order = list(range(250))
        order[10], order[11] = order[11], order[10]
        order[100], order[101] = order[101], order[100]
        raw = b''.join(self.line(f'act capbot rule=travel apl=- op=path -> refused path_not_found dist={i}',
                                 stamp=f'11/09/26 06:{i // 60:02d}:{i % 60:02d}:000') for i in order)
        bots, coverage = botsv2.read(self.write('caps.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted']), (250, 0))
        bot = bots[0]
        self.assertEqual(bot['counts']['refused'], 250)  # counts are not capped
        self.assertEqual(len(bot['events']), botsv2.MAX_EVENTS)
        self.assertEqual(bot['events'][0]['detail'], 'dist=249')
        self.assertEqual(bot['events'][-1]['detail'], 'dist=50')  # the oldest 50 are dropped
        self.assertEqual(len(bot['refusals']), botsv2.MAX_REFUSALS)
        self.assertEqual(bot['refusals'][0]['detail'], 'dist=249')
        self.assertEqual(bot['lastEventAt'], '2026-11-09T06:04:09.000Z')
        stamps = [e['ts'] for e in bot['events']]
        self.assertEqual(stamps, sorted(stamps, reverse=True))

    def test_real_export_totals_match_grep(self):
        bots, _ = botsv2.read(REAL)
        self.assertEqual(sum(b['counts']['ok'] for b in bots), 263)  # grep -c -- '-> ok ' on the export
        self.assertEqual(sum(b['counts']['refused'] for b in bots), 12)  # 6 refused lines + 6 held repeats

    def test_real_export_events_are_newest_first_and_bounded(self):
        bots, _ = botsv2.read(REAL)
        for bot in bots:
            with self.subTest(bot=bot['actorId']):
                stamps = [e['ts'] for e in bot['events']]
                self.assertEqual(stamps, sorted(stamps, reverse=True))
                self.assertLessEqual(len(bot['events']), botsv2.MAX_EVENTS)
                self.assertEqual(bot['events'][0]['ts'], bot['lastEventAt'])
                self.assertTrue(all(e['result'] == 'refused' for e in bot['refusals']))

    def test_real_export_owner_is_always_masked(self):
        bots, _ = botsv2.read(REAL)
        text = json.dumps(bots)
        self.assertIn('owner=<owner>', text)
        self.assertNotIn('Bobby', text)
        for token in text.split('owner=')[1:]:
            self.assertTrue(token.startswith('<owner>'), token[:20])

    def test_real_export_apl_is_optional_and_percent_free(self):
        bots, _ = botsv2.read(REAL)
        text = json.dumps(bots)
        self.assertNotIn('%%', text)
        shadow = next(b for b in bots if b['actorId'] == 'shadowtail')
        unstick = [e for e in shadow['events'] if e['rule'] == 'unstick']
        self.assertTrue(unstick)
        self.assertTrue(all(e['apl'] is None for e in unstick))

    # Synthetic edge cases

    def test_synthetic_coverage_is_exact(self):
        _, coverage = botsv2.read(SYNTHETIC)
        self.assertEqual(coverage['status'], 'Loaded')
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['ignored']),
                         (34, 10, 1, 2))
        self.assertEqual((coverage['budget'], coverage['system']), (1, 3))
        self.assertEqual(coverage['from'], '2026-11-09T05:00:00.001Z')
        self.assertEqual(coverage['to'], '2026-11-09T05:00:28.000Z')
        self.assertConserved(coverage, _lines(SYNTHETIC.read_bytes()))

    def test_synthetic_per_bot_counts(self):
        bots, _ = botsv2.read(SYNTHETIC)
        by_id = {b['actorId']: b for b in bots}
        nalu, pell = by_id['nalu'], by_id['pell']
        # refused: line 4 is 1 + 6, line 5 is 1 + 1, so 9. defend: line 7 is 1 + 3, so 4.
        self.assertEqual(nalu['counts'], {'ok': 2, 'refused': 9, 'defend': 4, 'tripStart': 1, 'tripEnd': 1,
                                          'noTrip': 0, 'stuck': 3, 'dead': 1, 'release': 1, 'return': 1,
                                          'weak': 0, 'rest': 0, 'mount': 0, 'advice': 0, 'party': 2, 'other': 4})
        self.assertEqual(pell['counts'], {'ok': 0, 'refused': 1, 'defend': 1, 'tripStart': 1, 'tripEnd': 0,
                                          'noTrip': 1, 'stuck': 0, 'dead': 0, 'release': 0, 'return': 0,
                                          'weak': 1, 'rest': 0, 'mount': 0, 'advice': 0, 'party': 3, 'other': 4})
        self.assertEqual((nalu['charId'], nalu['zoneId']), (2001, 119))
        self.assertEqual((pell['charId'], pell['zoneId']), (None, 300))
        self.assertEqual(len(nalu['events']), 19)
        self.assertEqual(len(pell['events']), 12)
        self.assertEqual(len(nalu['deaths']), 1)
        self.assertEqual(nalu['doing'], 'travel path')

    def test_synthetic_repeated_tails_add_n_plus_one_and_keep_n_in_the_event(self):
        bots, _ = botsv2.read(SYNTHETIC)
        nalu = next(b for b in bots if b['actorId'] == 'nalu')
        six = next(e for e in nalu['events'] if e['repeated'] == 6)
        self.assertEqual((six['result'], six['reason'], six['detail']), ('refused', 'path_not_found',
                                                                         'dist=289 path_long'))
        three = next(e for e in nalu['events'] if e['type'] == 'defend')
        self.assertEqual((three['repeated'], three['detail']), (3, 'hp=45pct attacker=Goblin_Mugger lv21'))
        self.assertEqual(nalu['counts']['defend'], 4)

    def test_synthetic_percent_unescape_is_observable(self):
        bots, _ = botsv2.read(SYNTHETIC)
        pell = next(b for b in bots if b['actorId'] == 'pell')
        refused = next(e for e in pell['refusals'])
        self.assertEqual(refused['detail'], '50% {x}')
        text = json.dumps(bots)
        # The one refused event sits in both events and refusals: two single '%', no escaped pair left.
        self.assertEqual((text.count('50% {x}'), text.count('%')), (2, 2))
        self.assertNotIn('%%', text)

    def test_synthetic_same_millisecond_order_is_by_line(self):
        bots, _ = botsv2.read(SYNTHETIC)
        nalu = next(b for b in bots if b['actorId'] == 'nalu')
        stuck = [e for e in nalu['events'] if e['type'] == 'stuck']
        # events are newest first: the later line of the same millisecond comes first.
        self.assertEqual([e['ts'] for e in stuck], ['2026-11-09T05:00:06.000Z', '2026-11-09T05:00:05.000Z',
                                                    '2026-11-09T05:00:05.000Z'])
        self.assertEqual([e['reason'] for e in stuck], ['homepoint_no_move', 'human_in_view', 'walk_out'])
        self.assertEqual(nalu['doing'], 'travel path')

    def test_synthetic_c28_kinds_and_stuck_wording(self):
        bots, _ = botsv2.read(SYNTHETIC)
        nalu = next(b for b in bots if b['actorId'] == 'nalu')
        dead = next(e for e in nalu['events'] if e['type'] == 'dead')
        self.assertEqual((dead['reason'], dead['detail']), (None, 'wait_raise=60 raisers=0 zone=119'))
        self.assertEqual(nalu['deaths'][0]['ts'], dead['ts'])
        self.assertEqual(sorted(e['type'] for e in nalu['events'] if e['type'] in ('release', 'return')),
                         ['release', 'return'])

    def test_synthetic_trip_group_fans_out_to_every_named_bot(self):
        bots, _ = botsv2.read(SYNTHETIC)
        for bot in bots:
            trips = [e for e in bot['events'] if e['type'] == 'tripStart']
            self.assertEqual(len(trips), 1, bot['actorId'])
            self.assertEqual(trips[0]['detail'], 'group=nalu+pell camp=meriphataud_windurst attached')

    def test_synthetic_nil_tokens_do_not_overwrite_ids(self):
        bots, _ = botsv2.read(SYNTHETIC)
        nalu = next(b for b in bots if b['actorId'] == 'nalu')
        self.assertEqual(nalu['zoneId'], 119)
        trip_end = next(e for e in nalu['events'] if e['type'] == 'tripEnd')
        self.assertEqual(trip_end['detail'], 'camp=nil out->home zone=nil')

    def test_synthetic_owner_names_are_masked_and_bad_lines_omitted(self):
        bots, coverage = botsv2.read(SYNTHETIC)
        text = json.dumps({'bots': bots, 'coverage': coverage})
        self.assertNotIn('Bobby', text)
        pell = next(b for b in bots if b['actorId'] == 'pell')
        self.assertTrue(all('Bobby' not in e['detail'] for e in pell['events']))
        self.assertEqual(coverage['omitted'], 10)

    def test_synthetic_random_junk_never_raises_and_conserves(self):
        rng = random.Random(20261109)
        pieces = [b'[BOTS-V2] ', b'[11/09/26 04:01:58:414][map][lua] [BOTS-V2] ', b'act ', b'defend ', b' -> ok ',
                  b'%%', b'(repeated ', b'owned by ', b'\x00', b'\xff', b' ', b'trip start group ', b'owns ']
        lines = []
        for _ in range(500):
            body = b''.join(rng.choice(pieces) + bytes(rng.randrange(256) for _ in range(rng.randint(0, 30)))
                            for _ in range(rng.randint(0, 4)))
            lines.append(body.replace(b'\n', b' '))
        raw = b'\n'.join(lines) + b'\n'
        path = self.write('junk.log', raw)
        bots, coverage = botsv2.read(path)
        self.assertEqual(coverage['status'], 'Loaded')
        self.assertConserved(coverage, _lines(raw))
        json.dumps(bots)

    def test_mutated_real_lines_never_raise_and_conserve(self):
        rng = random.Random(7)
        mutated = []
        for line in REAL.read_bytes().split(b'\n')[:-1]:
            body = bytearray(line)
            for _ in range(rng.randint(1, 3)):
                index = rng.randrange(len(body))
                action = rng.randrange(3)
                if action == 0:
                    del body[index]
                elif action == 1:
                    body[index:index] = bytes([rng.randrange(256)])
                else:
                    body[index] = rng.randrange(256)
            mutated.append(bytes(body).replace(b'\n', b' '))
        raw = b'\n'.join(mutated) + b'\n'
        path = self.write('mutated.log', raw)
        bots, coverage = botsv2.read(path)
        self.assertEqual(coverage['status'], 'Loaded')
        self.assertConserved(coverage, _lines(raw))
        json.dumps(bots)

    def test_random_single_lines_never_raise(self):
        rng = random.Random(11)
        for _ in range(2000):
            raw = bytes(rng.randrange(256) for _ in range(rng.randint(0, 300)))
            status, _ = botsv2._line(raw, 1)
            self.assertIn(status, ('record', 'ignored', 'unrecognized', 'omitted'))

    # Line-level validation

    def test_bad_dates_and_timestamps_are_omitted(self):
        for stamp in ('13/40/26 25:00:00:000', '02/30/26 01:00:00:000', '11/09/26 24:00:00:000'):
            with self.subTest(stamp=stamp):
                raw = self.line('owns nalu charid=1 zone=1', stamp=stamp)
                self.assertEqual(botsv2._line(raw.rstrip(b'\n'), 1)[0], 'omitted')

    def test_invalid_utf8_or_non_ascii_bots_line_is_omitted_and_other_bytes_ignored(self):
        bad = b'[11/09/26 05:10:00:000][map][lua] [BOTS-V2] owns nalu charid=\xff zone=1\n'
        other = b'[11/09/26 05:10:00:000][map][lua] \xff\xfe unrelated\n'
        path = self.write('bytes.log', bad + other)
        _, coverage = botsv2.read(path)
        self.assertEqual((coverage['omitted'], coverage['ignored']), (1, 1))

    def test_oversized_line_is_omitted_not_read(self):
        raw = b'[11/09/26 05:10:00:000][map][lua] [BOTS-V2] ' + b'x' * (botsv2.MAX_LINE + 1) + b'\n'
        _, coverage = botsv2.read(self.write('long.log', raw))
        self.assertEqual((coverage['status'], coverage['records'], coverage['omitted']), ('Loaded', 0, 1))

    def test_unknown_bots_lines_are_unrecognized_not_errors(self):
        raw = self.line('mystery nalu x=1') + self.line('owns nalu charid=7 zone=241')
        _, coverage = botsv2.read(self.write('unknown.log', raw))
        self.assertEqual((coverage['records'], coverage['unrecognized'], coverage['omitted']), (1, 1, 0))

    def test_malformed_known_shapes_are_omitted_not_repaired(self):
        cases = ['act nalu rule=zz -> ok x', 'defend pell hp=101pct attacker=none why=x',
                 'trip start group nalu+nalu camp=x', 'owns pell charid=12x zone=1',
                 'act nalu rule=a op=b -> ok', 'owned bot pell is in zone x: not driven']
        for body in cases:
            with self.subTest(body=body):
                self.assertEqual(botsv2._line(self.line(body).rstrip(b'\n'), 1)[0], 'omitted')

    def test_repeat_count_of_zero_is_malformed(self):
        raw = self.line('act nalu rule=travel apl=- op=path -> refused path_not_found (repeated 0 times)')
        self.assertEqual(botsv2._line(raw.rstrip(b'\n'), 1)[0], 'omitted')

    def test_owner_names_other_than_mask_are_omitted(self):
        cases = ['pell owned by Bobby (joined their party)', 'pell: owner Bobby left zone 241 for 119',
                 'order follow from Bobby -> nalu', 'pell ownership by Bobby ended: left_party',
                 'pell ownership by <owner> ended: dismissed by Bobby']
        for body in cases:
            with self.subTest(body=body):
                raw = self.line(body).rstrip(b'\n')
                self.assertEqual(botsv2._line(raw, 1)[0], 'omitted')
        self.assertEqual(botsv2._line(self.line('order follow from <owner> -> nalu').rstrip(b'\n'), 1)[0], 'record')

    def test_system_and_budget_lines_are_recognized_and_budget_is_coverage_only(self):
        raw = (self.line('budget 60s: windows=8 evals=9 deferred=0 maxMs=3.600 avgMs=0.753 budgetMs=10.0')
               + self.line('tell orders wired (chained before the existing handler)')
               + self.line('tick host live in zone 115'))
        bots, coverage = botsv2.read(self.write('system.log', raw))
        self.assertEqual(bots, [])
        self.assertEqual((coverage['records'], coverage['budget'], coverage['system']), (3, 1, 2))

    def test_non_bots_lines_are_ignored_and_counted(self):
        raw = b'[11/09/26 05:10:00:000][map][lua] something else\n\n' + self.line('owns nalu charid=7 zone=241')
        _, coverage = botsv2.read(self.write('ignored.log', raw))
        self.assertEqual((coverage['ignored'], coverage['records']), (2, 1))

    def test_bot_count_is_capped_and_says_so(self):
        raw = b''.join(self.line(f'owns bot{i:03d} charid={i} zone=241') for i in range(botsv2.MAX_BOTS + 1))
        bots, coverage = botsv2.read(self.write('many.log', raw))
        self.assertEqual(len(bots), botsv2.MAX_BOTS)
        self.assertIn(f'Showing the first {botsv2.MAX_BOTS} of {botsv2.MAX_BOTS + 1} bots', coverage['reason'])

    # Producer-exact tails, c2.8 kinds and stuck shapes

    def test_producer_tail_counts_the_printed_line_and_its_held_repeats(self):
        # banshee_bots_v2_exec.lua and test_travel_fix.lua (c2.7): six identical refusals at 1000..6000 ms and one at
        # 32000 ms. The producer prints the first, holds five, then prints the seventh with '(repeated 5 times'.
        # Seven calls, so seven counted. The defend tail is the same rule: the printed line plus three held.
        raw = (self.line('act pell rule=travel apl=- op=path -> refused path_not_found dist=289 path_long',
                         stamp='11/09/26 05:10:01:000')
               + self.line('act pell rule=travel apl=- op=path -> refused path_not_found dist=289 path_long '
                           '(repeated 5 times in the last 31s)', stamp='11/09/26 05:10:32:000')
               + self.line('defend pell hp=50pct attacker=Goblin_Mugger lv21 why=fight_back (repeated 3 times)',
                           stamp='11/09/26 05:10:40:000'))
        bots, coverage = botsv2.read(self.write('producer-tails.log', raw))
        self.assertConserved(coverage, 3)
        pell = bots[0]
        self.assertEqual((pell['counts']['refused'], pell['counts']['defend']), (7, 4))
        self.assertEqual([e['repeated'] for e in pell['events'] if e['type'] == 'act'], [5, 1])
        self.assertEqual(pell['refusals'][0]['repeated'], 5)

    def test_c28_kinds_use_their_exact_producer_formats(self):
        raw = b''.join([
            self.line('dead nalu wait_raise=60 raisers=1 zone=119', stamp='11/09/26 05:11:00:000'),
            self.line('release nalu why=no_raise zone=119 after 30s', stamp='11/09/26 05:11:01:000'),
            self.line('release nalu why=nil zone=nil after 4s', stamp='11/09/26 05:11:02:000'),
            self.line('weak nalu resting', stamp='11/09/26 05:11:03:000'),
            self.line('return nalu gave up why=refused_road after 40s', stamp='11/09/26 05:11:04:000'),
            self.line('return nalu arrived zone=119 after 12s', stamp='11/09/26 05:11:05:000'),
            self.line('return nalu to owner zone=241 from=119', stamp='11/09/26 05:11:06:000'),
            self.line('revived nalu at its home point zone=241 after 90s', stamp='11/09/26 05:11:07:000'),
            self.line('revived nalu raised zone=nil after 5s', stamp='11/09/26 05:11:08:000'),
        ])
        bots, coverage = botsv2.read(self.write('c28.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized']), (9, 0, 0))
        nalu = bots[0]
        self.assertEqual(nalu['counts'], {'ok': 0, 'refused': 0, 'defend': 0, 'tripStart': 0, 'tripEnd': 0,
                                          'noTrip': 0, 'stuck': 0, 'dead': 1, 'release': 2, 'return': 3, 'weak': 1, 'rest': 0, 'mount': 0, 'advice': 0,
                                          'party': 0, 'other': 0})
        chronological = list(reversed(nalu['events']))
        self.assertEqual([e['type'] for e in chronological],
                         ['dead', 'release', 'release', 'weak', 'return', 'return', 'return', 'revived', 'revived'])
        self.assertEqual([e['reason'] for e in chronological if e['type'] == 'release'], ['no_raise', None])
        self.assertEqual([e['reason'] for e in chronological if e['type'] == 'revived'], ['home_point', 'raised'])
        self.assertEqual(nalu['zoneId'], 241)
        self.assertEqual(nalu['doing'], 'revived raised')

    def test_live_c28_export_is_fully_recognized(self):
        # Export 2 (ffxi handoff 2026-11-09-botsv2-log-export-2): the live c2.8 run, 07:15Z-08:13Z, no human online.
        raw = C28.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), C28_SHA256)
        self.assertEqual(_lines(raw), 377)
        bots, coverage = botsv2.read(C28)
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['ignored']),
                         (375, 0, 0, 2))
        by = {bot['name']: bot for bot in bots}
        self.assertEqual(set(by), {'fumika', 'shadowtail', 'tomoe'})
        # grep "[BOTS-V2] act B " FILE | grep -c -- "-> ok " (no repeated tails in this export), and so on.
        self.assertEqual({name: (b['counts']['ok'], b['counts']['refused'], b['counts']['defend'], b['counts']['rest'])
                          for name, b in by.items()},
                         {'fumika': (109, 0, 1, 0), 'shadowtail': (77, 1, 1, 1), 'tomoe': (112, 0, 0, 0)})
        rests = [(e['type'], e['reason'], e['detail']) for e in reversed(by['shadowtail']['events'])
                 if e['type'] in ('rest', 'restEnd')]
        self.assertEqual(rests, [('rest', 'mp', 'mp=44 hp=100'), ('restEnd', 'full', 'mp=100 hp=100')])
        self.assertNotIn(b'Blizz', raw)

    def test_rest_lines_use_the_exact_c28_formats(self):
        raw = b''.join([
            self.line('rest nalu why=mp mp=44 hp=100', stamp='11/09/26 05:13:00:000'),
            self.line('rest end nalu mp=100 hp=100 why=full', stamp='11/09/26 05:13:01:000'),
            self.line('rest end why=hp mp=-1 hp=30', stamp='11/09/26 05:13:02:000'),  # a bot named 'end'
            self.line('rest nalu mp=44 hp=100', stamp='11/09/26 05:13:03:000'),  # no why=
            self.line('rest end nalu mp=100 why=full', stamp='11/09/26 05:13:04:000'),  # no hp=
            self.line('rest nalu why=mp mp=1000 hp=100', stamp='11/09/26 05:13:05:000'),  # mp too long
        ])
        bots, coverage = botsv2.read(self.write('rest.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized']), (3, 3, 0))
        by = {bot['name']: bot for bot in bots}
        self.assertEqual(by['nalu']['counts']['rest'], 1)
        self.assertEqual([e['type'] for e in reversed(by['nalu']['events'])], ['rest', 'restEnd'])
        self.assertEqual(by['end']['counts']['rest'], 1)

    def test_c29_order_and_levelsync_use_the_exact_formats(self):
        # Templates from ffxi handoff 2026-11-09-botsv2-c2.9-frozen (banshee_bots_v2.lua:781/788/816/821/1426).
        raw = b''.join([
            self.line('order nalu verb=stance arg=defensive by=<owner> channel=party', stamp='11/09/26 10:30:00:000'),
            self.line('order nalu verb=rally by=<owner> channel=tell', stamp='11/09/26 10:30:01:000'),
            self.line('order nalu verb=focusheal arg=Bobby by=<owner> channel=party', stamp='11/09/26 10:30:02:000'),
            self.line('order nalu verb=focusheal arg=<owner> by=<owner> channel=party', stamp='11/09/26 10:30:03:000'),
            self.line('order follow from <owner> -> nalu', stamp='11/09/26 10:30:04:000'),
            self.line('order nalu verb=focusheal arg=off by=<owner> channel=tell', stamp='11/09/26 10:30:04:500'),
            self.line('levelsync nalu to=20 from=26', stamp='11/09/26 10:30:05:000'),
            self.line('levelsync nalu off why=left_party', stamp='11/09/26 10:30:06:000'),
            self.line('levelsync nalu off why=external cur=20', stamp='11/09/26 10:30:07:000'),
            self.line('levelsync off: entity:levelRestriction is not bound (gated off)', stamp='11/09/26 10:30:08:000'),
            self.line('act nalu rule=order_flee apl=- op=path -> ok path', stamp='11/09/26 10:30:09:000'),
            self.line('defend nalu hp=90pct attacker=Goblin_Ambusher lv17 why=passive_to_owner',
                      stamp='11/09/26 10:30:10:000'),
        ])
        bots, coverage = botsv2.read(self.write('c29.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['system']),
                         (12, 0, 0, 1))
        nalu = bots[0]
        self.assertEqual((nalu['counts']['party'], nalu['counts']['other'], nalu['counts']['ok'],
                          nalu['counts']['defend']), (6, 3, 1, 1))
        chronological = list(reversed(nalu['events']))
        self.assertEqual([(e['reason'], e['detail']) for e in chronological if e['type'] == 'party'],
                         [('stance', 'arg=defensive by=<owner> channel=party'), ('rally', 'by=<owner> channel=tell'),
                          ('focusheal', 'arg=<member> by=<owner> channel=party'),
                          ('focusheal', 'arg=<owner> by=<owner> channel=party'), ('follow', 'from=<owner>'),
                          ('focusheal', 'arg=off by=<owner> channel=tell')])
        self.assertEqual([(e['reason'], e['detail']) for e in chronological if e['type'] == 'levelsync'],
                         [('on', 'to=20 from=26'), ('off', 'why=left_party'), ('off_external', 'cur=20')])
        self.assertNotIn('Bobby', json.dumps(bots))

    def test_c29_near_misses_are_omitted_not_guessed(self):
        cases = ['order nalu verb=hold by=Bobby channel=party',          # by= is not the masked owner
                 'order nalu verb=hold channel=party',                   # no by=
                 'order nalu verb=hold by=<owner>',                      # no channel=
                 'order nalu verb=Stance by=<owner> channel=party',      # verb is not lower case
                 'levelsync nalu to=20',                                 # no from=
                 'levelsync nalu off',                                   # no why=
                 'levelsync nalu to=x from=26']                          # not digits
        for body in cases:
            with self.subTest(body=body):
                self.assertEqual(botsv2._line(self.line(body).rstrip(b'\n'), 1)[0], 'omitted')

    def test_live_death_lines_reported_by_ffxi_parse(self):
        # Exact live lines from ffxi's report (11-09 10:08-10:09Z, c2.8 code on c2.8.1); export 3 will carry them.
        raw = b''.join([
            self.line('dead fumika wait_raise=30 raisers=0 zone=119', stamp='11/09/26 10:08:42:000'),
            self.line('act fumika rule=dead_wait apl=- op=release reason=solo -> ok release',
                      stamp='11/09/26 10:09:13:000'),
            self.line('release fumika why=solo zone=119 after 30s', stamp='11/09/26 10:09:13:100'),
            self.line('revived fumika at its home point zone=241 after 33s', stamp='11/09/26 10:09:15:000'),
            self.line('dead tomoe wait_raise=30 raisers=0 zone=119', stamp='11/09/26 10:09:11:000'),
            self.line('release tomoe why=solo zone=119 after 31s', stamp='11/09/26 10:09:42:000'),
            self.line('revived tomoe at its home point zone=241 after 34s', stamp='11/09/26 10:09:45:000'),
        ])
        bots, coverage = botsv2.read(self.write('death-live.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized']), (7, 0, 0))
        by = {bot['name']: bot for bot in bots}
        self.assertEqual({n: (b['counts']['dead'], b['counts']['release']) for n, b in by.items()},
                         {'fumika': (1, 1), 'tomoe': (1, 1)})
        self.assertEqual([(e['type'], e['reason']) for e in reversed(by['tomoe']['events'])],
                         [('dead', None), ('release', 'solo'), ('revived', 'home_point')])
        self.assertEqual(by['fumika']['zoneId'], 241)

    def test_live_c281_export_has_the_death_recovery(self):
        # Export 3 (ffxi handoff 2026-11-09-botsv2-log-export-3): the live c2.8.1 run, 09:26Z-10:27Z, no human online.
        raw = C281.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), C281_SHA256)
        self.assertEqual(_lines(raw), 436)
        bots, coverage = botsv2.read(C281)
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['ignored']),
                         (436, 0, 0, 0))
        by = {bot['name']: bot for bot in bots}
        # grep "[BOTS-V2] act B " FILE | grep -c -- "-> ok "; grep -c "[BOTS-V2] dead B "; grep -c "[BOTS-V2] release B "
        self.assertEqual({n: (b['counts']['ok'], b['counts']['dead'], b['counts']['release']) for n, b in by.items()},
                         {'fumika': (89, 1, 1), 'shadowtail': (119, 0, 0), 'tomoe': (126, 1, 1)})
        lines = raw.decode('ascii').splitlines()
        self.assertIn('dead fumika wait_raise=30 raisers=0 zone=119', lines[349])
        self.assertIn('revived tomoe at its home point zone=241 after 34s', lines[371])
        self.assertNotIn(b'Blizz', raw)

    def test_live_c291_export_rests_dies_and_never_unsticks(self):
        # Export 4 (ffxi handoff 2026-11-09-botsv2-log-export-4): the live c2.9.1 run, 10:29Z-11:29Z, no human online.
        raw = C291.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), C291_SHA256)
        self.assertEqual(_lines(raw), 591)
        bots, coverage = botsv2.read(C291)
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['ignored']),
                         (591, 0, 0, 0))
        by = {bot['name']: bot for bot in bots}
        # grep -c "[BOTS-V2] rest B ", "[BOTS-V2] dead B ", and act ... -> ok (no repeated tails in this export)
        self.assertEqual({n: (b['counts']['ok'], b['counts']['rest'], b['counts']['dead'], b['counts']['release'])
                          for n, b in by.items()},
                         {'fumika': (105, 0, 1, 1), 'shadowtail': (208, 4, 1, 1), 'tomoe': (156, 4, 1, 1)})
        self.assertNotIn(b'rule=unstick', raw)  # the c2.9.1 'not a stall' fix: 0 unstick lines in this run
        lines = raw.decode('ascii').splitlines()
        self.assertIn('rest shadowtail why=mp mp=12 hp=79', lines[164])
        self.assertIn('revived fumika at its home point zone=241 after 33s', lines[439])

    def test_live_c2101_export_mounts_and_dismounts(self):
        # Export 5 (ffxi handoff 2026-11-09-botsv2-log-export-5): the live c2.10.1 run, 11:32Z-12:32Z, no human online.
        raw = C2101.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), C2101_SHA256)
        self.assertEqual(_lines(raw), 575)
        bots, coverage = botsv2.read(C2101)
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['ignored']),
                         (575, 0, 0, 0))
        by = {bot['name']: bot for bot in bots}
        # grep -c "[BOTS-V2] mount B " FILE
        self.assertEqual({n: b['counts']['mount'] for n, b in by.items()}, {'fumika': 4, 'shadowtail': 5, 'tomoe': 5})
        dismounts = sorted({e['reason'] for b in bots for e in b['events'] if e['type'] == 'dismount'})
        self.assertEqual(dismounts, ['camp', 'cast', 'group', 'native'])
        lines = raw.decode('ascii').splitlines()
        self.assertIn('mount tomoe why=travel', lines[16])
        self.assertIn('dismount fumika why=group', lines[217])

    def test_live_j0b_export_has_the_first_sub_job_moves(self):
        # Export 6 (ffxi handoff 2026-11-09-botsv2-log-export-6): the live J0b run, 12:34Z-13:35Z, no human online.
        raw = J0B.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), J0B_SHA256)
        self.assertEqual(_lines(raw), 508)
        bots, coverage = botsv2.read(J0B)
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['ignored']),
                         (508, 0, 0, 0))
        shadowtail = next(b for b in bots if b['name'] == 'shadowtail')
        self.assertEqual([e['apl'] for e in shadowtail['events'] if (e['apl'] or '').startswith('sub_')],
                         ['sub_nuke'] * 3)  # grep -c "apl=sub_" FILE
        self.assertEqual((shadowtail['counts']['dead'], shadowtail['counts']['release']), (1, 1))
        self.assertFalse(any(e['type'] in ('profile', 'advice', 'adviceRequest') for b in bots for e in b['events']))
        lines = raw.decode('ascii').splitlines()
        self.assertIn('apl=sub_nuke op=cast spellId=154', lines[151])

    def test_c210_mount_lines_use_the_exact_formats(self):
        raw = b''.join([
            self.line('mount nalu why=owner', stamp='11/09/26 11:00:00:000'),
            self.line('dismount nalu why=combat', stamp='11/09/26 11:00:01:000'),
            self.line('mount nalu why=native', stamp='11/09/26 11:00:02:000'),
            self.line('mount_blocked nalu why=no_key_item ki=3072 (V2 grants none)', stamp='11/09/26 11:00:03:000'),
            self.line('mount_gate off: entity:botMount is not bound (gated off)', stamp='11/09/26 11:00:04:000'),
            self.line('act nalu rule=mount_up apl=- op=mount reason=travel -> ok mount', stamp='11/09/26 11:00:05:000'),
            self.line('mount nalu', stamp='11/09/26 11:00:06:000'),                             # no why=
            self.line('mount_blocked nalu why=no_key_item ki=3072', stamp='11/09/26 11:00:07:000'),  # no tail
        ])
        bots, coverage = botsv2.read(self.write('c210.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['system']),
                         (6, 2, 0, 1))
        nalu = bots[0]
        self.assertEqual((nalu['counts']['mount'], nalu['counts']['other'], nalu['counts']['ok']), (2, 1, 1))
        self.assertEqual([(e['type'], e['reason']) for e in reversed(nalu['events'])],
                         [('mount', 'owner'), ('dismount', 'combat'), ('mount', 'native'),
                          ('mountBlocked', 'no_key_item'), ('act', 'mount')])

    def test_j0_profile_subjob_and_advice_use_the_exact_formats(self):
        # Templates from ffxi handoff 2026-11-09-botsv2-j0b-frozen (banshee_bots_v2.lua:798/835/849,
        # banshee_bots_v2_advice.lua:97-199). Staged, not live.
        raw = b''.join([
            self.line('act nalu rule=combat apl=sub_dia op=cast spellId=23 targetId=17260601 -> ok cast',
                      stamp='11/09/26 12:00:00:000'),
            self.line('profile nalu to=conserve from=default why=advice', stamp='11/09/26 12:00:01:000'),
            self.line('advice nalu req kind=rotation_profile id=v2-nalu-1700000000-1 options=2 default=default',
                      stamp='11/09/26 12:00:02:000'),
            self.line('advice nalu answer kind=rotation_profile choice=conserve applied=yes why=held_60s',
                      stamp='11/09/26 12:00:03:000'),
            self.line('advice nalu answer kind=goal choice=null applied=no why=null', stamp='11/09/26 12:00:04:000'),
            self.line('advice nalu drop why=expired', stamp='11/09/26 12:00:05:000'),
            self.line('advice - drop why=unknown_id', stamp='11/09/26 12:00:06:000'),
            self.line('subjob off: entity:getSubLvl is not readable (gated off)', stamp='11/09/26 12:00:07:000'),
            self.line('advice off: banshee_bots_v2_advice.lua is not installed (gated off)',
                      stamp='11/09/26 12:00:08:000'),
            self.line('advice nalu answer kind=goal choice=x applied=maybe why=null', stamp='11/09/26 12:00:09:000'),
            self.line('advice nalu drop why=bored', stamp='11/09/26 12:00:10:000'),
            self.line('profile nalu to=conserve why=order', stamp='11/09/26 12:00:11:000'),
        ])
        bots, coverage = botsv2.read(self.write('j0.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['system']),
                         (9, 3, 0, 3))
        nalu = bots[0]
        self.assertEqual((nalu['counts']['advice'], nalu['counts']['other'], nalu['counts']['ok']), (2, 2, 1))
        chronological = list(reversed(nalu['events']))
        self.assertEqual([(e['type'], e['reason'], e['result']) for e in chronological],
                         [('act', 'cast', 'ok'), ('profile', 'advice', None), ('adviceRequest', 'rotation_profile', None),
                          ('advice', 'held_60s', 'applied'), ('advice', 'null', 'not_applied'),
                          ('adviceDrop', 'expired', None)])
        self.assertEqual(chronological[0]['apl'], 'sub_dia')

    def test_p2b_order_refusals_and_tactic_release(self):
        # Templates from ffxi handoff 2026-11-09-botsv2-p2b-frozen (banshee_bots_v2.lua:1683, advice.lua:276).
        raw = b''.join([
            self.line('order nalu verb=attack arg=bee by=<owner> channel=party refused=not_party_mob',
                      stamp='11/09/26 14:00:00:000'),
            self.line('order nalu verb=attack arg=Yagudo_Persecutor by=<owner> channel=party', stamp='11/09/26 14:00:01:000'),
            self.line('order nalu verb=query arg=stats by=<owner> channel=tell refused=rate', stamp='11/09/26 14:00:02:000'),
            self.line('order nalu verb=formation arg=tight by=<owner> channel=party', stamp='11/09/26 14:00:03:000'),
            self.line('profile nalu to=aoe from=default why=order_ended', stamp='11/09/26 14:00:04:000'),
            self.line('advice nalu answer kind=party_tactic choice=burst applied=no why=party_changed',
                      stamp='11/09/26 14:00:05:000'),
            self.line('advice nalu release kind=party_tactic choice=burst why=ttl', stamp='11/09/26 14:00:06:000'),
            self.line('advice nalu release kind=goal choice=x why=ttl', stamp='11/09/26 14:00:07:000'),  # only party_tactic
            self.line('order nalu verb=aoe arg=on by=<owner> channel=party refused=No', stamp='11/09/26 14:00:08:000'),
        ])
        bots, coverage = botsv2.read(self.write('p2b.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized']), (7, 2, 0))
        nalu = bots[0]
        self.assertEqual((nalu['counts']['party'], nalu['counts']['advice']), (4, 1))
        orders = [(e['reason'], e['result'], e['detail']) for e in reversed(nalu['events']) if e['type'] == 'party']
        self.assertEqual(orders, [('attack', 'refused', 'arg=bee by=<owner> channel=party refused=not_party_mob'),
                                  ('attack', None, 'arg=Yagudo_Persecutor by=<owner> channel=party'),
                                  ('query', 'refused', 'arg=stats by=<owner> channel=tell refused=rate'),
                                  ('formation', None, 'arg=tight by=<owner> channel=party')])
        release = [e for e in nalu['events'] if e['type'] == 'adviceRelease']
        self.assertEqual([(e['reason'], e['detail']) for e in release], [('ttl', 'kind=party_tactic choice=burst')])

    def test_live_j1234_export_dies_three_times_and_turns_home_on_bag_full(self):
        # Export 7 (ffxi handoff 2026-11-09-botsv2-log-export-7): the J1-J4 run, 13:37Z-17:10Z, no human interaction.
        raw = J1234.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), J1234_SHA256)
        self.assertEqual(_lines(raw), 1818)
        bots, coverage = botsv2.read(J1234)
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized'], coverage['ignored']),
                         (1818, 0, 0, 0))
        by_name = {b['name']: b for b in bots}
        tomoe = by_name['tomoe']
        self.assertEqual((tomoe['counts']['dead'], tomoe['counts']['release']), (3, 3))
        lines = raw.decode('ascii').splitlines()
        # The live C5 bug: the THF and WHM ride out and turn home with a full bag, so they never fight. Counted on the
        # raw lines because the view keeps only the most recent events per bot.
        for name in ('shadowtail', 'fumika'):
            self.assertEqual(sum(f'trip end {name} ' in l and 'why=bag_full' in l for l in lines), 3, name)
            self.assertFalse(any(f'act {name} rule=combat ' in l for l in lines), name)
            self.assertEqual(by_name[name]['counts']['tripEnd'], 8, name)
        self.assertFalse(any('apl=sub_' in l for l in lines))
        self.assertIn('dead tomoe wait_raise=30', lines[585])
        self.assertIn('revived tomoe at its home point', lines[590])

    def test_c31_group_survival_lines_use_the_existing_formats(self):
        # ffxi handoff 2026-11-09-botsv2-c3.1-frozen: no new log template (template diff vs P2b is empty); new values
        # only: rules retreat/mate_assist, defend why=retreat_*/cornered, no trip why=danger.
        raw = b''.join([
            self.line('act nalu rule=retreat apl=- op=path -> ok path', stamp='11/09/26 17:20:00:000'),
            self.line('act pell rule=mate_assist apl=- op=path -> ok path', stamp='11/09/26 17:20:01:000'),
            self.line('defend nalu hp=31pct attacker=Boggart lv27 why=retreat_to_healer', stamp='11/09/26 17:20:02:000'),
            self.line('defend nalu hp=12pct attacker=Boggart lv27 why=cornered (repeated 2 times)',
                      stamp='11/09/26 17:20:03:000'),
            self.line('no trip pell why=danger zone=119', stamp='11/09/26 17:20:04:000'),
        ])
        bots, coverage = botsv2.read(self.write('c31.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized']), (5, 0, 0))
        by_name = {b['name']: b for b in bots}
        self.assertEqual(by_name['nalu']['counts']['defend'], 4)
        self.assertEqual([e['reason'] for e in reversed(by_name['nalu']['events']) if e['type'] == 'defend'],
                         ['retreat_to_healer', 'cornered'])
        self.assertEqual(sorted(e['rule'] for b in bots for e in b['events'] if e['type'] == 'act'),
                         ['mate_assist', 'retreat'])
        self.assertEqual([e['reason'] for e in by_name['pell']['events'] if e['type'] == 'noTrip'], ['danger'])

    def test_c43_and_q11_lines_use_the_exact_formats(self):
        # Templates from ffxi handoffs 2026-11-09-botsv2-c4.3-frozen and -q1.1-frozen (banshee_bots_v2.lua:608/619/1517/
        # 1612/1629/1654/1774/1884). Frozen, not live.
        raw = b''.join([
            self.line('group party nalu members=nalu+pell+tomo', stamp='11/09/26 18:00:00:000'),
            self.line('group party nalu drop tomo why=no_accept', stamp='11/09/26 18:00:01:000'),
            self.line('group party nalu off why=owner_online', stamp='11/09/26 18:00:02:000'),
            self.line('slow eval pell rule=combat tier=near wallMs=7.31 cpuMs=n/a atomic=yes heapKB=2048->2101',
                      stamp='11/09/26 18:00:03:000'),
            self.line('progression pell level=26 why=levelup -> ok', stamp='11/09/26 18:00:04:000'),
            self.line('progression pell level=26 why=spawn -> refused bag_hold', stamp='11/09/26 18:00:05:000'),
            self.line('roe pell record=1 -> ok', stamp='11/09/26 18:00:06:000'),
            self.line('roe pell record=12 -> refused', stamp='11/09/26 18:00:07:000'),
            self.line('act pell rule=progression apl=- op=roe record=2 -> ok roe', stamp='11/09/26 18:00:08:000'),
            # near misses: omitted, never guessed
            self.line('group party nalu members=pell+nalu', stamp='11/09/26 18:00:09:000'),        # leader not first
            self.line('group party nalu members=nalu', stamp='11/09/26 18:00:10:000'),             # nobody joined
            self.line('group party nalu off', stamp='11/09/26 18:00:11:000'),                      # no why=
            self.line('slow eval pell rule=combat tier=near wallMs=7.3 cpuMs=n/a atomic=yes heapKB=1->2',
                      stamp='11/09/26 18:00:12:000'),                                                # %.2f
            self.line('progression pell level=26 why=levelup -> refused', stamp='11/09/26 18:00:13:000'),
            self.line('roe pell record=intro -> ok', stamp='11/09/26 18:00:14:000'),
        ])
        bots, coverage = botsv2.read(self.write('c43q11.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['unrecognized']), (9, 6, 0))
        by_name = {b['name']: b for b in bots}
        self.assertEqual(sorted(by_name), ['nalu', 'pell', 'tomo'])
        self.assertEqual(by_name['nalu']['counts']['other'], 2)  # formed + off
        self.assertEqual(by_name['tomo']['counts']['other'], 2)  # formed + dropped
        drop = next(e for e in by_name['tomo']['events'] if e['type'] == 'groupPartyDrop')
        self.assertEqual((drop['reason'], drop['detail']), ('no_accept', 'leader=nalu'))
        pell = by_name['pell']
        self.assertEqual(pell['counts']['other'], 6)
        self.assertEqual(pell['counts']['ok'], 1)
        got = [(e['type'], e['result'], e['reason'], e['detail']) for e in reversed(pell['events'])
               if e['type'] in ('slowEval', 'progression', 'roe')]
        self.assertEqual(got, [
            ('slowEval', None, 'combat', 'tier=near wallMs=7.31 cpuMs=n/a atomic=yes heapKB=2048->2101'),
            ('progression', 'ok', 'levelup', 'level=26'),
            ('progression', 'refused', 'spawn', 'level=26 refused=bag_hold'),
            ('roe', 'ok', None, 'record=1'),
            ('roe', 'refused', None, 'record=12'),
        ])

    def test_c28_near_misses_are_omitted_not_guessed(self):
        cases = ['release nalu zone=119 after 30s',        # no why=
                 'release nalu why=x zone=119',             # no after
                 'weak pell level=25',                      # the old generic weak shape
                 'return nalu arrived zone=119',            # no after
                 'return nalu to owner zone=x from=119',    # zone is not digits
                 'revived nalu fell zone=241 after 9s',     # not a revive kind
                 'dead nalu why=killed_by_mob hp=0']        # the old generic dead shape
        for body in cases:
            with self.subTest(body=body):
                self.assertEqual(botsv2._line(self.line(body).rstrip(b'\n'), 1)[0], 'omitted')

    def test_stuck_reasons_are_fixed_codes_from_the_exact_formats(self):
        raw = b''.join([
            self.line('stuck nalu resolved walk_out after 12s attempts=2', stamp='11/09/26 05:12:01:000'),
            self.line('stuck nalu resolved new_path rule=travel moved=12 after 9s attempts=1',
                      stamp='11/09/26 05:12:02:000'),
            self.line('stuck nalu waiting: human in view (3 min, no teleport while seen)',
                      stamp='11/09/26 05:12:03:000'),
            self.line('stuck nalu homepoint gave no move (3 accepted), left as is', stamp='11/09/26 05:12:04:000'),
            self.line('stuck nalu unresolved zone=119 at (12, -4) humans_in_view=0', stamp='11/09/26 05:12:05:000'),
            self.line('stuck nalu mystery', stamp='11/09/26 05:12:06:000'),
        ])
        bots, coverage = botsv2.read(self.write('stuck.log', raw))
        self.assertEqual((coverage['records'], coverage['omitted']), (5, 1))
        nalu = bots[0]
        self.assertEqual([e['reason'] for e in reversed(nalu['events'])],
                         ['walk_out', 'new_path', 'human_in_view', 'homepoint_no_move', 'unresolved'])
        self.assertEqual((nalu['counts']['stuck'], nalu['zoneId'], nalu['doing']), (5, 119, 'stuck unresolved'))

    def test_stuck_driven_trip_end_is_a_trip_end_not_a_stuck_line(self):
        raw = self.line('trip end nalu camp=x out->home zone=119 why=stuck', stamp='11/09/26 05:13:00:000')
        bots, _ = botsv2.read(self.write('stuck-trip.log', raw))
        self.assertEqual((bots[0]['counts']['tripEnd'], bots[0]['counts']['stuck']), (1, 0))
        self.assertEqual(bots[0]['events'][0]['reason'], 'stuck')

    # Switch and file refusals

    def test_off_by_default_reads_nothing(self):
        with patch('ffxi_botsv2_log.read_bytes', side_effect=AssertionError('read while off')):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop(botsv2.ENV, None)
                bots, coverage = botsv2.read()
            self.assertEqual((bots, coverage['status']), ([], 'Off'))
            with patch.dict(os.environ, {botsv2.ENV: ''}):
                bots, coverage = botsv2.read()
            self.assertEqual((bots, coverage['status']), ([], 'Off'))

    def test_env_switch_reads_the_named_file(self):
        with patch.dict(os.environ, {botsv2.ENV: str(REAL)}):
            bots, coverage = botsv2.read()
        self.assertEqual((coverage['status'], coverage['records']), ('Loaded', REAL_LINES))
        self.assertEqual(len(bots), 3)

    def test_relative_and_non_path_arguments_are_unavailable(self):
        for path in ('relative/bots.log', '', 12, b'/tmp/bots.log'):
            with self.subTest(path=path):
                bots, coverage = botsv2.read(path)
                self.assertEqual((bots, coverage['status']), ([], 'Unavailable'))
                self.assertIn('nothing imported', coverage['reason'])

    def test_missing_directory_and_symlink_are_refused(self):
        bots, coverage = botsv2.read(self.root / 'missing.log')
        self.assertEqual((bots, coverage['status']), ([], 'Unavailable'))
        self.assertIn('missing file', coverage['reason'])
        bots, coverage = botsv2.read(self.root)
        self.assertEqual((bots, coverage['status']), ([], 'Unavailable'))
        target = self.write('target.log', REAL.read_bytes())
        link = self.root / 'link.log'
        link.symlink_to(target)
        with patch('ffxi_botsv2_log.read_bytes', side_effect=AssertionError('followed a symlink')):
            bots, coverage = botsv2.read(link)
        self.assertEqual((bots, coverage['status']), ([], 'Unavailable'))
        self.assertIn('symlink refused', coverage['reason'])

    def test_fifo_is_refused_without_blocking(self):
        if not hasattr(os, 'mkfifo'):
            self.skipTest('no mkfifo')
        fifo = self.root / 'pipe.log'
        os.mkfifo(fifo)
        self.assertTrue(stat.S_ISFIFO(os.lstat(fifo).st_mode))
        bots, coverage = botsv2.read(fifo)
        self.assertEqual((bots, coverage['status']), ([], 'Unavailable'))

    def test_oversized_file_is_refused(self):
        path = self.write('big.log', b'x' * (botsv2.MAX_BYTES + 1))
        bots, coverage = botsv2.read(path)
        self.assertEqual((bots, coverage['status']), ([], 'Unavailable'))
        self.assertIn('oversized file', coverage['reason'])

    def test_too_many_lines_is_refused(self):
        path = self.write('lines.log', b'\n' * (botsv2.MAX_LINES + 1))
        bots, coverage = botsv2.read(path)
        self.assertEqual((bots, coverage['status']), ([], 'Unavailable'))
        self.assertIn('too many lines', coverage['reason'])

    def test_reason_never_echoes_the_path(self):
        secret = self.root / 'owner-Bobby-private.log'
        _, coverage = botsv2.read(secret)
        self.assertNotIn('Bobby', coverage['reason'])
        self.assertNotIn(str(self.root), coverage['reason'])

    def test_read_never_raises_on_hostile_arguments(self):
        for path in (None, object(), '\x00bad', 1.5, ['x']):
            with self.subTest(path=repr(path)):
                with patch.dict(os.environ, {botsv2.ENV: ''}):
                    bots, coverage = botsv2.read(path)
                self.assertIsInstance(coverage, dict)
                self.assertIsInstance(bots, list)

    def test_reads_do_not_modify_the_source(self):
        before = hashlib.sha256(REAL.read_bytes()).hexdigest()
        botsv2.read(REAL)
        self.assertEqual(hashlib.sha256(REAL.read_bytes()).hexdigest(), before)
        shutil.copy(REAL, self.root / 'copy.log')
        self.assertEqual(botsv2.read(self.root / 'copy.log')[1]['records'], REAL_LINES)


if __name__ == '__main__':
    unittest.main()
