import sqlite3
import tempfile
import unittest
from pathlib import Path

from owner_attention import pending_owner_decisions


class OwnerAttentionTests(unittest.TestCase):
    def test_only_unexpired_explicit_owner_decisions_in_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / 'tasks.sqlite'
            with sqlite3.connect(db_path) as db:
                db.executescript('CREATE TABLE approvals(id TEXT, project TEXT, title TEXT, status TEXT, created REAL, expires REAL); CREATE TABLE overnight_decisions(id TEXT);')
                db.executemany('INSERT INTO approvals VALUES (?,?,?,?,?,?)', [
                    ('1', 'claude-dit-v2-admin-center', 'Review draft', 'pending', 10, 100),
                    ('2', 'claude-dit-v2-admin-center', 'Expired', 'pending', 10, 20),
                    ('3', 'claude-dit-v2-admin-center', 'Overnight', 'pending', 10, 100),
                    ('4', 'other', 'Other project', 'pending', 10, 100),
                    ('5', 'claude-dit-human-behavior-platform', 'Decided', 'allowed', 10, 100),
                ])
                db.execute('INSERT INTO overnight_decisions VALUES (?)', ('3',))
            result = pending_owner_decisions(db_path, now=30)
            self.assertEqual([x['title'] for x in result['items']], ['Review draft'])
            self.assertIn('other requests may exist', result['coverage'])

    def test_unavailable_does_not_claim_no_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            result = pending_owner_decisions(Path(directory) / 'missing', now=30)
            self.assertEqual(result['items'], [])
            self.assertIn('unavailable', result['coverage'])


if __name__ == '__main__':
    unittest.main()
