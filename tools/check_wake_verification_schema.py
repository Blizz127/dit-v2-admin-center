#!/usr/bin/env python3
"""Offline producer-profile and actual projection checks for wake receipts."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wake_verification import GAMES, HELD, project, timestamp


def main(root=ROOT):
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from jsonschema.exceptions import SchemaError
    except ImportError:
        print(json.dumps({'status': 'blocked', 'reason': 'JSON Schema engine unavailable'}))
        return 2
    schema_path = root / 'schemas/wake-verification-v1.schema.json'
    directory = root / 'tests/fixtures/wake-verification'
    try:
        schema = json.loads(schema_path.read_text())
        cases = json.loads((root / 'schemas/wake-verification-v1.cases.json').read_text())
        discovered = {p.relative_to(directory).as_posix() for p in directory.rglob('*.json')}
        if not isinstance(cases, dict) or not cases or set(cases) != discovered:
            raise ValueError('Fixture inventory mismatch')
        formats = FormatChecker()

        @formats.checks('dit-wake-timestamp', raises=(ValueError, TypeError, OverflowError))
        def checked_time(value):
            timestamp(value)
            return True

        with patch('socket.socket.connect', side_effect=AssertionError('Network forbidden')), \
                patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('Network forbidden')):
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema, format_checker=formats)
            for name, expected in cases.items():
                if (not isinstance(expected, dict) or set(expected) != {'schemaValid', 'cutover', 'verifiedGames'} or
                        type(expected['schemaValid']) is not bool or type(expected['cutover']) is not bool or
                        not isinstance(expected['verifiedGames'], list) or
                        not all(isinstance(game, str) and game in GAMES and game not in HELD
                                for game in expected['verifiedGames']) or
                        len(set(expected['verifiedGames'])) != len(expected['verifiedGames'])):
                    raise ValueError('Invalid expectations')
                payload = json.loads((directory / name).read_text())
                if validator.is_valid(payload) != expected['schemaValid']:
                    raise ValueError('Structure disagreement')
                result = project(payload, datetime(2026, 1, 2, tzinfo=timezone.utc))
                rows = {row['game']: row['status'] for row in result['rows']}
                verified = {game for game, status in rows.items() if status == 'Verified readback (reported)'}
                if ((result['cutover'] is not None) != expected['cutover'] or
                        set(rows) != set(GAMES) or verified != set(expected['verifiedGames']) or
                        any(rows[game] != 'Held' for game in HELD) or
                        any(rows[game] != 'Unverified' for game in set(GAMES) - HELD - verified)):
                    raise ValueError('Projection disagreement')
    except (OSError, ValueError, TypeError, AssertionError, SchemaError):
        print(json.dumps({'status': 'failed', 'reason': 'Wake schema/fixture/projection checks did not agree'}))
        return 1
    print(json.dumps({
        'status': 'passed', 'engine': 'jsonschema', 'version': version('jsonschema'),
        'dialect': 'Draft202012Validator', 'formatChecker': 'existing timezone-qualified wake timestamp parser',
        'schemaSha256': hashlib.sha256(schema_path.read_bytes()).hexdigest(),
        'fixtureSha256': {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in sorted(cases)},
        'fixtures': len(cases), 'liveEvidence': 'NOT USED', 'heldGames': sorted(HELD),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
