import sqlite3
import json
import tempfile
import unittest
from pathlib import Path

from lead_timeline import timeline


class LeadTimelineTests(unittest.TestCase):
    def test_exact_scope_and_bounded_task_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with sqlite3.connect(root / 'tasks.sqlite') as db:
                db.executescript('CREATE TABLE tasks(id TEXT, project TEXT, agent TEXT); CREATE TABLE events(task TEXT, status TEXT, time REAL); CREATE TABLE watch_alerts(target TEXT, kind TEXT, time REAL);')
                db.execute('INSERT INTO tasks VALUES (?, ?, ?)', ('one', 'claude-dit-human-behavior-platform', 'claude'))
                db.execute('INSERT INTO tasks VALUES (?, ?, ?)', ('other', 'unrelated', 'claude'))
                db.executemany('INSERT INTO events VALUES (?, ?, ?)', [('one', 'working', n) for n in range(12)] + [('other', 'blocked', 99)])
            (root / 'watch.json').write_text(json.dumps({'targets': [{'name': 'hub-watch', 'project': 'claude-dit-human-behavior-platform', 'agent': 'claude'}]}))
            with sqlite3.connect(root / 'tasks.sqlite') as db:
                db.execute('INSERT INTO watch_alerts VALUES (?, ?, ?)', ('hub-watch', 'STALLED', 100))
                db.execute('INSERT INTO watch_alerts VALUES (?, ?, ?)', ('other', 'STOPPED', 101))
            rows = timeline(root)
            self.assertEqual(len(rows[0]['events']), 11)
            alerts = [e for e in rows[0]['events'] if e['kind'] == 'Watcher alert']
            self.assertEqual([e['status'] for e in alerts], ['STALLED'])
            self.assertEqual(rows[0]['watchCoverage'], 'Recent watcher alerts only')
            self.assertIn('unknown', rows[1]['coverage'])
            self.assertEqual(rows[1]['events'], [])

    def test_missing_database_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            result = timeline(Path(directory))
            self.assertTrue(all(r['coverage'] == 'Coordinator history unavailable' for r in result))
            self.assertFalse((Path(directory) / 'tasks.sqlite').exists())


if __name__ == '__main__':
    unittest.main()
