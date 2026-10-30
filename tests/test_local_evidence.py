"""Special-file refusals use only temporary synthetic paths, never real evidence."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import operation_sources
import wake_verification
from local_evidence import read_bytes
from tests.test_wake_verification import receipt


class LocalEvidenceTests(unittest.TestCase):
    def test_bounded_regular_read_and_both_reader_recovery_paths(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root)
            path = home / 'evidence'
            raw = json.dumps(receipt()).encode()
            spec = dict(operation_sources.SOURCES[0], path='evidence', sha256=hashlib.sha256(raw).hexdigest())
            path.write_bytes(raw)
            self.assertEqual(read_bytes(path, 8), raw[:9])
            with patch.object(operation_sources, 'SOURCES', (spec,)):
                for special in ('fifo', 'directory', 'symlink'):
                    path.unlink()
                    if special == 'fifo':
                        os.mkfifo(path)
                    elif special == 'directory':
                        path.mkdir()
                    else:
                        target = home / 'target'
                        target.write_bytes(raw)
                        path.symlink_to(target)
                    with self.subTest(special=special):
                        self.assertIsNone(wake_verification.read(path)['cutover'])
                        self.assertEqual(operation_sources.read(home)['rows'][0]['state'], 'Source unavailable')
                    if special == 'directory':
                        path.rmdir()
                    else:
                        path.unlink()
                    path.write_bytes(raw)
                    self.assertIsNotNone(wake_verification.read(path)['cutover'])
                    self.assertEqual(operation_sources.read(home)['rows'][0]['state'], 'Reviewed bytes match')

    def test_descriptor_is_closed_on_special_file_refusal(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'fifo'
            os.mkfifo(path)
            original_open = os.open
            descriptors = []
            def capture(*args, **kwargs):
                fd = original_open(*args, **kwargs)
                descriptors.append(fd)
                return fd
            with patch('local_evidence.os.open', side_effect=capture):
                with self.assertRaises(OSError):
                    read_bytes(path, 64)
            self.assertEqual(len(descriptors), 1)
            with self.assertRaises(OSError):
                os.fstat(descriptors[0])
