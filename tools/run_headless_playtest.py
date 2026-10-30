"""Run the synthetic artifact in existing Chromium with an isolated network.

No browser installation, server, credentials or sandbox-disabling flags.
Missing runtime/isolation exits 2; failed or incomplete DOM checks exit 1.
"""
import json
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import signal
import selectors
import subprocess
import sys
import tempfile
import time
from html.parser import HTMLParser

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.build_inspector_playtest import build


def run_bounded(command, timeout, *, stdout_limit=2 * 1024 * 1024, stderr_limit=64 * 1024):
    """Bound acquisition, including descendants holding either pipe open."""
    if timeout <= 0 or any(type(limit) is not int or limit < 0 for limit in (stdout_limit, stderr_limit)):
        raise ValueError('Invalid subprocess budget')
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            for stream, name, limit in ((process.stdout, 'stdout', stdout_limit),
                                        (process.stderr, 'stderr', stderr_limit)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, (name, limit))
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError('Headless command exceeded its deadline')
                for key, _ in selector.select(remaining):
                    name, limit = key.data
                    try:
                        # At the boundary, read just one extra byte to detect overflow.
                        chunk = os.read(key.fd, min(65536, limit - len(buffers[name]) + 1))
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    if len(buffers[name]) + len(chunk) > limit:
                        raise RuntimeError('Headless command exceeded its output budget')
                    buffers[name].extend(chunk)
        process.wait(timeout=max(0, deadline - time.monotonic()))
        try:
            return process.returncode, buffers['stdout'].decode('utf-8'), buffers['stderr'].decode('utf-8')
        except UnicodeDecodeError:
            raise RuntimeError('Headless command returned invalid UTF-8') from None
    except subprocess.TimeoutExpired:
        raise RuntimeError('Headless command exceeded its deadline') from None
    finally:
        # Include child browser processes, even if their parent already exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        # Do not drain unbounded output during cleanup. Close our pipe ends and
        # reap the owned parent with a separate finite cleanup allowance.
        process.stdout.close()
        process.stderr.close()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            raise RuntimeError('Headless process cleanup timed out') from None


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


def main(expected_artifact_sha256=None):
    if expected_artifact_sha256 is not None and (
            not isinstance(expected_artifact_sha256, str) or len(expected_artifact_sha256) != 64
            or any(c not in '0123456789abcdef' for c in expected_artifact_sha256)):
        print('FAIL: expected artifact SHA-256 must be 64 lowercase hex characters.', file=sys.stderr)
        return 1
    if 'DIT_CHROMIUM' in os.environ:
        requested = os.environ['DIT_CHROMIUM']
        browser = shutil.which(requested) if requested else None
    else:
        browser = next(
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
        artifact.write_bytes(build().encode('utf-8'))
        artifact_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if expected_artifact_sha256 is not None and artifact_digest != expected_artifact_sha256:
            print('FAIL: generated artifact differs from expected SHA-256; no browser started.', file=sys.stderr)
            return 1
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
                          'artifactSha256': artifact_digest,
                          'nativeKeyboard': result.keyboard_status,
                          'network': 'isolated namespace; inline synthetic responses',
                          'limitations': 'Automatic DOM execution; this runner does not inject native keys. No visual review, HTTP listener or live integration'}))
        return 0


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--expected-artifact-sha256', help='Refuse browser launch if the generated preview differs from this hash')
        args = parser.parse_args()
        sys.exit(main(expected_artifact_sha256=args.expected_artifact_sha256))
    except (OSError, RuntimeError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        sys.exit(1)
