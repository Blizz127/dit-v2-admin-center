"""Offline artifact checks; these do not claim that a browser executed the page."""
import base64
import hashlib
from html.parser import HTMLParser
import unittest
from unittest.mock import patch

from tools import build_inspector_playtest as harness


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.ids, self.external, self.scripts = [], [], []
        self.csp = None
        self.in_script = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy':
            self.csp = attrs['content']
        if tag in ('script', 'link', 'img', 'iframe') and ('src' in attrs or 'href' in attrs):
            self.external.append(attrs)
        if tag == 'script':
            self.in_script = True
            self.scripts.append('')

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False

    def handle_data(self, data):
        if self.in_script:
            self.scripts[-1] += data


class InspectorPlaytestTests(unittest.TestCase):
    def setUp(self):
        for target in ('socket.create_connection', 'socket.socket.connect'):
            guard = patch(target, side_effect=AssertionError('network forbidden'))
            guard.start()
            self.addCleanup(guard.stop)

    def test_artifact_embeds_actual_assets_with_no_external_resources(self):
        html = harness.build()
        doc = Document(html)
        self.assertEqual(doc.external, [])
        self.assertEqual(len(doc.ids), len(set(doc.ids)))
        self.assertEqual(len(doc.scripts), 1)
        self.assertIn((harness.ROOT / 'static/app.js').read_text(), doc.scripts[0])
        self.assertIn((harness.ROOT / 'static/style.css').read_text(), html)
        self.assertIn("connect-src 'none'", doc.csp)
        self.assertIn("form-action 'none'", doc.csp)
        digest = base64.b64encode(hashlib.sha256(doc.scripts[0].encode()).digest()).decode()
        self.assertIn("script-src 'sha256-" + digest + "'", doc.csp)
        self.assertIn('NOT RUN', html)
        self.assertNotIn('OMIT_RAW_ANSWER_AND_PLAYER_DATA', html)

    def test_snapshot_uses_actual_projection_without_accounts_or_server(self):
        rows = harness.snapshot()['learning']
        self.assertEqual([r['hasModelAnswer'] for r in rows], [True, False, True, None])
        self.assertEqual([r['evidence'] for r in rows], ['Not included', 'Unknown', 'Present', 'Not included'])
        self.assertTrue(all(r['policy'] == 'Unknown' and r['game'] == 'FFXI' for r in rows))
        self.assertTrue(all('Synthetic' in r['source'] for r in rows))

    def test_fixture_text_cannot_close_inline_script(self):
        data = harness.snapshot()
        data['learning'][0]['topic'] = '</script><script>throw "fixture"</script>'
        with patch.object(harness, 'snapshot', return_value=data):
            doc = Document(harness.build())
        self.assertEqual(len(doc.scripts), 1)
        self.assertIn('\\u003c/script>', doc.scripts[0])


if __name__ == '__main__':
    unittest.main()
