"""dit.bot_event.v1 offline import: off by default, strict rows, bounded reads, nothing repaired or invented."""
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import bot_event_v1 as events

FIXTURE = Path(__file__).resolve().parent / 'fixtures/bot-event-v1'
EXAMPLES = FIXTURE / 'EXAMPLES.jsonl'
MISSING = object()
DECISION_TS = '2026-11-09T05:00:00.000Z'
ADVICE_DETAILS = {'kind': 'rotation_profile', 'options': 3, 'default_option': 'standard', 'choice': 'conserve_mp',
                  'reason': 'mp low', 'route': 'cheap', 'outcome': 'applied'}
COVERAGE_KEYS = {'status', 'records', 'omitted', 'reason', 'files', 'games', 'from', 'to', 'omittedByReason'}


def base(**changes):
    """A valid swtor decision row. A MISSING value drops the key."""
    data = {'schema': events.SCHEMA, 'game': 'swtor', 'actor_id': 'bot-1', 'ts': DECISION_TS, 'session_seq': 1,
            'event_type': 'decision', 'severity': 1, 'reason': 'NO_PATH', 'summary': 'walking', 'level': 10,
            'area': 'Coruscant', 'details': {'intent': 'travel'}}
    for key, value in changes.items():
        if value is MISSING:
            data.pop(key, None)
        else:
            data[key] = value
    return data


def advice_row(detail_changes=None, **changes):
    details = dict(ADVICE_DETAILS)
    for key, value in (detail_changes or {}).items():
        if value is MISSING:
            details.pop(key, None)
        else:
            details[key] = value
    data = base(event_type='advice', reason='APPLIED', correlation_id='adv-7', details=details,
                summary='rotation_profile: conserve_mp')
    for key, value in changes.items():
        if value is MISSING:
            data.pop(key, None)
        else:
            data[key] = value
    return data


def death_row(details=None, **changes):
    data = base(event_type='death', reason='DIED', summary='died', level=10,
                details={'killer': 'Gorax', 'recent_decisions': [
                    {'action': 'travel', 'reason': 'NO_PATH'}, {'action': 'pull', 'reason': None}]})
    if details is not None:
        data['details'] = details
    for key, value in changes.items():
        if value is MISSING:
            data.pop(key, None)
        else:
            data[key] = value
    return data


def encode(item):
    if isinstance(item, bytes):
        return item
    if isinstance(item, str):
        return item.encode('utf-8')
    return json.dumps(item).encode('utf-8')


class BotEventTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def directory(self, files):
        """A fresh directory holding {name: [items]}; each item is a dict, a str or bytes line."""
        root = Path(tempfile.mkdtemp(dir=self.temp.name))
        for name, items in files.items():
            (root / name).write_bytes(b''.join(encode(item) + b'\n' for item in items))
        return root

    def run_rows(self, *items):
        """Read one file holding these items; return (bots, coverage)."""
        return events.read(str(self.directory({'swtor-2026-11-09.jsonl': list(items)})))

    def reasons(self, *items):
        return self.run_rows(*items)[1]['omittedByReason']

    def accepted(self, item):
        bots, coverage = self.run_rows(item)
        self.assertEqual((coverage['records'], coverage['omitted']), (1, 0), coverage['reason'])
        return bots

    def refused(self, item, reason):
        bots, coverage = self.run_rows(item)
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['omittedByReason']),
                         (0, 1, {reason: 1}), coverage['reason'])
        self.assertEqual(bots, [])

    def only_bot(self, *items):
        bots, _ = self.run_rows(*items)
        self.assertEqual(len(bots), 1)
        return bots[0]

    # Switch

    def test_unset_or_empty_env_is_off_and_reads_nothing(self):
        with patch('bot_event_v1.read_bytes', side_effect=AssertionError('read while off')):
            for environ in ({}, {events.ENV: ''}):
                with patch.dict(os.environ, environ, clear=True):
                    bots, coverage = events.read()
                    self.assertEqual(bots, [])
                    self.assertEqual(coverage['status'], 'Off')
                    self.assertEqual((coverage['records'], coverage['omitted'], coverage['files']), (0, 0, 0))
                    self.assertEqual(coverage['omittedByReason'], {})
                    self.assertIn(events.ENV, coverage['reason'])

    def test_env_names_the_directory_and_is_read_at_call_time(self):
        root = self.directory({'swtor-2026-11-09.jsonl': [base()]})
        with patch.dict(os.environ, {events.ENV: str(root)}, clear=True):
            bots, coverage = events.read()
        self.assertEqual((coverage['status'], coverage['records'], len(bots)), ('Loaded', 1, 1))

    def test_relative_directory_is_refused_and_nothing_is_read(self):
        with patch('bot_event_v1.read_bytes', side_effect=AssertionError('read a relative path')):
            for directory in ('relative/export', '.'):
                bots, coverage = events.read(directory)
                self.assertEqual((bots, coverage['status']), ([], 'Unavailable'))
                self.assertIn('absolute', coverage['reason'])
                self.assertIsNone(coverage['omitted'])
            with patch.dict(os.environ, {events.ENV: 'export'}, clear=True):
                self.assertEqual(events.read()[1]['status'], 'Unavailable')

    def test_coverage_shape_is_fixed(self):
        _, coverage = self.run_rows(base())
        self.assertEqual(set(coverage), COVERAGE_KEYS)
        self.assertEqual(coverage['status'], 'Loaded')
        self.assertEqual((coverage['files'], coverage['games'], coverage['from'], coverage['to']),
                         (1, ['swtor'], DECISION_TS, DECISION_TS))
        self.assertIn('not live', coverage['reason'])

    # Contract: the pinned schema and the examples

    def test_fixture_provenance_note_names_the_source_commit(self):
        note = (FIXTURE / 'SOURCE.txt').read_text()
        self.assertIn('ea92d35a', note)
        self.assertIn('dit.decision_advice.v1.schema.json', note)  # The substitution is recorded.
        for name in ('dit.bot_event.v1.schema.json', 'dit.decision_advice.v1.request.schema.json',
                     'dit.decision_advice.v1.response.schema.json', 'EXAMPLES.jsonl'):
            self.assertTrue((FIXTURE / name).is_file(), name)

    def test_constants_match_the_pinned_schema_file(self):
        schema = json.loads((FIXTURE / 'dit.bot_event.v1.schema.json').read_text())
        props = schema['properties']
        self.assertEqual(set(schema['required']), events.REQUIRED)
        self.assertEqual(set(props), events.FIELDS)
        self.assertIs(schema['additionalProperties'], False)
        self.assertEqual(props['schema']['const'], events.SCHEMA)
        self.assertEqual(props['game']['pattern'], '^' + events.GAME_PATTERN + '$')
        self.assertEqual(props['event_type']['pattern'], '^' + events.EVENT_TYPE_PATTERN + '$')
        self.assertEqual(props['severity']['enum'], sorted(events.SEVERITIES))
        self.assertEqual(props['actor_id']['minLength'], 1)
        for field, limit in events.LIMITS.items():
            self.assertEqual(props[field]['maxLength'], limit, field)
        self.assertEqual(set(props['details']['not']['anyOf'][0]['required']) | set(
            props['details']['not']['anyOf'][1]['required']), events.FORBIDDEN_DETAILS)
        allof = {branch['if']['properties']['event_type']['const']: branch['then'] for branch in schema['allOf']}
        advice = allof['advice']['properties']['details']
        self.assertEqual(set(advice['required']), events.ADVICE_REQUIRED)
        self.assertEqual(set(advice['properties']['kind']['enum']), events.ADVICE_KINDS)
        self.assertIn(None, advice['properties']['route']['enum'])
        self.assertEqual(set(advice['properties']['route']['enum']) - {None}, events.ADVICE_ROUTES)
        self.assertEqual(set(advice['properties']['outcome']['enum']), events.ADVICE_OUTCOMES)
        self.assertEqual((advice['properties']['options']['minimum'], advice['properties']['options']['maximum']),
                         (0, events.MAX_OPTIONS))
        self.assertEqual(advice['properties']['reason']['maxLength'], events.ADVICE_REASON)
        self.assertEqual(allof['advice']['properties']['correlation_id']['type'], 'string')
        chat = allof['chat']['properties']['details']
        self.assertEqual(set(chat['required']), events.CHAT_REQUIRED)
        self.assertEqual(set(chat['properties']['drop_reason']['enum']) - {None}, events.CHAT_DROP_REASONS)
        self.assertIn(None, chat['properties']['drop_reason']['enum'])
        self.assertEqual((chat['properties']['channel']['maxLength'], chat['properties']['origin']['maxLength'],
                          chat['properties']['route']['maxLength']),
                         (events.CHAT_CHANNEL, events.CHAT_ORIGIN, events.CHAT_ROUTE))
        voiced_rule, origin_rule = chat['allOf']
        self.assertEqual(voiced_rule['then']['properties']['origin']['const'], events.CHAT_AI)
        self.assertEqual(origin_rule['if']['properties']['origin']['not']['const'], events.CHAT_AI)
        self.assertEqual((origin_rule['then']['properties']['voiced']['const'],
                          origin_rule['then']['properties']['drop_reason']['const']), (False, 'NOT_AI'))
        self.assertEqual(allof['chat']['properties']['correlation_id']['type'], 'string')
        death = allof['death']['properties']['details']['properties']['recent_decisions']
        self.assertEqual((death['type'], death['maxItems']), ('array', events.MAX_RECENT))
        request = json.loads((FIXTURE / 'dit.decision_advice.v1.request.schema.json').read_text())
        self.assertEqual(request['properties']['default_option']['maxLength'], events.ADVICE_OPTION_ID)
        self.assertEqual(request['properties']['options']['items']['properties']['id']['maxLength'],
                         events.ADVICE_OPTION_ID)

    def test_example_rows_pass_and_map_and_the_advice_exchange_is_consistent(self):
        lines = [json.loads(line) for line in EXAMPLES.read_text().splitlines()]
        decision, advice, request, response, chat = lines
        bots, coverage = events.read(str(self.directory({'ffxi_forever-2026-11-09.jsonl': lines})))
        self.assertEqual((coverage['records'], coverage['omitted']), (3, 2))
        self.assertEqual(coverage['omittedByReason'], {'not_bot_event': 2})
        by_actor = {bot['actorId']: bot for bot in bots}
        self.assertEqual(set(by_actor), {'2001', '2002', 'vorrak'})
        # The 6.6 chat row carries only structured fields; no chat text exists or is surfaced.
        talker = by_actor['vorrak']
        self.assertEqual((talker['game'], talker['counts']), ('swtor', {'chat': 1}))
        self.assertEqual(talker['events'][0]['reason'], 'VOICED')
        self.assertNotIn('text', json.dumps(talker['events']))
        worker = by_actor['2001']
        self.assertEqual((worker['doing'], worker['level'], worker['area']), ('auto_pull', 6, '115'))
        self.assertEqual(worker['events'][0]['action'], 'auto_pull')
        self.assertEqual(worker['counts'], {'decision': 1})
        hub = by_actor['2002']
        self.assertEqual(hub['advice'], [{'ts': advice['ts'], 'kind': 'rotation_profile', 'chosen': 'conserve_mp',
                                          'outcome': 'applied', 'reason': advice['details']['reason']}])
        # The request, the response and the advice row describe one exchange.
        self.assertEqual(request['request_id'], advice['correlation_id'])
        self.assertEqual(response['request_id'], advice['correlation_id'])
        self.assertEqual(response['choice'], advice['details']['choice'])
        self.assertEqual(response['reason'], advice['details']['reason'])
        self.assertEqual(response['route'], advice['details']['route'])

    def test_example_private_details_are_not_surfaced(self):
        bots, _ = events.read(str(self.directory({'ffxi_forever-2026-11-09.jsonl': [
            json.loads(line) for line in EXAMPLES.read_text().splitlines()[:2]]})))
        text = json.dumps(bots)
        for private in ('owner_party', 'camp', 'rest_at', 'radius', 'fields', 'tank'):
            self.assertNotIn(private, text)
        self.assertEqual(set(bots[0]['events'][0]), {'ts', 'type', 'severity', 'reason', 'summary', 'action', 'result'})

    # Required fields, types, enums, lengths and patterns

    def test_schema_marker_and_missing_required_fields(self):
        for name in sorted(events.REQUIRED - {'schema'}):
            with self.subTest(missing=name):
                self.refused(base(**{name: MISSING}), 'missing_' + name)
        for marker in ('dit.bot_event.v2', 'dit.decision_advice.v1', None, 7):
            with self.subTest(schema=marker):
                self.refused(base(schema=marker), 'not_bot_event')
        self.refused(base(schema=MISSING), 'not_bot_event')

    def test_unknown_top_level_field_is_refused(self):
        self.refused(base(extra=1), 'unknown_field')

    def test_non_object_rows_are_refused(self):
        for line in ('[1,2]', '"x"', 'null', '3', 'true'):
            with self.subTest(line=line):
                self.refused(line, 'not_object')

    def test_type_and_enum_violations_are_omitted_with_their_reason(self):
        cases = [
            ('game', 'FFXI', 'invalid_game'), ('game', 'a', 'invalid_game'), ('game', 'a' * 33, 'invalid_game'),
            ('game', 'ffxi-forever', 'invalid_game'), ('game', 5, 'invalid_game'), ('game', None, 'invalid_game'),
            ('actor_id', '', 'invalid_actor_id'), ('actor_id', 5, 'invalid_actor_id'),
            ('ts', '2026-11-09T05:00:00Z', 'invalid_ts'), ('ts', '2026-11-09 05:00:00.000Z', 'invalid_ts'),
            ('ts', '2026-11-09T05:00:00.000+00:00', 'invalid_ts'), ('ts', '2026-11-09T05:00:00.1234Z', 'invalid_ts'),
            ('ts', '2026-02-30T05:00:00.000Z', 'invalid_ts'), ('ts', '2026-11-09T24:00:00.000Z', 'invalid_ts'),
            ('ts', 1234, 'invalid_ts'),
            ('ts', '\u0662\u0660\u0662\u0666-11-09T05:00:00.000Z', 'invalid_ts'),  # Arabic-Indic digits
            ('ts', '\uff12\uff10\uff12\uff16-11-09T05:00:00.000Z', 'invalid_ts'),  # Fullwidth digits
            ('session_seq', -1, 'invalid_session_seq'), ('session_seq', True, 'invalid_session_seq'),
            ('session_seq', 1.5, 'invalid_session_seq'), ('session_seq', 2 ** 63, 'invalid_session_seq'),
            ('event_type', 'Decision', 'invalid_event_type'), ('event_type', 'a', 'invalid_event_type'),
            ('event_type', 'a' * 33, 'invalid_event_type'), ('event_type', 'state-change', 'invalid_event_type'),
            ('event_type', '', 'invalid_event_type'), ('event_type', 7, 'invalid_event_type'),
            ('event_type', ['decision'], 'invalid_event_type'),
            ('severity', 4, 'invalid_severity'), ('severity', -1, 'invalid_severity'),
            ('severity', '1', 'invalid_severity'), ('severity', 1.0, 'invalid_severity'),
            ('severity', True, 'invalid_severity'), ('severity', None, 'invalid_severity'),
            ('severity', {'a': 1}, 'invalid_severity'),
            ('reason', 5, 'invalid_reason'), ('summary', ['a'], 'invalid_summary'),
            ('level', 256, 'invalid_level'), ('level', -1, 'invalid_level'), ('level', 1.0, 'invalid_level'),
            ('level', True, 'invalid_level'), ('level', 'six', 'invalid_level'),
            ('area', 7, 'invalid_area'), ('quest_id', 7, 'invalid_quest_id'), ('target', 7, 'invalid_target'),
            ('correlation_id', 7, 'invalid_correlation_id'),
            ('pos', {'x': 1, 'y': 2}, 'invalid_pos'), ('pos', {'x': 1, 'y': 2, 'z': 3, 'w': 4}, 'invalid_pos'),
            ('pos', 'pos', 'invalid_pos'), ('pos', {'x': True, 'y': 0, 'z': 0}, 'invalid_pos'),
            ('pos', {'x': '1', 'y': 0, 'z': 0}, 'invalid_pos'),
            ('details', 'string', 'invalid_details'), ('details', [], 'invalid_details'),
            ('details', None, 'invalid_details'), ('details', {'text': 'hi'}, 'forbidden_text'),
            ('details', {'chat_text': 'hi'}, 'forbidden_text'),
        ]
        for field, value, reason in cases:
            with self.subTest(field=field, value=value):
                self.refused(base(**{field: value}), reason)

    def test_length_limits_pass_at_the_limit_and_fail_one_over(self):
        for field, limit in events.LIMITS.items():
            with self.subTest(field=field):
                if field == 'actor_id':
                    accepted = base(actor_id='a' * limit)
                    refused = base(actor_id='a' * (limit + 1))
                else:
                    accepted = base(**{field: 'x' * limit})
                    refused = base(**{field: 'x' * (limit + 1)})
                self.accepted(accepted)
                self.refused(refused, 'invalid_' + field)

    def test_game_and_event_type_patterns_accept_their_bounds(self):
        self.accepted(base(game='ab', event_type='xy'))
        self.accepted(base(game='a' * 32, event_type='x' * 32))
        self.accepted(base(game='ffxi_forever9', event_type='state_change'))
        self.refused(base(game='a' * 33), 'invalid_game')

    def test_timestamps_must_be_utc_milliseconds_and_a_real_date(self):
        self.accepted(base(ts='2026-11-09T05:00:00.000Z'))
        self.accepted(base(ts='2028-02-29T23:59:59.999Z'))
        self.refused(base(ts='2026-02-29T00:00:00.000Z'), 'invalid_ts')

    def test_integers_are_integers_and_bounds_hold(self):
        self.accepted(base(level=255, session_seq=2 ** 63 - 1, severity=3))
        self.accepted(base(level=0, session_seq=0, severity=0))
        self.accepted(base(level=None, session_seq=None))
        self.accepted(base(session_seq=MISSING))

    def test_pos_accepts_finite_xyz_and_refuses_non_finite(self):
        self.accepted(base(pos={'x': -12.5, 'y': 0, 'z': 240.1}))
        self.accepted(base(pos=None))
        line = '{"schema":"dit.bot_event.v1","game":"swtor","actor_id":"b","ts":"2026-11-09T05:00:00.000Z",' \
               '"event_type":"decision","severity":1,"pos":{"x":NaN,"y":0,"z":0}}'
        self.refused(line, 'invalid_json')

    def test_null_optional_fields_are_accepted(self):
        self.accepted(base(reason=None, summary=None, area=None, quest_id=None, target=None, correlation_id=None,
                           level=None, pos=None))

    # Advice (BOT_BRAIN_STANDARD 6.5)

    def test_every_advice_outcome_is_accepted_and_surfaced(self):
        outcomes = ('applied', 'NO_ADVICE', 'TIMEOUT', 'INVALID_OPTION', 'STALE', 'REVALIDATE_FAIL')
        bots = self.run_rows(*(advice_row({'outcome': outcome}) for outcome in outcomes))[0]
        bot = bots[0]
        self.assertEqual(sorted(item['outcome'] for item in bot['advice']), sorted(outcomes))
        self.assertEqual(sorted(event['result'] for event in bot['events']), sorted(outcomes))

    def test_advice_entries_are_newest_first_and_capped_at_fifty(self):
        rows = [advice_row(ts=f'2026-11-09T05:00:{n:02d}.000Z', correlation_id=f'adv-{n}') for n in range(55)]
        bot = self.only_bot(*rows)
        self.assertEqual(len(bot['advice']), 50)
        self.assertEqual(bot['advice'][0]['ts'], '2026-11-09T05:00:54.000Z')
        self.assertEqual(bot['counts'], {'advice': 55})

    def test_advice_details_are_required_and_typed(self):
        cases = [
            ({'kind': 'unknown'}, 'invalid_advice'), ({'kind': None}, 'invalid_advice'),
            ({'options': 17}, 'invalid_advice'), ({'options': -1}, 'invalid_advice'),
            ({'options': True}, 'invalid_advice'), ({'options': '2'}, 'invalid_advice'),
            ({'default_option': 'x' * 65}, 'invalid_advice'), ({'default_option': MISSING}, 'invalid_advice'),
            ({'default_option': None}, 'invalid_advice'),
            ({'choice': MISSING}, 'invalid_advice'), ({'choice': 'x' * 65}, 'invalid_advice'),
            ({'reason': 'x' * 161}, 'invalid_advice'), ({'reason': 4}, 'invalid_advice'),
            ({'route': 'gpt'}, 'invalid_advice'), ({'route': 4}, 'invalid_advice'),
            ({'outcome': 'DONE'}, 'invalid_advice'), ({'outcome': MISSING}, 'invalid_advice'),
            ({'outcome': 'applied '}, 'invalid_advice'),
        ]
        for changes, reason in cases:
            with self.subTest(changes=changes):
                self.refused(advice_row(changes), reason)
        self.refused(advice_row(correlation_id=MISSING), 'invalid_correlation_id')
        self.refused(advice_row(correlation_id=None), 'invalid_correlation_id')
        self.refused(advice_row(details=None), 'invalid_details')

    def test_advice_row_without_details_is_refused(self):
        row = advice_row()
        row.pop('details')
        self.refused(row, 'missing_details')

    def test_advice_boundaries_and_optional_fields(self):
        self.accepted(advice_row({'options': 0}))
        self.accepted(advice_row({'options': 16}))
        self.accepted(advice_row({'choice': None, 'reason': None, 'route': None}))
        self.accepted(advice_row({'route': MISSING, 'reason': MISSING, 'choice': 'x' * 64}))
        self.accepted(advice_row({'reason': 'x' * 160, 'route': 'rules', 'choice': 'conserve_mp'}))
        self.accepted(advice_row({'route': 'planning', 'kind': 'goal'}))
        self.accepted(advice_row({'route': 'cheap', 'kind': 'party_tactic'}))

    def test_advice_action_and_result_in_events_are_choice_and_outcome(self):
        bot = self.only_bot(advice_row({'choice': None, 'outcome': 'NO_ADVICE'}))
        self.assertEqual(bot['events'][0]['action'], None)
        self.assertEqual(bot['events'][0]['result'], 'NO_ADVICE')
        self.assertEqual(bot['advice'][0]['chosen'], None)
        self.assertEqual(bot['advice'][0]['outcome'], 'NO_ADVICE')

    # Death (BOT_BRAIN_STANDARD 6.3)

    def test_death_carries_killer_and_recent_decisions(self):
        bot = self.only_bot(death_row())
        self.assertEqual(bot['deaths'], [{'ts': DECISION_TS, 'killer': 'Gorax', 'recentDecisions': [
            {'action': 'travel', 'reason': 'NO_PATH'}, {'action': 'pull', 'reason': None}]}])

    def test_recent_decisions_accept_the_latest_eight_and_refuse_nine(self):
        eight = [{'action': f'act{n}', 'reason': 'R'} for n in range(8)]
        bot = self.only_bot(death_row({'killer': 'Gorax', 'recent_decisions': eight}))
        self.assertEqual(len(bot['deaths'][0]['recentDecisions']), 8)
        self.refused(death_row({'killer': 'Gorax', 'recent_decisions': eight + [{'action': 'x'}]}), 'invalid_death')
        self.refused(death_row({'recent_decisions': 'notalist'}), 'invalid_death')
        self.refused(death_row({'recent_decisions': None}), 'invalid_death')

    def test_one_malformed_recent_item_empties_the_list_and_keeps_the_death(self):
        bad_items = ['pull', {'action': ''}, {'action': 5}, {'reason': 'R'}, {'action': 'a', 'reason': 'x' * 65},
                     {'action': 'a', 'reason': 4}]
        for item in bad_items:
            with self.subTest(item=item):
                bots, coverage = self.run_rows(death_row({'killer': 'Gorax', 'recent_decisions': [
                    {'action': 'ok'}, item]}))
                self.assertEqual((coverage['records'], coverage['omitted']), (1, 0))
                self.assertEqual(bots[0]['deaths'][0]['recentDecisions'], [])

    def test_recent_item_accepts_intent_as_the_action(self):
        bot = self.only_bot(death_row({'killer': 'Gorax', 'recent_decisions': [{'intent': 'pull'}]}))
        self.assertEqual(bot['deaths'][0]['recentDecisions'], [{'action': 'pull', 'reason': None}])

    def test_killer_is_bounded_text_or_a_name_object_or_none(self):
        self.assertEqual(self.only_bot(death_row({'killer': 'Gorax'}))['deaths'][0]['killer'], 'Gorax')
        self.assertEqual(self.only_bot(death_row({'killer': {'name': 'Gorax', 'level': 9}}))['deaths'][0]['killer'],
                         'Gorax')
        self.assertIsNone(self.only_bot(death_row({'killer': 'x' * 65}))['deaths'][0]['killer'])
        self.assertIsNone(self.only_bot(death_row({'killer': 9}))['deaths'][0]['killer'])
        row = death_row()
        row.pop('details')
        self.assertEqual(self.only_bot(row)['deaths'][0], {'ts': DECISION_TS, 'killer': None, 'recentDecisions': []})

    def test_deaths_are_newest_first_and_capped_at_fifty(self):
        rows = [death_row({'killer': f'k{n}'}, ts=f'2026-11-09T05:00:{n:02d}.000Z') for n in range(55)]
        bot = self.only_bot(*rows)
        self.assertEqual(len(bot['deaths']), 50)
        self.assertEqual(bot['deaths'][0]['killer'], 'k54')

    # Decision and projection

    def test_doing_is_the_latest_decision_action_then_summary(self):
        older = base(details={'action': 'pull'}, ts='2026-11-09T05:00:01.000Z')
        newer_summary = base(details={}, summary='walking', ts='2026-11-09T05:00:02.000Z')
        self.assertEqual(self.only_bot(older, newer_summary)['doing'], 'walking')
        newest = base(details={'action': 'camp'}, summary='camping', ts='2026-11-09T05:00:03.000Z')
        self.assertEqual(self.only_bot(older, newer_summary, newest)['doing'], 'camp')
        silent = base(details={}, summary=None, ts='2026-11-09T05:00:04.000Z')
        self.assertIsNone(self.only_bot(older, silent)['doing'])
        self.assertIsNone(self.only_bot(base(event_type='state_change', details={}, summary='x'))['doing'])

    def test_action_and_result_come_from_details_only_when_bounded_text(self):
        bot = self.only_bot(base(details={'action': 'x' * 65, 'intent': 'pull', 'result': 'NOT_REACHED'}))
        self.assertEqual((bot['events'][0]['action'], bot['events'][0]['result']), ('pull', 'NOT_REACHED'))
        bot = self.only_bot(base(details={'action': 7}))
        self.assertIsNone(bot['events'][0]['action'])

    def test_level_and_area_are_the_latest_non_null_values(self):
        bot = self.only_bot(base(level=9, area='Ronfaure', ts='2026-11-09T05:00:01.000Z'),
                            base(level=None, area=None, ts='2026-11-09T05:00:02.000Z'))
        self.assertEqual((bot['level'], bot['area']), (9, 'Ronfaure'))
        self.assertEqual(bot['lastEventAt'], '2026-11-09T05:00:02.000Z')

    def test_bots_group_by_game_and_actor_and_sort_by_game_then_actor(self):
        bots, coverage = self.run_rows(base(game='swtor', actor_id='b2'), base(game='ffxi', actor_id='b9'),
                                       base(game='swtor', actor_id='b1'), base(game='swtor', actor_id='b1',
                                                                               ts='2026-11-09T05:01:00.000Z'))
        self.assertEqual([(bot['game'], bot['actorId']) for bot in bots],
                         [('ffxi', 'b9'), ('swtor', 'b1'), ('swtor', 'b2')])
        self.assertEqual(bots[1]['counts'], {'decision': 2})
        self.assertEqual(coverage['games'], ['ffxi', 'swtor'])

    def test_events_are_newest_first_and_capped_at_two_hundred(self):
        rows = [base(ts=f'2026-11-09T05:{n // 60:02d}:{n % 60:02d}.000Z', summary=f'e{n}') for n in range(205)]
        bot = self.only_bot(*rows)
        self.assertEqual(len(bot['events']), 200)
        self.assertEqual(bot['events'][0]['summary'], 'e204')
        self.assertEqual(bot['events'][-1]['summary'], 'e5')
        self.assertEqual(bot['counts'], {'decision': 205})

    def test_same_timestamp_ties_keep_file_order_newest_first(self):
        directory = self.directory({'a.jsonl': [base(summary='from-a')], 'b.jsonl': [base(summary='from-b')]})
        bots, coverage = events.read(str(directory))
        self.assertEqual([event['summary'] for event in bots[0]['events']], ['from-b', 'from-a'])
        self.assertEqual((coverage['files'], coverage['records']), (2, 2))

    def test_files_are_read_in_name_order_and_coverage_reports_the_span(self):
        directory = self.directory({
            'swtor-2026-11-09.jsonl': [base(ts='2026-11-09T05:00:00.000Z')],
            'ffxi_forever-2026-11-08.jsonl': [base(game='ffxi_forever', ts='2026-11-08T23:59:59.000Z')],
        })
        bots, coverage = events.read(str(directory))
        self.assertEqual(coverage['games'], ['ffxi_forever', 'swtor'])
        self.assertEqual((coverage['from'], coverage['to']),
                         ('2026-11-08T23:59:59.000Z', '2026-11-09T05:00:00.000Z'))
        self.assertEqual(len(bots), 2)

    def test_most_recently_active_bots_are_kept_when_over_the_bot_limit(self):
        rows = [base(actor_id='old', ts='2026-11-09T05:00:01.000Z'),
                base(actor_id='mid', ts='2026-11-09T05:00:02.000Z'),
                base(actor_id='new', ts='2026-11-09T05:00:03.000Z')]
        with patch.object(events, 'MAX_BOTS', 2):
            bots, coverage = self.run_rows(*rows)
        self.assertEqual([bot['actorId'] for bot in bots], ['mid', 'new'])
        self.assertIn('Showing the 2 most recently active of 3 bots', coverage['reason'])
        self.assertEqual(coverage['records'], 3)

    # Limits, exactly at the limit and one over

    def test_file_count_limit_is_exact(self):
        ok = {f'f{n:03d}.jsonl': [base(summary=f'f{n}')] for n in range(events.MAX_FILES)}
        _, coverage = events.read(str(self.directory(ok)))
        self.assertEqual((coverage['files'], coverage['records'], coverage['status']),
                         (events.MAX_FILES, events.MAX_FILES, 'Loaded'))
        over = dict(ok, **{'zz.jsonl': [base(summary='extra')]})
        bots, coverage = events.read(str(self.directory(over)))
        self.assertEqual(coverage['files'], events.MAX_FILES)
        self.assertEqual(coverage['records'], events.MAX_FILES)
        self.assertIn('1 over the file limit', coverage['reason'])
        summaries = {event['summary'] for event in bots[0]['events']}
        self.assertIn('extra', summaries)  # The newest file is kept.
        self.assertNotIn('f0', summaries)  # The oldest name, f000, is the one refused.

    def test_directory_entry_limit_is_exact(self):
        with patch.object(events, 'MAX_DIR_ENTRIES', 5):
            root = self.directory({})
            for n in range(5):
                (root / f'note{n}.txt').write_text('x')
            self.assertEqual(events.read(str(root))[1]['status'], 'Loaded')
            (root / 'note5.txt').write_text('x')
            bots, coverage = events.read(str(root))
            self.assertEqual((bots, coverage['status']), ([], 'Unavailable'))
            self.assertIn('too many entries', coverage['reason'])

    def test_file_size_limit_is_exact(self):
        with patch.object(events, 'MAX_FILE_BYTES', 400):
            self.assertEqual(self.run_exact_size(400)[1]['records'], 1)
            bots, coverage = self.run_exact_size(401)
            self.assertEqual((coverage['records'], coverage['files']), (0, 0))
            self.assertIn('1 oversized', coverage['reason'])

    def test_total_byte_limit_is_exact_and_keeps_the_newest_files(self):
        with patch.object(events, 'MAX_FILE_BYTES', 400), patch.object(events, 'MAX_TOTAL_BYTES', 800):
            root = Path(tempfile.mkdtemp(dir=self.temp.name))
            (root / 'a.jsonl').write_bytes(self.sized(400, 'from-a'))
            (root / 'b.jsonl').write_bytes(self.sized(399, 'from-b'))
            (root / 'c.jsonl').write_bytes(b'\n')  # Exactly 800 bytes in all: every file fits.
            _, coverage = events.read(str(root))
            self.assertEqual((coverage['files'], coverage['records'], coverage['omitted']), (3, 2, 0))
            self.assertNotIn('total byte limit', coverage['reason'])
        with patch.object(events, 'MAX_FILE_BYTES', 400), patch.object(events, 'MAX_TOTAL_BYTES', 800):
            root = Path(tempfile.mkdtemp(dir=self.temp.name))
            (root / 'a.jsonl').write_bytes(self.sized(400, 'from-a'))
            (root / 'b.jsonl').write_bytes(self.sized(400, 'from-b'))
            (root / 'c.jsonl').write_bytes(b'\n')  # 801 bytes: the oldest file is the one refused.
            bots, coverage = events.read(str(root))
            self.assertEqual((coverage['files'], coverage['records']), (2, 1))
            self.assertIn('1 over the total byte limit', coverage['reason'])
            self.assertEqual({event['summary'] for event in bots[0]['events']}, {'from-b'})

    def test_newer_file_that_does_not_fit_ends_the_read_and_older_files_stay_unread(self):
        # The newest file is 400 bytes, the next is 400 bytes and would overflow the 300 bytes left, and the oldest is
        # a small row that does fit the 300 bytes left. The newest run is kept, so the small older row is dropped.
        small = len(encode(base(summary='from-a'))) + 1  # the row and its newline
        self.assertLessEqual(small, 300, 'the small row must fit the budget left after the newest file')
        self.assertEqual(len(self.sized(small, 'from-a')), small)
        with patch.object(events, 'MAX_FILE_BYTES', 400), patch.object(events, 'MAX_TOTAL_BYTES', 700):
            root = Path(tempfile.mkdtemp(dir=self.temp.name))
            (root / 'a.jsonl').write_bytes(self.sized(small, 'from-a'))
            (root / 'b.jsonl').write_bytes(self.sized(400, 'from-b'))
            (root / 'c.jsonl').write_bytes(self.sized(400, 'from-c'))
            bots, coverage = events.read(str(root))
        self.assertEqual((coverage['files'], coverage['records']), (1, 1))
        self.assertIn('2 over the total byte limit', coverage['reason'])
        self.assertEqual({event['summary'] for event in bots[0]['events']}, {'from-c'})

    def sized(self, total, summary='walking'):
        """One valid row line padded with spaces to exactly `total` bytes, newline included."""
        line = json.dumps(base(summary=summary)).encode('utf-8') + b'\n'
        return line[:-1] + b' ' * (total - len(line)) + b'\n'

    def run_exact_size(self, total):
        root = Path(tempfile.mkdtemp(dir=self.temp.name))
        (root / 'swtor-2026-11-09.jsonl').write_bytes(self.sized(total))
        return events.read(str(root))

    def test_line_length_limit_is_exact(self):
        with patch.object(events, 'MAX_LINE', 600):
            empty = json.dumps(base(details={'pad': ''})).encode('utf-8')
            exact = json.dumps(base(details={'pad': 'x' * (600 - len(empty))})).encode('utf-8')
            self.assertEqual(len(exact), 600)
            self.accepted(exact)
            over = json.dumps(base(details={'pad': 'x' * (601 - len(empty))})).encode('utf-8')
            self.assertEqual(len(over), 601)
            self.refused(over, 'oversized_line')

    def test_row_limit_is_exact_and_drops_the_oldest_rows(self):
        with patch.object(events, 'MAX_ROWS', 3):
            bots, coverage = self.run_rows(*(base(summary=f'r{n}') for n in range(5)))
        self.assertEqual((coverage['records'], coverage['omitted']), (3, 2))
        self.assertEqual(coverage['omittedByReason'], {'row_limit': 2})
        self.assertEqual({event['summary'] for event in bots[0]['events']}, {'r2', 'r3', 'r4'})

    def test_blank_lines_are_not_rows(self):
        root = Path(tempfile.mkdtemp(dir=self.temp.name))
        (root / 'swtor-2026-11-09.jsonl').write_bytes(b'\n\n   \n' + encode(base()) + b'\n\n')
        _, coverage = events.read(str(root))
        self.assertEqual((coverage['records'], coverage['omitted']), (1, 0))

    # Symlinks, FIFOs and non-files

    def test_symlinked_file_is_refused_and_the_others_load(self):
        root = self.directory({'swtor-2026-11-09.jsonl': [base()]})
        (root / 'link.jsonl').symlink_to(EXAMPLES)
        bots, coverage = events.read(str(root))
        self.assertEqual((coverage['records'], coverage['files'], len(bots)), (1, 1, 1))
        self.assertIn('1 symlink', coverage['reason'])
        self.assertEqual(coverage['omitted'], 0)

    def test_symlinked_directory_is_refused_and_nothing_is_read(self):
        real = self.directory({'swtor-2026-11-09.jsonl': [base()]})
        link = Path(self.temp.name) / 'link'
        link.symlink_to(real)
        with patch('bot_event_v1.read_bytes', side_effect=AssertionError('read through a symlink')):
            bots, coverage = events.read(str(link))
        self.assertEqual((bots, coverage['status']), ([], 'Unavailable'))
        self.assertIn('symbolic link', coverage['reason'])

    def test_fifo_named_jsonl_is_refused_without_blocking(self):
        root = self.directory({'swtor-2026-11-09.jsonl': [base()]})
        os.mkfifo(root / 'a-pipe.jsonl')
        outcome = {}
        worker = threading.Thread(target=lambda: outcome.update(result=events.read(str(root))), daemon=True)
        worker.start()
        worker.join(10)
        self.assertFalse(worker.is_alive(), 'read blocked on a FIFO')
        _, coverage = outcome['result']
        self.assertEqual((coverage['records'], coverage['status']), (1, 'Loaded'))
        self.assertIn('1 not a regular file', coverage['reason'])

    def test_directory_named_jsonl_is_refused(self):
        root = self.directory({'swtor-2026-11-09.jsonl': [base()]})
        (root / 'nested.jsonl').mkdir()
        _, coverage = events.read(str(root))
        self.assertEqual(coverage['records'], 1)
        self.assertIn('1 not a regular file', coverage['reason'])

    def test_other_suffixes_and_subdirectories_are_ignored(self):
        root = self.directory({'swtor-2026-11-09.jsonl': [base()], 'notes.json': [base(summary='no')],
                               'swtor.jsonl.bak': [base(summary='no')]})
        (root / 'sub').mkdir()
        (root / 'sub' / 'inner.jsonl').write_bytes(encode(base(summary='nested')) + b'\n')
        _, coverage = events.read(str(root))
        self.assertEqual((coverage['files'], coverage['records'], coverage['omitted']), (1, 1, 0))
        self.assertEqual(coverage['status'], 'Loaded')

    # Junk never raises; error text never echoes content

    def test_junk_directory_arguments_never_raise(self):
        root = self.directory({'swtor-2026-11-09.jsonl': [base()]})
        for junk in (123, 1.5, b'/tmp', ['x'], {'a': 1}, object(), '\x00', '/nonexistent/bot-events',
                     str(root / 'swtor-2026-11-09.jsonl')):
            with self.subTest(junk=repr(junk)[:40]):
                bots, coverage = events.read(junk)
                self.assertIsInstance(bots, list)
                self.assertIn(coverage['status'], ('Unavailable', 'Off', 'Loaded'))
                self.assertEqual(set(coverage), COVERAGE_KEYS)
        self.assertEqual(events.read(str(root / 'swtor-2026-11-09.jsonl'))[1]['status'], 'Unavailable')
        self.assertEqual(events.read(123)[1]['status'], 'Unavailable')

    def test_junk_file_contents_never_raise_and_are_omitted(self):
        junk = [bytes(b for b in os.urandom(3000) if b != 10), b'\xff\xfe not utf-8\n', '[' * 60000,
                '1' * 5000, '{"a":1,"a":2}',
                '{"x": NaN}', '{"x": Infinity}', '{"x": 1e400}', '{"x":', b'\x00\x00\x00', '{"a":"\\ud800"}']
        root = Path(tempfile.mkdtemp(dir=self.temp.name))
        (root / 'swtor-2026-11-09.jsonl').write_bytes(b''.join(encode(item) + b'\n' for item in junk))
        bots, coverage = events.read(str(root))
        self.assertEqual((bots, coverage['status'], coverage['records']), ([], 'Loaded', 0))
        self.assertEqual(coverage['omitted'], len(junk))
        self.assertTrue(set(coverage['omittedByReason']) <= {'invalid_json', 'oversized_line', 'not_object',
                                                             'not_bot_event'},
                        coverage['omittedByReason'])

    def test_error_text_never_echoes_file_content(self):
        sentinel = 'SENTINEL-7f3a-do-not-echo'
        bots, coverage = self.run_rows(base(severity=sentinel), base(summary=sentinel, severity=9),
                                       f'{{"x": "{sentinel}"', b'\xff' + sentinel.encode())
        self.assertEqual(coverage['records'], 0)
        self.assertNotIn(sentinel, json.dumps(coverage))
        self.assertNotIn(sentinel, json.dumps(bots))

    def test_unexpected_failures_are_contained_per_row_or_per_read(self):
        root = self.directory({'swtor-2026-11-09.jsonl': [base(), base(summary='second')]})
        with patch.object(events, '_parse', side_effect=[KeyError('boom'), events._row(base())]):
            bots, coverage = events.read(str(root))
        self.assertEqual((coverage['records'], coverage['omittedByReason']), (1, {'invalid_row': 1}))
        with patch('bot_event_v1.read_bytes', side_effect=RuntimeError('boom')):
            bots, coverage = events.read(str(root))
        self.assertEqual((bots, coverage['status'], coverage['omitted']), ([], 'Unavailable', None))

    # Privacy

    def test_undisclosed_details_never_surface(self):
        sentinels = ['SECRET-FIELDS-1', 'SECRET-OWNER-2', 'SECRET-CAMP-3', 'SECRET-ACCOUNT-4', 'SECRET-RAW-5',
                     'SECRET-ALT-6']
        rows = [
            base(details={'intent': 'pull', 'fields': {'radius': sentinels[0]}, 'owner_party': {'tank': sentinels[1]},
                          'camp': {'id': sentinels[2]}, 'account': {'email': sentinels[3]},
                          'alternatives': [{'action': sentinels[5], 'relevance': 3}]}),
            death_row({'killer': 'Gorax', 'account': sentinels[3], 'recent_decisions': [
                {'action': 'pull', 'reason': 'R', 'raw': sentinels[4], 'owner': sentinels[1]}]}),
            advice_row({'reason': 'short reason', 'extra_note': sentinels[4]}),
        ]
        bots, coverage = self.run_rows(*rows)
        text = json.dumps(bots)
        for sentinel in sentinels:
            self.assertNotIn(sentinel, text)
        self.assertNotIn(sentinels[5], json.dumps(coverage))

    def test_chat_rows_follow_ai_or_silence(self):
        # BOT_BRAIN_STANDARD 6.6 at ea92d35a: a voiced line is AI, and a non-AI line is logged as dropped.
        def chat(**details):
            return base(event_type='chat', reason='CHAT', correlation_id='hub-reply-1',
                        details={'channel': 'party', 'origin': 'ai', 'voiced': True, **details})
        rows = [chat(),
                chat(voiced=False, drop_reason='NO_LISTENER'),
                chat(voiced=False, drop_reason='NO_LISTENER'),
                chat(origin='canned', voiced=False, drop_reason='NOT_AI'),
                chat(voiced=False)]                                             # dropped, no reason given
        bots, coverage = self.run_rows(*rows)
        self.assertEqual((coverage['records'], coverage['omitted']), (5, 0))
        self.assertEqual(bots[0]['chat'], {'voiced': 1, 'dropped': 4,
                                           'byReason': {'NOT_AI': 1, 'NO_LISTENER': 2, 'not_voiced': 1}})
        self.assertEqual([(e['action'], e['result']) for e in reversed(bots[0]['events'])],
                         [('party', 'voiced'), ('party', 'NO_LISTENER'), ('party', 'NO_LISTENER'),
                          ('party', 'NOT_AI'), ('party', 'not_voiced')])
        # The rule itself: a canned line that was voiced is refused under its own code, never shown as chat.
        self.refused(chat(origin='canned'), 'chat_voiced_not_ai')
        for bad in (chat(origin='canned', voiced=False),                        # non-AI needs drop_reason NOT_AI
                    chat(origin='canned', voiced=False, drop_reason='STALE'),
                    chat(voiced='yes'), chat(drop_reason='BORED'), chat(channel=7), chat(origin=None),
                    chat(route=5), chat(channel='c' * 33),
                    base(event_type='chat', details={'channel': 'party', 'origin': 'ai'})):  # voiced missing
            self.refused(bad, 'invalid_chat')
        self.refused(base(event_type='chat', details=MISSING), 'missing_details')
        self.refused(chat() | {'correlation_id': None}, 'invalid_correlation_id')
        # A bot with no chat rows still has the totals, all zero.
        self.assertEqual(self.accepted(base())[0]['chat'], {'voiced': 0, 'dropped': 0, 'byReason': {}})

    def test_chat_text_rows_are_refused_not_stripped(self):
        sentinel = 'SECRET-CHAT-9'
        bots, coverage = self.run_rows(base(details={'chat_text': sentinel, 'intent': 'say'}),
                                       base(details={'text': sentinel}))
        self.assertEqual((coverage['records'], coverage['omittedByReason']), (0, {'forbidden_text': 2}))
        self.assertNotIn(sentinel, json.dumps([bots, coverage]))

    def test_fixture_directory_loads_as_a_whole(self):
        bots, coverage = events.read(str(FIXTURE))
        self.assertEqual(coverage['status'], 'Loaded')
        self.assertEqual((coverage['records'], coverage['omitted']), (3, 2))
        self.assertEqual(coverage['omittedByReason'], {'not_bot_event': 2})
        self.assertEqual([bot['actorId'] for bot in bots], ['2001', '2002', 'vorrak'])

    def test_schema_files_are_never_read_as_rows(self):
        root = Path(tempfile.mkdtemp(dir=self.temp.name))
        schema = json.loads((FIXTURE / 'dit.bot_event.v1.schema.json').read_text())
        (root / 'schema.jsonl').write_text(json.dumps(schema) + '\n')  # One line, as a row would be.
        _, coverage = events.read(str(root))
        self.assertEqual(coverage['omittedByReason'], {'not_bot_event': 1})

    def test_parse_refuses_oversized_lines_and_surfaces_only_the_mapped_fields(self):
        with self.assertRaises(events.RowRefused):
            events._parse(b'x' * (events.MAX_LINE + 1))
        parsed = events._parse(json.dumps(base()).encode())
        self.assertEqual(set(parsed), {'game', 'actorId', 'ts', 'type', 'severity', 'reason', 'summary', 'level',
                                       'area', 'action', 'result', 'advice', 'killer', 'recent', 'chat'})


if __name__ == '__main__':
    unittest.main()
