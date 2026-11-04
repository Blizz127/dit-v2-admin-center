import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import context_capture
from server import make_server

FIXTURE = Path(__file__).parent / 'fixtures/context-status-integration/ffxi-companion.json'


class ContextCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(0, 'synthetic-context-token')
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'capture.json'
        self.path.write_bytes(FIXTURE.read_bytes())
        env = patch.dict(os.environ, {context_capture.ENV: str(self.path)})
        env.start(); self.addCleanup(env.stop)
        for name in ('server.HubReader', 'server.BRIDGE.read', 'server.overview', 'subprocess.Popen'):
            guard = patch(name, side_effect=AssertionError('Unexpected external collection'))
            guard.start(); self.addCleanup(guard.stop)

    def request(self, token='synthetic-context-token', path='/api/context-capture', method='GET'):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        headers = {} if token is None else {'Authorization': 'Bearer ' + token}
        connection.request(method, path, headers=headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_authentication_precedes_file_reads_and_queries_are_refused(self):
        with patch('context_capture.read_json', side_effect=AssertionError('Must not read')) as read:
            for token in (None, 'wrong'):
                self.assertEqual(self.request(token)[0], 401)
            self.assertEqual(self.request(path='/api/context-capture?file=forbidden')[0], 400)
            self.assertEqual(self.request(method='POST')[0], 405)
            read.assert_not_called()

    def test_authenticated_loopback_startup_and_exact_capture_smoke(self):
        status, headers, body = self.request()
        data = json.loads(body)
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        self.assertEqual(status, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(int(headers['Content-Length']), len(body))
        self.assertIsNone(headers.get('Access-Control-Allow-Origin'))
        self.assertEqual(data['status'], 'Loaded')
        self.assertEqual(data['capture'], json.loads(FIXTURE.read_text()))
        self.assertNotIn(str(self.path).encode(), body)
        self.assertNotIn(b'synthetic-context-token', body)

    def test_unconfigured_does_not_read_or_fall_back(self):
        with patch.dict(os.environ, {context_capture.ENV: ''}), patch('context_capture.read_json') as read:
            self.assertEqual(json.loads(self.request()[2]), {'status': 'Not configured', 'capture': None})
            read.assert_not_called()

    def test_corruption_clears_previous_capture_and_corrected_file_recovers(self):
        self.assertEqual(json.loads(self.request()[2])['status'], 'Loaded')
        for raw in (b'{"schema":', b'[]', b'x' * (context_capture.LIMIT + 1), b'[' * 1800 + b'0' + b']' * 1800):
            self.path.write_bytes(raw)
            self.assertEqual(json.loads(self.request()[2]), {'status': 'Unavailable', 'capture': None})
        self.path.write_bytes(FIXTURE.read_bytes())
        self.assertEqual(json.loads(self.request()[2])['status'], 'Loaded')

    def test_extra_file_fields_are_not_exported(self):
        data = json.loads(FIXTURE.read_text())
        data['privateExtra'] = 'OMIT_EXTRA_FILE_CONTENT'
        data['statusBinding']['privateExtra'] = 'OMIT_EXTRA_FILE_CONTENT'
        data['statusBinding']['View']['Fields'][0]['privateExtra'] = 'OMIT_EXTRA_FILE_CONTENT'
        self.path.write_text(json.dumps(data))
        status, _, body = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['status'], 'Loaded')
        self.assertNotIn(b'OMIT_EXTRA_FILE_CONTENT', body)

    def test_valid_unknown_packets_load_without_reusing_previous_native_values(self):
        self.assertEqual(json.loads(self.request()[2])['status'], 'Loaded')
        for fixture in sorted((FIXTURE.parent.parent / 'context-status-unavailable').glob('*.json')):
            data = json.loads(fixture.read_text())
            data['statusBinding']['Lookup']['privateExtra'] = 'OMIT_EXTRA_FILE_CONTENT'
            self.path.write_text(json.dumps(data))
            status, _, body = self.request()
            with self.subTest(fixture=fixture.name):
                self.assertEqual(status, 200)
                response = json.loads(body)
                self.assertEqual(response['status'], 'Loaded')
                self.assertEqual(response['capture']['statusBinding']['State'], data['statusBinding']['State'])
                self.assertEqual(response['capture']['userMessage'], data['userMessage'])
                self.assertNotIn(b'Synthetic native west entrance', body)
                self.assertNotIn(b'OMIT_EXTRA_FILE_CONTENT', body)
        self.path.write_bytes(FIXTURE.read_bytes())
        self.assertEqual(json.loads(self.request()[2])['status'], 'Loaded')

    def test_non_synthetic_file_missing_file_and_leaf_symlink_are_unavailable(self):
        data = json.loads(FIXTURE.read_text()); data['synthetic'] = False
        self.path.write_text(json.dumps(data))
        self.assertEqual(json.loads(self.request()[2])['status'], 'Unavailable')
        self.path.unlink()
        self.assertEqual(json.loads(self.request()[2])['status'], 'Unavailable')
        self.path.symlink_to(FIXTURE.resolve())
        self.assertEqual(json.loads(self.request()[2])['status'], 'Unavailable')
