"""Synthetic malformed-input checks for runtime JSON and JSONL readers."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import lead_binding
import presence_examples
import quota_history
import resume_signal
import routing_audit
import server
import session_markers
from tools import build_inspector_playtest


BAD_JSON = (b' ' * (1024 * 1024 + 1), b'{"incomplete":', b'[]', b'[' * 20000 + b']' * 20000,
            b'{"key":1,"key":2}', b'{"value":NaN}', b'{"value":1e999}')


class RuntimeJsonInputTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.path = self.root / 'fixture.json'

    def test_cached_quota_and_binding_fail_closed(self):
        for raw in BAD_JSON:
            with self.subTest(size=len(raw)):
                self.path.write_bytes(raw)
                self.assertEqual(quota_history.observations(self.path), [])
                binding = lead_binding.current_codex_binding(self.path, self.root / 'absent.sqlite', self.root)
                self.assertIsNone(binding['provider'])
                self.assertIn('unverified', binding['coverage'])

    def test_committed_fixtures_are_bounded_and_invalid_is_unknown(self):
        model = self.root / 'data/fixtures/model-comparison.json'
        model.parent.mkdir(parents=True)
        # A list is valid for the two list-shaped fixture readers, so use an object instead.
        for raw in (BAD_JSON[0], BAD_JSON[1], b'{}', *BAD_JSON[3:]):
            with self.subTest(size=len(raw)):
                self.path.write_bytes(raw)
                model.write_bytes(raw)
                with patch.object(presence_examples, 'FIXTURE', self.path), \
                     patch.object(routing_audit, 'FIXTURE', self.path), \
                     patch.object(server, 'PROJECT', self.root):
                    self.assertIsNone(presence_examples.examples())
                    self.assertIsNone(routing_audit.examples())
                    self.assertIsNone(server.model_call_examples())

    def test_bad_handoff_metadata_is_unknown(self):
        sessions = self.root / 'sessions'
        sessions.mkdir()
        session_file = sessions / 'fixture.json'
        for raw in BAD_JSON:
            with self.subTest(size=len(raw)):
                self.path.write_bytes(raw)
                session_file.write_bytes(raw)
                report = session_markers.handoff_codex_markers(self.root / 'absent.sqlite', self.root,
                                                               self.root, self.path, 'Example')
                self.assertTrue(report['coverage'].startswith('Session marker coverage unknown'))
                self.assertEqual(report['markers'], [])
                report = session_markers.claude_markers(self.root, self.root / 'project', 'fixture', 'Example')
                self.assertTrue(report['coverage'].startswith('Session marker coverage unknown'))

    def test_bad_jsonl_tail_never_establishes_marker_or_resume_coverage(self):
        valid = json.dumps({'type': 'event_msg', 'timestamp': '2026-01-01T00:00:00Z',
                            'payload': {'type': 'goal_stopped'}}).encode()
        for raw in (b' ' * (resume_signal.MAX_TAIL + 1), BAD_JSON[1], BAD_JSON[2], BAD_JSON[3]):
            with self.subTest(size=len(raw)):
                self.path.write_bytes(valid + b'\n' + raw)
                self.assertIsNone(session_markers.scan(self.path))
                self.assertIsNone(resume_signal.work_items(self.path))
        self.path.unlink()
        os.mkfifo(self.path)
        self.assertIsNone(session_markers.scan(self.path))
        self.assertIsNone(resume_signal.work_items(self.path))

    def test_preview_fixture_reader_refuses_bad_input(self):
        for raw in (BAD_JSON[0], BAD_JSON[1], b'[]', BAD_JSON[3]):
            with self.subTest(size=len(raw)):
                self.path.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, 'fixture unavailable'):
                    build_inspector_playtest.fixture_json(self.path, dict)

    def test_bad_model_fixture_does_not_break_authenticated_overview(self):
        from test_offline_inspector_handler import MemoryConnection
        path = self.root / 'data/fixtures/model-comparison.json'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'{"private marker":')
        wire = (b'GET /api/overview HTTP/1.1\r\nHost: fixture.invalid\r\n'
                b'Authorization: Bearer fixture-token\r\nConnection: close\r\n\r\n')
        connection = MemoryConnection(wire)
        with patch.dict('os.environ', {}, clear=True), patch.object(Path, 'home', return_value=self.root), \
             patch.object(server, 'PROJECT', self.root), patch.object(server, 'LOCAL_DATA', self.root / 'local'):
            server.Handler(connection, ('127.0.0.1', 0), SimpleNamespace(admin_token='fixture-token'))
        head, body = bytes(connection.outgoing).split(b'\r\n\r\n', 1)
        self.assertEqual(int(head.split()[1]), 200)
        self.assertIsNone(json.loads(body)['modelCalls'])
        self.assertNotIn(b'private marker', body)


if __name__ == '__main__':
    unittest.main()
