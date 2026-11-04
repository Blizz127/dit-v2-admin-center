import sqlite3
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from lead_timeline import add_checkout_history, add_current_evidence, monitoring_issues, timeline


class LeadTimelineTests(unittest.TestCase):
    def test_bad_watcher_config_preserves_task_history_as_unverified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with sqlite3.connect(root / 'tasks.sqlite') as db:
                db.executescript('CREATE TABLE tasks(id TEXT, project TEXT, agent TEXT); CREATE TABLE events(task TEXT, status TEXT, time REAL); CREATE TABLE watch_alerts(target TEXT, kind TEXT, time REAL);')
                db.execute('INSERT INTO tasks VALUES (?, ?, ?)', ('one', 'claude-dit-human-behavior-platform', 'claude'))
                db.execute('INSERT INTO events VALUES (?, ?, ?)', ('one', 'working', 1000))
            for raw in (b' ' * (1024 * 1024 + 1), b'{"targets":', b'[]', b'[' * 20000 + b']' * 20000):
                with self.subTest(size=len(raw)):
                    (root / 'watch.json').write_bytes(raw)
                    row = timeline(root)[0]
                    self.assertEqual(row['events'][0]['status'], 'working')
                    self.assertEqual(row['watchCoverage'], 'Unknown: no unambiguous watcher target')

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

    def test_session_activity_and_watcher_remain_distinct(self):
        rows = [{'lead': 'Example', 'events': []}]
        add_current_evidence(rows, [{'lead': 'Example', 'sessionActivity': '2026-01-01T01:00:00+00:00',
                                    'stall': 'STOPPED', 'stallObservedAt': '2026-01-01T02:00:00+00:00'}])
        self.assertEqual(rows[0]['events'][0]['kind'], 'Watcher classification')
        self.assertEqual(rows[0]['events'][1]['status'], 'Activity observed; idle state unknown')
        self.assertIn('may be stale', rows[0]['events'][0]['source'])

    def test_stopped_session_is_not_a_stopped_goal(self):
        issues = monitoring_issues([{'lead': 'Example', 'stall': 'STOPPED', 'stallObservedAt': '2026-01-01T00:00:00Z'}])
        self.assertEqual(issues[0]['status'], 'Unknown')
        self.assertIn('not a stopped-goal report', issues[1]['detail'])
        self.assertIn('session', issues[1]['title'])
        self.assertEqual(len(monitoring_issues([{'lead': 'Example', 'stall': 'Unknown'}])), 1)

    def test_commit_history_is_bounded_labeled_and_ordered(self):
        rows = [{'lead': 'Example', 'events': [{'kind': 'Watcher alert', 'status': 'STALLED', 'at': '2026-01-01T00:00:00Z', 'source': 'Watcher'}]}]
        with patch('subprocess.run', return_value=SimpleNamespace(stdout=('a' * 40 + '\t2026-01-02T00:00:00+00:00\n'))) as run:
            add_checkout_history(rows, {'Example': Path('/example')})
        self.assertIn('-10', run.call_args.args[0])
        self.assertEqual(rows[0]['events'][0]['kind'], 'Checkout commit')
        self.assertIn('not attributed', rows[0]['events'][0]['source'])
        self.assertEqual(rows[0]['events'][1]['kind'], 'Watcher alert')

    def test_missing_checkout_does_not_invent_commits(self):
        rows = [{'lead': 'Example', 'events': []}]
        add_checkout_history(rows, {})
        self.assertEqual(rows[0]['events'], [])
        self.assertEqual(rows[0]['commitCoverage'], 'Checkout commit history unavailable')

    def test_missing_database_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            result = timeline(Path(directory))
            self.assertTrue(all(r['coverage'] == 'Coordinator history unavailable' for r in result))
            self.assertFalse((Path(directory) / 'tasks.sqlite').exists())


if __name__ == '__main__':
    unittest.main()
