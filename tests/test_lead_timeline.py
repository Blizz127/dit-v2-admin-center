import sqlite3
import tempfile
import unittest
from pathlib import Path

from lead_timeline import timeline


class LeadTimelineTests(unittest.TestCase):
    def test_exact_scope_and_bounded_task_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with sqlite3.connect(root / 'tasks.sqlite') as db:
                db.executescript('CREATE TABLE tasks(id TEXT, project TEXT, agent TEXT); CREATE TABLE events(task TEXT, status TEXT, time REAL);')
                db.execute('INSERT INTO tasks VALUES (?, ?, ?)', ('one', 'claude-dit-human-behavior-platform', 'claude'))
                db.execute('INSERT INTO tasks VALUES (?, ?, ?)', ('other', 'unrelated', 'claude'))
                db.executemany('INSERT INTO events VALUES (?, ?, ?)', [('one', 'working', n) for n in range(12)] + [('other', 'blocked', 99)])
            rows = timeline(root)
            self.assertEqual(len(rows[0]['events']), 10)
            self.assertTrue(all(e['status'] == 'working' and e['kind'] == 'Task status' for e in rows[0]['events']))
            self.assertIn('unknown', rows[1]['coverage'])
            self.assertEqual(rows[1]['events'], [])

    def test_missing_database_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            result = timeline(Path(directory))
            self.assertTrue(all(r['coverage'] == 'Coordinator history unavailable' for r in result))
            self.assertFalse((Path(directory) / 'tasks.sqlite').exists())


if __name__ == '__main__':
    unittest.main()
