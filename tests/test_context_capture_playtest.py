import base64
import hashlib
import json
from html.parser import HTMLParser
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.build_context_capture_playtest import build, ROOT


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.scripts = []
        self.inline = False
        self.csp = ''
        self.sources = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self.inline = True
            self.scripts.append('')
        if 'src' in attrs:
            self.sources.append(attrs['src'])
        if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy':
            self.csp = attrs['content']

    def handle_data(self, text):
        if self.inline:
            self.scripts[-1] += text

    def handle_endtag(self, tag):
        if tag == 'script':
            self.inline = False


class ContextPanelPlaytestTests(unittest.TestCase):
    def test_artifact_binds_actual_application_and_all_six_validated_captures(self):
        page = Page(build())
        self.assertEqual(len(page.scripts), 1)
        script = page.scripts[0]
        self.assertIn((ROOT / 'static/app.js').read_text(), script)
        payload = script.split('const fixtures = ', 1)[1].split(';\nconst sessionStorage', 1)[0]
        data = json.loads(payload)
        self.assertEqual(len(data['captures']), 6)
        for name, capture in data['captures'].items():
            self.assertEqual(capture, json.loads((ROOT / 'tests/fixtures/context-status-integration' / (name + '.json')).read_text()))

    def test_artifact_blocks_network_and_script_is_valid_without_launching_browser(self):
        page = Page(build())
        self.assertEqual(page.sources, [])
        self.assertIn("connect-src 'none'", page.csp)
        self.assertIn("default-src 'none'", page.csp)
        digest = base64.b64encode(hashlib.sha256(page.scripts[0].encode()).digest()).decode()
        self.assertIn("script-src 'sha256-" + digest + "'", page.csp)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture.js'
            path.write_text(page.scripts[0])
            result = subprocess.run(['node', '--check', str(path)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
