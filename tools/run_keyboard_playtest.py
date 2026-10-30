"""Run native assignment keys in installed Chromium, offline and time-bounded.

No install, TCP listener, live data, persistent profile or sandbox bypass.
Exit 2 means runtime/isolation blocked; exit 1 means incomplete/failed checks.
"""
import json
import math
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

MAX_RECEIPT_BYTES = 64 * 1024


def runtime_preflight():
    """Resolve installed executables only; do not execute, search caches or alter PATH."""
    def selected(variable, aliases):
        # An explicit but invalid/empty override must not silently pick another runtime.
        if variable in os.environ:
            requested = os.environ[variable]
            return shutil.which(requested) if requested else None
        return next((path for name in aliases if (path := shutil.which(name))), None)

    paths = {
        'Chromium': selected('DIT_CHROMIUM', ('chromium', 'chromium-browser', 'google-chrome', 'chrome-headless-shell')),
        'Node': selected('DIT_NODE', ('node',)),
        'unshare': shutil.which('unshare'),
        'true': shutil.which('true'),
    }
    return paths, [name for name, path in paths.items() if path is None]


def decode_receipt(source):
    """One bounded JSON receipt; duplicate claims are ambiguous even if identical."""
    if not isinstance(source, str) or len(source) > MAX_RECEIPT_BYTES or len(source.encode('utf-8')) > MAX_RECEIPT_BYTES:
        raise ValueError('Receipt exceeds parser budget')

    def unique_fields(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Ambiguous receipt fields')
            result[key] = value
        return result

    def reject_constant(_value):
        raise ValueError('Non-finite receipt token')

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Receipt number overflow')
        return number

    return json.loads(source, object_pairs_hook=unique_fields, parse_constant=reject_constant,
                      parse_float=finite_float)


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


def valid_audit_receipt(result):
    audit = result.get('routingAudit') if isinstance(result, dict) else None
    return (isinstance(audit, dict) and audit.get('status') == 'passed'
            and audit.get('counts') == [3, 2, 1, 0, 3]
            and all(type(n) is int for n in audit['counts'])
            and audit.get('traversal') == 'Tab/Shift+Tab'
            and audit.get('selection') == 'Home/ArrowDown'
            and audit.get('reset') == 'Enter' and audit.get('focusRetained') is True)


def valid_draft_receipt(result):
    draft = result.get('draftReview') if isinstance(result, dict) else None
    return (isinstance(draft, dict) and draft.get('status') == 'passed'
            and draft.get('targetId') == 'offline-inspector-bot'
            and draft.get('traversal') == 'Tab/Shift+Tab' and draft.get('activation') == 'Enter'
            and draft.get('textInput') == 'Input.insertText' and draft.get('unknownBaseline') == 'personality'
            and all(draft.get(key) is True for key in ('matchesLoadedGoal', 'discardCleared', 'focusRetained')))


def main(screenshots=False, gap_export=False, expected_artifact_sha256=None, preflight_only=False,
         routing_audit=False, draft_review=False):
    if expected_artifact_sha256 is not None and (
            not isinstance(expected_artifact_sha256, str) or len(expected_artifact_sha256) != 64
            or any(c not in '0123456789abcdef' for c in expected_artifact_sha256)):
        print('FAIL: expected artifact SHA-256 must be 64 lowercase hex characters.', file=sys.stderr)
        return 1
    paths, missing = runtime_preflight()
    if preflight_only:
        print(json.dumps({'preflight': 'blocked' if missing else 'executables-found',
                          'executables': {name: 'found' if path else 'missing' for name, path in paths.items()},
                          'nativeRun': 'NOT RUN', 'isolation': 'NOT CHECKED'}))
        return 2 if missing else 0
    if missing:
        print('BLOCKED: missing executable(s): ' + ', '.join(missing) +
              '. Checked PATH or explicit DIT_CHROMIUM/DIT_NODE selection. '
              'No browser started, PATH changed or download attempted.', file=sys.stderr)
        return 2
    browser, node, unshare, true = (paths[name] for name in ('Chromium', 'Node', 'unshare', 'true'))
    isolation = [unshare, '--user', '--map-current-user', '--net', '--']
    if run_bounded(isolation + [true], 3)[0]:
        print('BLOCKED: network isolation denied; no browser started or bypass attempted.', file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix='dit-keyboard-') as directory:
        artifact = Path(directory) / 'playtest.html'
        artifact.write_bytes(build().encode('utf-8'))
        artifact_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if expected_artifact_sha256 is not None and artifact_digest != expected_artifact_sha256:
            print('FAIL: generated artifact differs from expected SHA-256; no browser started.', file=sys.stderr)
            return 1
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
        if routing_audit or draft_review:
            # Keep optional positional slots stable when captures/downloads are absent.
            if not screenshots and not gap_export:
                command.append('')
            if not gap_export:
                command.append('')
            command.append('routing-audit' if routing_audit else '')
        if draft_review:
            command.append('draft-review')
        code, stdout, _ = run_bounded(command, 30, stdout_limit=MAX_RECEIPT_BYTES)
        try:
            result = decode_receipt(stdout) if not code else None
        except (ValueError, RecursionError):
            result = None
        if not valid_receipt(result):
            print('FAIL: native keyboard run was incomplete or failed. Browser output withheld.', file=sys.stderr)
            return 1
        if gap_export and not valid_export_receipt(result):
            print('FAIL: native gap download receipt incomplete; no export success claimed.', file=sys.stderr)
            return 1
        if routing_audit and not valid_audit_receipt(result):
            print('FAIL: native audit filter receipt incomplete; no audit success claimed.', file=sys.stderr)
            return 1
        if draft_review and not valid_draft_receipt(result):
            print('FAIL: native draft-review receipt incomplete; no draft success claimed.', file=sys.stderr)
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
    parser.add_argument('--draft-review', action='store_true', help='Check local draft typing, focus, Unknown baseline and discard with native input')
    parser.add_argument('--routing-audit', action='store_true', help='Check synthetic audit selectors and reset with native keys')
    parser.add_argument('--gap-export', action='store_true', help='Check gap table and native Enter download in a disposable directory')
    parser.add_argument('--expected-artifact-sha256', help='Refuse to start the browser if the generated preview differs from this exact hash')
    parser.add_argument('--preflight-only', action='store_true', help='Resolve executable availability only; no process, namespace or browser launch')
    try:
        args = parser.parse_args()
        sys.exit(main(screenshots=args.screenshots, gap_export=args.gap_export,
                      expected_artifact_sha256=args.expected_artifact_sha256,
                      preflight_only=args.preflight_only, routing_audit=args.routing_audit, draft_review=args.draft_review))
    except (OSError, RuntimeError):
        print('FAIL: bounded browser run could not complete; no success claimed.', file=sys.stderr)
        sys.exit(1)
