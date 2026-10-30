#!/usr/bin/env python3
"""Validate every registered formal offline schema and its declared fixtures."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.check_learning_assessment_schema import main as check_learning

CHECKERS = {'learning-assessment-draft-v1.schema.json': check_learning}


def main(root=ROOT):
    discovered = {p.relative_to(root / 'schemas').as_posix()
                  for p in (root / 'schemas').rglob('*.schema.json')}
    if discovered != set(CHECKERS):
        print(json.dumps({'status': 'failed', 'reason': 'Offline schema/checker inventory mismatch'}))
        return 1
    for name in sorted(CHECKERS):
        result = CHECKERS[name](root)
        if result:
            return result
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
