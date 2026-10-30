import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import operation_sources as sources


class OperationSourcesTests(unittest.TestCase):
    def test_matching_changed_missing_and_oversize_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / 'note.md'
            raw = b'private source bytes never projected'
            spec = dict(sources.SOURCES[0], path='note.md', sha256=hashlib.sha256(raw).hexdigest())
            with patch.object(sources, 'SOURCES', (spec,)):
                path.write_bytes(raw)
                result = sources.read(home)
                self.assertEqual(result['rows'][0]['state'], 'Reviewed bytes match')
                self.assertNotIn('private source bytes', json.dumps(result))
                self.assertNotIn('path', result['rows'][0])
                for replacement in (b'new receipt', b'x' * (sources.LIMIT + 1)):
                    path.write_bytes(replacement)
                    self.assertEqual(sources.read(home)['rows'][0]['state'], 'Source changed — review required')
                path.unlink()
                self.assertEqual(sources.read(home)['rows'][0]['state'], 'Source unavailable')

    def test_standalone_never_reads_external_files_or_claims_acceptance(self):
        with patch.object(Path, 'open', side_effect=AssertionError('External read')):
            rows = sources.read()['rows']
        self.assertEqual([r['id'] for r in rows], ['wake-8450', 'ashes', 'lotro'])
        self.assertTrue(all(r['state'] == 'Not checked in standalone preview' for r in rows))
        self.assertTrue(all('no 8450 binding' in r['missing'] for r in rows[1:]))
        self.assertNotIn('authenticated', rows[0])
