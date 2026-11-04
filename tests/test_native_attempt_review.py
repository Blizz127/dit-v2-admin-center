"""Entirely synthetic returned reports, never evidence of a device run."""
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tools import review_native_attempt as reviewer

NOW = datetime(2026, 10, 31, tzinfo=timezone.utc)


def seed(root):
    metadata = {**reviewer.PIN, 'startedAt': '2026-10-30T03:00:00Z',
                'finishedAt': '2026-10-30T03:00:20Z',
                'versions': dict(browser='synthetic browser', node='synthetic node',
                                 python='synthetic python', unshare='synthetic unshare')}
    (root / 'attempt.json').write_text(json.dumps(metadata))
    manifest = (Path(__file__).parent / 'fixtures/native-8eb2c9f-SHA256SUMS').read_bytes()
    (root / 'SHA256SUMS').write_bytes(manifest)
    names = [line.split(maxsplit=1)[1] for line in manifest.decode().splitlines()]
    for name in ('pre-sums.txt', 'build-sums.txt', 'post-sums.txt'):
        (root / name).write_text(''.join(n + ': OK\n' for n in names))
    for name, text in {
        'started-at.txt': metadata['startedAt'], 'finished-at.txt': metadata['finishedAt'],
        'native-exit.txt': '0', 'post-manifest-exit.txt': '0', 'native-stderr.txt': '',
        'artifact-sha256.txt': reviewer.PIN['artifactSha256'] + '  build/inspector-playtest.html',
    }.items():
        (root / name).write_text(text)
    receipt = dict(status='passed', nativeKeyboard='passed', escapeCancellation='passed', automaticDOM='passed', steps=12,
                   shell=dict(status='passed', sections=8, widths=[1280, 390], traversal='Tab/Shift+Tab', activation='Enter'),
                   gapExport=dict(status='passed', savedBytes=512, candidates=2, selectedSnapshotRow=2,
                                  nativeActivation='Enter', sha256='a' * 64, table=dict(rows=9, columns=3, width=390)))
    (root / 'native-result.json').write_text(json.dumps(receipt))
    return metadata, receipt


class NativeAttemptReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.metadata, self.receipt = seed(self.root)
        for target in ('socket.socket', 'subprocess.Popen'):
            guard = patch(target, side_effect=AssertionError('No external execution'))
            guard.start()
            self.addCleanup(guard.stop)

    def review(self):
        return reviewer.review(self.root, NOW)

    def test_legacy_success_is_reported_only_and_does_not_require_newer_fields(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        result = self.review()
        self.assertEqual(result['status'], 'reported-pass')
        self.assertIn('not independently authenticated', result['scope'])
        self.assertIn('newer previews unverified', result['scope'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_blocked_and_failed_never_promote_partial_stdout(self):
        for message in reviewer.BLOCKERS:
            (self.root / 'native-exit.txt').write_text('2')
            (self.root / 'native-stderr.txt').write_text(message + '\n')
            (self.root / 'native-result.json').write_text('')
            self.assertEqual(self.review()['status'], 'blocked')
            (self.root / 'native-result.json').write_text(json.dumps(self.receipt))
            self.assertEqual(self.review()['status'], 'incomplete')
        for code in ('1', '124', '137'):
            (self.root / 'native-exit.txt').write_text(code)
            self.assertEqual(self.review()['status'], 'failed')

    def test_wrong_pin_executor_host_or_original_attempt_is_rejected(self):
        for key in reviewer.PIN:
            (self.root / 'attempt.json').write_text(json.dumps({**self.metadata, key: 'wrong'}))
            self.assertEqual(self.review()['status'], 'incomplete', key)
        for fields in ({'startedAt': '2026-10-29T23:20:30Z'}, {'finishedAt': '2999-01-01T00:00:00Z'},
                       {'finishedAt': '2026-10-30T02:59:59Z'}, {'startedAt': '2026-10-30T03:00:00'},
                       {'finishedAt': '2026-10-30T03:00:21Z'}, {'versions': {}}):
            (self.root / 'attempt.json').write_text(json.dumps({**self.metadata, **fields}))
            self.assertEqual(self.review()['status'], 'incomplete')

    def test_missing_duplicate_or_failed_manifest_reports_and_wrong_artifact(self):
        for filename in ('pre-sums.txt', 'build-sums.txt', 'post-sums.txt'):
            path = self.root / filename
            original = path.read_text()
            for modified in ('\n'.join(original.splitlines()[:-1]), original + original.splitlines()[0] + '\n',
                             original.replace(': OK', ': FAILED', 1)):
                path.write_text(modified)
                self.assertEqual(self.review()['status'], 'incomplete')
            path.write_text(original)
        for filename in ('SHA256SUMS', 'artifact-sha256.txt', 'post-manifest-exit.txt'):
            original = (self.root / filename).read_bytes()
            (self.root / filename).write_text('PRIVATE invalid')
            self.assertEqual(self.review()['status'], 'incomplete')
            (self.root / filename).write_bytes(original)

    def test_incomplete_keyboard_export_or_contradictory_hash_is_rejected(self):
        for field in self.receipt:
            (self.root / 'native-result.json').write_text(json.dumps({**self.receipt, field: None}))
            self.assertEqual(self.review()['status'], 'incomplete', field)
        (self.root / 'native-result.json').write_text(json.dumps({**self.receipt, 'artifactSha256': 'b' * 64}))
        self.assertEqual(self.review()['status'], 'incomplete')
        for value in (True, 10**400, -1, '390'):
            receipt = json.loads(json.dumps(self.receipt))
            receipt['gapExport']['table']['width'] = value
            (self.root / 'native-result.json').write_text(json.dumps(receipt))
            self.assertEqual(self.review()['status'], 'incomplete')

    def test_bounded_strict_files_and_redacted_cli(self):
        path = self.root / 'attempt.json'
        for raw in (b'', b'\xff', b'[]', b'[' * 20000 + b']' * 20000,
                    b'{' + b'"host":"PRIVATE",' + json.dumps(self.metadata).encode()[1:],
                    b'{"extra":1e999}', b' ' * (reviewer.LIMIT + 1)):
            path.write_bytes(raw)
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(reviewer.main([str(self.root)]), 1)
            self.assertNotIn('PRIVATE', stdout.getvalue())
            self.assertEqual(json.loads(stdout.getvalue())['status'], 'incomplete')
        path.unlink()
        path.symlink_to(self.root / 'native-exit.txt')
        self.assertEqual(self.review()['status'], 'incomplete')
        path.unlink()
        os.mkfifo(path)
        self.assertEqual(self.review()['status'], 'incomplete')
