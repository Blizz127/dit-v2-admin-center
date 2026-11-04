import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.build_delivery_correlation_preview import ROOT, build, scenarios


class DeliveryCorrelationPreviewTests(unittest.TestCase):
    def cli(self, *arguments):
        return subprocess.run([sys.executable, '-m', 'tools.correlate_delivery', *arguments], cwd=ROOT,
                              capture_output=True, text=True, timeout=5)

    def test_cli_default_off_synthetic_opt_in_and_unavailable_recovery(self):
        result = self.cli('--capture', '/unavailable-and-must-not-open')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['status'], 'Disabled')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.json'
            valid = (ROOT / 'tests/fixtures/delivery-correlation/ffxi.json').read_bytes()
            path.write_bytes(valid)
            for simulate in (False, True):
                arguments = ['--enable-offline', '--capture', str(path)]
                if simulate: arguments.append('--simulate-native-receipts')
                result = self.cli(*arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report['counts']['syntheticConfirmed'], 2 if simulate else 0)
                self.assertFalse(report['nativeDeliveryVerified'])
                self.assertIsNone(report['deliveredInGame'])
                self.assertEqual(path.read_bytes(), valid)
            path.write_text('{"broken":')
            result = self.cli('--enable-offline', '--capture', str(path))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)['records'], [])
            self.assertNotIn(str(path), result.stdout + result.stderr)
            path.write_bytes(valid)
            self.assertEqual(self.cli('--enable-offline', '--capture', str(path)).returncode, 0)
        self.assertEqual(self.cli('--simulate-native-receipts').returncode, 2)

    def test_six_preview_states_keep_actual_delivery_unknown_without_active_content(self):
        cases = scenarios()
        self.assertEqual(len(cases), 6)
        self.assertEqual(cases[1][1]['counts']['syntheticConfirmed'], 2)
        self.assertEqual(cases[2][1]['counts']['conflicted'], 2)
        page = build()
        self.assertEqual(page.count('<section>'), 6)
        self.assertIn('Actual in-game delivery: Unknown', page)
        self.assertIn('Native browser: NOT RUN', page)
        self.assertIn("connect-src 'none'", page)
        self.assertNotIn('<script', page)
        self.assertNotIn('src=', page)
        self.assertIn('Native observation time (fixture)', page)
        self.assertIn('Receipt time (fixture)', page)
        cases[1][1]['records'][0]['text'] = '<img src=x onerror=alert(1)>'
        with patch('tools.build_delivery_correlation_preview.scenarios', return_value=cases):
            escaped = build()
        self.assertNotIn('<img', escaped)
        self.assertIn('&lt;img', escaped)
