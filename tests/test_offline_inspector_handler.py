"""Actual handler dispatch and serialization with memory-only HTTP request bytes.

No listener, live overview collection, token file or DOM dependency is used.
"""
import io
import json
from email.parser import BytesParser
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import server
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
                       'server.HubReader'):
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

    def test_mutation_method_is_rejected_before_collection(self):
        status, _, _ = self.request(method='POST')
        self.assertEqual(status, 501)
        self.overview.assert_not_called()


if __name__ == '__main__':
    unittest.main()
