import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from server import lead_monitoring


class LeadBindingTests(unittest.TestCase):
    def test_only_fresh_exact_thread_watcher_is_attributed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / '.local/share/devbox-coordinator-state'
            root.mkdir(parents=True)
            target = {'name': 'bound', 'project': 'claude-dit-human-behavior-platform',
                      'agent': 'codex', 'session': 'fixture-thread'}
            binding = {'provider': 'codex', 'thread': 'fixture-thread', 'coverage': 'Fixture binding'}
            for session, checked, expected in [('fixture-thread', 1000, 'OK'),
                                               ('old-thread', 1000, 'Unknown'),
                                               ('fixture-thread', 800, 'Unknown'),
                                               ('fixture-thread', 1011, 'Unknown')]:
                (root / 'watch.json').write_text(json.dumps({'targets': [{**target, 'session': session}]}))
                (root / 'watch-state.json').write_text(json.dumps({'bound': {'kind': 'OK', 'checked': checked}}))
                with self.subTest(session=session, checked=checked), \
                     patch('pathlib.Path.home', return_value=Path(directory)), \
                     patch('server.current_codex_binding', return_value=binding), \
                     patch('server.time.time', return_value=1010), \
                     patch('server.session_activity', return_value='fixture'):
                    hub = lead_monitoring()[0]
                    self.assertEqual(hub['stall'], expected)
                    self.assertEqual(hub['provider'], 'codex')
                    self.assertEqual(hub['quota'], 'Unknown')

    def test_old_provider_watcher_not_attributed_to_rotated_lead(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / '.local/share/devbox-coordinator-state'
            root.mkdir(parents=True)
            (root / 'watch.json').write_text(json.dumps({'targets': [
                {'name': 'old', 'project': 'claude-dit-human-behavior-platform', 'agent': 'claude'}]}))
            (root / 'watch-state.json').write_text(json.dumps({'old': {'kind': 'OK', 'checked': 1000}}))
            (root / 'routing-capacity.json').write_text(json.dumps({'checked_at': 1000, 'providers': {'claude': {'remaining': 1}}}))
            with patch('pathlib.Path.home', return_value=Path(directory)), patch('server.session_activity', return_value='fixture'):
                hub = lead_monitoring()[0]
            self.assertEqual(hub['stall'], 'Unknown')
            self.assertIn('binding is unverified', hub['stallReason'])
            self.assertEqual(hub['poolCapacity'], 'Unknown')
            self.assertIn('identity is not established', hub['poolReason'])


if __name__ == '__main__': unittest.main()
