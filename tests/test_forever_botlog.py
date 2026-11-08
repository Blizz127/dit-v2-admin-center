"""Offline Forever bot-log import: off by default, strict rows, nothing repaired or invented."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import forever_botlog as botlog

FIXTURE = Path(__file__).resolve().parent / 'fixtures/forever-botlog'


class ForeverBotlogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'export'
        shutil.copytree(FIXTURE, self.root)
        self.manifest = json.loads((FIXTURE / 'manifest.json').read_text())
        self.bots = [json.loads(l) for l in (FIXTURE / 'bots.jsonl').read_text().splitlines()]
        self.events = [json.loads(l) for l in (FIXTURE / 'events.jsonl').read_text().splitlines()]

    def write(self, manifest=None, bots=None, events=None):
        if manifest is not None:
            (self.root / 'manifest.json').write_text(json.dumps(manifest))
        if bots is not None:
            (self.root / 'bots.jsonl').write_text(''.join(json.dumps(b) + '\n' for b in bots))
        if events is not None:
            (self.root / 'events.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events))
        return botlog.load(self.root)

    def row(self, id):
        return next(e for e in self.events if e['id'] == id)

    def event(self, id=900, bot_guid=1001, ts='2026-11-01 11:00:00', event_type='stuck', severity=1, **extra):
        return {'id': id, 'ts': ts, 'bot_guid': bot_guid, 'event_type': event_type, 'severity': severity, **extra}

    def bot(self, activity, guid):
        return next(a for a in activity if a['botGuid'] == str(guid))

    def assertUnavailable(self, result, text=None):
        activity, coverage = result
        self.assertEqual(activity, [])
        self.assertEqual((coverage['status'], coverage['records'], coverage['omitted']), ('Unavailable', 0, None))
        self.assertIn('nothing imported', coverage['reason'])
        if text:
            self.assertIn(text, coverage['reason'])

    # Switch

    def test_off_by_default_reads_nothing(self):
        with patch('forever_botlog.read_bytes', side_effect=AssertionError('read while off')):
            for environ in ({}, {botlog.ENV: ''}):
                activity, coverage = botlog.from_env(environ)
                self.assertEqual(activity, [])
                self.assertEqual(coverage['status'], 'Not configured')
                self.assertEqual((coverage['records'], coverage['omitted']), (0, 0))
                self.assertIn(botlog.ENV, coverage['reason'])

    def test_from_env_loads_the_named_directory(self):
        activity, coverage = botlog.from_env({botlog.ENV: str(self.root)})
        self.assertEqual((coverage['status'], len(activity)), ('Loaded', 3))

    # Projection

    def test_fixture_projects_bots_most_recently_active_first(self):
        activity, coverage = botlog.load(FIXTURE)
        self.assertEqual((coverage['status'], coverage['records'], coverage['omitted']), ('Loaded', 20, 0))
        self.assertEqual([a['botGuid'] for a in activity], ['1003', '1002', '1001'])
        self.assertEqual([a['lastEventAt'] for a in activity],
                         ['2026-11-01T10:04:31Z', '2026-11-01T10:03:40Z', '2026-11-01T10:02:20Z'])
        self.assertIn('exported log, not live', coverage['reason'])
        self.assertIn('2026-11-01T12:00:00.000Z', coverage['reason'])
        self.assertIn('source revision fixture-0001', coverage['reason'])
        self.assertIn('3 bots', coverage['reason'])
        self.assertIn("Forever's log shape", coverage['reason'])
        shape = {'botGuid', 'name', 'classId', 'raceId', 'faction', 'engine', 'lastEventAt', 'level', 'zoneId',
                 'doing', 'decisions', 'deaths', 'quests', 'counts'}
        self.assertTrue(all(set(a) == shape for a in activity))

    def test_identity_comes_from_bots_rows_and_event_only_bots_have_none(self):
        activity, _ = botlog.load(FIXTURE)
        thalindor = self.bot(activity, 1001)
        self.assertEqual((thalindor['name'], thalindor['classId'], thalindor['raceId'], thalindor['faction']),
                         ('Thalindor', 8, 1, 'alliance'))
        stranger = self.bot(activity, 1003)
        self.assertEqual((stranger['name'], stranger['classId'], stranger['raceId'], stranger['faction']),
                         (None, None, None, None))

    def test_engine_state_and_doing_line(self):
        activity, _ = botlog.load(FIXTURE)
        dead = self.bot(activity, 1001)
        self.assertEqual((dead['engine'], dead['doing'], dead['level'], dead['zoneId']), ('dead', 'Releasing spirit', 13, 12))
        # No engine state_change: the latest decision's engine stands in.
        brakka = self.bot(activity, 1002)
        self.assertEqual((brakka['engine'], brakka['doing'], brakka['level'], brakka['zoneId']), ('noncombat', 'Unsticking', 9, 14))
        # Only a lifecycle state_change (no kind) and no decisions: nothing is inferred.
        nobody = self.bot(activity, 1003)
        self.assertEqual((nobody['engine'], nobody['doing'], nobody['level'], nobody['zoneId']), ('Unknown', 'Unknown', 5, 17))

    def test_doing_falls_back_to_action_via_trigger_when_summary_is_missing(self):
        events = [e for e in self.events if e['bot_guid'] == 1001 and e['event_type'] == 'decision']
        for e in events:
            e['summary'] = None
        activity, _ = self.write(events=events)
        self.assertEqual(self.bot(activity, 1001)['doing'], 'release_spirit via corpse_tick')

    def test_engine_follows_the_latest_engine_change_over_decisions(self):
        # Drop the combat->dead change but keep the later dead-engine decision: the state_change still wins.
        events = [e for e in self.events if e['bot_guid'] == 1001 and e['id'] != 8]
        activity, _ = self.write(events=events)
        self.assertEqual(self.bot(activity, 1001)['engine'], 'combat')
        self.assertEqual(self.bot(activity, 1001)['decisions'][0]['engine'], 'dead')

    def test_lifecycle_state_change_without_engine_kind_is_not_an_engine_change(self):
        events = [self.event(1, event_type='state_change', details={'from': 'offline', 'to': 'combat', 'cause': 'login'})]
        activity, _ = self.write(events=events)
        self.assertEqual(self.bot(activity, 1001)['engine'], 'Unknown')

    def test_engine_change_to_an_unrecognised_engine_is_unknown_not_a_stale_value(self):
        events = [e for e in self.events if e['bot_guid'] == 1001]
        events.append(self.event(901, ts='2026-11-01 10:30:00', event_type='state_change',
                                 details={'kind': 'engine', 'from': 'dead', 'to': 'frozen', 'cause': 'x'}))
        activity, _ = self.write(events=events)
        self.assertEqual(self.bot(activity, 1001)['engine'], 'Unknown')

    def test_decisions_are_newest_first_with_alternatives_order_preserved(self):
        activity, _ = botlog.load(FIXTURE)
        decisions = self.bot(activity, 1001)['decisions']
        self.assertEqual([d['action'] for d in decisions],
                         ['release_spirit', 'use_potion', 'cast_fireball', 'grind', 'quest_travel'])
        self.assertEqual(decisions[0], {'ts': '2026-11-01T10:02:20Z', 'engine': 'dead', 'trigger': 'corpse_tick',
                                        'action': 'release_spirit', 'reason': 'CORPSE', 'relevance': 100,
                                        'band': 'DEAD', 'effective': 100, 'alternatives': []})
        self.assertEqual([(a['action'], a['relevance'], a['result']) for a in decisions[4]['alternatives']],
                         [('grind', 50, 'NOT_REACHED'), ('rest', 0, 'MULTIPLIED_TO_ZERO'), ('vendor', 30, 'NOT_USEFUL')])
        self.assertEqual([a['result'] for a in decisions[3]['alternatives']],
                         ['NOT_USEFUL', 'EXECUTE_FAILED', 'NOT_POSSIBLE'])  # string details were parsed
        self.assertEqual(decisions[3]['ts'], '2026-11-01T10:01:10Z')
        self.assertEqual({d['engine'] for d in decisions}, {'noncombat', 'combat', 'dead'})

    def test_only_the_latest_eight_decisions_are_kept(self):
        base = self.row(3)
        events = []
        for i in range(12):
            row = copy.deepcopy(base)
            row['id'], row['ts'] = 700 + i, f'2026-11-01 10:10:{i:02d}'
            row['details']['action'] = f'act{i}'
            events.append(row)
        decisions = self.bot(self.write(events=events)[0], 1001)['decisions']
        self.assertEqual([d['action'] for d in decisions], [f'act{i}' for i in range(11, 3, -1)])

    def test_death_carries_killer_and_recent_decisions(self):
        activity, _ = botlog.load(FIXTURE)
        self.assertEqual(self.bot(activity, 1001)['deaths'], [{
            'ts': '2026-11-01T10:02:10Z', 'reason': 'KILLED_BY_CREATURE', 'summary': 'Killed by Rotfang Gnoll (level 15)',
            'killerEntry': 4101, 'killerLevel': 15, 'levelGap': 2,
            'recentDecisions': [{'msAgo': 800, 'action': 'use_potion', 'reason': 'LOW_HEALTH'},
                                {'msAgo': 4200, 'action': 'cast_fireball', 'reason': 'IN_RANGE'},
                                {'msAgo': 70000, 'action': 'grind', 'reason': 'MOB_NEARBY'}]}])
        self.assertEqual(self.bot(activity, 1002)['deaths'], [])

    def test_deaths_are_capped_at_three_newest_first(self):
        events = [self.event(800 + i, ts=f'2026-11-01 10:20:0{i}', event_type='death', severity=2,
                             reason='KILLED_BY_CREATURE', details=None) for i in range(5)]
        deaths = self.bot(self.write(events=events)[0], 1001)['deaths']
        self.assertEqual([d['ts'] for d in deaths],
                         ['2026-11-01T10:20:04Z', '2026-11-01T10:20:03Z', '2026-11-01T10:20:02Z'])
        self.assertEqual(deaths[0], {'ts': '2026-11-01T10:20:04Z', 'reason': 'KILLED_BY_CREATURE', 'summary': None,
                                     'killerEntry': None, 'killerLevel': None, 'levelGap': None, 'recentDecisions': []})

    def test_quests_and_counts(self):
        activity, _ = botlog.load(FIXTURE)
        brakka = self.bot(activity, 1002)
        self.assertEqual([(q['reason'], q['questId'], q['summary']) for q in brakka['quests']],
                         [('QUEST_REWARDED', 7001, 'Rewarded: Gnoll Trouble'), ('QUEST_COMPLETE', 7001, 'Gnoll Trouble complete'),
                          ('QUEST_PROGRESS', 7001, 'Gnoll Trouble 3/8'), ('QUEST_ACCEPTED', 7001, 'Accepted: Gnoll Trouble')])
        self.assertEqual(brakka['quests'][0]['ts'], '2026-11-01T10:03:05Z')
        self.assertEqual(brakka['counts'], {'decision': 2, 'quest': 4, 'stuck': 1})
        self.assertEqual(self.bot(activity, 1001)['counts'], {'state_change': 4, 'decision': 5, 'death': 1})
        self.assertEqual(self.bot(activity, 1003)['counts'], {'state_change': 1, 'path_fail': 1, 'xp': 1})

    def test_quests_are_capped_at_five_and_unknown_quest_reasons_are_only_counted(self):
        events = [self.event(600 + i, ts=f'2026-11-01 10:30:0{i}', event_type='quest', reason='QUEST_PROGRESS',
                             quest_id=7000 + i) for i in range(7)]
        events.append(self.event(610, ts='2026-11-01 10:31:00', event_type='quest', reason='QUEST_MYSTERY', quest_id=1))
        bot = self.bot(self.write(events=events)[0], 1001)
        self.assertEqual([q['questId'] for q in bot['quests']], [7006, 7005, 7004, 7003, 7002])
        self.assertEqual(bot['counts'], {'quest': 8})

    def test_generated_columns_are_ignored_not_read(self):
        events = [self.event(1, level=7, zone_id=3, killer_entry='not-an-int', xp_amount=None, src='engine')]
        activity, coverage = self.write(events=events)
        self.assertEqual((coverage['records'], coverage['omitted']), (1, 0))
        self.assertEqual(self.bot(activity, 1001)['level'], 7)

    def test_level_and_zone_come_from_the_latest_non_null_values(self):
        events = [self.event(1, ts='2026-11-01 10:00:00', level=10, zone_id=4),
                  self.event(2, ts='2026-11-01 10:05:00', level=11),
                  self.event(3, ts='2026-11-01 10:06:00')]
        bot = self.bot(self.write(events=events)[0], 1001)
        self.assertEqual((bot['level'], bot['zoneId'], bot['lastEventAt']), (11, 4, '2026-11-01T10:06:00Z'))

    def test_bots_without_events_are_omitted_and_only_the_latest_200_are_shown(self):
        bots = self.bots + [{'guid': 5000, 'name': 'Idle', 'class_id': 1, 'race_id': 1, 'faction': 'alliance'}]
        activity, _ = self.write(bots=bots)
        self.assertNotIn('5000', [a['botGuid'] for a in activity])
        events = [self.event(i, bot_guid=2000 + i, ts=f'2026-11-01 11:{i // 60:02d}:{i % 60:02d}') for i in range(205)]
        activity, coverage = self.write(events=events)
        self.assertEqual(len(activity), 200)
        self.assertEqual(activity[0]['botGuid'], '2204')
        self.assertEqual(activity[-1]['botGuid'], '2005')
        self.assertIn('Showing the 200 most recently active of 205 bots', coverage['reason'])

    def test_ordering_compares_parsed_times_not_text(self):
        events = [self.event(1, bot_guid=1, ts='2026-11-01 10:00:00.5'), self.event(2, bot_guid=2, ts='2026-11-01T10:00:00Z'),
                  self.event(3, bot_guid=3, ts='2026-11-01 10:00:00.25')]
        activity, _ = self.write(events=events)
        self.assertEqual([a['botGuid'] for a in activity], ['1', '3', '2'])

    # Timestamps

    def test_both_timestamp_formats_normalise_to_iso_z(self):
        for raw, expected in (('2026-11-01 10:00:00', '2026-11-01T10:00:00Z'),
                              ('2026-11-01 10:00:00.250', '2026-11-01T10:00:00.250Z'),
                              ('2026-11-01T10:00:00Z', '2026-11-01T10:00:00Z'),
                              ('2026-11-01T10:00:00.250Z', '2026-11-01T10:00:00.250Z')):
            with self.subTest(raw=raw):
                activity, coverage = self.write(events=[self.event(1, ts=raw)])
                self.assertEqual(coverage['omitted'], 0)
                self.assertEqual(activity[0]['lastEventAt'], expected)

    def test_other_timestamp_forms_are_omitted(self):
        for raw in ('2026-11-01T10:00:00', '2026-11-01 10:00:00Z', '2026-11-01T10:00:00+00:00', '2026-13-01 10:00:00',
                    '2026-11-01 25:00:00', '1730455200', 1730455200, None, '', '2026-11-01 10:00:00.1234567'):
            with self.subTest(raw=raw):
                activity, coverage = self.write(events=[self.event(1, ts=raw)])
                self.assertEqual((activity, coverage['records'], coverage['omitted']), ([], 0, 1))

    # Manifest

    def test_manifest_refusals(self):
        future = (datetime.now(timezone.utc) + timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        cases = {
            'kind': {**self.manifest, 'kind': 'other'},
            'version': {**self.manifest, 'version': 2},
            'bool version': {**self.manifest, 'version': True},
            'float version': {**self.manifest, 'version': 1.0},
            'extra field': {**self.manifest, 'note': 'x'},
            'future time': {**self.manifest, 'exportedAtUtc': future},
            'bad time': {**self.manifest, 'exportedAtUtc': '2026-11-01 12:00:00'},
            'bad revision': {**self.manifest, 'sourceRevision': 'has space'},
            'non-string revision': {**self.manifest, 'sourceRevision': 7},
            'not an object': [self.manifest],
        }
        for name, manifest in cases.items():
            with self.subTest(name):
                self.assertUnavailable(self.write(manifest=manifest), 'Export unreadable')
        for missing in ('kind', 'version', 'exportedAtUtc'):
            with self.subTest('missing ' + missing):
                self.assertUnavailable(self.write(manifest={k: v for k, v in self.manifest.items() if k != missing}))

    def test_manifest_without_source_revision_and_recent_export_are_accepted(self):
        recent = (datetime.now(timezone.utc) + timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        manifest = {'kind': botlog.KIND, 'version': 1, 'exportedAtUtc': recent}
        activity, coverage = self.write(manifest=manifest)
        self.assertEqual(coverage['status'], 'Loaded')
        self.assertIn('source revision not reported', coverage['reason'])

    def test_manifest_with_duplicate_keys_nan_or_bad_bytes_is_refused(self):
        for raw in (b'{"kind":"forever-botlog-export","kind":"forever-botlog-export","version":1,"exportedAtUtc":"2026-11-01T12:00:00Z"}',
                    b'{"kind":"forever-botlog-export","version":NaN,"exportedAtUtc":"2026-11-01T12:00:00.000Z"}',
                    b'\xff\xfe', b'', b'{'):
            with self.subTest(raw=raw):
                (self.root / 'manifest.json').write_bytes(raw)
                self.assertUnavailable(botlog.load(self.root))

    def test_missing_files_are_unavailable(self):
        for name in ('manifest.json', 'bots.jsonl', 'events.jsonl'):
            with self.subTest(name):
                path = self.root / name
                saved = path.read_bytes()
                path.unlink()
                self.assertUnavailable(botlog.load(self.root), 'FileNotFoundError')
                path.write_bytes(saved)

    # Malformed rows

    def test_malformed_event_rows_are_counted_and_omitted_never_repaired(self):
        good = self.event(1)
        bad = {
            'missing id': {k: v for k, v in good.items() if k != 'id'},
            'missing ts': {k: v for k, v in good.items() if k != 'ts'},
            'missing bot_guid': {k: v for k, v in good.items() if k != 'bot_guid'},
            'missing event_type': {k: v for k, v in good.items() if k != 'event_type'},
            'missing severity': {k: v for k, v in good.items() if k != 'severity'},
            'severity too high': {**good, 'severity': 4},
            'severity negative': {**good, 'severity': -1},
            'severity bool': {**good, 'severity': True},
            'severity string': {**good, 'severity': '1'},
            'severity float': {**good, 'severity': 1.0},
            'id bool': {**good, 'id': True},
            'id string': {**good, 'id': '2'},
            'id negative': {**good, 'id': -2},
            'guid string': {**good, 'bot_guid': '1001'},
            'event_type empty': {**good, 'event_type': ''},
            'event_type long': {**good, 'event_type': 'x' * 33},
            'event_type number': {**good, 'event_type': 4},
            'reason long': {**good, 'reason': 'x' * 65},
            'reason number': {**good, 'reason': 5},
            'summary long': {**good, 'summary': 'x' * 256},
            'level float': {**good, 'level': 12.5},
            'level string': {**good, 'level': '12'},
            'level too big': {**good, 'level': 256},
            'zone object': {**good, 'zone_id': {}},
            'pos string': {**good, 'pos_x': 'a'},
            'pos bool': {**good, 'pos_x': True},
            'unknown key': {**good, 'extra': 1},
            'details list': {**good, 'details': [1]},
            'details number': {**good, 'details': 7},
            'details bool': {**good, 'details': True},
            'details plain string': {**good, 'details': 'just words'},
            'details string list': {**good, 'details': '[1, 2]'},
            'details string null': {**good, 'details': 'null'},
            'details empty string': {**good, 'details': ''},
            'details string duplicate key': {**good, 'details': '{"a": 1, "a": 2}'},
            'details string nan': {**good, 'details': '{"a": NaN}'},
            'details string infinity': {**good, 'details': '{"a": 1e999}'},
            'details string too long': {**good, 'details': '{"a": "' + 'x' * 70000 + '"}'},
        }
        events = [{**good, 'id': 2}] + [{**row, **({'id': 100 + i} if row.get('id') is good['id'] else {})}
                                         for i, row in enumerate(bad.values())]
        activity, coverage = self.write(events=events)
        self.assertEqual((coverage['records'], coverage['omitted']), (1, len(bad)))
        self.assertEqual(activity[0]['counts'], {'stuck': 1})

    def test_unparseable_lines_are_omitted(self):
        lines = [json.dumps(self.event(1)), '{not json', '[1]', '"x"', 'null', '{"id": 2, "id": 3}', '\xff'.encode('latin-1').decode('latin-1'),
                 '', '   ', json.dumps(self.event(2)), '{"id": NaN}']
        (self.root / 'events.jsonl').write_bytes('\n'.join(lines).encode('latin-1', 'replace'))
        activity, coverage = botlog.load(self.root)
        self.assertEqual((coverage['records'], coverage['omitted']), (2, 7))
        deep = '[' * 100000 + ']' * 100000
        (self.root / 'events.jsonl').write_text(json.dumps(self.event(1)) + '\n' + deep + '\n')
        self.assertEqual(botlog.load(self.root)[1]['omitted'], 1)

    def test_details_may_be_an_object_a_json_object_string_or_null(self):
        events = [self.event(1, details={'a': 1}), self.event(2, details='{"a": 1}'), self.event(3, details=None), self.event(4)]
        self.assertEqual(self.write(events=events)[1]['omitted'], 0)

    def test_malformed_bot_rows_are_omitted(self):
        good = self.bots[0]
        bad = [{k: v for k, v in good.items() if k != 'name'}, {**good, 'faction': 'neutral'}, {**good, 'faction': ['horde']},
               {**good, 'name': 'x' * 25}, {**good, 'name': ''}, {**good, 'guid': True}, {**good, 'guid': '1001'},
               {**good, 'class_id': 1.5}, {**good, 'race_id': -1}, {**good, 'extra': 1}, {**good, 'first_seen': 'yesterday'}]
        activity, coverage = self.write(bots=bad + [self.bots[1]])
        self.assertEqual(coverage['omitted'], len(bad))
        self.assertIn(f'{len(bad)} of them bot rows', coverage['reason'])
        self.assertEqual(self.bot(activity, 1001)['name'], None)  # its only row was malformed
        self.assertEqual(self.bot(activity, 1002)['name'], 'Brakka')

    # Decision / death shapes

    def decision_row(self, details, id=1, **extra):
        return self.event(id, event_type='decision', severity=0, reason='WHY', summary='Does a thing', details=details, **extra)

    def test_decision_with_unmatched_details_keeps_columns_and_marks_structure_unknown(self):
        good = self.row(3)['details']
        broken = {
            'engine': {**good, 'engine': 'swimming'}, 'engine type': {**good, 'engine': ['combat']},
            'trigger missing': {k: v for k, v in good.items() if k != 'trigger'},
            'relevance string': {**good, 'relevance': '80'}, 'relevance bool': {**good, 'relevance': True},
            'effective missing': {k: v for k, v in good.items() if k != 'effective'},
            'band number': {**good, 'band': 3}, 'alternatives dict': {**good, 'alternatives': {}},
            'alternatives missing': {k: v for k, v in good.items() if k != 'alternatives'},
            'alternative not object': {**good, 'alternatives': ['x']},
            'alternative missing result': {**good, 'alternatives': [{'action': 'a', 'relevance': 1}]},
            'alternative relevance': {**good, 'alternatives': [{'action': 'a', 'relevance': 'x', 'result': 'NOT_USEFUL'}]},
            'detail not object': {**good, 'detail': 'x'},
            'no details': None,
        }
        for name, details in broken.items():
            with self.subTest(name):
                activity, coverage = self.write(events=[self.decision_row(details)])
                self.assertEqual((coverage['records'], coverage['omitted']), (1, 0))
                bot = self.bot(activity, 1001)
                self.assertEqual(bot['decisions'], [{'ts': '2026-11-01T11:00:00Z', 'engine': 'Unknown', 'trigger': 'Unknown',
                                                     'action': 'Unknown', 'reason': 'WHY', 'relevance': None, 'band': 'Unknown',
                                                     'effective': None, 'alternatives': []}])
                self.assertEqual(bot['engine'], 'Unknown')  # an unmatched decision never sets the engine
                self.assertEqual(bot['doing'], 'Does a thing')
                self.assertEqual(bot['counts'], {'decision': 1})

    def test_huge_integers_omit_or_unknown_the_part_never_crash_the_load(self):
        huge = 10 ** 400
        activity, coverage = self.write(events=[self.event(1), self.event(2, pos_x=huge)])
        self.assertEqual((coverage['status'], coverage['records'], coverage['omitted']), ('Loaded', 1, 1))
        good = self.row(3)['details']
        for name, details in (('relevance', {**good, 'relevance': huge}), ('effective', {**good, 'effective': huge}),
                              ('alternative', {**good, 'alternatives': [{'action': 'a', 'relevance': huge, 'result': 'NOT_USEFUL'}]})):
            with self.subTest(name):
                activity, coverage = self.write(events=[self.decision_row(details)])
                self.assertEqual((coverage['status'], coverage['records'], coverage['omitted']), ('Loaded', 1, 0))
                bot = self.bot(activity, 1001)
                self.assertEqual((bot['decisions'][0]['action'], bot['doing']), ('Unknown', 'Does a thing'))

    def test_unknown_decision_without_summary_has_unknown_doing(self):
        row = self.decision_row({'engine': 'nope'})
        row['summary'] = None
        self.assertEqual(self.bot(self.write(events=[row])[0], 1001)['doing'], 'Unknown')

    def test_decision_extra_detail_keys_and_empty_alternatives_are_accepted(self):
        details = {**self.row(3)['details'], 'alternatives': [], 'detail': {'spell': 1}, 'future_field': 1}
        decision = self.bot(self.write(events=[self.decision_row(details)])[0], 1001)['decisions'][0]
        self.assertEqual((decision['engine'], decision['action'], decision['alternatives']), ('noncombat', 'quest_travel', []))

    def test_death_with_unmatched_parts_keeps_columns_and_marks_those_parts_unknown(self):
        killer = {'entry': 4101, 'level': 15, 'lvl_diff': 2}
        recent = [{'ms_ago': 5, 'action': 'a', 'reason': 'r'}]
        cases = {
            'killer string': ({'killer': 'wolf', 'recent_decisions': recent}, (None, None, None), recent),
            'killer field type': ({'killer': {**killer, 'level': 'x'}, 'recent_decisions': recent}, (None, None, None), recent),
            'killer bool': ({'killer': {**killer, 'entry': True}}, (None, None, None), []),
            'recent not list': ({'killer': killer, 'recent_decisions': 'x'}, (4101, 15, 2), []),
            'recent bad element': ({'killer': killer, 'recent_decisions': recent + [{'ms_ago': -1, 'action': 'a', 'reason': 'r'}]},
                                   (4101, 15, 2), []),
            'recent missing key': ({'killer': killer, 'recent_decisions': [{'ms_ago': 5, 'action': 'a'}]}, (4101, 15, 2), []),
            'killer partial': ({'killer': {'entry': 4101}}, (4101, None, None), []),
            'no details': (None, (None, None, None), []),
        }
        for name, (details, killer_fields, expected_recent) in cases.items():
            with self.subTest(name):
                row = self.event(1, event_type='death', severity=2, reason='KILLED', summary='Died', details=details)
                activity, coverage = self.write(events=[row])
                self.assertEqual((coverage['records'], coverage['omitted']), (1, 0))
                death = self.bot(activity, 1001)['deaths'][0]
                self.assertEqual((death['reason'], death['summary']), ('KILLED', 'Died'))
                self.assertEqual((death['killerEntry'], death['killerLevel'], death['levelGap']), killer_fields)
                self.assertEqual([(d['msAgo'], d['action'], d['reason']) for d in death['recentDecisions']],
                                 [(d['ms_ago'], d['action'], d['reason']) for d in expected_recent])

    # Duplicates and ambiguity

    def test_duplicate_event_ids_omit_every_copy(self):
        events = self.events + [{**self.row(1), 'ts': '2026-11-01 10:00:09'}]
        activity, coverage = self.write(events=events)
        self.assertEqual((coverage['records'], coverage['omitted']), (19, 2))
        self.assertIn('2 event rows share an id', coverage['reason'])
        self.assertEqual(self.bot(activity, 1001)['counts'], {'state_change': 3, 'decision': 5, 'death': 1})

    def test_duplicate_ids_across_different_bots_are_still_duplicates(self):
        events = [self.event(5, bot_guid=1), self.event(5, bot_guid=2), self.event(6, bot_guid=3)]
        activity, coverage = self.write(events=events)
        self.assertEqual(([a['botGuid'] for a in activity], coverage['records'], coverage['omitted']), (['3'], 1, 2))

    def test_malformed_row_does_not_poison_a_valid_row_with_the_same_id(self):
        events = [self.event(5), {**self.event(5), 'severity': 9}]
        self.assertEqual(self.write(events=events)[1]['records'], 1)

    def test_conflicting_bot_rows_withhold_identity_and_are_reported(self):
        bots = self.bots + [{**self.bots[0], 'name': 'Impostor'}]
        activity, coverage = self.write(bots=bots)
        ambiguous = self.bot(activity, 1001)
        self.assertEqual((ambiguous['name'], ambiguous['classId'], ambiguous['raceId'], ambiguous['faction']),
                         (None, None, None, None))
        self.assertEqual(self.bot(activity, 1002)['name'], 'Brakka')
        self.assertIn('1 bot guid(s) have conflicting rows', coverage['reason'])
        self.assertEqual(coverage['omitted'], 0)

    def test_identical_duplicate_bot_rows_are_not_ambiguous(self):
        activity, coverage = self.write(bots=self.bots + [self.bots[0], {**self.bots[0], 'first_seen': '2026-10-31 01:00:00'}])
        self.assertEqual(self.bot(activity, 1001)['name'], 'Thalindor')
        self.assertNotIn('conflicting', coverage['reason'])

    # Refusals

    def test_relative_directory_is_refused_and_nothing_is_read(self):
        with patch('forever_botlog.read_bytes', side_effect=AssertionError('read a relative path')):
            self.assertUnavailable(botlog.load('relative/export'), 'absolute')
            self.assertUnavailable(botlog.from_env({botlog.ENV: 'export'}), 'absolute')

    def test_fifo_is_refused_without_blocking(self):
        for name in ('manifest.json', 'bots.jsonl', 'events.jsonl'):
            with self.subTest(name):
                path = self.root / name
                saved = path.read_bytes()
                path.unlink()
                os.mkfifo(path)
                self.assertUnavailable(botlog.load(self.root))
                path.unlink()
                path.write_bytes(saved)

    def test_symlinked_files_are_refused(self):
        for name in ('manifest.json', 'bots.jsonl', 'events.jsonl'):
            with self.subTest(name):
                path = self.root / name
                saved = path.read_bytes()
                path.unlink()
                path.symlink_to(FIXTURE / name)
                self.assertUnavailable(botlog.load(self.root))
                path.unlink()
                path.write_bytes(saved)

    def test_directories_in_place_of_files_are_refused(self):
        (self.root / 'events.jsonl').unlink()
        (self.root / 'events.jsonl').mkdir()
        self.assertUnavailable(botlog.load(self.root))

    def test_oversized_files_are_refused(self):
        (self.root / 'manifest.json').write_text(json.dumps({**self.manifest, 'sourceRevision': 'x' * botlog.MANIFEST_LIMIT}))
        self.assertUnavailable(botlog.load(self.root), 'oversized manifest')
        self.write(manifest=self.manifest)
        (self.root / 'bots.jsonl').write_bytes(b' ' * (botlog.BOTS_LIMIT + 1))
        self.assertUnavailable(botlog.load(self.root), 'oversized bots')
        self.write(bots=self.bots)
        (self.root / 'events.jsonl').write_bytes(b' ' * (botlog.EVENTS_LIMIT + 1))
        self.assertUnavailable(botlog.load(self.root), 'oversized events')

    def test_files_at_the_exact_limit_are_not_oversized(self):
        (self.root / 'events.jsonl').write_bytes(b'\n' * botlog.EVENTS_LIMIT)
        activity, coverage = botlog.load(self.root)
        self.assertEqual((activity, coverage['status'], coverage['records']), ([], 'Loaded', 0))

    def test_too_many_lines_are_refused(self):
        (self.root / 'bots.jsonl').write_bytes(b'{}\n' * (botlog.MAX_BOTS_LINES + 1))
        self.assertUnavailable(botlog.load(self.root), 'too many bots')
        self.write(bots=self.bots)
        (self.root / 'events.jsonl').write_bytes(b'{}\n' * (botlog.MAX_EVENT_LINES + 1))
        self.assertUnavailable(botlog.load(self.root), 'too many events')

    def test_oversized_single_row_is_omitted_not_fatal(self):
        long_row = json.dumps(self.event(2, summary='x' * 255, details={'pad': 'y' * botlog.MAX_LINE}))
        (self.root / 'events.jsonl').write_text(json.dumps(self.event(1)) + '\n' + long_row + '\n')
        _, coverage = botlog.load(self.root)
        self.assertEqual((coverage['records'], coverage['omitted']), (1, 1))

    def test_error_messages_never_echo_file_content(self):
        secret = 'SECRET-TOKEN-4711'
        (self.root / 'manifest.json').write_text(json.dumps({**self.manifest, 'kind': secret}))
        self.assertNotIn(secret, botlog.load(self.root)[1]['reason'])
        (self.root / 'manifest.json').write_text('{"' + secret + '": 1, "' + secret + '": 2}')
        self.assertNotIn(secret, botlog.load(self.root)[1]['reason'])
        self.write(manifest=self.manifest)
        _, coverage = self.write(events=[self.event(1, summary=secret, extra=secret)])
        self.assertNotIn(secret, coverage['reason'])




class OverviewSwitchTests(unittest.TestCase):
    def test_overview_bot_activity_only_when_switched_on(self):
        import tempfile
        from unittest.mock import patch
        from pathlib import Path
        import server
        fixture = Path(__file__).resolve().parent / 'fixtures/forever-botlog'
        with tempfile.TemporaryDirectory() as home:
            def overview(environ):
                with patch.dict('os.environ', environ, clear=True), \
                     patch.object(Path, 'home', return_value=Path(home)), \
                     patch('server.LOCAL_DATA', Path(home) / 'local'):
                    return server.overview()
            off = overview({})
            on = overview({'DIT_FOREVER_BOTLOG_DIR': str(fixture)})
        self.assertEqual((off['botActivity']['coverage']['status'], off['botActivity']['bots']), ('Not configured', []))
        self.assertEqual(on['botActivity']['coverage']['status'], 'Loaded')
        self.assertEqual(len(on['botActivity']['bots']), 3)


if __name__ == '__main__':
    unittest.main()
