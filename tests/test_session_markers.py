import json
import os
import re
import uuid
import sqlite3
import tempfile
import unittest
from pathlib import Path

from session_markers import admin_markers, claude_markers, handoff_codex_markers, scan


class SessionMarkerTests(unittest.TestCase):
    def test_native_events_only_and_no_text_returned(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rollout.jsonl'
            rows = [
                {'type': 'response_item', 'timestamp': '2026-01-01T00:00:00Z', 'payload': {'type': 'message', 'role': 'user', 'text': 'goal stopped'}},
                {'type': 'event_msg', 'timestamp': '2026-01-01T00:01:00Z', 'payload': {'type': 'error', 'message': 'Usage limit reached; private details'}},
                {'type': 'event_msg', 'timestamp': '2026-01-01T00:02:00Z', 'payload': {'type': 'goal_stopped'}},
            ]
            path.write_text('\n'.join(json.dumps(r) for r in rows))
            hits = scan(path)
            self.assertEqual([h['kind'] for h in hits], ['Possible usage limit', 'Possible goal stop'])
            self.assertNotIn('private details', str(hits))

    def test_claude_requires_exact_live_binding_and_system_event(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); project = root / 'project'; session = str(uuid.uuid4())
            (root / 'sessions').mkdir(); slug = re.sub(r'[^A-Za-z0-9]', '-', str(project))
            transcript = root / 'projects' / slug / (session + '.jsonl'); transcript.parent.mkdir(parents=True)
            transcript.write_text(json.dumps({'type': 'system', 'subtype': 'error', 'timestamp': '2026-01-01T00:00:00Z', 'content': 'Usage limit reached'}))
            info = {'pid': os.getpid(), 'sessionId': session, 'cwd': str(project), 'tmux': 'lead:0', 'peerProtocol': 1, 'messagingSocketPath': '/example'}
            (root / 'sessions' / 'one.json').write_text(json.dumps(info))
            report = claude_markers(root, project, 'lead', 'Example')
            self.assertEqual(report['markers'][0]['kind'], 'Possible usage limit')
            (root / 'sessions' / 'two.json').write_text(json.dumps(info))
            self.assertIn('no unique live native Claude session', claude_markers(root, project, 'lead', 'Example')['coverage'])

    def test_handoff_requires_unique_marker_and_exact_project(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); sessions = root / 'sessions'; sessions.mkdir(); project = root / 'project'
            rollout = sessions / 'rollout.jsonl'; rollout.write_text(json.dumps({'type': 'event_msg', 'timestamp': '2026-01-01T00:00:00Z', 'payload': {'type': 'goal_stopped'}}))
            db = root / 'state.sqlite'; lane = root / 'lane.json'
            lane.write_text(json.dumps({'provider': 'codex', 'cwd': str(project), 'marker': 'UNIQUE'}))
            with sqlite3.connect(db) as connection:
                connection.execute('CREATE TABLE threads(id TEXT, cwd TEXT, archived INTEGER, rollout_path TEXT, first_user_message TEXT)')
                connection.execute('INSERT INTO threads VALUES (?,?,0,?,?)', ('one', str(project), str(rollout), 'assignment UNIQUE'))
            result = handoff_codex_markers(db, sessions, project, lane, 'Lead')
            self.assertEqual(result['markers'][0]['kind'], 'Possible goal stop')
            self.assertIn('live process unverified', result['coverage'])
            with sqlite3.connect(db) as connection:
                connection.execute('INSERT INTO threads VALUES (?,?,0,?,?)', ('two', str(project), str(rollout), 'assignment UNIQUE'))
            self.assertIn('exactly one', handoff_codex_markers(db, sessions, project, lane, 'Lead')['coverage'])

    def test_ambiguous_or_outside_session_remains_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); sessions = root / 'sessions'; sessions.mkdir()
            db_path = root / 'state.sqlite'; project = root / 'project'
            with sqlite3.connect(db_path) as db:
                db.execute('CREATE TABLE threads(cwd TEXT, archived INTEGER, rollout_path TEXT)')
                db.execute('INSERT INTO threads VALUES (?,0,?)', (str(project), str(root / 'outside.jsonl')))
            (root / 'outside.jsonl').write_text('')
            self.assertEqual(admin_markers(db_path, sessions, project)['coverage'], 'Session marker coverage unknown')
            with sqlite3.connect(db_path) as db:
                db.execute('INSERT INTO threads VALUES (?,0,?)', (str(project), str(root / 'outside.jsonl')))
            self.assertEqual(admin_markers(db_path, sessions, project)['markers'], [])


if __name__ == '__main__':
    unittest.main()
