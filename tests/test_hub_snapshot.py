"""Exported hub snapshots: same validation as live reads, never labeled live, no hub access."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from hub_snapshot import ENV, SnapshotReader
from live_hub import HubReadError, project_hub_health, read_views
from interaction_projection import project_interaction
import server
from types import SimpleNamespace
from test_offline_inspector_handler import MemoryConnection

FIXTURE = Path(__file__).resolve().parent / 'fixtures/hub-snapshot'
NOW = lambda: datetime(2026, 1, 2, tzinfo=timezone.utc)


class HubSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'export'
        shutil.copytree(FIXTURE, self.root)

    def manifest(self, **changes):
        data = json.loads((FIXTURE / 'manifest.json').read_text())
        data.update(changes)
        (self.root / 'manifest.json').write_text(json.dumps({k: v for k, v in data.items() if v is not None}))

    def test_views_project_through_existing_validation_and_are_labeled_exported(self):
        result = read_views(SnapshotReader(self.root, NOW))
        feeds = {(f['game'], f['view']): f for f in result['feeds']}
        for view in ('bots', 'learning', 'server-status'):
            self.assertEqual(feeds[('FFXI', view)]['status'], 'Exported snapshot')
            self.assertIn('not live', feeds[('FFXI', view)]['at'])
            self.assertIn('reported hub revision example-rev', feeds[('FFXI', view)]['at'])
            # SWTOR was not exported: per-view synthetic fallback, not an error for the whole snapshot.
            self.assertEqual(feeds[('SWTOR', view)]['status'], 'Unavailable')
        self.assertEqual(result['bots']['ffxi'][0]['name'], 'Snapshot fixture bot')
        self.assertIn('exported snapshot', result['bots']['ffxi'][0]['source'])
        self.assertEqual(result['learning']['ffxi'][0]['id'], 'live:ffxi:snapshot-one')
        self.assertEqual(result['gameStatus']['ffxi']['xpRate'], 2)
        self.assertNotIn('Live response', json.dumps(result))

    def test_health_and_interaction_use_live_projections(self):
        reader = SnapshotReader(self.root, NOW)
        health = project_hub_health(*reader.health())
        self.assertEqual(health['services'][0]['state'], 'quiet')
        self.assertIn('not live', health['fetchedAt'])
        interaction = project_interaction(*reader.interaction())
        self.assertEqual(interaction['bots'], [])
        with self.assertRaises(HubReadError):
            reader.trace('ffxi', 'any-correlation')

    def test_malformed_snapshot_values_remain_unknown_or_isolated(self):
        (self.root / 'ffxi/server-status.json').write_text(json.dumps({
            'gameId': 'ffxi', 'status': {'xpRate': 10**400}}))
        (self.root / 'health.json').write_text(json.dumps({
            'services': [{'game': 'ffxi', 'label': 'Example', 'state': []}]}))
        (self.root / 'interaction.json').write_text(json.dumps({
            'switches': {'contract': True}, 'freshForSeconds': 10**400,
            'scopes': [{'gameId': 'ffxi', 'caller': 'test', 'serverInstanceId': 'test',
                        'bots': [{'actorKey': 'test', 'fresh': True, 'activity': [], 'source': {}}]}]}))
        reader = SnapshotReader(self.root, NOW)
        self.assertIsNone(read_views(reader)['gameStatus']['ffxi']['xpRate'])
        self.assertEqual(project_hub_health(*reader.health())['services'][0]['state'], 'Unknown')
        interaction = project_interaction(*reader.interaction())
        self.assertIsNone(interaction['freshForSeconds'])
        self.assertIsNone(interaction['bots'][0]['activity'])
        self.assertIsNone(interaction['bots'][0]['source'])

    def test_invalid_manifest_withholds_every_view(self):
        cases = [dict(kind='other'), dict(version=2), dict(version=True), dict(exportedAtUtc='2026-01-01 12:00'),
                 dict(exportedAtUtc='2027-01-01T00:00:00Z'), dict(hubRevision='has space'), dict(extra='x')]
        for change in cases:
            with self.subTest(change=change):
                self.manifest(**change)
                result = read_views(SnapshotReader(self.root, NOW))
                self.assertEqual(result['bots'], {})
                self.assertTrue(all(f['status'] == 'Unavailable' for f in result['feeds']))
        (self.root / 'manifest.json').unlink()
        self.assertEqual(read_views(SnapshotReader(self.root, NOW))['bots'], {})

    def test_malformed_manifest_bytes_withhold_all_views(self):
        path = self.root / 'manifest.json'
        for raw in (b' ' * 4097, b'{"broken":', b'[]', b'[' * 2000 + b']' * 2000):
            with self.subTest(size=len(raw)):
                path.write_bytes(raw)
                result = read_views(SnapshotReader(self.root, NOW))
                self.assertEqual((result['bots'], result['learning'], result['gameStatus']), ({}, {}, {}))
                self.assertTrue(all(feed['status'] == 'Unavailable' for feed in result['feeds']))

    def test_unsafe_or_invalid_view_files_fall_back_per_view(self):
        (self.root / 'ffxi/bots.json').write_text('[{"key":"a","name":"A"},{"key":"a","name":"B"}]')
        (self.root / 'ffxi/learning.json').write_text('{"gameId": "ffxi", "gameId": "swtor"}')
        (self.root / 'ffxi/server-status.json').unlink()
        os.mkfifo(self.root / 'ffxi/server-status.json')
        (self.root / 'health.json').unlink()
        (self.root / 'health.json').symlink_to(FIXTURE / 'health.json')
        reader = SnapshotReader(self.root, NOW)
        result = read_views(reader)
        self.assertEqual((result['bots'], result['learning'], result['gameStatus']), ({}, {}, {}))
        with self.assertRaises(HubReadError):
            reader.health()
        with self.assertRaises(ValueError):
            reader.get('bots', '../ffxi')
        with self.assertRaises(ValueError):
            SnapshotReader('relative/path')

    def test_server_switch_routes_and_refuses_ambiguous_configuration(self):
        def overview(environ, source='hub'):
            with patch.dict('os.environ', environ, clear=True), \
                 patch.object(Path, 'home', return_value=Path(self.temp.name)), \
                 patch('server.LOCAL_DATA', Path(self.temp.name) / 'local'), \
                 patch('server.HubReader', side_effect=AssertionError('live hub read in snapshot mode')):
                return server.overview(source)
        on = overview({ENV: str(self.root)})
        self.assertEqual(on['mode'], 'mixed')
        self.assertTrue(any(b['name'] == 'Snapshot fixture bot' for b in on['bots']))
        mock = overview({ENV: str(self.root)}, 'mock')
        self.assertEqual(mock['hubFeeds'][0]['status'], 'Mock selected')
        both = overview({ENV: str(self.root), 'HUB_READONLY_URL': 'http://127.0.0.1:1'})
        self.assertEqual(both['hubFeeds'][0]['status'], 'Invalid configuration')
        self.assertFalse(any(b['name'] == 'Snapshot fixture bot' for b in both['bots']))
        off = overview({})
        self.assertEqual(off['hubFeeds'][0]['status'], 'Not configured')


    def http(self, path, environ):
        wire = (f'GET {path} HTTP/1.1\r\nHost: fixture.invalid\r\nAuthorization: Bearer fixture-token\r\n'
                'Connection: close\r\n\r\n').encode()
        connection = MemoryConnection(wire)
        with patch.dict('os.environ', environ, clear=True), \
             patch('server.HubReader', side_effect=AssertionError('live hub read in snapshot mode')), \
             patch('socket.create_connection', side_effect=AssertionError('network use')):
            server.Handler(connection, ('127.0.0.1', 0), SimpleNamespace(admin_token='fixture-token'))
        head, body = bytes(connection.outgoing).split(b'\r\n\r\n', 1)
        return int(head.split()[1]), json.loads(body)

    def test_snapshot_endpoints(self):
        env = {ENV: str(self.root)}
        status, body = self.http('/api/hub-health', env)
        self.assertEqual((status, body['services'][0]['state']), (200, 'quiet'))
        self.assertIn('not live', body['fetchedAt'])
        status, body = self.http('/api/interaction', env)
        self.assertEqual((status, body['bots']), (200, []))
        status, body = self.http('/api/trace?gameId=ffxi&correlationId=abc-1', env)
        self.assertEqual((status, body['error']), (503, 'trace unavailable from exported snapshot'))
        both = dict(env, HUB_READONLY_URL='http://127.0.0.1:1', HUB_TOKEN_FILE='/forbidden/token')
        for path in ('/api/hub-health', '/api/interaction', '/api/trace?gameId=ffxi&correlationId=abc-1'):
            self.assertEqual(self.http(path, both), (503, {'error': 'hub not configured'}))
        self.manifest(kind='other')
        self.assertEqual(self.http('/api/hub-health', env)[0], 503)


    def test_server_status_host_paths_never_reach_output(self):
        marker = '/srv/hub-host-only/OMIT_HOST_PATH/settings.lua'
        (self.root / 'ffxi/server-status.json').write_text(json.dumps({
            'gameId': 'ffxi', 'status': {'checkedAtUtc': '2026-01-01T11:30:00Z', 'xpRate': 2},
            'sources': [{'kind': 'settings', 'path': marker}]}))
        with patch.dict('os.environ', {ENV: str(self.root)}, clear=True), \
             patch.object(Path, 'home', return_value=Path(self.temp.name)), \
             patch('server.LOCAL_DATA', Path(self.temp.name) / 'local'):
            data = server.overview('hub')
        self.assertEqual([s['xpRate'] for s in data['gameStatus'] if s['game'] == 'FFXI'], [2])
        self.assertNotIn('OMIT_HOST_PATH', json.dumps(data))


if __name__ == '__main__':
    unittest.main()
