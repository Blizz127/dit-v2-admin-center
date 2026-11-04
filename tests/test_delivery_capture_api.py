import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import delivery_correlation
from server import make_server

FIXTURE = Path(__file__).parent / 'fixtures/delivery-correlation/ffxi.json'


class DeliveryCaptureApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(0, 'synthetic-delivery-token')
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'capture.json'
        self.path.write_bytes(FIXTURE.read_bytes())
        env = patch.dict(os.environ, {delivery_correlation.ENV: str(self.path)})
        env.start(); self.addCleanup(env.stop)
        for name in ('server.HubReader', 'server.BRIDGE.read', 'server.overview', 'subprocess.Popen'):
            guard = patch(name, side_effect=AssertionError('No external collection'))
            guard.start(); self.addCleanup(guard.stop)

    def request(self, token='synthetic-delivery-token', path='/api/delivery-capture', method='GET'):
        client = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        client.request(method, path, headers={} if token is None else {'Authorization': 'Bearer ' + token})
        response = client.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        client.close()
        return result

    def test_auth_queries_and_writes_are_refused_before_file_reads(self):
        with patch('delivery_correlation.read_json', side_effect=AssertionError('Must not read')) as read:
            for token in (None, 'wrong'):
                self.assertEqual(self.request(token=token)[0], 401)
            for query in ('file=forbidden', 'simulate-native-receipts=true'):
                self.assertEqual(self.request(path='/api/delivery-capture?' + query)[0], 400)
            self.assertEqual(self.request(method='POST')[0], 405)
            read.assert_not_called()

    def test_localhost_smoke_has_no_native_verifier_or_extra_field_export(self):
        data = json.loads(FIXTURE.read_text())
        data['privateExtra'] = 'OMIT_PRIVATE_EXTRA'
        for receipt in data['receipts']:
            receipt['trusted'] = True
        self.path.write_text(json.dumps(data))
        before = self.path.read_bytes()
        status, headers, raw = self.request()
        report = json.loads(raw)
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        self.assertEqual(status, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(report['status'], 'Loaded')
        self.assertEqual(report['counts']['publicationMatched'], 2)
        self.assertEqual(report['counts']['syntheticConfirmed'], 0)
        self.assertFalse(report['nativeDeliveryVerified'])
        self.assertFalse(report['replayAuthorized'])
        for hidden in ('OMIT_PRIVATE_EXTRA', str(self.path), 'synthetic-delivery-token'):
            self.assertNotIn(hidden.encode(), raw)
        self.assertEqual(self.path.read_bytes(), before)

    def test_default_off_and_unavailable_clear_and_recovery(self):
        with patch.dict(os.environ, {delivery_correlation.ENV: ''}), patch('delivery_correlation.read_json') as read:
            self.assertEqual(json.loads(self.request()[2])['status'], 'Not configured')
            read.assert_not_called()
        self.assertEqual(json.loads(self.request()[2])['status'], 'Loaded')
        self.path.write_text('{"partial":')
        report = json.loads(self.request()[2])
        self.assertEqual(report['status'], 'Unavailable')
        self.assertEqual(report['records'], [])
        self.assertIsNone(report['counts'])
        self.path.write_bytes(FIXTURE.read_bytes())
        self.assertEqual(json.loads(self.request()[2])['status'], 'Loaded')
