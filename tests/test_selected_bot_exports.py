"""Explicit private export builds reuse the offline parsers, never live sources."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import ffxi_botsv2_log
import bot_event_v1
from tools import build_inspector_playtest as preview
from tools.selected_bot_exports import read_selected_exports
from tests.test_inspector_playtest import Document


class SelectedBotExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ffxi = preview.ROOT / 'tests/fixtures/ffxi-botsv2/synthetic-post-h1-readiness.log'
        self.events = preview.ROOT / 'tests/fixtures/bot-event-swtor'

    def cli(self, *args):
        return subprocess.run(['python3', str(preview.ROOT / 'tools/build_inspector_playtest.py'), *map(str, args)],
                              cwd=preview.ROOT, capture_output=True, text=True, timeout=20)

    def test_no_arguments_do_not_enable_environment_selected_imports(self):
        with patch.dict(os.environ, {'DIT_FFXI_BOTSV2_LOG': str(self.ffxi), 'DIT_BOT_EVENT_DIR': str(self.events)}):
            self.assertIsNone(read_selected_exports())
            result = read_selected_exports(ffxi_log=self.ffxi)
        self.assertEqual([s['coverage']['status'] for s in result['sources']], ['Off', 'Loaded', 'Off', 'Off'])
        self.assertEqual(result['bots'], [])
        self.assertEqual(result['coverage']['status'], 'Off')
        for source in result['sources']:
            if source['coverage']['status'] == 'Off':
                self.assertEqual(source['bots'], [])
                self.assertIsNone(source['projectionSha256'])

    def test_selected_data_matches_existing_parser_and_fingerprint(self):
        result = read_selected_exports(ffxi_log=self.ffxi, bot_events_dir=self.events)
        for source, expected in zip(result['sources'][1:3],
                                    (ffxi_botsv2_log.read(self.ffxi), bot_event_v1.read(str(self.events)))):
            self.assertEqual((source['bots'], source['coverage']), expected)
            projected = json.dumps(dict(bots=source['bots'], coverage=source['coverage']),
                                   sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            self.assertEqual(source['projectionSha256'], hashlib.sha256(projected).hexdigest())
            self.assertIn('not live', source['note'])
        self.assertNotIn(str(preview.ROOT), json.dumps(result))

    def test_partial_input_keeps_coverage_and_never_embeds_unparsed_lines(self):
        source = self.root / 'PRIVATE_INPUT_LOCATION.log'
        source.write_bytes(self.ffxi.read_bytes() + b'\nRAW_PRIVATE_UNPARSED_LINE\n')
        selected = read_selected_exports(ffxi_log=source)
        self.assertGreater(selected['sources'][1]['coverage']['ignored'], 0)
        html = preview.build(ffxi_log=source)
        self.assertNotIn(str(source), html)
        self.assertNotIn('PRIVATE_INPUT_LOCATION', html)
        self.assertNotIn('RAW_PRIVATE_UNPARSED_LINE', html)
        self.assertIn('Selected offline exports', html)
        self.assertIn('OFFLINE · EXPORT REVIEW', html)
        self.assertIn('selected-export-provenance', html)
        self.assertEqual(preview.snapshot()['baselineConformance'], preview.baseline_conformance())

    def test_unavailable_and_symlinked_selected_sources_refuse_build(self):
        link = self.root / 'link.log'
        link.symlink_to(self.ffxi)
        for path in (self.root / 'missing.log', link, self.root):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    preview.build(ffxi_log=path)
        events_link = self.root / 'events-link'
        events_link.symlink_to(self.events, target_is_directory=True)
        with self.assertRaises(ValueError):
            preview.build(bot_events_dir=events_link)
        output = self.root / 'missing-output.html'
        result = self.cli('--ffxi-log', link, '--output', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())
        self.assertNotIn(str(link), result.stderr)

    def test_oversized_selected_file_is_refused(self):
        source = self.root / 'large.log'
        with source.open('wb') as f:
            f.truncate(ffxi_botsv2_log.MAX_BYTES + 1)
        with self.assertRaises(ValueError):
            read_selected_exports(ffxi_log=source)

    def test_combined_artifact_size_is_bounded(self):
        with patch.object(preview, 'MAX_ARTIFACT_BYTES', 1024):
            with self.assertRaisesRegex(ValueError, 'artifact limit'):
                preview.build(ffxi_log=self.ffxi)

    def test_private_cli_output_is_exclusive_and_preserves_earlier_report(self):
        output = self.root / 'review.html'
        result = self.cli('--ffxi-log', self.ffxi, '--output', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
        original = output.read_bytes()
        result = self.cli('--ffxi-log', self.ffxi, '--output', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), original)
        link = self.root / 'output-link.html'
        link.symlink_to(output)
        result = self.cli('--ffxi-log', self.ffxi, '--output', link)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), original)

    def test_selected_text_cannot_escape_inline_script_and_csp_matches(self):
        selected = read_selected_exports(ffxi_log=self.ffxi)
        selected['sources'][1]['bots'][0]['name'] = '</script><img src=x onerror=alert(1)>'
        with patch.object(preview, 'read_selected_exports', return_value=selected):
            doc = Document(preview.build(ffxi_log=self.ffxi))
        self.assertEqual(len(doc.scripts), 1)
        self.assertEqual(doc.external, [])
        self.assertIn('\\u003c/script>', doc.scripts[0])
        import base64
        digest = base64.b64encode(hashlib.sha256(doc.scripts[0].encode()).digest()).decode()
        self.assertIn("script-src 'sha256-" + digest + "'", doc.csp)
        self.assertIn("connect-src 'none'", doc.csp)


if __name__ == '__main__':
    unittest.main()
