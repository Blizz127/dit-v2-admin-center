"""Read committed synthetic audit examples; never execute a routing change."""
import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / 'data/fixtures/routing-audit.json'


def examples():
    try:
        data = json.loads(FIXTURE.read_text())
        return data if isinstance(data, list) else None
    except (OSError, ValueError):
        return None  # Missing examples are unknown, not proof of an empty real audit.
