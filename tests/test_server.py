import http.client
import json
import threading
import unittest

from server import make_server


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(0, "test-private-token")
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, token=None):
        conn = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        headers = {"Authorization": "Bearer " + token} if token else {}
        conn.request(method, path, headers=headers)
        response = conn.getresponse()
        body = response.read()
        result = response.status, dict(response.getheaders()), body
        conn.close()
        return result

    def test_loopback_and_token_required(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        for token in (None, "wrong"):
            status, _, body = self.request("GET", "/api/overview", token)
            self.assertEqual(status, 401)
            self.assertNotIn(b"Aster", body)
        with self.assertRaises(ValueError):
            make_server(0, "")

    def test_mock_and_no_writes(self):
        status, headers, body = self.request("GET", "/api/overview", "test-private-token")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        data = json.loads(body)
        self.assertEqual(data["mode"], "mock")
        self.assertEqual(data["ledger"][0]["verification"], "Pending")
        self.assertEqual(self.request("POST", "/api/overview", "test-private-token")[0], 501)
        self.assertEqual(self.request("GET", "/api/missing", "test-private-token")[0], 404)


if __name__ == "__main__":
    unittest.main()
