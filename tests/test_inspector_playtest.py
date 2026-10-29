"""Offline artifact checks; these do not claim that a browser executed the page."""
import base64
import hashlib
import os
import subprocess
import tempfile
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
        self.assertIn('harness-provenance', doc.ids)
        for name, digest in harness.source_fingerprints().items():
            self.assertIn(name, html)
            self.assertIn(digest, html)

    def test_snapshot_uses_actual_projection_without_accounts_or_server(self):
        rows = harness.snapshot()['learning']
        self.assertEqual([r['hasModelAnswer'] for r in rows], [True, False, True, None])
        self.assertEqual([r['evidence'] for r in rows], ['Not included', 'Unknown', 'Present', 'Not included'])
        self.assertTrue(all(r['policy'] == 'Unknown' and r['game'] == 'FFXI' for r in rows))
        self.assertTrue(all('Synthetic' in r['source'] for r in rows))

    def test_generated_javascript_compiles_without_executing(self):
        # Parse the complete assembled app + driver + fixtures. This is not DOM execution.
        doc = Document(harness.build())
        self.assertEqual(len(doc.scripts), 1)
        with tempfile.TemporaryDirectory() as temp:
            script = os.path.join(temp, 'synthetic-artifact.js')
            with open(script, 'w') as output:
                output.write(doc.scripts[0])
            result = subprocess.run(['node', '--check', script], capture_output=True,
                                    text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')

    def test_fixture_text_cannot_close_inline_script(self):
        data = harness.snapshot()
        data['learning'][0]['topic'] = '</script><script>throw "fixture"</script>'
        with patch.object(harness, 'snapshot', return_value=data):
            doc = Document(harness.build())
        self.assertEqual(len(doc.scripts), 1)
        self.assertIn('\\u003c/script>', doc.scripts[0])

    def test_missing_dom_runtime_is_a_blocked_exit_not_a_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                ['node', str(harness.ROOT / 'tools/run_inspector_playtest.cjs')],
                env={**os.environ, 'DIT_JSDOM_MODULE': temp + '/missing-runtime'},
                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('BLOCKED: jsdom is not installed', result.stderr)
        self.assertNotIn('passed', result.stdout)

    def test_party_comparison_uses_reviewer_without_promoting_queue_to_speech(self):
        examples = dict(harness.party_review_examples())
        self.assertEqual(len(examples), 4)
        self.assertIn('matching new queue', examples['Queue report only']['queuedReply'])
        self.assertEqual(examples['Queue report only']['nativeSpeech'], 'Unknown')
        self.assertEqual(examples['Owner report without queue telemetry']['queuedReply'], 'Unknown')
        self.assertIn('Owner-reported', examples['Owner report without queue telemetry']['nativeSpeech'])
        self.assertIn('Mixed enqueue claims', examples['Mixed enqueue claims']['queueReview'])
        self.assertEqual(examples['Old retained queue row']['queuedReply'], 'Unknown')
        self.assertTrue(all(row['modelOrigin'] == 'Unknown' for row in examples.values()))
        html = harness.party_review_html()
        self.assertIn('not live results', html)
        self.assertEqual(html.count('<tr>'), 5)
        self.assertIn('scope="col"', html)
        self.assertIn('scope="row"', html)
        self.assertIn('tabindex="0"', html)

    def test_party_comparison_escapes_text_and_never_embeds_raw_metadata(self):
        hostile = '<script>PRIVATE_FIXTURE</script>'
        result = dict(queuedReply=hostile, queueReview='Unknown', nativeSpeech='Unknown', modelOrigin='Unknown')
        with patch.object(harness, 'party_review_examples', return_value=[(hostile, result)]):
            html = harness.party_review_html()
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertEqual(Document(html).scripts, [])
        normal = harness.party_review_html()
        self.assertNotIn('fixture-attempt', normal)
        self.assertNotIn('fixture-party', normal)


if __name__ == '__main__':
    unittest.main()
