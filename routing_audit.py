"""Read committed synthetic audit examples; never execute a routing change."""
from pathlib import Path
from local_evidence import read_json

FIXTURE = Path(__file__).resolve().parent / 'data/fixtures/routing-audit.json'


def examples():
    try:
        data = read_json(FIXTURE, 256 * 1024)
        return data if isinstance(data, list) else None
    except (OSError, ValueError, RecursionError):
        return None  # Missing examples are unknown, not proof of an empty real audit.
