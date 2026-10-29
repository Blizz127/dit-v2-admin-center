"""Actual handler dispatch and serialization with memory-only HTTP request bytes.

No listener, live overview collection, token file or DOM dependency is used.
"""
import io
import json
import subprocess
from email.parser import BytesParser
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from unittest.mock import Mock

import server
from bridge_status import BridgeObserver
from tools.build_inspector_playtest import snapshot


class MemoryConnection:
    def __init__(self, request):
        self.incoming = io.BytesIO(request)
        self.outgoing = bytearray()

    def makefile(self, mode, buffering=None):
        if mode != 'rb':
            raise AssertionError('Unexpected connection stream mode')
        return self.incoming

    def sendall(self, data):
        self.outgoing.extend(data)


class OfflineInspectorHandlerTests(unittest.TestCase):
    def setUp(self):
        # Also reject local listeners and subprocess-backed collectors.
        for target in ('socket.socket', 'socket.create_connection', 'subprocess.Popen',
                       'sqlite3.connect', 'server.BRIDGE.read', 'server.HUB_VIEWS.get',
                       'server.HubReader', 'server.HUB_HEALTH.get', 'server.HUB_INTERACTION.get'):
            guard = patch(target, side_effect=AssertionError('External dependency forbidden: ' + target))
            guard.start()
            self.addCleanup(guard.stop)
        guard = patch('server.overview', side_effect=lambda source: snapshot())
        self.overview = guard.start()
        self.addCleanup(guard.stop)

    def request(self, path='/api/overview?source=mock', token='fixture-token', method='GET'):
        headers = ['Host: offline.invalid', 'Connection: close']
        if token is not None:
            headers.append('Authorization: Bearer ' + token)
        wire = (method + ' ' + path + ' HTTP/1.1\r\n' + '\r\n'.join(headers) + '\r\n\r\n').encode()
        connection = MemoryConnection(wire)
        server.Handler(connection, ('127.0.0.1', 0), SimpleNamespace(admin_token='fixture-token'))
        head, body = bytes(connection.outgoing).split(b'\r\n\r\n', 1)
        status, header_bytes = head.split(b'\r\n', 1)
        return int(status.split()[1]), BytesParser().parsebytes(header_bytes), body

    def test_projected_flags_and_evidence_survive_authenticated_handler(self):
        status, headers, body = self.request()
        self.assertEqual(status, 200)
        self.overview.assert_called_once_with('mock')
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(int(headers['Content-Length']), len(body))
        self.assertIsNone(headers['Access-Control-Allow-Origin'])
        rows = json.loads(body)['learning']
        self.assertEqual([row['hasModelAnswer'] for row in rows], [True, False, True, None])
        self.assertEqual([row['evidence'] for row in rows], ['Not included', 'Unknown', 'Present', 'Not included'])
        self.assertTrue(all(row['status'] == 'verified' and row['policy'] == 'Unknown' for row in rows))
        self.assertNotIn(b'OMIT_RAW_ANSWER_AND_PLAYER_DATA', body)
        self.assertNotIn(b'fixture-token', body)

    def test_bridge_rejects_parameters_before_observer_and_auth_still_runs_first(self):
        # setUp guards the real observer: rejected queries must not reach it.
        for query in ('refresh=1', 'host=example.invalid', 'token=OMIT_PRIVATE_QUERY', 'flag'):
            with self.subTest(query=query):
                path = '/api/bridge-status?' + query
                status, _, body = self.request(path)
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body), {'error': 'bridge status takes no parameters'})
                self.assertNotIn(b'OMIT_PRIVATE', body)
                self.assertEqual(self.request(path, token='wrong')[0], 401)
        with patch('server.BRIDGE.read', return_value={'unit': 'unknown'}) as observer:
            self.assertEqual(self.request('/api/bridge-status')[0], 200)
            observer.assert_called_once_with()

    def test_unauthorized_requests_cannot_collect_or_return_fixture(self):
        for token in (None, 'wrong', ''):
            with self.subTest(token=token):
                status, headers, body = self.request(token=token)
                self.assertEqual(status, 401)
                self.assertEqual(json.loads(body), {'error': 'unauthorized'})
                self.assertEqual(headers['Cache-Control'], 'no-store')
        self.overview.assert_not_called()

    def test_invalid_scope_does_not_collect_data(self):
        for query in ('source=mock&source=hub', 'source=', 'source=other', 'source=mock&token=unexpected'):
            with self.subTest(query=query):
                status, _, body = self.request('/api/overview?' + query)
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body), {'error': 'invalid source'})
        self.overview.assert_not_called()

    def test_malformed_query_fields_fail_before_any_read(self):
        cases = {
            '/api/overview': ['source=mock&', '&source=mock', 'source=mock&&',
                              'source', 'source=mock&source=mock', '%FF=mock',
                              'source=mock&' + '&'.join('extra=x' for _ in range(30))],
            '/api/trace': ['gameId=ffxi&correlationId=valid&', 'gameId=ffxi&&correlationId=valid',
                          'gameId=ffxi&correlationId', 'gameId=ffxi&correlationId=%FF',
                          'gameId=ffxi&correlationId=valid&extra=OMIT_PRIVATE_QUERY'],
        }
        with patch.dict('os.environ', {}, clear=True):
            for route, queries in cases.items():
                for query in queries:
                    with self.subTest(route=route, query=query):
                        status, _, body = self.request(route + '?' + query)
                        self.assertEqual(status, 400)
                        self.assertEqual(set(json.loads(body)), {'error'})
                        self.assertNotIn(b'OMIT_PRIVATE', body)
                        self.assertEqual(self.request(route + '?' + query, token='wrong')[0], 401)
        self.overview.assert_not_called()

    def test_valid_encoded_query_and_default_overview_keep_existing_behavior(self):
        for path in ('/api/overview', '/api/overview?', '/api/overview?%73ource=mo%63k'):
            self.assertEqual(self.request(path)[0], 200)
        self.assertEqual([call.args for call in self.overview.call_args_list], [('mock',)] * 3)
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(self.request('/api/trace?correlationId=fixture%3A1&gameId=ffxi')[0], 503)

    def test_mutation_method_is_rejected_before_collection(self):
        status, _, _ = self.request(method='POST')
        self.assertEqual(status, 501)
        self.overview.assert_not_called()

    def test_unknown_control_paths_and_write_methods_cannot_reach_dependencies(self):
        for path in ('/api/model', '/api/stop', '/api/unknown?token=OMIT_PRIVATE_QUERY'):
            with self.subTest(path=path):
                self.assertEqual(self.request(path, token='wrong')[0], 401)
                status, _, body = self.request(path)
                self.assertEqual(status, 404)
                self.assertEqual(json.loads(body), {'error': 'not found'})
        for path in ('/api/overview', '/api/trace', '/api/hub-health', '/api/interaction', '/api/bridge-status'):
            for method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                with self.subTest(path=path, method=method):
                    status, headers, body = self.request(path, method=method)
                    self.assertEqual(status, 501)
                    self.assert_error_envelope(headers, body)
                    self.assertEqual(json.loads(body), {'error': 'method not supported'})
        self.overview.assert_not_called()

    def assert_error_envelope(self, headers, body):
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(int(headers['Content-Length']), len(body))
        payload = json.loads(body)
        self.assertEqual(set(payload), {'error'})
        self.assertIsInstance(payload['error'], str)
        self.assertTrue(payload['error'])
        for private in (b'OMIT_PRIVATE', b'fixture-token', b'/fixture', b'Traceback'):
            self.assertNotIn(private, body)

    def test_read_api_error_envelopes_are_consistent(self):
        routes = ('/api/overview', '/api/trace', '/api/hub-health', '/api/interaction', '/api/bridge-status')
        with patch.dict('os.environ', {}, clear=True):
            for route in routes:
                with self.subTest(route=route, status=401):
                    status, headers, body = self.request(route, token='OMIT_PRIVATE_TOKEN')
                    self.assertEqual(status, 401)
                    self.assert_error_envelope(headers, body)
                with self.subTest(route=route, status=400):
                    status, headers, body = self.request(route + '?OMIT_PRIVATE_QUERY=1')
                    self.assertEqual(status, 400)
                    self.assert_error_envelope(headers, body)
            for route in ('/api/hub-health', '/api/interaction', '/api/trace?gameId=ffxi&correlationId=example'):
                status, headers, body = self.request(route)
                self.assertEqual(status, 503)
                self.assert_error_envelope(headers, body)
        status, headers, body = self.request('/api/OMIT_PRIVATE_PATH')
        self.assertEqual(status, 404)
        self.assert_error_envelope(headers, body)
        self.overview.assert_not_called()

    def test_head_error_has_json_headers_without_body_or_request_details(self):
        status, headers, body = self.request('/api/bridge-status?OMIT_PRIVATE_QUERY', method='HEAD')
        self.assertEqual(status, 501)
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertGreater(int(headers['Content-Length']), 0)
        self.assertEqual(body, b'')
        status, headers, body = self.request('/api/bridge-status?OMIT_PRIVATE_QUERY', method='OMIT_PRIVATE_METHOD')
        self.assertEqual(status, 501)
        self.assert_error_envelope(headers, body)

    def test_invalid_trace_values_rejected_before_configuration_or_reader(self):
        with patch.dict('os.environ', {}, clear=True), patch('server.HubReader') as reader:
            for query in ('gameId=other&correlationId=ok', 'gameId=ffxi&correlationId=',
                          'gameId=ffxi&correlationId=bad%2Fid', 'gameId=ffxi&correlationId=' + 'x' * 129):
                with self.subTest(query=query):
                    status, _, _ = self.request('/api/trace?' + query)
                    self.assertEqual(status, 400)
            reader.assert_not_called()

    def test_cached_views_validate_before_read_and_keep_errors_private(self):
        configured = {'HUB_READONLY_URL': 'http://127.0.0.1:1', 'HUB_TOKEN_FILE': '/fixture/not-read'}
        for route, target in (('/api/interaction', 'server.HUB_INTERACTION.get'),
                              ('/api/hub-health', 'server.HUB_HEALTH.get')):
            with self.subTest(route=route), patch(target) as read:
                with patch.dict('os.environ', {}, clear=True):
                    self.assertEqual(self.request(route)[0], 503)
                    self.assertEqual(self.request(route + '?unexpected=1')[0], 400)
                    self.assertEqual(self.request(route, token=None)[0], 401)
                    read.assert_not_called()
                with patch.dict('os.environ', configured, clear=True):
                    for failure, status in ((ValueError('OMIT_PRIVATE_PATH'), 502),
                                            (server.HubReadError('OMIT_PRIVATE_TOKEN'), 503)):
                        read.side_effect = failure
                        actual, headers, body = self.request(route)
                        self.assertEqual(actual, status)
                        self.assert_error_envelope(headers, body)
                        self.assertEqual(headers['Cache-Control'], 'no-store')
                        self.assertNotIn(b'OMIT_PRIVATE', body)
                        self.assertNotIn(b'/fixture', body)
                        self.assertEqual(set(json.loads(body)), {'error'})

    def test_trace_projects_fixture_and_redacts_read_failures(self):
        configured = {'HUB_READONLY_URL': 'http://127.0.0.1:1', 'HUB_TOKEN_FILE': '/fixture/not-read'}
        raw = [{'kind': 'outcome', 'type': 'example.outcome', 'occurredAtUtc': '2026-01-01T12:00:00Z',
                'body': json.dumps({'classification': 'queued_for_native_delivery', 'isFinal': False,
                                    'private': 'OMIT_RAW_PLAYER_DATA'})}]
        read = Mock(return_value=(raw, 'fixture-fetch-time'))
        with patch.dict('os.environ', configured, clear=True), patch('server.HubReader', return_value=SimpleNamespace(trace=read)):
            status, _, body = self.request('/api/trace?gameId=ffxi&correlationId=example:1')
            self.assertEqual(status, 200)
            read.assert_called_once_with('ffxi', 'example:1')
            result = json.loads(body)
            self.assertEqual(result['fetchedAt'], 'fixture-fetch-time')
            self.assertIs(result['records'][0]['isFinal'], False)
            self.assertNotIn(b'OMIT_RAW', body)
            read.return_value = ({'invalid': 'OMIT_PRIVATE'}, 'fixture-fetch-time')
            status, _, body = self.request('/api/trace?gameId=ffxi&correlationId=example:1')
            self.assertEqual(status, 502)
            self.assertNotIn(b'OMIT_PRIVATE', body)
            read.side_effect = server.HubReadError('OMIT_PRIVATE_TOKEN')
            status, _, body = self.request('/api/trace?gameId=ffxi&correlationId=example:1')
            self.assertEqual(status, 503)
            self.assertNotIn(b'OMIT_PRIVATE', body)

    def test_nested_trace_body_keeps_metadata_and_unknown_outcome(self):
        record = {'kind': 'outcome', 'type': 'fixture.outcome',
                  'occurredAtUtc': '2026-01-01T00:00:00Z',
                  'body': '[' * 10000 + '"OMIT_PRIVATE_TRACE"' + ']' * 10000}
        with patch.dict('os.environ', {'HUB_READONLY_URL': 'http://127.0.0.1:1',
                                      'HUB_TOKEN_FILE': '/fixture/not-read'}, clear=True), \
                patch('server.HubReader', return_value=SimpleNamespace(trace=lambda *_: ([record], 'fixture-fetch'))):
            status, headers, body = self.request('/api/trace?gameId=ffxi&correlationId=fixture')
        self.assertEqual(status, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        row = json.loads(body)['records'][0]
        self.assertEqual(row['type'], 'fixture.outcome')
        self.assertEqual(row['occurredAt'], record['occurredAtUtc'])
        for field in ('classification', 'disposition', 'isFinal'):
            self.assertIsNone(row[field])
        self.assertNotIn(b'OMIT_PRIVATE_TRACE', body)

    def test_bridge_auth_and_method_rejection_do_not_reach_observer(self):
        runner = Mock(side_effect=AssertionError('Observer must not be reached'))
        with patch('server.BRIDGE', BridgeObserver(runner, lambda: 0)):
            for token in (None, '', 'wrong'):
                with self.subTest(token=token):
                    status, headers, body = self.request('/api/bridge-status', token=token)
                    self.assertEqual(status, 401)
                    self.assertEqual(headers['Cache-Control'], 'no-store')
                    self.assertEqual(json.loads(body), {'error': 'unauthorized'})
            self.assertEqual(self.request('/api/bridge-status', method='POST')[0], 501)
        runner.assert_not_called()

    def test_bridge_permission_denial_and_timeout_return_unknown_without_details(self):
        failures = [
            PermissionError('OMIT_PRIVATE_PATH'),
            subprocess.CalledProcessError(255, ['fixture-ssh'], output='OMIT_PRIVATE_OUTPUT', stderr='OMIT_PRIVATE_DENIAL'),
            subprocess.TimeoutExpired(['fixture-ssh'], 8, output='OMIT_PRIVATE_OUTPUT', stderr='OMIT_PRIVATE_TIMEOUT'),
        ]
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                runner = Mock(side_effect=failure)
                with patch('server.BRIDGE', BridgeObserver(runner, lambda: 0)):
                    status, headers, body = self.request('/api/bridge-status')
                self.assertEqual(status, 200)  # Observation unavailable, not an auth failure.
                self.assertEqual(headers['Cache-Control'], 'no-store')
                result = json.loads(body)
                self.assertIsNone(result['observedAt'])
                for field in ('unit', 'substate', 'result', 'marker', 'markerReason'):
                    self.assertEqual(result[field], 'unknown')
                self.assertNotIn(b'OMIT_PRIVATE', body)
                self.assertNotIn(b'fixture-token', body)
                runner.assert_called_once()
                command, options = runner.call_args
                self.assertIn('StrictHostKeyChecking=yes', command[0])
                self.assertEqual(options['timeout'], 8)
                self.assertTrue(options['check'])

    def test_bridge_failed_refresh_replaces_healthy_snapshot_and_recovers_after_ttl(self):
        good = {'observedAt': '2026-01-01T00:00:00Z', 'unit': 'active', 'substate': 'running',
                'result': 'success', 'marker': 'absent', 'markerReason': 'unknown'}
        runner = Mock(side_effect=[SimpleNamespace(stdout=json.dumps(good)),
                                   subprocess.TimeoutExpired(['fixture-ssh'], 8),
                                   SimpleNamespace(stdout=json.dumps({**good, 'observedAt': '2026-01-01T00:00:30Z'}))])
        clock = [0]
        with patch('server.BRIDGE', BridgeObserver(runner, lambda: clock[0])):
            first = json.loads(self.request('/api/bridge-status')[2])
            self.assertEqual(first['unit'], 'active')
            clock[0] = 15
            failed = json.loads(self.request('/api/bridge-status')[2])
            self.assertEqual(failed['unit'], 'unknown')
            self.assertIsNone(failed['observedAt'])
            clock[0] = 29.9
            self.assertEqual(json.loads(self.request('/api/bridge-status')[2]), failed)
            self.assertEqual(runner.call_count, 2)
            clock[0] = 30
            recovered = json.loads(self.request('/api/bridge-status')[2])
            self.assertEqual(recovered['observedAt'], '2026-01-01T00:00:30Z')
            self.assertEqual(recovered['unit'], 'active')
            self.assertEqual(runner.call_count, 3)


if __name__ == '__main__':
    unittest.main()
