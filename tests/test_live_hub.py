import json
import http.client
import os
from unittest.mock import patch
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from live_hub import HubReader, HubReadError


class Stub(BaseHTTPRequestHandler):
    requests = []
    def do_GET(self):
        Stub.requests.append((self.path, self.headers.get('Authorization')))
        if self.path.startswith('/v1/control/bots'):
            self.send_response(200); self.end_headers(); self.wfile.write(b'[{"key":"fixture","name":"Fixture bot"}]')
        elif self.path.startswith('/v1/control/learning'):
            self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({'gameId': 'ffxi', 'tasks': [{'id': 'fixture-one', 'gameId': 'ffxi', 'topic': 'Fixture learning gap', 'status': 'unverified', 'reason': 'Example missing evidence', 'updatedAtUtc': '2026-01-01T00:00:00Z'}]}).encode())
        else:
            self.send_response(302); self.send_header('Location', 'http://example.invalid/'); self.end_headers()
    def log_message(self, *args): pass


class HubReaderTests(unittest.TestCase):
    def test_allowlisted_gets_only_and_sanitized_failures(self):
        Stub.requests = []
        with tempfile.TemporaryDirectory() as directory:
            token = Path(directory) / 'token'; token.write_text('test-token')
            server = ThreadingHTTPServer(('127.0.0.1', 0), Stub)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                reader = HubReader(f'http://127.0.0.1:{server.server_port}', token)
                data, stamp = reader.get('bots', 'ffxi'); self.assertEqual(data[0]['name'], 'Fixture bot'); self.assertTrue(stamp)
                reader.get('learning', 'ffxi')
                self.assertEqual(Stub.requests[0][1], 'Bearer test-token')
                self.assertIn('light=true', Stub.requests[1][0])
                with self.assertRaises(ValueError): reader.get('goals', 'ffxi')
                with self.assertRaises(ValueError): reader.get('bots', '../other')
                token.unlink()
                with self.assertRaises(HubReadError) as error: reader.get('bots', 'ffxi')
                self.assertNotIn('test-token', str(error.exception))
            finally:
                server.shutdown(); server.server_close(); thread.join()

    def test_rejects_nonlocal_or_credential_urls(self):
        for url in ('http://example.com:7390', 'http://127.0.0.1:7390/path', 'http://user:pass@127.0.0.1:7390', 'https://127.0.0.1:7390'):
            with self.assertRaises(ValueError): HubReader(url, '/tmp/no-token')



class ProjectionTests(unittest.TestCase):
    def test_merge_replaces_only_successful_scope(self):
        from live_hub import merge_views
        snapshot = {'bots': [{'game': 'FFXI'}, {'game': 'SWTOR'}], 'learning': [{'game': 'FFXI'}, {'game': 'SWTOR'}], 'issues': []}
        live = {'bots': {'ffxi': [{'game': 'FFXI', 'source': 'Live'}]}, 'learning': {}, 'issues': {}, 'feeds': []}
        result = merge_views(snapshot, live)
        self.assertEqual(result['mode'], 'mixed')
        self.assertEqual(len(result['bots']), 2)
        self.assertEqual(len(result['learning']), 2)
        self.assertEqual(result['bots'][-1]['source'], 'Live')

    def test_partial_failure_keeps_games_scoped_and_presence_unknown(self):
        from live_hub import read_views
        class Reader:
            def get(self, view, game):
                if game == 'swtor': raise HubReadError('Unavailable')
                if view == 'bots': return ([{'key': 'one', 'name': 'Example'}], '2026-01-01T00:00:00Z')
                return ({'gameId': 'ffxi', 'tasks': [{'id': 'a', 'gameId': 'ffxi', 'topic': 'Example', 'status': 'failed'}]}, '2026-01-01T00:00:00Z')
        result = read_views(Reader())
        self.assertEqual(result['bots']['ffxi'][0]['status'], 'Unknown')
        self.assertIsNone(result['bots']['ffxi'][0]['observedAt'])
        self.assertNotIn('swtor', result['bots'])
        self.assertEqual(result['learning']['ffxi'][0]['policy'], 'Unknown')
        self.assertEqual(result['issues']['ffxi'][0]['learningId'], 'live:ffxi:a')
        self.assertEqual([x['status'] for x in result['feeds']], ['Live response', 'Live response', 'Unavailable', 'Unavailable'])

class EndToEndTests(unittest.TestCase):
    def test_mock_source_never_initializes_upstream_reader(self):
        from server import overview
        with patch.dict(os.environ, {'HUB_READONLY_URL': 'http://127.0.0.1:7390', 'HUB_TOKEN_FILE': '/nonexistent'}), patch('server.HubReader') as reader:
            payload = overview('mock')
        reader.assert_not_called()
        self.assertEqual(payload['mode'], 'mock')
        self.assertEqual(payload['hubFeeds'][0]['status'], 'Mock selected')

    def test_admin_response_uses_stub_live_reads_and_fallback(self):
        from server import make_server
        with tempfile.TemporaryDirectory() as directory:
            token = Path(directory) / 'hub-token'; token.write_text('synthetic-hub-token')
            hub = ThreadingHTTPServer(('127.0.0.1', 0), Stub)
            hub_thread = threading.Thread(target=hub.serve_forever, daemon=True); hub_thread.start()
            app = make_server(0, 'synthetic-owner-token')
            app_thread = threading.Thread(target=app.serve_forever, daemon=True); app_thread.start()
            try:
                with patch.dict(os.environ, {'HUB_READONLY_URL': f'http://127.0.0.1:{hub.server_port}', 'HUB_TOKEN_FILE': str(token)}):
                    conn = http.client.HTTPConnection(*app.server_address, timeout=8)
                    conn.request('GET', '/api/overview?source=hub', headers={'Authorization': 'Bearer synthetic-owner-token'})
                    response = conn.getresponse(); body = response.read(); conn.close()
                self.assertEqual(response.status, 200)
                self.assertNotIn(b'synthetic-hub-token', body)
                payload = json.loads(body)
                self.assertEqual(payload['mode'], 'mixed')
                bot = next(row for row in payload['bots'] if row['id'] == 'live:ffxi:fixture')
                self.assertEqual(bot['status'], 'Unknown')
                self.assertNotIn('routing', bot)
                self.assertTrue(any(f['status'] == 'Unavailable' for f in payload['hubFeeds']))
                self.assertTrue(any(f['status'] == 'Live response' for f in payload['hubFeeds']))
                need = next(row for row in payload['learning'] if row.get('id') == 'live:ffxi:fixture-one')
                issue = next(row for row in payload['issues'] if row.get('learningId') == need['id'])
                self.assertEqual((need['evidence'], need['policy']), ('Not included', 'Unknown'))
                self.assertEqual(issue['detail'], 'Example missing evidence')
                self.assertEqual(issue['updatedAt'], '2026-01-01T00:00:00Z')
            finally:
                app.shutdown(); app.server_close(); app_thread.join()
                hub.shutdown(); hub.server_close(); hub_thread.join()


if __name__ == '__main__': unittest.main()
