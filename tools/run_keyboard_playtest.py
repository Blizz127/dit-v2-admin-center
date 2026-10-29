"""Run native assignment keys in installed Chromium, offline and time-bounded.

No install, TCP listener, live data, persistent profile or sandbox bypass.
Exit 2 means runtime/isolation blocked; exit 1 means incomplete/failed checks.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_inspector_playtest import build
from tools.run_headless_playtest import run_bounded


def valid_receipt(result):
    return (isinstance(result, dict) and result.get('status') == 'passed'
            and result.get('nativeKeyboard') == 'passed' and result.get('steps') == 12
            and result.get('escapeCancellation') == 'passed'
            and result.get('automaticDOM') == 'passed')


def main():
    requested = os.environ.get('DIT_CHROMIUM')
    browser = shutil.which(requested) if requested else next(
        (path for name in ('chromium', 'chromium-browser', 'google-chrome', 'chrome-headless-shell')
         if (path := shutil.which(name))), None)
    node, unshare, true = (shutil.which(name) for name in ('node', 'unshare', 'true'))
    if not all((browser, node, unshare, true)):
        print('BLOCKED: installed Chromium, Node and namespace tooling are required. No download attempted.', file=sys.stderr)
        return 2
    isolation = [unshare, '--user', '--map-current-user', '--net', '--']
    if run_bounded(isolation + [true], 3)[0]:
        print('BLOCKED: network isolation denied; no browser started or bypass attempted.', file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix='dit-keyboard-') as directory:
        artifact = Path(directory) / 'playtest.html'
        artifact.write_text(build())
        command = isolation + [node, str(ROOT / 'tools/keyboard_cdp.cjs'), browser,
                               str(artifact), str(Path(directory) / 'profile')]
        code, stdout, _ = run_bounded(command, 30)
        try:
            result = json.loads(stdout) if not code else None
        except (ValueError, RecursionError):
            result = None
        if not valid_receipt(result):
            print('FAIL: native keyboard run was incomplete or failed. Browser output withheld.', file=sys.stderr)
            return 1
        print(json.dumps(result))
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError):
        print('FAIL: bounded browser run could not complete; no success claimed.', file=sys.stderr)
        sys.exit(1)
