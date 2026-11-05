import copy
import json
from pathlib import Path
from queue import Queue
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from local_evidence import read_json
from tools import run_candidate_delivery_harness as harness

ROOT = Path(__file__).resolve().parents[1]


class CandidateDeliveryHarnessTests(unittest.TestCase):
    def fixture(self, game='ffxi', state='fresh'):
        return read_json(harness.FIXTURES / f'{game}-{state}.json', 262144)

    def test_disabled_does_not_read_or_start_a_worker(self):
        with patch.object(harness, 'read_json', side_effect=AssertionError('No read')), \
                patch.object(harness, 'Thread', side_effect=AssertionError('No worker')):
            self.assertEqual(harness.run()['status'], 'Disabled')
            self.assertEqual(harness.exercise(object())['status'], 'Disabled')
            with self.assertRaises(ValueError):
                harness.run(enabled=1)

    def test_actual_candidate_exports_deliver_only_after_receipt_is_received(self):
        for game in ('ffxi', 'swtor'):
            data = self.fixture(game)
            original = copy.deepcopy(data)
            report = harness.exercise(data, enabled=True)
            with self.subTest(game=game):
                self.assertEqual(report['status'], 'Passed')
                result, = report['results']
                self.assertEqual(result['beforeReceipt']['counts']['syntheticConfirmed'], 0)
                self.assertEqual(result['issuedBeforeReceive']['rejectedReceipts'], 1)
                self.assertEqual(result['afterReceipt']['counts']['syntheticConfirmed'], 1)
                self.assertEqual(result['receivedPackets'], 1)
                self.assertEqual(result['afterReceipt']['records'][0]['text'], data['reply']['Decisions'][0]['Text'])
                self.assertEqual(data, original)
                self.assertFalse(report['nativeDeliveryVerified'])
                self.assertIsNone(report['deliveredInGame'])
                self.assertFalse(report['replayAuthorized'])

    def test_withheld_duplicate_and_corrupted_receipt_transports(self):
        for game in ('ffxi', 'swtor'):
            for case in ('withheld', 'duplicate', 'tampered', 'wrong-session'):
                with self.subTest(game=game, case=case):
                    report = harness.exercise(self.fixture(game), case, enabled=True)
                    self.assertEqual(report['status'], 'Passed')
                    result, = report['results']
                    self.assertEqual(result['afterReceipt']['counts']['syntheticConfirmed'], int(case == 'duplicate'))
                    self.assertEqual(result['afterReceipt']['counts']['duplicateReceiptRecords'], int(case == 'duplicate'))
                    self.assertEqual(result['afterReceipt']['records'][0]['actualDelivery'], 'Unknown')

    def test_candidate_status_refusal_never_starts_a_publication_worker(self):
        for game in ('ffxi', 'swtor'):
            with self.subTest(game=game), patch.object(harness, 'Thread', side_effect=AssertionError('No publication')):
                report = harness.exercise(self.fixture(game, 'expired'), enabled=True)
                result, = report['results']
                self.assertEqual(report['status'], 'Passed')
                self.assertTrue(result['candidateWithheld'])
                self.assertEqual(result['emittedPackets'], 0)
                self.assertEqual(result['receivedPackets'], 0)
                self.assertEqual(result['afterReceipt']['records'], [])

    def test_malformed_or_scope_changed_candidate_is_refused_before_transport(self):
        mutations = [lambda d: d.update(synthetic=False), lambda d: d.update(game='swtor'),
                     lambda d: d.update(channel='wrong-channel'),
                     lambda d: d['capture']['contextReceipt'].update(PromptSha256='0' * 64),
                     lambda d: d['reply']['Decisions'][0].update(Action={'move': True}),
                     lambda d: d['reply']['Decisions'][0].update(ActorKey='another-bot'),
                     lambda d: d['reply']['Decisions'][0].update(Recipient='PrivatePlayer'),
                     lambda d: d.update(scenario='expired-during-generation')]
        for index, mutate in enumerate(mutations):
            data = self.fixture(); mutate(data)
            with self.subTest(index=index), patch.object(harness, 'Thread', side_effect=AssertionError('No transport')):
                with self.assertRaises(ValueError):
                    harness.exercise(data, enabled=True)

    def test_worker_error_cannot_be_a_pass_and_leaves_no_thread(self):
        with patch.object(harness, 'receipt_key', side_effect=ValueError('Synthetic failure')):
            with self.assertRaises(RuntimeError):
                harness.exercise(self.fixture(), enabled=True)
        self.assertFalse(any(thread.name == 'synthetic-receipt-observer' for thread in threading.enumerate()))

    def test_assertions_do_not_mark_missing_confirmation_as_passed(self):
        report = harness.exercise(self.fixture(), enabled=True)
        result, = report['results']
        result['afterReceipt']['counts']['syntheticConfirmed'] = 0
        with self.assertRaises(RuntimeError):
            harness.checked(result)

    def test_receipt_replayed_from_an_earlier_harness_run_cannot_confirm(self):
        previous = []
        results = []
        check = harness.checked

        class ReplayReturnedQueue(Queue):
            def put(self, item, *args, **kwargs):
                if self.maxsize == 2:  # Receipt channel; leave publications untouched.
                    if not previous:
                        previous.append(item)
                    else:
                        item = previous[0]
                return super().put(item, *args, **kwargs)

        def record_check(result):
            results.append(copy.deepcopy(result))
            return check(result)

        with patch.object(harness, 'Queue', ReplayReturnedQueue), patch.object(harness, 'checked', record_check):
            self.assertEqual(harness.exercise(self.fixture(), enabled=True)['status'], 'Passed')
            # The second observer issued a new receipt, but transport returns the old one.
            with self.assertRaisesRegex(RuntimeError, 'invariant failed'):
                harness.exercise(self.fixture(), enabled=True)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[1]['afterReceipt']['counts']['syntheticConfirmed'], 0)
        self.assertEqual(results[1]['afterReceipt']['rejectedReceipts'], 1)
        self.assertEqual(results[1]['afterReceipt']['records'][0]['actualDelivery'], 'Unknown')

    def test_changed_export_is_refused_before_any_worker_starts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for file in harness.FIXTURES.glob('*.json'):
                (root / file.name).write_bytes(file.read_bytes())
            data = self.fixture()
            data['reply']['Decisions'][0]['Text'] = 'different synthetic wording'
            (root / 'ffxi-fresh.json').write_text(json.dumps(data))
            with patch.object(harness, 'FIXTURES', root), patch.object(harness, 'Thread', side_effect=AssertionError('No worker')):
                with self.assertRaisesRegex(ValueError, 'content changed'):
                    harness.run(enabled=True)

    def test_manifest_cannot_select_unlisted_input_files(self):
        manifest = read_json(harness.FIXTURES / 'manifest.json', 4096)
        manifest['contentSha256']['../unrelated.json'] = '0' * 64
        with patch.object(harness, 'read_json', return_value=manifest) as read:
            with self.assertRaises(ValueError):
                harness.run(enabled=True)
            self.assertEqual(read.call_count, 1)

    def test_cli_runs_only_the_explicit_offline_suite(self):
        for args, expected in [([], 'Disabled'), (['--enable-offline'], 'Passed')]:
            run = subprocess.run([sys.executable, '-m', 'tools.run_candidate_delivery_harness', *args],
                                 cwd=ROOT, text=True, capture_output=True, timeout=15)
            with self.subTest(args=args):
                self.assertEqual(run.returncode, 0, run.stderr)
                result = json.loads(run.stdout)
                self.assertEqual(result['status'], expected)
                self.assertEqual(len(result['results']), 12 if args else 0)
                self.assertFalse(result['nativeDeliveryVerified'])
                self.assertIsNone(result['deliveredInGame'])
