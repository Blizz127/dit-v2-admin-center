#!/usr/bin/env python3
"""Validate every registered formal offline schema and its declared fixtures."""
import json
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.check_learning_assessment_schema import main as check_learning
from tools.check_wake_verification_schema import main as check_wake

CHECKERS = {'learning-assessment-draft-v1.schema.json': check_learning,
            'wake-verification-v1.schema.json': check_wake}


def main(root=ROOT):
    discovered = {p.relative_to(root / 'schemas').as_posix()
                  for p in (root / 'schemas').rglob('*.schema.json')}
    if discovered != set(CHECKERS):
        print(json.dumps({'status': 'failed', 'reason': 'Offline schema/checker inventory mismatch'}))
        return 1
    reports = {}
    for name in sorted(CHECKERS):
        output = io.StringIO()
        with redirect_stdout(output):
            result = CHECKERS[name](root)
        if result:
            print(output.getvalue(), end='')
            return result
        try:
            raw = output.getvalue()
            if len(raw.encode('utf-8')) > 256 * 1024:
                raise ValueError('Checker report too large')
            report = json.loads(raw)
            if not isinstance(report, dict) or report.get('status') != 'passed':
                raise ValueError('Invalid checker report')
            reports[name] = report
        except (ValueError, UnicodeError, RecursionError):
            print(json.dumps({'status': 'failed', 'reason': 'Offline checker report unavailable or invalid'}))
            return 1
    print(json.dumps({'status': 'passed', 'contracts': reports}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
