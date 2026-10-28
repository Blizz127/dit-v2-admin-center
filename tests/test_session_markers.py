import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from session_markers import admin_markers, scan


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
