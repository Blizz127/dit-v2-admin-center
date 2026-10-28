import json
import tempfile
import unittest
from pathlib import Path

from quota_history import collect, history


class QuotaHistoryTests(unittest.TestCase):
    def test_snapshot_deduplicated_and_sensitive_fields_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'state.json'
            source.write_text(json.dumps({'accounts': {
                'first': {'email': 'person@example.invalid', 'usage': {'checked_at': 1000, 'rows': [{'quota': {'unified5h': .25, 'unified7d': .5}}]}},
                'excluded': {'email': 'person@sbisd.invalid', 'usage': {'checked_at': 1000, 'rows': [{'quota': {'unified5h': .1}}]}},
                'error': {'email': 'person@example.invalid', 'usage': {'checked_at': 1000, 'error': 'example', 'rows': [{'quota': {'unified5h': .1}}]}},
            }}))
            self.assertEqual(collect(source, root / 'local'), 2)
            self.assertEqual(collect(source, root / 'local'), 0)
            rows = history(root / 'local')
            self.assertEqual(len(rows), 2)
            self.assertEqual({r['remainingPercent'] for r in rows}, {75.0, 50.0})
            self.assertNotIn('person', str(rows))
            self.assertNotIn('first', str(rows))
            self.assertEqual((root / 'local' / 'codex-quota.sqlite').stat().st_mode & 0o777, 0o600)

    def test_missing_or_invalid_source_never_becomes_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(collect(root / 'missing', root / 'local'), 0)
            self.assertEqual(history(root / 'local'), [])
            self.assertFalse((root / 'local').exists())


if __name__ == '__main__':
    unittest.main()
