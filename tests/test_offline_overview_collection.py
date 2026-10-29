"""Real overview collection and HTTP dispatch against a temporary synthetic home.

No listener, real coordinator database, process probe, git command or hub read.
"""
from contextlib import ExitStack, closing
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import server
from test_offline_inspector_handler import MemoryConnection


class OfflineOverviewCollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / '.local/share/devbox-coordinator-state'
        self.root.mkdir(parents=True)
        self.database = self.root / 'tasks.sqlite'
        self.local = self.home / 'local'
        self.connect = sqlite3.connect
        self.path_open = Path.open
        self.reads = []

    def seed(self):
        with closing(self.connect(self.database)) as db, db:
            db.executescript('''
                CREATE TABLE tasks(id TEXT, project TEXT, agent TEXT, status TEXT, summary TEXT, updated REAL);
                CREATE TABLE events(task TEXT, status TEXT, time REAL);
                CREATE TABLE watch_alerts(target TEXT, kind TEXT, time REAL);
                CREATE TABLE approvals(id TEXT, project TEXT, title TEXT, created REAL, expires REAL, status TEXT);
                CREATE TABLE overnight_decisions(id TEXT);
                CREATE TABLE messages(id TEXT, project TEXT, created REAL, delivered REAL, status TEXT, origin TEXT, text TEXT, agent TEXT, session TEXT);
                CREATE TABLE replies(message_id TEXT, time REAL);
            ''')
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?)',
                       ('fixture', 'claude-dit-human-behavior-platform', 'claude', 'working',
                        'Bearer OMIT_PRIVATE_SUMMARY', 1767225600))
            db.execute('INSERT INTO events VALUES (?,?,?)', ('fixture', 'working', 1767225600))
            db.execute('INSERT INTO approvals VALUES (?,?,?,?,?,?)',
                       ('decision', 'claude-dit-v2-admin-center', 'Synthetic review decision',
                        1767225600, 4102444800, 'pending'))
            db.execute('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?)',
                       ('nudge', 'claude-dit-v2-admin-center', 1767225600, 1767225610,
                        'delivered', 'watcher', 'OMIT_PRIVATE_MESSAGE', 'codex', None))
            db.execute('INSERT INTO replies VALUES (?,?)', ('nudge', 1767225620))
        self.local.mkdir()
        with closing(self.connect(self.local / 'codex-quota.sqlite')) as db, db:
            db.execute('CREATE TABLE samples(account TEXT, observed REAL, window TEXT, used REAL)')
            db.execute('INSERT INTO samples VALUES (?,?,?,?)', ('synthetic-account', 1767225600, 'unified5h', 0.25))

    def fingerprint(self):
        return {str(path.relative_to(self.home)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.home.rglob('*') if path.is_file()}

    def request(self, path='/api/overview?source=mock', token='fixture-token'):
        connections = []
        def connect(database_uri, *args, **kwargs):
            self.assertTrue(kwargs.get('uri'), 'Collector must use SQLite URI mode')
            self.assertTrue(database_uri.startswith(self.home.as_uri() + '/'))
            self.assertTrue(database_uri.endswith('?mode=ro'), 'Collection must be read-only')
            self.reads.append(database_uri)
            connection = self.connect(database_uri, *args, **kwargs)
            connection.execute('PRAGMA query_only=ON')
            connections.append(connection)
            return connection

        def path_open(path, *args, **kwargs):
            self.assertTrue(path.resolve().is_relative_to(self.home), 'Read escaped the synthetic home')
            return self.path_open(path, *args, **kwargs)

        with ExitStack() as stack:
            for target in ('socket.socket', 'socket.create_connection', 'subprocess.Popen',
                           'server.BRIDGE.read', 'server.HubReader', 'server.HUB_VIEWS.get',
                           'server.HUB_HEALTH.get', 'server.HUB_INTERACTION.get', 'os.kill'):
                stack.enter_context(patch(target, side_effect=AssertionError('External dependency forbidden: ' + target)))
            # Missing command evidence is modeled; no native subprocess runs.
            stack.enter_context(patch('subprocess.run', side_effect=OSError('Synthetic command unavailable')))
            stack.enter_context(patch.object(Path, 'home', return_value=self.home))
            stack.enter_context(patch.object(Path, 'open', path_open))
            stack.enter_context(patch('server.PROJECT', self.home / 'dev/admin'))
            stack.enter_context(patch('server.LOCAL_DATA', self.local))
            stack.enter_context(patch('sqlite3.connect', side_effect=connect))
            stack.enter_context(patch.dict('os.environ', {
                'HUB_READONLY_URL': 'http://127.0.0.1:1', 'HUB_TOKEN_FILE': '/forbidden/token'}, clear=True))
            wire = f'GET {path} HTTP/1.1\r\nHost: fixture.invalid\r\nAuthorization: Bearer {token}\r\nConnection: close\r\n\r\n'.encode()
            connection = MemoryConnection(wire)
            server.Handler(connection, ('127.0.0.1', 0), SimpleNamespace(admin_token='fixture-token'))
        for database in connections:
            with self.assertRaises(sqlite3.ProgrammingError, msg='Collector left a SQLite connection open'):
                database.execute('SELECT 1')
        headers, body = bytes(connection.outgoing).split(b'\r\n\r\n', 1)
        status, headers = headers.split(b'\r\n', 1)
        self.assertEqual(BytesParser().parsebytes(headers)['Cache-Control'], 'no-store')
        self.assertNotIn(b'OMIT_PRIVATE', body)
        return int(status.split()[1]), json.loads(body)

    def test_populated_collection_is_read_only_scoped_and_not_live(self):
        self.seed()
        before = self.fingerprint()
        status, data = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(data['hubFeeds'][0]['status'], 'Mock selected')
        self.assertEqual(data['leadActivity'][0]['taskStatus'], 'working')
        self.assertIn('withheld', data['leadActivity'][0]['taskSummary'])
        self.assertIsNone(data['leadActivity'][0]['commitAt'])
        self.assertEqual(data['leadTimeline'][0]['events'][0]['status'], 'working')
        self.assertEqual(data['ownerAttention']['items'][0]['title'], 'Synthetic review decision')
        self.assertEqual(data['quotaHistory'][0]['remainingPercent'], 75)
        self.assertEqual(data['nudgeHistory'][1]['nudges'][0]['replySeconds'], 20)
        self.assertTrue(all(row['quota'] == 'Unknown' for row in data['leadMonitoring']))
        self.assertTrue(all(row['stall'] == 'Unknown' for row in data['leadMonitoring']))
        self.assertTrue(self.reads)
        self.assertEqual(self.fingerprint(), before)

    def test_missing_and_malformed_records_remain_unknown_without_creating_files(self):
        for malformed in (False, True):
            with self.subTest(malformed=malformed):
                if malformed:
                    self.database.write_bytes(b'not sqlite')
                    (self.root / 'watch.json').write_text('{broken')
                    (self.root / 'watch-state.json').write_text('null')
                before = self.fingerprint()
                status, data = self.request()
                self.assertEqual(status, 200)
                self.assertEqual(data['quotaHistory'], [])
                self.assertEqual(data['ownerAttention']['items'], [])
                self.assertTrue(all(row['taskStatus'] == 'Unknown' for row in data['leadActivity']))
                self.assertTrue(all(row['coverage'] == 'Coordinator history unavailable' for row in data['leadTimeline']))
                self.assertEqual(self.fingerprint(), before)

    def test_auth_and_query_rejection_precede_collection(self):
        self.assertEqual(self.request(token='wrong')[0], 401)
        self.assertEqual(self.request(path='/api/overview?source=other')[0], 400)
        self.assertEqual(self.reads, [])


if __name__ == '__main__':
    unittest.main()
