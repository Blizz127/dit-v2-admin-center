import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from delivery_correlation import LIMIT, correlate, from_file

FIXTURES = Path(__file__).parent / 'fixtures/delivery-correlation'


class DeliveryCorrelationTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((FIXTURES / 'ffxi.json').read_text())

    def check(self, data=None, verifier=lambda _: True):
        return correlate(self.data if data is None else data, enabled=True, native_verifier=verifier)

    def test_disabled_never_reads_file_or_verifies(self):
        with patch('delivery_correlation.read_json', side_effect=AssertionError('No read')) as read:
            self.assertEqual(from_file('/unrelated')['status'], 'Disabled')
            with self.assertRaises(ValueError):
                from_file('/unrelated', enabled=1)
            read.assert_not_called()
        self.assertEqual(correlate(object(), native_verifier=lambda _: self.fail('No verification'))['status'], 'Disabled')

    def test_sent_and_matching_text_are_publication_only_without_verifier(self):
        for receipt in self.data['receipts']:
            receipt['trusted'] = True
        report = self.check(verifier=None)
        self.assertEqual(report['counts']['publicationMatched'], 2)
        self.assertEqual(report['counts']['syntheticConfirmed'], 0)
        self.assertTrue(all(row['actualDelivery'] == 'Unknown' for row in report['records']))
        self.assertIsNone(report['deliveredInGame'])
        self.assertFalse(report['nativeDeliveryVerified'])
        self.assertFalse(report['replayAuthorized'])

    def test_two_games_and_intentional_repeats_keep_separate_native_identities(self):
        for game in ('ffxi', 'swtor'):
            data = json.loads((FIXTURES / (game + '.json')).read_text())
            report = self.check(data)
            with self.subTest(game=game):
                self.assertEqual(report['counts']['syntheticConfirmed'], 2)
                first, second, rotated, draft = report['records']
                self.assertEqual(first['text'], second['text'])
                self.assertNotEqual(first['correlationId'], second['correlationId'])
                self.assertNotEqual(first['nativeObservationId'], second['nativeObservationId'])
                self.assertEqual(rotated['publication'], 'Uncorroborated')
                self.assertEqual(draft['publication'], 'Not evidenced')
                self.assertTrue(all(row['actualDelivery'] == 'Unknown' for row in report['records']))

    def test_duplicate_logs_and_receipts_do_not_double_count(self):
        self.data['decisions'].append(copy.deepcopy(self.data['decisions'][0]))
        self.data['inbox'].append(copy.deepcopy(self.data['inbox'][0]))
        self.data['receipts'].append(copy.deepcopy(self.data['receipts'][0]))
        report = self.check()
        self.assertEqual(report['counts']['recordedAttempts'], 4)
        self.assertEqual(report['counts']['syntheticConfirmed'], 2)
        self.assertEqual(report['counts']['duplicateDecisionRecords'], 1)
        self.assertEqual(report['counts']['duplicateReceiptRecords'], 1)

    def test_scope_epoch_session_and_text_digest_must_match(self):
        for field in (*self.data['scope'], 'bridgeSession', 'textSha256'):
            data = copy.deepcopy(self.data)
            data['receipts'] = data['receipts'][:1]
            receipt = data['receipts'][0]
            if field in data['scope']:
                receipt['scope'][field] = 'swtor' if field == 'game' else 'another'
            else:
                receipt[field] = '0' * 64 if field == 'textSha256' else 'another'
            with self.subTest(field=field):
                report = self.check(data)
                self.assertEqual(report['counts']['syntheticConfirmed'], 0)
                self.assertEqual(report['rejectedReceipts'], 1)

    def test_receipt_identity_collision_and_two_observations_of_one_send_are_conflicts(self):
        for field in ('receiptId', 'observationId', 'inboxSeq'):
            data = copy.deepcopy(self.data)
            data['receipts'][1][field] = data['receipts'][0][field]
            report = self.check(data)
            with self.subTest(field=field):
                self.assertEqual(report['counts']['syntheticConfirmed'], 0)
                self.assertGreater(report['counts']['conflicted'], 0)

    def test_conflicting_publication_records_cannot_be_confirmed(self):
        for kind in ('inbox', 'decision'):
            data = copy.deepcopy(self.data)
            if kind == 'inbox':
                data['inbox'].append(data['inbox'][0] | {'text': 'different'})
            else:
                conflict = copy.deepcopy(data['decisions'][0])
                conflict['replies'][0]['text_final'] = 'different'
                data['decisions'].append(conflict)
            with self.subTest(kind=kind):
                first = self.check(data)['records'][0]
                self.assertEqual(first['publication'], 'Conflict')
                self.assertEqual(first['fixtureConfirmation'], 'Unknown')

    def test_missing_inbox_or_receipt_does_not_mean_not_delivered(self):
        for key in ('inbox', 'receipts'):
            data = copy.deepcopy(self.data); data[key] = []
            report = self.check(data)
            with self.subTest(key=key):
                self.assertEqual(report['counts']['syntheticConfirmed'], 0)
                self.assertIsNone(report['deliveredInGame'])
                self.assertTrue(all(row['actualDelivery'] == 'Unknown' for row in report['records']))

    def test_conflicting_wording_is_withheld_in_either_record_order(self):
        for reverse in (False, True):
            data = copy.deepcopy(self.data)
            conflict = copy.deepcopy(data['decisions'][0])
            conflict['replies'][0].update(text_final='ARBITRARY_CONFLICTING_WORDING', bot='AnotherLabel')
            data['decisions'].append(conflict)
            if reverse:
                data['decisions'].reverse()
            report = self.check(data)
            record = next(row for row in report['records'] if row['inboxSeq'] == 41)
            with self.subTest(reverse=reverse):
                self.assertEqual(record['publication'], 'Conflict')
                self.assertIsNone(record['text'])
                self.assertIsNone(record['bot'])
                self.assertNotIn('ARBITRARY_CONFLICTING_WORDING', json.dumps(report))

    def test_receipt_arrival_order_does_not_rewrite_native_observation_time(self):
        self.data['receipts'].reverse()
        report = self.check()
        first = report['records'][0]
        self.assertEqual(first['observedAtUtc'], '2030-01-01T00:00:01Z')
        self.assertEqual(first['receivedAtUtc'], '2030-01-01T00:00:11Z')
        for observed, received in [('2029-12-31T23:59:59Z', '2030-01-01T00:00:11Z'),
                                   ('2030-01-01T00:00:12Z', '2030-01-01T00:00:11Z')]:
            data = copy.deepcopy(self.data)
            data['receipts'] = [data['receipts'][1] | dict(observedAtUtc=observed, receivedAtUtc=received)]
            self.assertEqual(self.check(data)['counts']['syntheticConfirmed'], 0)

    def test_verifier_is_explicit_exact_boolean_and_cannot_mutate_binding(self):
        def mutate(receipt):
            receipt['scope']['game'] = 'swtor'
            return True
        for verifier in (None, lambda _: 1, lambda _: False, mutate):
            self.assertEqual(self.check(verifier=verifier)['counts']['syntheticConfirmed'], 0)
        self.assertEqual(self.data['scope']['game'], 'ffxi')

    def test_bad_scope_or_shape_fails_whole_capture_and_bad_receipt_is_counted(self):
        for change in ('synthetic', 'scope', 'type', 'number', 'count'):
            data = copy.deepcopy(self.data)
            if change == 'synthetic': data['synthetic'] = False
            if change == 'scope': data['decisions'][0]['scope'] = 'different-room'
            if change == 'type': data['decisions'][0]['replies'] = {}
            if change == 'number': data['inbox'][0]['seq'] = True
            if change == 'count': data['inbox'] *= 129
            with self.subTest(change=change):
                report = self.check(data)
                self.assertEqual(report['status'], 'Unavailable')
                self.assertIsNone(report['counts'])
                self.assertEqual(report['records'], [])
        self.data['receipts'] = [None, {}, {'trusted': True}]
        self.assertEqual(self.check()['rejectedReceipts'], 3)

    def test_bounded_file_reader_recovers_without_mutating_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'fixture.json'
            valid = json.dumps(self.data).encode()
            for content in (b'{"schema":', b'[]', b'x' * (LIMIT + 1), b'[' * 1800 + b'0' + b']' * 1800,
                            b'{"schema":1,"schema":2}'):
                path.write_bytes(content)
                self.assertEqual(from_file(path, enabled=True)['status'], 'Unavailable')
                self.assertEqual(path.read_bytes(), content)
            path.write_bytes(valid)
            self.assertEqual(from_file(path, enabled=True)['status'], 'Loaded')
            self.assertEqual(path.read_bytes(), valid)
            link = path.with_name('link.json'); link.symlink_to(path)
            self.assertEqual(from_file(link, enabled=True)['status'], 'Unavailable')
