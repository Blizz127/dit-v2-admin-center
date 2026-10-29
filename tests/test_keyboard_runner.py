"""Runner contracts only; fabricated receipts are never native runtime evidence."""
import io
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
from tools import run_keyboard_playtest as runner


SHELL = dict(status="passed", sections=8, widths=[1280, 390], traversal="Tab/Shift+Tab", activation="Enter")


class KeyboardRunnerTests(unittest.TestCase):
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
        with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (0, json.dumps(good), '')]) as run, \
                patch.object(runner, 'build', return_value='<html>fixture</html>'), redirect_stdout(io.StringIO()):
            self.assertEqual(runner.main(), 0)
            command, timeout = run.call_args.args
            self.assertEqual(command[:5], ['/fixture/unshare', '--user', '--map-current-user', '--net', '--'])
            self.assertEqual(command[5], '/fixture/node')
            self.assertTrue(command[6].endswith('/tools/keyboard_cdp.cjs'))
            self.assertEqual(timeout, 30)
            self.assertTrue(command[-1].endswith('/profile'))

    def test_bad_receipt_or_failed_browser_is_redacted(self):
        for code, output in [(0, 'PRIVATE_BAD_JSON'), (0, '{"status":"passed"}'), (1, 'PRIVATE_BROWSER_ERROR')]:
            stderr = io.StringIO()
            with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                    patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (code, output, 'PRIVATE_STDERR')]), \
                    patch.object(runner, 'build', return_value='<html>fixture</html>'), redirect_stderr(stderr):
                self.assertEqual(runner.main(), 1)
                self.assertNotIn('PRIVATE', stderr.getvalue())
