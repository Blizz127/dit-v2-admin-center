"""Runner contract checks, not browser-execution evidence."""
import unittest
import io
import json
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from tools import run_headless_playtest as runner


def completed_document():
    rows = ['PASS — check'] * 28 + ['PASS — Health recovers', 'PASS — Both bridge cards recover']
    return '<html data-playtest="passed"><ol id="harness-checks">' + ''.join(
        '<li>' + row + '</li>' for row in rows) + '</ol></html>'


class HeadlessRunnerTests(unittest.TestCase):
    def test_artifact_pin_refuses_mismatch_and_cleans_generated_file(self):
        with TemporaryDirectory() as directory:
            with patch.object(runner.tempfile, 'tempdir', directory), \
                    patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                    patch.object(runner, 'build', return_value='<html>changed</html>'), \
                    patch.object(runner, 'run_bounded', return_value=(0, '', '')) as run:
                self.assertEqual(runner.main(expected_artifact_sha256='a'*64), 1)
                self.assertEqual(run.call_count, 1)  # Fabricated isolation check only.
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_invalid_pin_does_not_resolve_or_launch_any_runtime(self):
        for invalid in ('', 'A'*64, 'g'*64, True, 'private/path'):
            with patch.object(runner.shutil, 'which') as which, \
                    patch.object(runner, 'build') as build, patch.object(runner, 'run_bounded') as run:
                self.assertEqual(runner.main(expected_artifact_sha256=invalid), 1)
                which.assert_not_called()
                build.assert_not_called()
                run.assert_not_called()

    def test_matching_pin_is_utf8_and_still_requires_completed_dom(self):
        artifact = '<html>synthetic 名é</html>'
        digest = hashlib.sha256(artifact.encode('utf-8')).hexdigest()
        for document, expected in ((completed_document(), 0), ('<html>incomplete</html>', 1)):
            output = io.StringIO()
            with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                    patch.object(runner, 'build', return_value=artifact), \
                    patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (0, document, '')]), \
                    redirect_stdout(output):
                self.assertEqual(runner.main(expected_artifact_sha256=digest), expected)
            if expected == 0:
                self.assertEqual(json.loads(output.getvalue())['artifactSha256'], digest)
            else:
                self.assertEqual(output.getvalue(), '')

    def setUp(self):
        # A fabricated browser success must not look like a real runtime receipt.
        for redirect in (redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO())):
            redirect.__enter__()
            self.addCleanup(redirect.__exit__, None, None, None)

    def test_missing_browser_never_launches(self):
        with patch.object(runner.shutil, 'which', return_value=None), patch.object(runner, 'run_bounded') as run:
            self.assertEqual(runner.main(), 2)
            run.assert_not_called()

    def test_explicit_browser_selection_cannot_fall_back_to_path(self):
        for requested in ('', '/fixture/missing-browser'):
            with patch.dict(runner.os.environ, {'DIT_CHROMIUM': requested}), \
                    patch.object(runner.shutil, 'which', side_effect=lambda name: None if name == requested else '/fixture/' + name) as which, \
                    patch.object(runner, 'run_bounded') as run, patch.object(runner, 'build') as build:
                self.assertEqual(runner.main(), 2)
                self.assertEqual([call.args[0] for call in which.call_args_list], [requested] if requested else [])
                run.assert_not_called()
                build.assert_not_called()

    def test_denied_isolation_never_launches_browser(self):
        with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                patch.object(runner, 'run_bounded', return_value=(1, '', 'denied')) as run:
            self.assertEqual(runner.main(), 2)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][-1], '/fixture/true')

    def test_success_requires_isolated_temporary_profile_and_completed_cards(self):
        with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (0, completed_document(), '')]) as run:
            self.assertEqual(runner.main(), 0)
            command, timeout = run.call_args.args
            self.assertEqual(command[:5], ['/fixture/unshare', '--user', '--map-current-user', '--net', '--'])
            self.assertIn('--headless', command)
            self.assertNotIn('--no-sandbox', command)
            self.assertTrue(command[-1].startswith('file:///'))
            self.assertTrue(any(arg.startswith('--user-data-dir=') for arg in command))
            self.assertEqual(timeout, 20)

    def test_incomplete_or_failed_report_is_not_a_pass(self):
        good = completed_document()
        self.assertTrue(runner.Result(good).valid())
        for document in ('', good.replace('data-playtest="passed"', 'data-playtest="failed"'),
                         good.replace('Both bridge cards recover', 'unrelated'),
                         good.replace('PASS — check', 'FAIL — check')):
            with self.subTest(document=document[:60]):
                self.assertFalse(runner.Result(document).valid())

    def test_keyboard_result_is_separate_from_automatic_dom_success(self):
        good = completed_document()
        self.assertEqual(runner.Result(good).keyboard_status, 'unknown')
        for state in ('not-run', 'running', 'cancelled', 'failed', 'passed', 'invalid'):
            with self.subTest(state=state):
                result = runner.Result(good.replace('<html ', '<html data-keyboard-playtest="' + state + '" '))
                self.assertTrue(result.valid())  # Automatic checks only.
                self.assertEqual(result.keyboard_status, state if state != 'invalid' else 'unknown')

    def test_runner_does_not_promote_unrun_keyboard_check_to_pass(self):
        document = completed_document().replace('<html ', '<html data-keyboard-playtest="not-run" ')
        output = io.StringIO()
        with patch.object(runner.shutil, 'which', side_effect=lambda name: '/fixture/' + name), \
                patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (0, document, '')]), \
                redirect_stdout(output):
            self.assertEqual(runner.main(), 0)
        receipt = json.loads(output.getvalue())
        self.assertEqual(receipt['status'], 'passed')
        self.assertEqual(receipt['nativeKeyboard'], 'not-run')
        self.assertIn('does not inject native keys', receipt['limitations'])


if __name__ == '__main__':
    unittest.main()
