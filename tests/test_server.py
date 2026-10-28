import http.client
import json
import threading
import tempfile
from pathlib import Path
import unittest

from server import capacity_context, make_server


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

    def test_playtest_guide_is_read_only_and_labels_data(self):
        status, _, body = self.request("GET", "/playtest")
        self.assertEqual(status, 200)
        self.assertIn(b'hub is not configured', body)
        self.assertIn(b'Model changes remain disabled', body)
        self.assertEqual(self.request("POST", "/playtest")[0], 501)

    def test_workspace_changelog_is_visible_and_labeled(self):
        page = self.request("GET", "/")[2].decode()
        self.assertIn("What's new", page)
        self.assertIn('curated changelog, not a live activity feed', page)
        self.assertIn('model controls remain disabled', page)

    def test_global_controls_are_disabled(self):
        from html.parser import HTMLParser
        class Controls(HTMLParser):
            def __init__(self):
                super().__init__(); self.disabled = False; self.controls = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "fieldset": self.disabled = "disabled" in attrs
                if attrs.get("id") in ("global-model", "global-model-toggle"):
                    self.controls.append(self.disabled or "disabled" in attrs)
            def handle_endtag(self, tag):
                if tag == "fieldset": self.disabled = False
        page = self.request("GET", "/")[2].decode()
        parser = Controls(); parser.feed(page)
        self.assertEqual(parser.controls, [True, True])

    def test_source_parameter_rejects_invalid_values(self):
        self.assertEqual(self.request("GET", "/api/overview?source=unknown", "test-private-token")[0], 400)
        self.assertEqual(self.request("GET", "/api/overview?source=mock&source=hub", "test-private-token")[0], 400)
        self.assertEqual(self.request("GET", "/api/overview?unrecognized=1", "test-private-token")[0], 400)

    def test_mock_and_no_writes(self):
        status, headers, body = self.request("GET", "/api/overview", "test-private-token")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        data = json.loads(body)
        self.assertEqual(data["mode"], "mock")
        self.assertEqual(data["ledger"][0]["verification"], "Pending")
        self.assertEqual(self.request("POST", "/api/overview", "test-private-token")[0], 501)
        self.assertEqual(self.request("GET", "/api/missing", "test-private-token")[0], 404)


class CapacityTests(unittest.TestCase):
    def test_pool_scope_and_stale_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "routing-capacity.json").write_text(json.dumps({
                "checked_at": 1000, "providers": {"claude": {"remaining": 0.75}}
            }))
            value, reason = capacity_context(root, "claude", now=1010)
            self.assertEqual(value, "75%")
            self.assertIn("not the lead's own quota", reason)
            self.assertEqual(capacity_context(root, "claude", now=1181)[0], "Unknown")
            self.assertEqual(capacity_context(root, None, now=1010)[0], "Unknown")


if __name__ == "__main__":
    unittest.main()
