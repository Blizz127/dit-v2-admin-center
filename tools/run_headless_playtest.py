"""Run the synthetic artifact in existing Chromium with an isolated network.

No browser installation, server, credentials or sandbox-disabling flags.
Missing runtime/isolation exits 2; failed or incomplete DOM checks exit 1.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.build_inspector_playtest import build


def run_bounded(command, timeout):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        raise RuntimeError('Headless command exceeded its deadline') from None
    finally:
        # Include child browser processes, even if their parent already exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()


class Result(HTMLParser):
    def __init__(self, document):
        super().__init__()
        self.status = None
        self.keyboard_status = 'unknown'
        self.in_checks = False
        self.in_row = False
        self.rows = []
        self.feed(document)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.status = attrs.get('data-playtest')
            keyboard = attrs.get('data-keyboard-playtest')
            self.keyboard_status = keyboard if keyboard in ('not-run', 'running', 'cancelled', 'passed', 'failed') else 'unknown'
        if tag == 'ol' and attrs.get('id') == 'harness-checks':
            self.in_checks = True
        if tag == 'li' and self.in_checks:
            self.in_row = True
            self.rows.append('')

    def handle_endtag(self, tag):
        if tag == 'ol':
            self.in_checks = False
        if tag == 'li':
            self.in_row = False

    def handle_data(self, data):
        if self.in_row:
            self.rows[-1] += data

    def valid(self):
        return (self.status == 'passed' and len(self.rows) >= 30
                and all(row.startswith('PASS — ') for row in self.rows)
                and any('Health recovers' in row for row in self.rows)
                and any('Both bridge cards recover' in row for row in self.rows))


def main():
    requested = os.environ.get('DIT_CHROMIUM')
    browser = shutil.which(requested) if requested else next(
        (path for name in ('chromium', 'chromium-browser', 'google-chrome', 'chrome-headless-shell')
         if (path := shutil.which(name))), None)
    if not browser:
        print('BLOCKED: no Chromium executable. Set DIT_CHROMIUM to an installed binary. No download attempted.', file=sys.stderr)
        return 2
    unshare, true = shutil.which('unshare'), shutil.which('true')
    if not unshare or not true:
        print('BLOCKED: network namespace tooling is unavailable.', file=sys.stderr)
        return 2
    isolation = [unshare, '--user', '--map-current-user', '--net', '--']
    if run_bounded(isolation + [true], 3)[0]:
        print('BLOCKED: network namespace denied. No browser started; isolation will not be bypassed.', file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix='dit-headless-') as directory:
        artifact = Path(directory) / 'playtest.html'
        artifact.write_text(build())
        command = isolation + [browser, '--headless', '--disable-gpu', '--disable-background-networking',
                               '--no-first-run', '--no-default-browser-check',
                               '--user-data-dir=' + directory + '/profile', '--dump-dom',
                               '--virtual-time-budget=10000', artifact.as_uri()]
        code, document, _ = run_bounded(command, 20)
        result = Result(document)
        if code or not result.valid():
            print('FAIL: browser exited unsuccessfully or artifact checks were incomplete.', file=sys.stderr)
            return 1
        print(json.dumps({'status': 'passed', 'runtime': browser, 'checks': len(result.rows),
                          'nativeKeyboard': result.keyboard_status,
                          'network': 'isolated namespace; inline synthetic responses',
                          'limitations': 'Automatic DOM execution; this runner does not inject native keys. No visual review, HTTP listener or live integration'}))
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        sys.exit(1)
