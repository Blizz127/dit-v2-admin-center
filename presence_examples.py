"""Committed explanatory fixtures, never a live presence reader or assessment."""
from pathlib import Path
from local_evidence import read_json

FIXTURE = Path(__file__).resolve().parent / 'data/fixtures/presence-examples.json'


def examples():
    try:
        data = read_json(FIXTURE, 256 * 1024)
        return data if isinstance(data, dict) and data.get('kind') == 'synthetic' else None
    except (OSError, ValueError, RecursionError):
        return None
