import copy
from pathlib import Path
import unittest

from local_evidence import read_json
from tools.build_integrated_context_preview import build, validate

FIXTURES = Path(__file__).parent / 'fixtures/context-status-integration'


class IntegratedPreviewTests(unittest.TestCase):
    def setUp(self):
        self.data = read_json(FIXTURES / 'ffxi-companion.json', 262144)

    def test_six_actual_service_captures_match_their_status_and_prompt(self):
        captures = [read_json(p, 262144) for p in sorted(FIXTURES.glob('*.json'))]
        self.assertEqual(len(captures), 6)
        page = build(captures)
        self.assertEqual(page.count('12 / 12 supplied turns retained'), 6)
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
