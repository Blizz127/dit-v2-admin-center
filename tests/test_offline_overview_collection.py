"""Real overview collection and HTTP dispatch against a temporary synthetic home.

No listener, real coordinator database, process probe, git command or hub read.
"""
from contextlib import ExitStack, closing
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import server
import routing_audit
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
        self.os_open = os.open
        self.reads = []
        self.routing_fixture = self.home / 'routing-audit-fixture.json'
        self.routing_fixture.write_bytes(routing_audit.FIXTURE.read_bytes())

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

        def fd_open(path, flags, *args, **kwargs):
            self.assertTrue(Path(path).resolve().is_relative_to(self.home), 'FD read escaped the synthetic home')
            self.assertFalse(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC), 'Evidence read must not write')
            return self.os_open(path, flags, *args, **kwargs)

        with ExitStack() as stack:
            stack.enter_context(patch('routing_audit.FIXTURE', self.routing_fixture))
            for target in ('socket.socket', 'socket.create_connection', 'subprocess.Popen',
                           'server.BRIDGE.read', 'server.HubReader', 'server.HUB_VIEWS.get',
                           'server.HUB_HEALTH.get', 'server.HUB_INTERACTION.get', 'os.kill'):
                stack.enter_context(patch(target, side_effect=AssertionError('External dependency forbidden: ' + target)))
            # Missing command evidence is modeled; no native subprocess runs.
            stack.enter_context(patch('subprocess.run', side_effect=OSError('Synthetic command unavailable')))
            stack.enter_context(patch.object(Path, 'home', return_value=self.home))
            stack.enter_context(patch.object(Path, 'open', path_open))
            stack.enter_context(patch('os.open', fd_open))
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

    def test_fifo_evidence_does_not_block_overview_or_promote_acceptance(self):
        import operation_sources
        self.seed()
        os.mkfifo(self.local / 'wake-verification.json')
        os.mkfifo(self.home / 'note.md')
        spec = dict(operation_sources.SOURCES[0], path='note.md')
        with patch.object(operation_sources, 'SOURCES', (spec,)):
            status, data = self.request()
        self.assertEqual(status, 200)
        self.assertIsNone(data['wakeVerification']['cutover'])
        self.assertTrue(all(r['status'] in ('Unverified', 'Held') for r in data['wakeVerification']['rows']))
        self.assertEqual(data['operationSources']['rows'][0]['state'], 'Source unavailable')

    def test_operation_notes_refresh_without_promoting_game_acceptance(self):
        import operation_sources
        self.seed()
        raw = b'OMIT_PRIVATE source report'
        spec = dict(operation_sources.SOURCES[0], path='note.md',
                    sha256=hashlib.sha256(raw).hexdigest())
        path = self.home / 'note.md'
        path.write_bytes(raw)
        with patch.object(operation_sources, 'SOURCES', (spec,)):
            before = self.fingerprint()
            status, data = self.request()
            self.assertEqual(status, 200)
            self.assertEqual(data['operationSources']['rows'][0]['state'], 'Reviewed bytes match')
            self.assertTrue(all(r['status'] in ('Unverified', 'Held') for r in data['wakeVerification']['rows']))
            self.assertEqual(self.fingerprint(), before)
            path.write_bytes(b'changed')
            _, data = self.request()
            self.assertEqual(data['operationSources']['rows'][0]['state'], 'Source changed — review required')
            path.unlink()
            _, data = self.request()
            self.assertEqual(data['operationSources']['rows'][0]['state'], 'Source unavailable')

    def test_wake_receipt_refresh_and_withdrawal_are_local_only(self):
        from tests.test_wake_verification import receipt
        self.seed()
        path = self.local / 'wake-verification.json'
        path.write_text(json.dumps(receipt()))
        before = self.fingerprint()
        status, data = self.request()
        self.assertEqual(status, 200)
        rows = {r['game']: r for r in data['wakeVerification']['rows']}
        self.assertEqual(rows['enb']['status'], 'Verified readback (reported)')
        self.assertEqual(rows['ffxi']['status'], 'Unverified')
        self.assertEqual(rows['war']['status'], 'Held')
        self.assertEqual(self.fingerprint(), before)
        path.unlink()
        status, data = self.request()
        self.assertEqual(status, 200)
        self.assertTrue(all(r['status'] in ('Unverified', 'Held') for r in data['wakeVerification']['rows']))

    def test_populated_collection_is_read_only_scoped_and_not_live(self):
        self.seed()
        before = self.fingerprint()
        status, data = self.request()
        self.assertEqual(status, 200)
        self.assertIn('9ba4ccb', data['ffxiFocus']['closest'])
        self.assertIn('22:53:01 UTC', data['ffxiFocus']['closest'])
        self.assertIn('not exercised', data['ffxiFocus']['unverified'])
        self.assertIn('not a current poll', data['ffxiFocus']['source'])
        self.assertEqual(data['hubFeeds'][0]['status'], 'Mock selected')
        self.assertEqual([row['scopeKind'] for row in data['routingAudit']], ['bot', 'all', 'bot'])
        self.assertIn('Simulated rejection', data['routingAudit'][2]['result'])
        self.assertTrue(all(change['effective'] is None for row in data['routingAudit'] for change in row['changes']))
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
