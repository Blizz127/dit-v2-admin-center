#!/usr/bin/env python3
"""Run a real Draft 2020-12 engine on fixed, synthetic proposal cases only.

Use /usr/bin/python3 on this host (jsonschema 4.19.2 already installed there).
Missing engine is BLOCKED/exit 2, never a skipped pass. No dependencies installed.
"""
import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from learning_assessment_draft import _timestamp, review
from local_evidence import read_json


def main(root=ROOT):
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from jsonschema.exceptions import SchemaError
    except ImportError:
        print(json.dumps({'status': 'blocked', 'reason': 'JSON Schema engine unavailable'}))
        return 2

    schema_path = root / 'schemas/learning-assessment-draft-v1.schema.json'
    fixture_root = root / 'tests/fixtures/learning-assessment-draft'
    try:
        schema = read_json(schema_path, 256 * 1024)
        cases = read_json(root / 'schemas/learning-assessment-draft-v1.cases.json', 256 * 1024)
        discovered = {p.relative_to(fixture_root).as_posix() for p in fixture_root.rglob('*.json')}
        if not isinstance(cases, dict) or not cases or set(cases) != discovered or 'mixed.json' not in cases:
            raise ValueError('Fixture inventory mismatch')
        for expected in cases.values():
            if (not isinstance(expected, dict) or set(expected) != {'schemaValid', 'reviewStatus'} or
                    type(expected['schemaValid']) is not bool or
                    expected['reviewStatus'] not in ('reviewed-synthetic', 'unavailable')):
                raise ValueError('Invalid case expectations')
        fixtures = {name: read_json(fixture_root / name, 256 * 1024) for name in sorted(cases)}
        if not isinstance(fixtures['mixed.json'], dict) or not isinstance(fixtures['mixed.json'].get('scope'), dict):
            raise ValueError('Invalid mixed fixture')
    except (OSError, ValueError, TypeError, RecursionError):
        print(json.dumps({'status': 'failed', 'reason': 'Draft schema/fixture inventory is incomplete or invalid'}))
        return 1
    mixed = fixtures['mixed.json']
    scope = copy.deepcopy(mixed['scope'])
    now = datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc)
    formats = FormatChecker()

    @formats.checks('date-time', raises=(ValueError, TypeError))
    def strict_profile_timestamp(value):
        # Draft's own profile requires calendar-valid UTC seconds, not arbitrary
        # RFC3339 offsets. Do not silently skip optional format validation.
        _timestamp(value)
        return True

    def require(condition, label):
        if not condition:
            raise ValueError(label)

    try:
        with patch('socket.socket.connect', side_effect=AssertionError('Network forbidden')), \
                patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('Network forbidden')):
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema, format_checker=formats)
            for name, payload in fixtures.items():
                require(validator.is_valid(payload) == cases[name]['schemaValid'], 'fixture structure: ' + name)
                require(review(payload, scope, now=now, max_age_seconds=300)['status'] == cases[name]['reviewStatus'],
                        'fixture semantics: ' + name)

            structural = []
            p = copy.deepcopy(mixed); p['privateText'] = 'OMIT_PRIVATE'; structural.append(p)
            p = copy.deepcopy(mixed); p['environment'] = 'production'; structural.append(p)
            p = copy.deepcopy(mixed); p['generatedAt'] = '2026-02-30T00:00:00Z'; structural.append(p)
            p = copy.deepcopy(mixed); p['generatedAt'] = '2026-01-01T00:00:00+00:00'; structural.append(p)
            p = copy.deepcopy(mixed); p['scope']['nativeBotId'] += '\n'; structural.append(p)
            p = copy.deepcopy(mixed); p['assessments'][0]['evidenceIds'] = []; structural.append(p)
            p = copy.deepcopy(mixed); p['assessments'][0]['evidenceIds'] *= 2; structural.append(p)
            p = copy.deepcopy(mixed); p['evidence'] *= 11; structural.append(p)
            p = copy.deepcopy(mixed); del p['scope']['callerId']; structural.append(p)
            for index, payload in enumerate(structural):
                require(not validator.is_valid(payload), f'structural refusal {index}')
                require(review(payload, scope, now=now, max_age_seconds=300)['status'] == 'unavailable',
                        f'semantic refusal of malformed structure {index}')

            semantic = []
            p = copy.deepcopy(mixed); p['assessments'][1] = copy.deepcopy(p['assessments'][0]); semantic.append(p)
            p = copy.deepcopy(mixed); p['assessments'][0]['evidenceIds'] = ['absent']; semantic.append(p)
            p = copy.deepcopy(mixed); p['evidence'][0]['observedAt'] = '2025-12-31T00:00:00Z'; semantic.append(p)
            p = copy.deepcopy(mixed); p['generatedAt'] = '2026-01-01T00:03:00Z'; semantic.append(p)
            for index, payload in enumerate(semantic):
                require(validator.is_valid(payload), f'structurally valid semantic case {index}')
                require(review(payload, scope, now=now, max_age_seconds=300)['status'] == 'unavailable',
                        f'semantic refusal {index}')
    except (ValueError, TypeError, AssertionError, RecursionError, SchemaError):
        print(json.dumps({'status': 'failed', 'reason': 'Draft schema/semantic checks did not agree'}))
        return 1

    print(json.dumps({
        'status': 'passed', 'engine': 'jsonschema', 'version': version('jsonschema'),
        'dialect': 'Draft202012Validator', 'formatChecker': 'explicit strict UTC-second draft profile',
        'schemaSha256': hashlib.sha256(schema_path.read_bytes()).hexdigest(),
        'fixtureSha256': {name: hashlib.sha256((fixture_root / name).read_bytes()).hexdigest() for name in fixtures},
        'fixtures': len(fixtures), 'structuralRefusals': len(structural), 'semanticRefusals': len(semantic),
        'hubApproval': 'NOT CLAIMED', 'liveEvidence': 'NOT USED',
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
