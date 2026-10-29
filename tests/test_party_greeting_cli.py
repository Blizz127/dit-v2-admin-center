"""Invoke the offline reviewer with temporary synthetic files, never live logs."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PartyGreetingCLITests(unittest.TestCase):
    def run_file(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private-metadata.json'
            if raw is not None:
                path.write_bytes(raw)
            result = subprocess.run([sys.executable, str(ROOT / 'tools/review_party_greeting.py'), str(path)],
                                    capture_output=True, text=True, timeout=3)
            if raw is not None:
                self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(set(Path(directory).iterdir()), {path} if raw is not None else set())
            return result

    def test_invalid_files_are_redacted_and_never_produce_an_assessment(self):
        cases = [None, b'', b'{"OMIT_PRIVATE_CHAT":', b'\xff', b' ' * 65537,
                 b'[' * 10000 + b']' * 10000,
                 b'{"ownerGenerated":false,"ownerGenerated":true}',
                 b'{"scope":{"botId":"one","botId":"two"}}',
                 b'{"value":NaN}', b'{"value":Infinity}', b'{"value":1e999}',
                 b'{"scope":{"extra":-1e999}}']
        for raw in cases:
            with self.subTest(raw=repr(raw)[:45]):
                result = self.run_file(raw)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertEqual(result.stderr, 'Unavailable or invalid review metadata; no evidence assessed.\n')

    def test_valid_fixture_is_read_only_and_keeps_evidence_stages_separate(self):
        raw = (ROOT / 'tests/fixtures/party-greeting-review.json').read_bytes()
        data = json.loads(raw)
        data['chat'] = 'OMIT_PRIVATE_CHAT'
        result = self.run_file(json.dumps(data).encode())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, '')
        self.assertNotIn('OMIT_PRIVATE_CHAT', result.stdout)
        assessment = json.loads(result.stdout)
        self.assertIn('matching new queue', assessment['queuedReply'])
        self.assertEqual(assessment['nativeSpeech'], 'Unknown')
        self.assertEqual(assessment['modelOrigin'], 'Unknown')
        self.assertNotIn('passed', assessment.values())
