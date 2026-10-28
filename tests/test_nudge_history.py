import sqlite3
import tempfile
import unittest
from pathlib import Path
from nudge_history import nudge_history


class NudgeHistoryTests(unittest.TestCase):
    def test_scoped_metadata_and_reply_is_not_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'tasks.sqlite'
            with sqlite3.connect(path) as db:
                db.executescript('CREATE TABLE messages(id TEXT, project TEXT, origin TEXT, text TEXT, created REAL, delivered REAL, status TEXT); CREATE TABLE replies(message_id TEXT, time REAL);')
                db.executemany('INSERT INTO messages VALUES (?,?,?,?,?,?,?)', [
                    ('a', 'claude-dit-v2-admin-center', 'coordinator:relay', 'stall watch: private message', 100, 110, 'replied'),
                    ('b', 'claude-dit-v2-admin-center', 'watcher', 'private alert', 200, None, 'queued'),
                    ('c', 'other', 'watcher', 'private', 300, None, 'queued'),
                    ('d', 'claude-dit-v2-admin-center', 'untrusted', 'stall watch', 400, None, 'queued'),
                ])
                db.executemany('INSERT INTO replies VALUES (?,?)', [('a', 90), ('a', 145)])
            records = nudge_history(path)[1]['nudges']
            self.assertEqual(len(records), 2)
            self.assertEqual(records[1]['replySeconds'], 45)
            self.assertIsNone(records[1]['resumeSeconds'])
            self.assertIsNone(records[0]['repliedAt'])
            self.assertNotIn('private', str(records))

    def test_missing_store_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            results = nudge_history(Path(directory) / 'missing')
            self.assertTrue(all('unavailable' in item['coverage'] for item in results))


if __name__ == '__main__':
    unittest.main()
