"""Fake capture-header contracts; no browser or image-rendering evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from tools.run_keyboard_playtest import publish_captures


class CapturePublicationTests(unittest.TestCase):
    def test_complete_set_is_published_with_hashes_and_unique_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / 'synthetic.html'
            artifact.write_text('synthetic')
            captures = []
            for name, width, height in [('desktop.png', 1280, 1000), ('narrow-left.png', 390, 844), ('narrow-right.png', 390, 844)]:
                (root / name).write_bytes(b'\x89PNG\r\n\x1a\n' + bytes(8) + width.to_bytes(4, 'big') + height.to_bytes(4, 'big'))
                captures.append(dict(file=name, width=width, height=height))
            result = {'visual': dict(status='captured', captures=captures)}
            output = root / 'published'
            first = Path(publish_captures(result, root, artifact, output))
            second = Path(publish_captures(result, root, artifact, output))
            self.assertNotEqual(first, second)
            receipt = json.loads((first / 'receipt.json').read_text())
            self.assertEqual(len(receipt['visual']['artifactSha256']), 64)
            self.assertTrue(all(len(item['sha256']) == 64 for item in receipt['visual']['captures']))
            bad = copy.deepcopy(result)
            bad['visual']['captures'][0]['file'] = '../outside.png'
            with self.assertRaises(ValueError):
                publish_captures(bad, root, artifact, output)
            (root / 'narrow-right.png').write_bytes(b'truncated')
            with self.assertRaises(ValueError):
                publish_captures(result, root, artifact, output)
            self.assertEqual(len(list(output.iterdir())), 2)

    def test_incomplete_receipt_creates_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for visual in [{}, {'status':'captured', 'captures':[]}]:
                with self.assertRaises(ValueError):
                    publish_captures({'visual':visual}, root, root/'unused', root/'out')
            self.assertFalse((root/'out').exists())
