"""Bounded deterministic truncation and wrong-type checks using synthetic inputs."""
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from types import SimpleNamespace

import bakeoff_run
import evaluator_snapshot
import hub_snapshot
import project_issues
import quota_history
import wake_verification
from bridge_status import BridgeObserver
from live_hub import HubReadError, HubReader, MAX_RESPONSE, read_views
from mock_routing import BotKey
from mock_routing_api import MockRoutingAPI, PATH
from tools import review_native_attempt, run_keyboard_playtest

FIXTURES = Path(__file__).resolve().parent / 'fixtures'


def mutations(raw):
    # Only genuinely invalid JSON prefixes; some empty inputs or numeric values
    # can otherwise be valid JSON values, depending on the fixture.
    cuts = sorted({1, 2, len(raw) // 5, len(raw) // 2, len(raw) - 1})
    for cut in cuts:
        candidate = raw[:cut]
        try:
            json.loads(candidate)
        except (ValueError, RecursionError):
            yield candidate
    yield from (b'null', b'true', b'"wrong-type"')


class JsonPrefixMutationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_snapshot_and_bakeoff_manifest_mutations_withhold_runs(self):
        snapshot = self.root / 'snapshot'
        run = self.root / 'run'
        shutil.copytree(FIXTURES / 'hub-snapshot', snapshot)
        shutil.copytree(FIXTURES / 'bakeoff-run', run)
        now = lambda: datetime(2026, 1, 2, tzinfo=timezone.utc)
        for root, reader in ((snapshot, 'hub'), (run, 'bakeoff')):
            path = root / 'manifest.json'
            original = path.read_bytes()
            for raw in mutations(original):
                with self.subTest(reader=reader, length=len(raw)):
                    path.write_bytes(raw)
                    if reader == 'hub':
                        with self.assertRaises(HubReadError):
                            hub_snapshot.SnapshotReader(root, now).label()
                    else:
                        rows, coverage = bakeoff_run.load(root)
                        self.assertEqual((rows, coverage['status']), ([], 'Unavailable'))

    def test_evaluator_and_wake_mutations_do_not_invent_results(self):
        path = self.root / 'input.json'
        sources = (('evaluator', (FIXTURES / 'evaluator-snapshot.json').read_bytes()),
                   ('wake', (FIXTURES / 'wake-verification/reported.json').read_bytes()))
        for kind, original in sources:
            for raw in mutations(original):
                with self.subTest(reader=kind, length=len(raw)):
                    path.write_bytes(raw)
                    if kind == 'evaluator':
                        rows, coverage = evaluator_snapshot.load(path)
                        self.assertEqual((rows, coverage['status']), ([], 'Unavailable'))
                    else:
                        result = wake_verification.read(path)
                        self.assertIsNone(result['cutover'])
                        self.assertTrue(all(row['status'] in ('Held', 'Unverified') for row in result['rows']))

    def test_quota_and_document_mutations_remain_unknown(self):
        quota = self.root / 'quota.json'
        original = json.dumps({'accounts': {'fixture': {'email': 'fixture@example.invalid',
                   'usage': {'checked_at': 1000, 'rows': [{'quota': {'unified5h': .25}}]}}}}).encode()
        for raw in mutations(original):
            with self.subTest(reader='quota', length=len(raw)):
                quota.write_bytes(raw)
                self.assertEqual(quota_history.observations(quota), [])
        name = project_issues.DOCUMENTS[0]
        document = self.root / name
        document.parent.mkdir(parents=True, exist_ok=True)
        issue = {'id': 'example', 'title': 'Example', 'scope': 'Network', 'status': 'Documented gap',
                 'detail': 'Synthetic detail', 'suggestedFix': 'Review'}
        for raw in mutations(json.dumps([issue]).encode()):
            with self.subTest(reader='document', length=len(raw)):
                document.write_bytes(project_issues.START.encode() + b'\n```json\n' + raw + b'\n```\n' + project_issues.END.encode())
                self.assertEqual(project_issues.read(self.root)[0]['status'], 'Unknown')

    def test_bridge_and_mock_request_mutations_do_not_create_claims(self):
        bridge = {'observedAt': '2026-01-01T00:00:00Z', 'unit': 'active', 'substate': 'running',
                  'result': 'success', 'marker': 'absent', 'markerReason': 'unknown'}
        for raw in mutations(json.dumps(bridge).encode()):
            with self.subTest(reader='bridge', length=len(raw)):
                observer = BridgeObserver(lambda *_args, **_kwargs: SimpleNamespace(stdout=raw.decode()), lambda: 0)
                self.assertEqual(observer.read()['unit'], 'unknown')
        request = (FIXTURES / 'mock-routing-write.json').read_bytes()
        api = MockRoutingAPI([BotKey('example-game', 'example-realm', 'example-bot', 'conversation')],
                             ['example-model'])
        before = api.request('GET', PATH)
        for raw in mutations(request):
            with self.subTest(reader='mock routing', length=len(raw)):
                self.assertEqual(api.request('POST', PATH, raw)[0], 400)
                self.assertEqual(api.request('GET', PATH), before)

    def test_hub_response_mutations_fall_back_without_network(self):
        token = self.root / 'fixture-token'
        token.write_text('synthetic-token')
        response = json.dumps([{'key': 'fixture', 'name': 'Fixture'}]).encode()
        raw_cases = list(mutations(response)) + [b' ' * (MAX_RESPONSE + 1), b'[' * 20000 + b']' * 20000]
        for raw in raw_cases:
            with self.subTest(length=len(raw)):
                reader = HubReader('http://127.0.0.1:1', token)
                reader.opener = SimpleNamespace(open=lambda *_args, **_kwargs: io.BytesIO(raw))
                result = read_views(reader, games=('ffxi',))
                self.assertEqual((result['bots'], result['learning'], result['gameStatus']), ({}, {}, {}))
                self.assertTrue(all(feed['status'] == 'Unavailable' for feed in result['feeds']))

    def test_reported_device_receipts_do_not_pass_on_mutated_inputs(self):
        from test_native_attempt_review import seed
        seed(self.root)
        path = self.root / 'attempt.json'
        original = path.read_bytes()
        for raw in mutations(original):
            with self.subTest(reader='native review', length=len(raw)):
                path.write_bytes(raw)
                self.assertEqual(review_native_attempt.review(self.root, datetime(2026, 10, 31, tzinfo=timezone.utc))['status'],
                                 'incomplete')
        receipt = json.dumps({'status': 'passed', 'nativeKeyboard': 'passed', 'steps': 12}).encode()
        for raw in mutations(receipt):
            with self.subTest(reader='keyboard receipt', length=len(raw)):
                try:
                    parsed = run_keyboard_playtest.decode_receipt(raw.decode())
                except (ValueError, RecursionError):
                    continue
                self.assertFalse(run_keyboard_playtest.valid_receipt(parsed))


if __name__ == '__main__':
    unittest.main()
