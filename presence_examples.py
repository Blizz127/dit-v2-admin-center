"""Committed explanatory fixtures, never a live presence reader or assessment."""
import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / 'data/fixtures/presence-examples.json'


def examples():
    try:
        data = json.loads(FIXTURE.read_text())
        return data if isinstance(data, dict) and data.get('kind') == 'synthetic' else None
    except (OSError, ValueError):
        return None
