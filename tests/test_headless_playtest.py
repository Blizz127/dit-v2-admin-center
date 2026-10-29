"""Runner contract checks, not browser-execution evidence."""
import unittest
import io
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from tools import run_headless_playtest as runner


def completed_document():
    rows = ['PASS — check'] * 28 + ['PASS — Health recovers', 'PASS — Both bridge cards recover']
    return '<html data-playtest="passed"><ol id="harness-checks">' + ''.join(
        '<li>' + row + '</li>' for row in rows) + '</ol></html>'


class HeadlessRunnerTests(unittest.TestCase):
    def setUp(self):
        # A fabricated browser success must not look like a real runtime receipt.
        for redirect in (redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO())):
            redirect.__enter__()
            self.addCleanup(redirect.__exit__, None, None, None)

    def test_missing_browser_never_launches(self):
        with patch.object(runner.shutil, 'which', return_value=None), patch.object(runner, 'run_bounded') as run:
            self.assertEqual(runner.main(), 2)
            run.assert_not_called()

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


if __name__ == '__main__':
    unittest.main()
