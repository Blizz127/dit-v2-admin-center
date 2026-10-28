import json
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
            self.send_response(200); self.end_headers(); self.wfile.write(b'[]')
        elif self.path.startswith('/v1/control/learning'):
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"gameId":"ffxi","tasks":[]}')
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
                data, stamp = reader.get('bots', 'ffxi'); self.assertEqual(data, []); self.assertTrue(stamp)
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


if __name__ == '__main__': unittest.main()
