import copy
import hashlib
from pathlib import Path
import unittest

from local_evidence import read_json
from tools.build_context_receipt_preview import build, utf16_length, validate

FIXTURES = Path(__file__).parent / 'fixtures/context-captures'


def rehash(data):
    system, user = data['systemMessage'], data['userMessage']
    data['receipt']['SerializedCharacters'] = utf16_length(system) + utf16_length(user)
    data['receipt']['PromptSha256'] = hashlib.sha256(
        f'{utf16_length(system)}:{system}{utf16_length(user)}:{user}'.encode()).hexdigest()


class ContextReceiptPreviewTests(unittest.TestCase):
    def setUp(self):
        self.data = read_json(FIXTURES / 'ffxi-rewrite.json', 262144)

    def test_actual_captured_ffxi_and_swtor_prompts_keep_the_exchange(self):
        paths = sorted(FIXTURES.glob('*.json'))
        self.assertEqual(len(paths), 4)
        records = [read_json(p, 262144) for p in paths]
        page = build(records)
        self.assertEqual(page.count('12 of 12 supplied turns included'), 4)
        self.assertIn('FFXI · rewrite', page)
        self.assertIn('SWTOR · reply', page)
        self.assertIn('Shared status projection: not implemented', page)
        self.assertIn('Native delivery: not attempted', page)
        self.assertNotIn('<script', page.lower())
        self.assertIn("default-src 'none'", page)

    def test_mismatched_digest_and_coverage_are_refused(self):
        for field, value in [('PromptSha256', '0' * 64), ('IncludedHistoryTurns', 11),
                             ('SuppliedHistoryTurns', True), ('OmittedHistoryTurns', -1),
                             ('SerializedCharacters', 1), ('MaximumSerializedCharacters', 50000)]:
            data = copy.deepcopy(self.data)
            data['receipt'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(data)

    def test_missing_current_input_or_reordered_turns_are_refused_even_with_matching_hash(self):
        for replacement in ('current', 'turn'):
            data = copy.deepcopy(self.data)
            if replacement == 'current':
                data['userMessage'] = data['userMessage'].replace('LATEST LINE, the one you are answering:', 'Removed:')
            else:
                data['suppliedHistory'][0], data['suppliedHistory'][1] = data['suppliedHistory'][1], data['suppliedHistory'][0]
            rehash(data)
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                validate(data)

    def test_prompt_markup_is_displayed_as_text(self):
        data = copy.deepcopy(self.data)
        data['systemMessage'] += '\n<script>alert(1)</script><img src=https://example.invalid>'
        rehash(data)
        page = build([data])
        self.assertNotIn('<script>', page)
        self.assertNotIn('<img ', page)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)

    def test_live_or_invented_verification_claims_are_refused(self):
        for key, value in [('synthetic', False), ('status', 'fresh'), ('delivery', 'delivered'), ('tokens', 0)]:
            data = copy.deepcopy(self.data); data[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(data)

    def test_receipt_counts_utf16_not_python_codepoints(self):
        data = copy.deepcopy(self.data)
        data['systemMessage'] += ' 🧭'
        rehash(data)
        self.assertIs(validate(data), data)
        data['receipt']['SerializedCharacters'] = len(data['systemMessage']) + len(data['userMessage'])
        with self.assertRaises(ValueError):
            validate(data)
