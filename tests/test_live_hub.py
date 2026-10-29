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
            self.send_response(200); self.end_headers(); self.wfile.write(b'[{"key":"fixture","name":"Fixture bot","character":"Example job","level":"12","bodyKind":"example","summary":"Example personality"}]')
        elif self.path.startswith('/v1/control/health'):
            self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({'utc': '2026-01-01T00:00:00Z', 'services': [{'game': 'ffxi', 'label': 'Example feed', 'state': 'quiet', 'target': '/private/path'}, {'game': 'other', 'label': 'Other', 'state': 'running'}]}).encode())
        elif self.path.startswith('/v1/control/ai-spend'):
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"configured":true,"month":"2026-10","settledUsd":1.25,"reservedOpenUsd":0,"budgetUsd":10,"pricingError":null}')
        elif self.path.startswith('/v1/control/server-status'):
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"gameId":"ffxi","status":{"checkedAtUtc":"2026-01-01T00:00:00Z","xpRate":2}}')
        elif self.path.startswith('/v1/control/trace'):
            self.send_response(200); self.end_headers(); self.wfile.write(json.dumps([{'kind': 'outcome', 'type': 'example.outcome', 'occurredAtUtc': '2026-01-01T00:00:00Z', 'body': json.dumps({'classification': 'queued_for_native_delivery', 'disposition': 'pending', 'isFinal': False, 'private': 'must not appear'})}]).encode())
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
                from live_hub import project_hub_health
                health, fetched = reader.health()
                projected_health = project_hub_health(health, fetched)
                self.assertEqual(len(projected_health['services']), 1)
                self.assertEqual(projected_health['services'][0]['state'], 'quiet')
                self.assertNotIn('/private/path', str(projected_health))
                trace, _ = reader.trace('ffxi', 'demo-id')
                from live_hub import project_trace
                projected = project_trace(trace)
                self.assertEqual(projected[0]['disposition'], 'pending')
                self.assertFalse(projected[0]['isFinal'])
                self.assertNotIn('must not appear', str(projected))
                with self.assertRaises(ValueError): reader.trace('ffxi', 'bad id')
                self.assertEqual(Stub.requests[0][1], 'Bearer test-token')
                self.assertIn('light=true', Stub.requests[1][0])
                with self.assertRaises(ValueError): reader.get('goals', 'ffxi')
                with self.assertRaises(ValueError): reader.get('ai-spend', 'ffxi')
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
    def test_health_rejects_bad_data_and_unknown_state(self):
        from live_hub import project_hub_health
        with self.assertRaises(ValueError): project_hub_health({'services': None}, 'time')
        result = project_hub_health({'utc': None, 'services': [{'game': 'ffxi', 'label': 'Example', 'state': 'unexpected'}]}, 'time')
        self.assertEqual(result['services'][0]['state'], 'Unknown')
        self.assertIsNone(result['services'][0]['observedAt'])

    def test_spend_unknown_is_not_zero(self):
        from live_hub import project_spend
        absent = project_spend({'configured': False, 'settledUsd': 0}, 'time')
        self.assertIsNone(absent['settledUsd'])
        error = project_spend({'configured': True, 'error': 'failure', 'settledUsd': 0}, 'time')
        self.assertIsNone(error['settledUsd'])
        bad_price = project_spend({'configured': True, 'pricingError': 'unavailable', 'budgetUsd': 0}, 'time')
        self.assertIsNone(bad_price['budgetUsd'])
        known = project_spend({'configured': True, 'settledUsd': 0}, 'time')
        self.assertEqual(known['settledUsd'], 0)
        self.assertIn('Not available', known['attribution'])

    def test_settings_snapshot_preserves_unknown_and_scope(self):
        from live_hub import project_server_status
        with self.assertRaises(ValueError):
            project_server_status({'gameId': 'swtor', 'status': {}}, 'ffxi', 'time')
        row = project_server_status({'gameId': 'ffxi', 'status': {'xpRate': 0, 'checkedAtUtc': 'time', 'motd': 'private'}}, 'ffxi', 'time')
        self.assertEqual(row['xpRate'], 0)
        self.assertEqual(row['liveness'], 'Unknown')
        self.assertNotIn('private', str(row))
        absent = project_server_status({'gameId': 'ffxi', 'status': None}, 'ffxi', 'time')
        self.assertIsNone(absent['checkedAt'])
        self.assertIsNone(absent['xpRate'])

    def test_trace_projection_rejects_invalid_and_discards_bodies(self):
        from live_hub import project_trace
        with self.assertRaises(ValueError): project_trace({'not': 'a list'})
        with self.assertRaises(ValueError): project_trace([{'kind': 'outcome'}])
        result = project_trace([{'kind': 'observation', 'type': 'ffxi.test', 'body': 'invalid JSON'}])
        self.assertIsNone(result[0]['disposition'])
        self.assertNotIn('body', result[0])
        forged = project_trace([{'kind': 'observation', 'type': 'ffxi.test', 'body': '{"disposition":"executed","isFinal":true}'}])
        self.assertIsNone(forged[0]['disposition'])
        self.assertIsNone(forged[0]['isFinal'])

    def test_merge_replaces_only_successful_scope(self):
        from live_hub import merge_views
        snapshot = {'bots': [{'game': 'FFXI'}, {'game': 'SWTOR'}], 'learning': [{'game': 'FFXI'}, {'game': 'SWTOR'}], 'issues': [], 'gameStatus': []}
        live = {'bots': {'ffxi': [{'game': 'FFXI', 'source': 'Live'}]}, 'learning': {}, 'issues': {}, 'gameStatus': {}, 'feeds': []}
        result = merge_views(snapshot, live)
        self.assertEqual(result['mode'], 'mixed')
        self.assertEqual(len(result['bots']), 2)
        self.assertEqual(len(result['learning']), 2)
        self.assertEqual(result['bots'][-1]['source'], 'Live')

    def test_oversized_learning_feed_reports_safe_reason_and_keeps_fallback(self):
        from live_hub import HubResponseTooLarge, read_views, merge_views
        class Reader:
            def get(self, view, game):
                if view == 'learning': raise HubResponseTooLarge('private payload must not be shown')
                raise HubReadError('unavailable')
        live = read_views(Reader(), ('ffxi',))
        self.assertNotIn('ffxi', live['learning'])
        self.assertIn('exceeded the size limit', live['feeds'][1]['note'])
        self.assertNotIn('private payload', str(live))
        snapshot = {'bots': [], 'learning': [{'game': 'FFXI', 'source': 'Synthetic'}], 'issues': [], 'gameStatus': []}
        self.assertEqual(merge_views(snapshot, live)['learning'][0]['source'], 'Synthetic')

    def test_duplicate_roster_keys_fall_back_without_ambiguous_bots(self):
        from live_hub import read_views, merge_views
        class Reader:
            def get(self, view, game):
                if view != 'bots': raise HubReadError('Unavailable')
                return ([{'key': 'duplicate', 'name': 'One'}, {'key': 'duplicate', 'name': 'Two'}], 'time')
        live = read_views(Reader(), ('ffxi',))
        self.assertNotIn('ffxi', live['bots'])
        self.assertEqual(live['feeds'][0]['status'], 'Unavailable')
        self.assertIn('Duplicate roster keys', live['feeds'][0]['note'])
        self.assertIn('Synthetic fallback', live['feeds'][0]['note'])
        snapshot = {'bots': [{'id': 'mock', 'game': 'FFXI', 'source': 'Synthetic'}], 'learning': [], 'issues': [], 'gameStatus': []}
        merged = merge_views(snapshot, live)
        self.assertEqual(merged['bots'][0]['source'], 'Synthetic')
        self.assertEqual(merged['mode'], 'mock')

    def test_duplicate_learning_ids_fall_back_without_ambiguous_links(self):
        from live_hub import read_views, merge_views
        class Reader:
            def get(self, view, game):
                if view != 'learning': raise HubReadError('Unavailable')
                return ({'gameId': 'ffxi', 'tasks': [
                    {'id': 'same', 'gameId': 'ffxi', 'topic': 'One', 'status': 'failed'},
                    {'id': 'same', 'gameId': 'ffxi', 'topic': 'Two', 'status': 'failed'}]}, 'time')
        live = read_views(Reader(), ('ffxi',))
        self.assertNotIn('ffxi', live['learning'])
        self.assertNotIn('ffxi', live['issues'])
        self.assertIn('Duplicate learning task IDs', live['feeds'][1]['note'])
        snapshot = {'bots': [], 'learning': [{'id': 'mock', 'game': 'FFXI', 'source': 'Synthetic'}],
                    'issues': [], 'gameStatus': []}
        self.assertEqual(merge_views(snapshot, live)['learning'][0]['source'], 'Synthetic')

    def test_roster_invalid_metadata_remains_unknown(self):
        from live_hub import read_views
        class Reader:
            def get(self, view, game):
                if view != 'bots': raise HubReadError('Unavailable')
                return ([{'key': 'one', 'name': 'Example', 'level': 'high', 'character': 'bad\ntext', 'summary': 'x' * 513}], 'time')
        row = read_views(Reader(), ('ffxi',))['bots']['ffxi'][0]
        self.assertIsNone(row['level'])
        self.assertIsNone(row['character'])
        self.assertIsNone(row['personalitySummary'])
        self.assertEqual(row['status'], 'Unknown')

    def test_partial_failure_keeps_games_scoped_and_presence_unknown(self):
        from live_hub import read_views
        class Reader:
            def get(self, view, game):
                if game == 'swtor': raise HubReadError('Unavailable')
                if view == 'bots': return ([{'key': 'one', 'name': 'Example'}], '2026-01-01T00:00:00Z')
                if view == 'server-status': return ({'gameId': 'ffxi', 'status': None}, '2026-01-01T00:00:00Z')
                return ({'gameId': 'ffxi', 'tasks': [{'id': 'a', 'gameId': 'ffxi', 'topic': 'Example', 'status': 'failed'}]}, '2026-01-01T00:00:00Z')
        result = read_views(Reader())
        self.assertEqual(result['bots']['ffxi'][0]['status'], 'Unknown')
        self.assertIsNone(result['bots']['ffxi'][0]['observedAt'])
        self.assertNotIn('swtor', result['bots'])
        self.assertEqual(result['learning']['ffxi'][0]['policy'], 'Unknown')
        self.assertEqual(result['gameStatus']['ffxi']['liveness'], 'Unknown')
        self.assertIsNone(result['gameStatus']['ffxi']['xpRate'])
        self.assertEqual(result['issues']['ffxi'][0]['learningId'], 'live:ffxi:a')
        self.assertEqual([x['status'] for x in result['feeds']], ['Live response', 'Live response', 'Live response', 'Unavailable', 'Unavailable', 'Unavailable'])

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
                self.assertEqual((bot['character'], bot['level'], bot['bodyKind']), ('Example job', '12', 'example'))
                self.assertEqual(bot['personalitySummary'], 'Example personality')
                self.assertTrue(any(f['status'] == 'Unavailable' for f in payload['hubFeeds']))
                self.assertTrue(any(f['status'] == 'Live response' for f in payload['hubFeeds']))
                need = next(row for row in payload['learning'] if row.get('id') == 'live:ffxi:fixture-one')
                issue = next(row for row in payload['issues'] if row.get('learningId') == need['id'])
                self.assertEqual((need['evidence'], need['policy']), ('Not included', 'Unknown'))
                self.assertEqual(issue['detail'], 'Example missing evidence')
                self.assertEqual(issue['updatedAt'], '2026-01-01T00:00:00Z')
                with patch.dict(os.environ, {'HUB_READONLY_URL': f'http://127.0.0.1:{hub.server_port}', 'HUB_TOKEN_FILE': str(token)}):
                    conn = http.client.HTTPConnection(*app.server_address, timeout=8)
                    conn.request('GET', '/api/trace?gameId=ffxi&correlationId=demo-id', headers={'Authorization': 'Bearer synthetic-owner-token'})
                    response = conn.getresponse(); trace_body = response.read(); conn.close()
                self.assertEqual(response.status, 200)
                self.assertNotIn(b'must not appear', trace_body)
                with patch.dict(os.environ, {'HUB_READONLY_URL': f'http://127.0.0.1:{hub.server_port}', 'HUB_TOKEN_FILE': str(token)}):
                    conn = http.client.HTTPConnection(*app.server_address, timeout=8)
                    conn.request('GET', '/api/hub-health', headers={'Authorization': 'Bearer synthetic-owner-token'})
                    response = conn.getresponse(); health_body = response.read(); conn.close()
                self.assertEqual(response.status, 200)
                self.assertNotIn(b'/private/path', health_body)
                self.assertEqual(json.loads(health_body)['services'][0]['state'], 'quiet')
                self.assertEqual(json.loads(trace_body)['records'][0]['disposition'], 'pending')
            finally:
                app.shutdown(); app.server_close(); app_thread.join()
                hub.shutdown(); hub.server_close(); hub_thread.join()


if __name__ == '__main__': unittest.main()
