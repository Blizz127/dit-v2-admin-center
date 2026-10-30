"""Runner contracts only; fabricated receipts are never native runtime evidence."""
import io
import hashlib
import math
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
from tools import run_keyboard_playtest as runner


SHELL = dict(status="passed", sections=8, widths=[1280, 390], traversal="Tab/Shift+Tab", activation="Enter",
             coverage=[dict(width=1280, cards=3, layout='columns'), dict(width=390, cards=3, layout='stacked')])


class KeyboardRunnerTests(unittest.TestCase):
    def test_expected_artifact_mismatch_stops_before_browser_and_removes_temp_file(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as root:
            owned = Path(root) / 'owned-profile-root'
            owned.mkdir()
            with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                    patch.object(runner, 'run_bounded', return_value=(0, '', '')) as run, \
                    patch.object(runner, 'build', return_value='<html>changed fixture</html>'), \
                    patch.object(runner.tempfile, 'tempdir', str(owned)), \
                    redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(runner.main(expected_artifact_sha256='a' * 64), 1)
                self.assertEqual(run.call_count, 1)  # Isolation preflight only, never browser.
                self.assertEqual(list(owned.iterdir()), [])
                self.assertEqual(stdout.getvalue(), '')
                self.assertIn('no browser started', stderr.getvalue())
        for invalid in ('', 'A' * 64, 'g' * 64, True, 'private/path'):
            with patch.object(runner, 'run_bounded') as run, \
                    patch.object(runner, 'build') as build, redirect_stderr(io.StringIO()):
                self.assertEqual(runner.main(expected_artifact_sha256=invalid), 1)
                run.assert_not_called()
                build.assert_not_called()

    def test_expected_artifact_match_is_still_subject_to_native_receipt_checks(self):
        artifact = '<html>synthetic é</html>'
        digest = hashlib.sha256(artifact.encode('utf-8')).hexdigest()
        good = dict(status='passed', nativeKeyboard='passed', steps=12,
                    escapeCancellation='passed', automaticDOM='passed', shell=SHELL)
        for result, expected in ((good, 0), ({'status': 'passed'}, 1)):
            with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                    patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (0, json.dumps(result), '')]) as run, \
                    patch.object(runner, 'build', return_value=artifact), \
                    redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()):
                self.assertEqual(runner.main(expected_artifact_sha256=digest), expected)
                self.assertEqual(run.call_count, 2)
                if expected == 0:
                    self.assertEqual(json.loads(stdout.getvalue())['artifactSha256'], digest)
                else:
                    self.assertEqual(stdout.getvalue(), '')

    def test_ambiguous_nonfinite_and_oversized_receipts_are_rejected(self):
        good = dict(status='passed', nativeKeyboard='passed', steps=12,
                    escapeCancellation='passed', automaticDOM='passed', shell=SHELL)
        source = json.dumps(good)
        self.assertEqual(runner.decode_receipt(source), good)
        self.assertEqual(runner.decode_receipt('{"fraction":1.25}'), {'fraction': 1.25})
        padded = source + ' ' * (runner.MAX_RECEIPT_BYTES - len(source.encode()))
        self.assertEqual(runner.decode_receipt(padded), good)
        bad = [
            '{"status":"failed",' + source[1:],
            '{"status":"passed",' + source[1:],
            source.replace('"sections": 8', '"sections": 0, "sections": 8'),
            source.replace('"width": 1280', '"width": 0, "width": 1280'),
            source[:-1] + ',"unused":NaN}',
            source[:-1] + ',"unused":Infinity}',
            source[:-1] + ',"unused":-Infinity}',
            source[:-1] + ',"unused":1e999}',
            source[:-1] + ',"unused":-1e999}',
            padded + ' ',
            '{"private":"' + 'é' * (runner.MAX_RECEIPT_BYTES // 2) + '"}',
        ]
        for output in bad:
            with self.subTest(bytes=len(output.encode())):
                with self.assertRaises(ValueError):
                    runner.decode_receipt(output)
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                        patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (0, output, 'PRIVATE_STDERR')]), \
                        patch.object(runner, 'build', return_value='<html>fixture</html>'), \
                        redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(runner.main(), 1)
                self.assertEqual(stdout.getvalue(), '')
                self.assertIn('Browser output withheld', stderr.getvalue())
                self.assertNotIn('PRIVATE', stderr.getvalue())

    def test_export_width_refuses_malformed_values_without_crashing(self):
        keyboard = dict(status='passed', nativeKeyboard='passed', steps=12,
                        escapeCancellation='passed', automaticDOM='passed', shell=SHELL)
        export = dict(status='passed', savedBytes=1024, sha256='a' * 64, candidates=2,
                      selectedSnapshotRow=2, nativeActivation='Enter', table=dict(rows=9, columns=3, width=390))
        for width in (1, 390, 1280):
            candidate = {**export, 'table': {**export['table'], 'width': width}}
            self.assertTrue(runner.valid_export_receipt(dict(gapExport=candidate)))
        for width in (True, None, '390', [], 0, -1, 1281, 10**400, float('inf'), float('-inf'), float('nan')):
            with self.subTest(width_type=type(width).__name__):
                candidate = {**export, 'table': {**export['table'], 'width': width}}
                self.assertFalse(runner.valid_export_receipt(dict(gapExport=candidate)))
                receipt = {**keyboard, 'gapExport': candidate, 'private': 'PRIVATE_RECEIPT_DETAIL'}
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                        patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (0, json.dumps(receipt), '')]), \
                        patch.object(runner, 'build', return_value='<html>fixture</html>'), \
                        redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(runner.main(gap_export=True), 1)
                self.assertEqual(stdout.getvalue(), '')
                expected = ('Browser output withheld' if isinstance(width, float) and not math.isfinite(width)
                            else 'native gap download receipt incomplete')
                self.assertIn(expected, stderr.getvalue())
                self.assertNotIn('PRIVATE', stderr.getvalue())

    def test_gap_export_requires_saved_file_and_layout_receipt(self):
        keyboard = dict(status='passed', nativeKeyboard='passed', steps=12,
                        escapeCancellation='passed', automaticDOM='passed', shell=SHELL)
        export = dict(status='passed', savedBytes=1024, sha256='a' * 64, candidates=2,
                      selectedSnapshotRow=2, nativeActivation='Enter', table=dict(rows=9, columns=3, width=390))
        self.assertTrue(runner.valid_export_receipt(dict(gapExport=export)))
        for key in export:
            self.assertFalse(runner.valid_export_receipt(dict(gapExport={**export, key: None})), key)
        for field in ('rows', 'columns', 'width'):
            self.assertFalse(runner.valid_export_receipt(dict(gapExport={**export, 'table': {**export['table'], field: None}})))
        for include, expected_code in ((False, 1), (True, 0)):
            receipt = {**keyboard, **({'gapExport': export} if include else {})}
            with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                    patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (0, json.dumps(receipt), '')]) as run, \
                    patch.object(runner, 'build', return_value='<html>fixture</html>'), \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(runner.main(gap_export=True), expected_code)
                command, timeout = run.call_args.args
                self.assertEqual(command[-2], '')
                self.assertTrue(command[-1].endswith('/downloads'))
                self.assertEqual(timeout, 30)
                self.assertEqual(run.call_args.kwargs['stdout_limit'], runner.MAX_RECEIPT_BYTES)

    def test_missing_browser_blocks_without_process_or_artifact(self):
        with patch.object(runner.shutil, 'which', return_value=None), \
                patch.object(runner, 'run_bounded') as run, patch.object(runner, 'build') as build, \
                redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(), 2)
            run.assert_not_called()
            build.assert_not_called()

    def test_isolation_denial_blocks_before_browser(self):
        with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                patch.object(runner, 'run_bounded', return_value=(1, '', 'private')) as run, \
                patch.object(runner, 'build') as build, redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(), 2)
            self.assertEqual(run.call_count, 1)
            build.assert_not_called()

    def test_native_success_requires_every_receipt_field(self):
        good = dict(status='passed', nativeKeyboard='passed', steps=12,
                    escapeCancellation='passed', automaticDOM='passed', shell=SHELL)
        self.assertTrue(runner.valid_receipt(good))
        for key in good:
            broken = {**good, key: None}
            self.assertFalse(runner.valid_receipt(broken), key)
        for key in SHELL:
            self.assertFalse(runner.valid_receipt({**good, 'shell': {**SHELL, key: None}}), key)
        self.assertFalse(runner.valid_receipt(dict(status='passed', nativeKeyboard='not-run')))
        stdout = io.StringIO()
        with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (0, json.dumps(good), '')]) as run, \
                patch.object(runner, 'build', return_value='<html>fixture</html>'), redirect_stdout(stdout):
            self.assertEqual(runner.main(), 0)
            command, timeout = run.call_args.args
            self.assertEqual(command[:5], ['/fixture/unshare', '--user', '--map-current-user', '--net', '--'])
            self.assertEqual(command[5], '/fixture/node')
            self.assertTrue(command[6].endswith('/tools/keyboard_cdp.cjs'))
            self.assertEqual(timeout, 30)
            self.assertTrue(command[-1].endswith('/profile'))
        self.assertEqual(json.loads(stdout.getvalue())['artifactSha256'],
                         hashlib.sha256(b'<html>fixture</html>').hexdigest())

    def test_bad_receipt_or_failed_browser_is_redacted(self):
        for code, output in [(0, 'PRIVATE_BAD_JSON'), (0, '{"status":"passed"}'), (1, 'PRIVATE_BROWSER_ERROR')]:
            stderr = io.StringIO()
            with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                    patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (code, output, 'PRIVATE_STDERR')]), \
                    patch.object(runner, 'build', return_value='<html>fixture</html>'), redirect_stderr(stderr):
                self.assertEqual(runner.main(), 1)
                self.assertNotIn('PRIVATE', stderr.getvalue())
