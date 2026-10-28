import sqlite3
import json
import tempfile
import unittest
from pathlib import Path
from nudge_history import nudge_history


class NudgeHistoryTests(unittest.TestCase):
    def test_scoped_metadata_and_reply_is_not_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'tasks.sqlite'
            with sqlite3.connect(path) as db:
                db.executescript('CREATE TABLE messages(id TEXT, project TEXT, origin TEXT, text TEXT, created REAL, delivered REAL, status TEXT, agent TEXT, session TEXT); CREATE TABLE replies(message_id TEXT, time REAL);')
                db.executemany('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?)', [
                    ('a', 'claude-dit-v2-admin-center', 'coordinator:relay', 'stall watch: private message', 100, 110, 'replied', 'codex', 'thread'),
                    ('b', 'claude-dit-v2-admin-center', 'watcher', 'private alert', 200, None, 'queued', 'codex', 'thread'),
                    ('c', 'other', 'watcher', 'private', 300, None, 'queued', 'codex', 'thread'),
                    ('d', 'claude-dit-v2-admin-center', 'untrusted', 'stall watch', 400, None, 'queued', 'codex', 'thread'),
                ])
                db.executemany('INSERT INTO replies VALUES (?,?)', [('a', 90), ('a', 145)])
            records = nudge_history(path)[1]['nudges']
            self.assertEqual(len(records), 2)
            self.assertEqual(records[1]['replySeconds'], 45)
            self.assertIsNone(records[1]['resumeSeconds'])
            self.assertIsNone(records[0]['repliedAt'])
            self.assertNotIn('private', str(records))

    def test_matched_rollout_signal_is_scoped_and_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); sessions = root / 'sessions'; sessions.mkdir(); project = root / 'project'
            rollout = sessions / 'rollout.jsonl'
            rollout.write_text(json.dumps({'type': 'response_item', 'timestamp': '2026-01-01T00:00:07Z', 'payload': {'type': 'function_call', 'arguments': 'private'}}))
            codex = root / 'codex.sqlite'; board = root / 'board.sqlite'
            with sqlite3.connect(codex) as c:
                c.execute('CREATE TABLE threads(id TEXT, cwd TEXT, archived INTEGER, rollout_path TEXT)')
                c.execute('INSERT INTO threads VALUES (?,?,0,?)', ('thread', str(project), str(rollout)))
            with sqlite3.connect(board) as c:
                c.executescript('CREATE TABLE messages(id TEXT, project TEXT, origin TEXT, text TEXT, created REAL, delivered REAL, status TEXT, agent TEXT, session TEXT); CREATE TABLE replies(message_id TEXT, time REAL);')
                c.execute('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?)', ('a', 'claude-dit-v2-admin-center', 'watcher', 'private', 1767225600, 1767225605, 'delivered', 'codex', 'thread'))
            records = nudge_history(board, codex, sessions, {'claude-dit-v2-admin-center': project})[1]['nudges']
            self.assertEqual(records[0]['resumeSignal']['seconds'], 2)
            self.assertIsNone(records[0]['resumeSeconds'])
            self.assertNotIn('private', str(records))
            with sqlite3.connect(codex) as c:
                c.execute('INSERT INTO threads VALUES (?,?,0,?)', ('other', str(project), str(rollout)))
            self.assertIsNone(nudge_history(board, codex, sessions, {'claude-dit-v2-admin-center': project})[1]['nudges'][0]['resumeSignal'])

    def test_missing_store_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            results = nudge_history(Path(directory) / 'missing')
            self.assertTrue(all('unavailable' in item['coverage'] for item in results))


if __name__ == '__main__':
    unittest.main()
