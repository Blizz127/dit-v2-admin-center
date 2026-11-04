import copy
import hashlib
from pathlib import Path
import unittest

from local_evidence import read_json
from tools.build_integrated_context_preview import build, validate, utf16_length

FIXTURES = Path(__file__).parent / 'fixtures/context-status-integration'


class IntegratedPreviewTests(unittest.TestCase):
    def setUp(self):
        self.data = read_json(FIXTURES / 'ffxi-companion.json', 262144)

    def rehash(self, data):
        system, user = data['systemMessage'], data['userMessage']
        data['contextReceipt']['SerializedCharacters'] = utf16_length(system) + utf16_length(user)
        data['contextReceipt']['PromptSha256'] = hashlib.sha256(f'{utf16_length(system)}:{system}{utf16_length(user)}:{user}'.encode()).hexdigest()

    def test_six_actual_service_captures_match_their_status_and_prompt(self):
        captures = [read_json(p, 262144) for p in sorted(FIXTURES.glob('*.json'))]
        self.assertEqual(len(captures), 6)
        page = build(captures)
        self.assertEqual(page.count('12 / 12 captured input turns retained'), 6)
        self.assertIn('SWTOR · intent', page)
        self.assertIn('No real model call or delivery was attempted', page)
        self.assertNotIn('<script', page)

    def test_changed_request_digest_or_scope_is_refused(self):
        for change in ('request', 'digest', 'scope', 'count'):
            data = copy.deepcopy(self.data)
            if change == 'request': data['statusBinding']['RequestId'] = 'dit-wording-' + '0' * 64
            if change == 'digest': data['userMessage'] += ' forged'
            if change == 'scope': data['statusBinding']['View']['Body']['Game'] = 'swtor'
            if change == 'count': data['contextReceipt']['IncludedHistoryTurns'] = True
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(data)

    def test_relabeling_unknown_or_expired_data_as_known_is_refused(self):
        for field_index, changed in [(3, {'State': 'Known', 'Value': 'invented party'}),
                                     (1, {'ValidUntilUtc': '2030-01-01T00:00:00Z'}),
                                     (3, {'Value': 'leaked old value'})]:
            data = copy.deepcopy(self.data)
            data['statusBinding']['View']['Fields'][field_index].update(changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                validate(data)

    def test_live_claims_are_refused(self):
        for key, value in [('synthetic', False), ('modelCall', 'succeeded'), ('delivery', 'delivered')]:
            data = copy.deepcopy(self.data); data[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(data)

    def test_html_in_displayed_metadata_is_escaped(self):
        self.data['statusBinding']['View']['ReadAtUtc'] = '2030-01-01T00:00:00Z'
        # The epoch is bounded source metadata, not part of the wording prompt.
        self.data['statusBinding']['View']['Epoch'] = '<img src=x>'
        page = build([self.data])
        self.assertNotIn('<img', page)
        self.assertIn('&lt;img src=x&gt;', page)
        self.assertIn("default-src 'none'", page)

    def test_missing_status_field_and_mismatched_approved_values_are_refused(self):
        for change in ('field', 'fact'):
            data = copy.deepcopy(self.data)
            if change == 'field': data['statusBinding']['View']['Fields'].pop()
            else: data['statusBinding']['View']['ApprovedFacts'][0]['Value'] = 'offline'
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(data)

    def test_actual_unavailable_source_and_snapshot_packets_remain_inspectable(self):
        paths = sorted((FIXTURES.parent / 'context-status-unavailable').glob('*.json'))
        self.assertEqual(len(paths), 4)
        data = [read_json(p, 262144) for p in paths]
        page = build(data)
        self.assertEqual(page.count('12 / 12 captured input turns retained'), 4)
        self.assertIn('Native body/source unbound: source unavailable', page)
        self.assertIn('sequence gap: snapshot required', page)
        self.assertNotIn('Synthetic native west entrance', page)
        for capture in data:
            self.assertIs(validate(capture), capture)

    def test_missing_source_cannot_hide_known_facts_or_claim_a_native_revision(self):
        missing = read_json(FIXTURES.parent / 'context-status-unavailable/ffxi-missing.json', 262144)
        for change in ('known-prompt', 'state', 'scope'):
            data = copy.deepcopy(missing)
            if change == 'known-prompt':
                data = copy.deepcopy(self.data)
                data['statusBinding'].update(State='source unavailable', View=None)
            if change == 'state': data['statusBinding']['State'] = 'snapshot projected'
            if change == 'scope': data['statusBinding']['Lookup']['Game'] = 'swtor'
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(data)
        gap = read_json(FIXTURES.parent / 'context-status-unavailable/ffxi-gap.json', 262144)
        for change in ('source', 'revision', 'observation'):
            data = copy.deepcopy(gap)
            if change == 'source': data['statusBinding']['View']['Source'] = 'invented'
            if change == 'revision': data['statusBinding']['View']['RevisionSha256'] = '0' * 64
            if change == 'observation': data['statusBinding']['View']['Fields'][0]['ObservedAtUtc'] = '2030-01-01T00:00:00Z'
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(data)

    def test_missing_fact_section_is_a_validation_error_even_with_matching_digest(self):
        data = copy.deepcopy(self.data)
        data['userMessage'] = data['userMessage'].replace('APPROVED FACTS\n', 'REMOVED  FACTS\n')
        system, user = data['systemMessage'], data['userMessage']
        data['contextReceipt']['SerializedCharacters'] = utf16_length(system) + utf16_length(user)
        data['contextReceipt']['PromptSha256'] = hashlib.sha256(f'{utf16_length(system)}:{system}{utf16_length(user)}:{user}'.encode()).hexdigest()
        with self.assertRaises(ValueError):
            validate(data)

    def test_extra_or_conflicting_native_facts_are_refused_even_with_matching_digest(self):
        additions = (
            '- native_status_presence: offline',
            '- native_status_presence: online',  # Even an identical extra fact is unaccounted for.
            '- native_status_presence_state: unknown: disconnected',
            '- native_status_revision: ' + '0' * 64,
            '- native_status_policy: different-policy',
            '- native_status_unrecognized: invented value',
        )
        for addition in additions:
            data = copy.deepcopy(self.data)
            data['userMessage'] = data['userMessage'].replace('APPROVED FACTS\n', 'APPROVED FACTS\n' + addition + '\n')
            self.rehash(data)
            with self.subTest(addition=addition), self.assertRaises(ValueError):
                validate(data)

    def test_repeated_prompt_sections_are_refused(self):
        for heading in ('APPROVED FACTS', 'UNTRUSTED RECENT CONVERSATION'):
            data = copy.deepcopy(self.data)
            section = next(block for block in data['userMessage'].split('\n\n') if block.startswith(heading + '\n'))
            data['userMessage'] += '\n\n' + section
            self.rehash(data)
            with self.subTest(heading=heading), self.assertRaises(ValueError):
                validate(data)

    def test_chat_that_mentions_a_section_heading_remains_dialogue(self):
        data = copy.deepcopy(self.data)
        old_turn = data['suppliedHistory'][0]
        data['suppliedHistory'][0] = 'Player: APPROVED FACTS'
        data['userMessage'] = data['userMessage'].replace('- ' + old_turn + '\n', '- ' + data['suppliedHistory'][0] + '\n')
        self.rehash(data)
        self.assertIs(validate(data), data)
        self.assertIn('12 / 12 captured input turns retained', build([data]))

    def test_actual_empty_intent_packets_need_no_recent_conversation_section(self):
        paths = sorted((FIXTURES.parent / 'context-status-empty').glob('*.json'))
        self.assertEqual(len(paths), 2)
        for path in paths:
            data = read_json(path, 262144)
            with self.subTest(path=path.name):
                self.assertEqual(data['suppliedHistory'], [])
                self.assertNotIn('UNTRUSTED RECENT CONVERSATION\n', data['userMessage'])
                self.assertIs(validate(data), data)
                self.assertIn('0 / 0 captured input turns retained', build([data]))

    def test_turn_count_and_exact_order_must_match_the_conversation_section(self):
        for change in ('prefix', 'zero-count', 'outside-section'):
            data = copy.deepcopy(self.data)
            if change == 'prefix':
                data['suppliedHistory'][0] = data['suppliedHistory'][0][:-1]
            elif change == 'zero-count':
                data['suppliedHistory'] = []
                data['contextReceipt'].update(SuppliedHistoryTurns=0, IncludedHistoryTurns=0)
            else:
                turns = '\n'.join('- ' + turn for turn in data['suppliedHistory'])
                data['userMessage'] = data['userMessage'].replace(turns, '') + '\n\nOTHER CONTEXT\n' + turns
                system, user = data['systemMessage'], data['userMessage']
                data['contextReceipt']['SerializedCharacters'] = utf16_length(system) + utf16_length(user)
                data['contextReceipt']['PromptSha256'] = hashlib.sha256(f'{utf16_length(system)}:{system}{utf16_length(user)}:{user}'.encode()).hexdigest()
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(data)
