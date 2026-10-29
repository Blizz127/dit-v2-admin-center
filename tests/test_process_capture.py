"""Real disposable local subprocesses only; no browser, service or network."""
from pathlib import Path
import sys
import tempfile
import time
import unittest

from tools.run_headless_playtest import run_bounded


class ProcessCaptureTests(unittest.TestCase):
    def run_python(self, code, *args, timeout=2, stdout_limit=256, stderr_limit=256):
        return run_bounded([sys.executable, '-c', code, *args], timeout,
                           stdout_limit=stdout_limit, stderr_limit=stderr_limit)

    def test_exact_byte_budgets_and_return_code(self):
        result = self.run_python('import os; os.write(1,b"a"*256); os.write(2,b"b"*256); raise SystemExit(7)')
        self.assertEqual(result, (7, 'a' * 256, 'b' * 256))
        self.assertEqual(self.run_python('pass', stdout_limit=0, stderr_limit=0), (0, '', ''))

    def test_utf8_is_decoded_after_chunks_are_collected(self):
        code = 'import os; data="名é".encode(); [(os.write(1,bytes([b])),os.write(2,bytes([b]))) for b in data]'
        self.assertEqual(self.run_python(code), (0, '名é', '名é'))

    def test_either_pipe_overflow_fails_without_returning_output(self):
        for descriptor in (1, 2):
            with self.subTest(descriptor=descriptor):
                started = time.monotonic()
                with self.assertRaisesRegex(RuntimeError, '^Headless command exceeded its output budget$'):
                    self.run_python(f'import os,time; os.write({descriptor},b"PRIVATE"*100000); time.sleep(30)')
                self.assertLess(time.monotonic() - started, 5)

    def test_invalid_utf8_is_redacted(self):
        with self.assertRaisesRegex(RuntimeError, '^Headless command returned invalid UTF-8$'):
            self.run_python('import os; os.write(1,b"PRIVATE\\xff")')

    def test_closed_pipes_do_not_remove_process_deadline(self):
        with self.assertRaisesRegex(RuntimeError, '^Headless command exceeded its deadline$'):
            self.run_python('import os,time; os.close(1); os.close(2); time.sleep(30)', timeout=.2)

    def test_parent_exit_does_not_leave_descendant_holding_pipes(self):
        with tempfile.TemporaryDirectory(prefix='dit-capture-test-') as temp:
            pid_file = Path(temp) / 'child.pid'
            code = ('import subprocess,sys; from pathlib import Path; '
                    'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); '
                    'Path(sys.argv[1]).write_text(str(p.pid))')
            with self.assertRaisesRegex(RuntimeError, '^Headless command exceeded its deadline$'):
                self.run_python(code, str(pid_file), timeout=1)
            child = int(pid_file.read_text())
            # A killed orphan can briefly remain a zombie until the host reaps it.
            # The check proves it is no longer executing, not that PID 1 reaped it.
            deadline = time.monotonic() + 1
            while True:
                try:
                    state = Path(f'/proc/{child}/stat').read_text().rsplit(')', 1)[1].split()[0]
                except FileNotFoundError:
                    break
                if state == 'Z':
                    break
                if time.monotonic() >= deadline:
                    self.fail('Owned descendant still executing after cleanup')
                time.sleep(.01)

    def test_invalid_budget_does_not_start_child(self):
        with self.assertRaises(ValueError):
            self.run_python('raise SystemExit("SHOULD_NOT_RUN")', stdout_limit=-1)


if __name__ == '__main__':
    unittest.main()
