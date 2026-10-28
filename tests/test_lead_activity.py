import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lead_activity import lead_activity


class LeadActivityTests(unittest.TestCase):
    def test_exact_latest_task_and_checkout_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); db = root / 'board.sqlite'
            with sqlite3.connect(db) as c:
                c.execute('CREATE TABLE tasks(project TEXT, agent TEXT, status TEXT, summary TEXT, updated REAL)')
                c.executemany('INSERT INTO tasks VALUES (?,?,?,?,?)', [('proj', 'codex', 'working', 'Older', 1), ('proj', 'codex', 'blocked', 'Waiting for review', 2), ('other', 'codex', 'working', 'Other', 3)])
            with patch('lead_activity.project_commit', return_value='2026-01-01T00:00:00+00:00'):
                rows = lead_activity(db, [('Lead', 'proj', 'codex', root), ('Missing', 'none', 'codex', root)])
            self.assertEqual(rows[0]['taskSummary'], 'Waiting for review')
            self.assertIn('not attributed', rows[0]['commitSource'])
            self.assertEqual(rows[1]['taskSummary'], 'Unknown')

    def test_sensitive_summary_withheld_and_missing_db_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); db=root/'board.sqlite'
            with sqlite3.connect(db) as c:
                c.execute('CREATE TABLE tasks(project TEXT, agent TEXT, status TEXT, summary TEXT, updated REAL)')
                c.execute('INSERT INTO tasks VALUES (?,?,?,?,?)', ('proj', 'codex', 'working', 'token=example-secret', 1))
            with patch('lead_activity.project_commit', return_value=None):
                row=lead_activity(db, [('Lead', 'proj', 'codex', root)])[0]
                missing=lead_activity(root/'missing', [('Lead', 'proj', 'codex', root)])[0]
            self.assertNotIn('example-secret', row['taskSummary'])
            self.assertIn('withheld', row['taskSummary'])
            self.assertEqual(missing['taskStatus'], 'Unknown')


if __name__ == '__main__':
    unittest.main()
