"""Review returned 8eb2c9f device evidence offline; never launch or collect anything.

This checks consistency of supplied reports, not their authenticity. Only the
trusted executor handoff can establish that a device actually produced them.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

LIMIT = 65536
PIN = {
    'schema': 'dit-admin-native-attempt-v1',
    'sequence': 'ece1ccc9149873b9',
    'executor': '852bb105-8f9d-4a3f-a986-89a7981756dc',
    'host': 'bazzite',
    'sourceRevision': '8eb2c9f51dfbf0302b0a924b8075f039fed1b6ee',
    'bundleSha256': 'a0bc47b1530d54ebb29b300e913f00a3ab6db434fca2007f0acabbafa1192ca7',
    'artifactSha256': 'ef740241746a1d9609b0c1fe41855d46931f2d01e99ceb493d335eb0678e77c2',
}
MANIFEST_SHA = '4c1ef8fd8a4fd665e411b3cc48a89961f0367b1c97dd4d9f1e401743d0073b79'
SEQUENCED_AT = datetime(2026, 10, 30, 2, 32, tzinfo=timezone.utc)
BLOCKERS = {
    'BLOCKED: installed Chromium, Node and namespace tooling are required. No download attempted.': 'Missing runtime prerequisite (reported)',
    'BLOCKED: network isolation denied; no browser started or bypass attempted.': 'Network isolation denied (reported)',
}


def read_file(root, name):
    # Fixed filenames only; do not follow a returned symlink or block on a FIFO.
    fd = os.open(root / name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Not a regular evidence file')
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('Evidence exceeds limit')
    return raw


def strict_json(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError('Duplicate field')
            result[key] = value
        return result

    def reject(_value):
        raise ValueError('Non-finite number')

    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Number overflow')
        return number

    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=reject, parse_float=finite)


def timestamp(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError('Invalid time')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('Timezone missing')
    return result


def legacy_pass(result):
    """The approved pin's measurements; do not require newer coverage geometry."""
    if not isinstance(result, dict):
        return False
    shell, export = result.get('shell'), result.get('gapExport')
    if not isinstance(shell, dict) or not isinstance(export, dict):
        return False
    table = export.get('table')
    if not isinstance(table, dict):
        return False
    return (all(result.get(k) == 'passed' for k in ('status', 'nativeKeyboard', 'escapeCancellation', 'automaticDOM'))
            and type(result.get('steps')) is int and result['steps'] == 12
            and shell.get('status') == 'passed' and type(shell.get('sections')) is int and shell['sections'] == 8
            and shell.get('widths') == [1280, 390]
            and shell.get('traversal') == 'Tab/Shift+Tab' and shell.get('activation') == 'Enter'
            and export.get('status') == 'passed' and type(export.get('savedBytes')) is int
            and 0 < export['savedBytes'] <= 256 * 1024
            and type(export.get('candidates')) is int and export['candidates'] == 2
            and type(export.get('selectedSnapshotRow')) is int and export['selectedSnapshotRow'] == 2
            and export.get('nativeActivation') == 'Enter'
            and isinstance(export.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', export['sha256']) is not None
            and type(table.get('rows')) is int and table['rows'] == 9
            and type(table.get('columns')) is int and table['columns'] == 3
            and type(table.get('width')) in (int, float) and 0 < table['width'] <= 1280)


def review(root, now=None):
    result = dict(status='incomplete', reason='Evidence missing or invalid',
                  sourceRevision=PIN['sourceRevision'], artifactSha256=PIN['artifactSha256'],
                  scope='Supplied executor reports only; not independently authenticated. Approved pin only; newer previews unverified.')
    try:
        root = Path(root)
        metadata = strict_json(read_file(root, 'attempt.json'))
        if not isinstance(metadata, dict) or any(metadata.get(k) != v for k, v in PIN.items()):
            raise ValueError('Wrong identity')
        start, finish = timestamp(metadata.get('startedAt')), timestamp(metadata.get('finishedAt'))
        if not SEQUENCED_AT <= start <= finish <= (now or datetime.now(timezone.utc)):
            raise ValueError('Wrong attempt time')
        if (timestamp(read_file(root, 'started-at.txt').decode('utf-8').strip()) != start
                or timestamp(read_file(root, 'finished-at.txt').decode('utf-8').strip()) != finish):
            raise ValueError('Contradictory time reports')
        manifest = read_file(root, 'SHA256SUMS')
        if hashlib.sha256(manifest).hexdigest() != MANIFEST_SHA:
            raise ValueError('Wrong manifest')
        names = [line.split(maxsplit=1)[1] for line in manifest.decode('utf-8').splitlines()]
        expected = Counter(name + ': OK' for name in names)
        for name in ('pre-sums.txt', 'build-sums.txt', 'post-sums.txt'):
            if Counter(read_file(root, name).decode('utf-8').splitlines()) != expected:
                raise ValueError('Incomplete manifest report')
        if read_file(root, 'artifact-sha256.txt').decode('utf-8').strip() != PIN['artifactSha256'] + '  build/inspector-playtest.html':
            raise ValueError('Wrong generated artifact')
        if read_file(root, 'post-manifest-exit.txt').strip() != b'0':
            raise ValueError('Manifest check failed')
        code = read_file(root, 'native-exit.txt').strip()
        if not re.fullmatch(rb'(0|[1-9][0-9]{0,2})', code) or int(code) > 255:
            raise ValueError('Invalid exit')
        stdout, stderr = read_file(root, 'native-result.json'), read_file(root, 'native-stderr.txt')
        if code == b'2':
            reason = BLOCKERS.get(stderr.decode('utf-8').strip())
            if stdout or not reason:
                raise ValueError('Contradictory blocker')
            result.update(status='blocked', reason=reason)
        elif code != b'0':
            result.update(status='failed', reason='Executor returned nonzero exit; partial output is not a pass')
        else:
            versions = metadata.get('versions')
            if (not isinstance(versions, dict) or not all(
                    isinstance(versions.get(k), str) and 0 < len(versions[k]) <= 160
                    and versions[k].strip() and all(c.isprintable() for c in versions[k])
                    for k in ('browser', 'node', 'python', 'unshare'))):
                raise ValueError('Runtime identity missing')
            receipt = strict_json(stdout)
            if (stderr or not legacy_pass(receipt)
                    or ('artifactSha256' in receipt and receipt['artifactSha256'] != PIN['artifactSha256'])):
                raise ValueError('Incomplete success receipt')
            result.update(status='reported-pass', reason='Approved pin keyboard and parsed-JSON download checks reported passed')
        result.update(startedAt=start.isoformat(), finishedAt=finish.isoformat())
    except (OSError, ValueError, TypeError, KeyError, IndexError, RecursionError, OverflowError):
        pass  # Never echo untrusted file contents, paths or exception text.
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='Local copy of one returned attempt; fixed filenames only')
    args = parser.parse_args(argv)
    result = review(args.directory)
    print(json.dumps(result))
    return {'reported-pass': 0, 'blocked': 2}.get(result['status'], 1)


if __name__ == '__main__':
    raise SystemExit(main())
