"""Installed-path selection only: no actual Node/browser/namespace execution."""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from tools import run_keyboard_playtest as runner


class KeyboardPreflightTests(unittest.TestCase):
    def test_receipt_environment_identifies_only_missing_browser_and_node(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch.object(runner.shutil, 'which', side_effect=lambda name: '/usr/bin/' + name if name in ('unshare', 'true') else None), \
                patch.object(runner, 'run_bounded') as run, patch.object(runner, 'build') as build, \
                redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(runner.main(), 2)
            self.assertIn('missing executable(s): Chromium, Node.', stderr.getvalue())
            self.assertNotIn('missing executable(s): unshare', stderr.getvalue())
            run.assert_not_called()
            build.assert_not_called()

    def test_explicit_paths_outside_path_with_spaces_are_resolved_without_execution(self):
        with tempfile.TemporaryDirectory() as root:
            paths = [Path(root) / name for name in ('installed browser', 'installed node', 'not executable')]
            for path in paths:
                path.write_text('DO NOT EXECUTE')
            for path in paths[:2]:
                path.chmod(0o700)
            env = {'PATH': '', 'DIT_CHROMIUM': str(paths[0]), 'DIT_NODE': str(paths[1])}
            with patch.dict(os.environ, env, clear=True):
                found, missing = runner.runtime_preflight()
                self.assertEqual(found['Chromium'], str(paths[0]))
                self.assertEqual(found['Node'], str(paths[1]))
                self.assertEqual(missing, ['unshare', 'true'])
                os.environ['DIT_NODE'] = str(paths[2])
                self.assertIsNone(runner.runtime_preflight()[0]['Node'])

    def test_invalid_explicit_selection_never_falls_back_to_path_alias(self):
        for value in ('', '/missing/PRIVATE_NODE'):
            with patch.dict(os.environ, {'DIT_NODE': value, 'DIT_CHROMIUM': value}, clear=True), \
                    patch.object(runner.shutil, 'which', side_effect=lambda name: None if name == value else '/bin/' + name) as which:
                _, missing = runner.runtime_preflight()
                self.assertEqual(missing, ['Chromium', 'Node'])
                aliases = [call.args[0] for call in which.call_args_list]
                self.assertNotIn('node', aliases)
                self.assertNotIn('chromium', aliases)

    def test_preflight_only_never_launches_or_builds_even_when_everything_is_found(self):
        for available, code in ((False, 2), (True, 0)):
            with patch.dict(os.environ, {}, clear=True), \
                    patch.object(runner.shutil, 'which', side_effect=lambda name: '/bin/' + name if available else None), \
                    patch.object(runner, 'run_bounded') as run, patch.object(runner, 'build') as build, \
                    redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(runner.main(preflight_only=True), code)
                result = json.loads(stdout.getvalue())
                self.assertEqual(result['nativeRun'], 'NOT RUN')
                self.assertEqual(result['isolation'], 'NOT CHECKED')
                self.assertEqual(result['preflight'], 'executables-found' if available else 'blocked')
                run.assert_not_called()
                build.assert_not_called()

    def test_selected_node_is_used_as_one_argument_and_isolation_is_still_required(self):
        selected = '/installed tools/node'
        with patch.dict(os.environ, {'DIT_NODE': selected}, clear=True), \
                patch.object(runner.shutil, 'which', side_effect=lambda name: selected if name == selected else '/bin/' + name), \
                patch.object(runner, 'run_bounded', side_effect=[(0, '', ''), (1, '', '')]) as run, \
                patch.object(runner, 'build', return_value='<html>fixture</html>'), redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(), 1)
            self.assertEqual(run.call_args.args[0][5], selected)
        with patch.dict(os.environ, {'DIT_NODE': selected}, clear=True), \
                patch.object(runner.shutil, 'which', return_value=selected), \
                patch.object(runner, 'run_bounded', return_value=(1, '', '')) as run, \
                patch.object(runner, 'build') as build, redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(), 2)
            self.assertEqual(run.call_count, 1)
            build.assert_not_called()
