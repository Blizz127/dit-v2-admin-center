"""Exercise worker scheduling with synthetic files and no thread or real wait."""
from contextlib import ExitStack
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import server
from quota_history import collect, history


class StopAfter:
    def __init__(self, iterations, after_wait=lambda count: None):
        self.iterations = iterations
        self.waits = []
        self.after_wait = after_wait

    def is_set(self):
        return len(self.waits) >= self.iterations

    def wait(self, seconds):
        self.waits.append(seconds)
        self.after_wait(len(self.waits))
        return self.is_set()


class QuotaWorkerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source, self.local = self.root / 'synthetic-state.json', self.root / 'history'
        self.write_source(1767225600, 0.25)
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch('server.QUOTA_SOURCE', self.source))
        stack.enter_context(patch('server.LOCAL_DATA', self.local))
        for target in ('socket.socket', 'socket.create_connection', 'subprocess.Popen', 'server.HubReader'):
            stack.enter_context(patch(target, side_effect=AssertionError('External dependency forbidden')))

    def write_source(self, checked, used):
        self.source.write_text(json.dumps({'accounts': {'fixture-key': {
            'email': 'fixture@example.invalid', 'secret': 'OMIT_PRIVATE_FIXTURE',
            'usage': {'checked_at': checked, 'rows': [{'quota': {'unified5h': used}}]}}}}))

    def test_minute_interval_deduplication_and_new_snapshot(self):
        def advance(count):
            if count == 2:
                self.write_source(1767225660, 0.5)
        stop = StopAfter(3, advance)
        server.run_quota_collector(stop)
        self.assertEqual(stop.waits, [60, 60, 60])
        rows = history(self.local)
        self.assertEqual(len(rows), 2, 'Repeated source observation is not a new quota sample')
        self.assertEqual({row['remainingPercent'] for row in rows}, {75, 50})
        self.assertNotIn('fixture-key', str(rows))
        self.assertNotIn('OMIT_PRIVATE_FIXTURE', (self.local / 'codex-quota.sqlite').read_bytes().decode('latin1'))
        self.assertEqual((self.local / 'codex-quota.sqlite').stat().st_mode & 0o777, 0o600)

    def test_transient_storage_failures_wait_and_recover_without_changing_source(self):
        original = self.source.read_bytes()
        calls = []
        def attempt(source, root):
            self.assertEqual((source, root), (self.source, self.local))
            calls.append(1)
            if len(calls) == 1:
                raise PermissionError('Synthetic write denied')
            if len(calls) == 2:
                raise sqlite3.OperationalError('Synthetic database locked')
            return collect(source, root)
        stop = StopAfter(3)
        with patch('server.collect', side_effect=attempt):
            server.run_quota_collector(stop)
        self.assertEqual(stop.waits, [60, 60, 60], 'Failure must not create a tight retry loop')
        self.assertEqual(len(history(self.local)), 1)
        self.assertEqual(self.source.read_bytes(), original)

    def test_preexisting_stop_prevents_collection_and_storage_creation(self):
        stop = StopAfter(0)
        with patch('server.collect', side_effect=AssertionError('Collector called after stop')):
            server.run_quota_collector(stop)
        self.assertEqual(stop.waits, [])
        self.assertFalse(self.local.exists())


if __name__ == '__main__':
    unittest.main()
