"""Run native assignment keys in installed Chromium, offline and time-bounded.

No install, TCP listener, live data, persistent profile or sandbox bypass.
Exit 2 means runtime/isolation blocked; exit 1 means incomplete/failed checks.
"""
import json
import argparse
import hashlib
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
    shell = result.get('shell', {}) if isinstance(result, dict) else {}
    return (isinstance(result, dict) and result.get('status') == 'passed'
            and result.get('nativeKeyboard') == 'passed' and result.get('steps') == 12
            and result.get('escapeCancellation') == 'passed'
            and result.get('automaticDOM') == 'passed'
            and isinstance(shell, dict) and shell.get('status') == 'passed'
            and shell.get('sections') == 8 and shell.get('widths') == [1280, 390]
            and shell.get('traversal') == 'Tab/Shift+Tab' and shell.get('activation') == 'Enter'
            and shell.get('coverage') == [dict(width=1280, cards=3, layout='columns'),
                                          dict(width=390, cards=3, layout='stacked')])


def publish_captures(result, directory, artifact, output_root):
    """Publish only complete bounded captures; PNG header checks are not image decoding."""
    expected = [('desktop.png', 1280, 1000), ('narrow-left.png', 390, 844),
                ('narrow-right.png', 390, 844)]
    visual = result.get('visual', {})
    captures = visual.get('captures') if isinstance(visual, dict) else None
    if visual.get('status') != 'captured' or not isinstance(captures, list) or len(captures) != 3:
        raise ValueError('Incomplete captures')
    for item, (name, width, height) in zip(captures, expected):
        if not isinstance(item, dict) or (item.get('file'), item.get('width'), item.get('height')) != (name, width, height):
            raise ValueError('Unexpected capture')
        source = directory / name
        if source.is_symlink() or not 24 <= source.stat().st_size <= 16 * 1024 * 1024:
            raise ValueError('Invalid capture file')
        data = source.read_bytes()
        if data[:8] != b'\x89PNG\r\n\x1a\n' or int.from_bytes(data[16:20], 'big') != width or int.from_bytes(data[20:24], 'big') != height:
            raise ValueError('Invalid capture header')
        item['sha256'] = hashlib.sha256(data).hexdigest()
    visual['artifactSha256'] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    output_root.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix='comparisons-', dir=output_root))
    try:
        for name, _, _ in expected:
            shutil.copyfile(directory / name, destination / name)
        (destination / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    except OSError:
        shutil.rmtree(destination)
        raise
    return str(destination)


def valid_export_receipt(result):
    export = result.get('gapExport', {}) if isinstance(result, dict) else {}
    table = export.get('table', {}) if isinstance(export, dict) else {}
    return (isinstance(export, dict) and export.get('status') == 'passed'
            and type(export.get('savedBytes')) is int and 0 < export['savedBytes'] <= 256 * 1024
            and export.get('candidates') == 2 and export.get('selectedSnapshotRow') == 2
            and export.get('nativeActivation') == 'Enter'
            and isinstance(export.get('sha256'), str) and len(export['sha256']) == 64
            and all(c in '0123456789abcdef' for c in export['sha256'])
            and isinstance(table, dict) and table.get('rows') == 9 and table.get('columns') == 3
            # The fixed native workflow uses 1280/390px viewports. Comparing
            # bounds before any float conversion also rejects huge JSON ints,
            # infinities and NaN without raising OverflowError.
            and type(table.get('width')) in (int, float) and 0 < table['width'] <= 1280)


def main(screenshots=False, gap_export=False):
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
        artifact_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        command = isolation + [node, str(ROOT / 'tools/keyboard_cdp.cjs'), browser,
                               str(artifact), str(Path(directory) / 'profile')]
        captures = Path(directory) / 'captures'
        if screenshots:
            captures.mkdir()
            command.append(str(captures))
        if gap_export:
            if not screenshots:
                command.append('')
            downloads = Path(directory) / 'downloads'
            downloads.mkdir(mode=0o700)
            command.append(str(downloads))
        code, stdout, _ = run_bounded(command, 30)
        try:
            result = json.loads(stdout) if not code else None
        except (ValueError, RecursionError):
            result = None
        if not valid_receipt(result):
            print('FAIL: native keyboard run was incomplete or failed. Browser output withheld.', file=sys.stderr)
            return 1
        if gap_export and not valid_export_receipt(result):
            print('FAIL: native gap download receipt incomplete; no export success claimed.', file=sys.stderr)
            return 1
        if screenshots:
            try:
                result['screenshotDirectory'] = publish_captures(
                    result, captures, artifact, ROOT / 'build/screenshots')
            except (ValueError, OSError, TypeError, AttributeError):
                print('FAIL: screenshot set incomplete; no visual success claimed.', file=sys.stderr)
                return 1
        result['artifactSha256'] = artifact_digest
        print(json.dumps(result))
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screenshots', action='store_true', help='Capture synthetic comparisons after native checks pass')
    parser.add_argument('--gap-export', action='store_true', help='Check gap table and native Enter download in a disposable directory')
    try:
        args = parser.parse_args()
        sys.exit(main(screenshots=args.screenshots, gap_export=args.gap_export))
    except (OSError, RuntimeError):
        print('FAIL: bounded browser run could not complete; no success claimed.', file=sys.stderr)
        sys.exit(1)
