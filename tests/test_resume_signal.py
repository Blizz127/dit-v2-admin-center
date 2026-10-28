import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from resume_signal import first_signal, resolve_rollout, work_items


class ResumeSignalTests(unittest.TestCase):
    def test_first_tool_request_in_delivery_window_and_no_content_leak(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rollout.jsonl'
            rows = [
                {'type': 'event_msg', 'timestamp': '2026-01-01T00:00:00Z', 'payload': {'type': 'task_started'}},
                {'type': 'response_item', 'timestamp': '2026-01-01T00:00:07Z', 'payload': {'type': 'function_call', 'arguments': 'private'}},
                {'type': 'response_item', 'timestamp': '2026-01-01T00:00:12Z', 'payload': {'type': 'custom_tool_call', 'input': 'private'}},
            ]
            path.write_text('\n'.join(json.dumps(r) for r in rows))
            observed = work_items(path); start = 1767225605
            signal = first_signal(observed, start, start + 5)
            self.assertEqual(signal['seconds'], 2)
            self.assertNotIn('private', str(signal))
            self.assertIsNone(first_signal(observed, start + 3, start + 5))
            self.assertIsNone(first_signal({'truncated': True, 'earliest': start+1, 'items': [start+2]}, start))
            self.assertIsNone(first_signal(observed, None))

    def test_requires_exact_unique_thread_and_safe_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); sessions=root/'sessions'; sessions.mkdir(); rollout=sessions/'rollout.jsonl'; rollout.write_text('')
            db=root/'threads.sqlite'; project=root/'project'
            with sqlite3.connect(db) as c:
                c.execute('CREATE TABLE threads(id TEXT, cwd TEXT, archived INTEGER, rollout_path TEXT)')
                c.execute('INSERT INTO threads VALUES (?,?,0,?)', ('thread', str(project), str(rollout)))
            self.assertEqual(resolve_rollout(db, sessions, project, 'thread'), rollout)
            self.assertIsNone(resolve_rollout(db, sessions, project, 'wrong'))
            with sqlite3.connect(db) as c: c.execute('INSERT INTO threads VALUES (?,?,0,?)', ('other', str(project), str(rollout)))
            self.assertIsNone(resolve_rollout(db, sessions, project, 'thread'))


if __name__ == '__main__':
    unittest.main()
