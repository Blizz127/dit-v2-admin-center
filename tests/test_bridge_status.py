import json
import subprocess
import unittest
from types import SimpleNamespace
from bridge_status import BridgeObserver


class BridgeObserverTests(unittest.TestCase):
    def test_read_only_fixed_command_and_cache(self):
        calls = []
        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(stdout=json.dumps({'observedAt': '2026-01-01T00:00:00Z', 'unit': 'failed', 'substate': 'failed', 'result': 'exit-code', 'marker': 'present', 'markerReason': 'delayed_delivery_failed'}))
        observer = BridgeObserver(runner, lambda: 10)
        result = observer.read(); observer.read()
        self.assertEqual(result['marker'], 'present')
        self.assertEqual(len(calls), 1)
        self.assertIn('StrictHostKeyChecking=yes', calls[0][0])
        self.assertIn("os.O_RDONLY", calls[0][1]['input'])
        self.assertNotIn('restart', calls[0][0])

    def test_fail_closed_on_timeout_or_unexpected_data(self):
        def timeout(*args, **kwargs): raise subprocess.TimeoutExpired('ssh', 8)
        self.assertEqual(BridgeObserver(timeout, lambda: 0).read()['marker'], 'unknown')
        def invalid(*args, **kwargs): return SimpleNamespace(stdout=json.dumps({'observedAt': 'x', 'unit': 'active', 'substate': 'running', 'result': 'success', 'marker': 'present', 'markerReason': 'private'}))
        result = BridgeObserver(invalid, lambda: 0).read()
        self.assertEqual(result['unit'], 'unknown')
        self.assertNotIn('private', str(result))

    def test_rejects_missing_timestamp_or_fault_without_marker(self):
        good = {'observedAt': '2026-01-01T00:00:00Z', 'unit': 'active', 'substate': 'running',
                'result': 'success', 'marker': 'absent', 'markerReason': 'unknown'}
        for override in ({'observedAt': ''}, {'observedAt': '2026-01-01T00:00:00'},
                         {'markerReason': 'delayed_delivery_failed'}):
            payload = {**good, **override}
            observer = BridgeObserver(lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps(payload)), lambda: 0)
            with self.subTest(override=override):
                result = observer.read()
                self.assertEqual(result['unit'], 'unknown')
                self.assertEqual(result['markerReason'], 'unknown')
        observer = BridgeObserver(lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps(good)), lambda: 0)
        self.assertEqual(observer.read()['marker'], 'absent')


if __name__ == '__main__': unittest.main()
