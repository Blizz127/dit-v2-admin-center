"""Bounded, read-only heuristic for explicit native Codex system markers.

Never return rollout text, inspect prompts, or equate missing markers with a running goal.
"""
from contextlib import closing
from datetime import datetime
import json
from pathlib import Path
import re
import sqlite3

MAX_TAIL = 256 * 1024
PATTERNS = (
    ('Possible goal stop', re.compile(r'\bgoal (?:has )?(?:been )?stopped\b', re.I)),
    ('Possible usage limit', re.compile(r'\b(?:usage limit (?:reached|exceeded)|(?:hit|reached) (?:your |the )?usage limit)\b', re.I)),
)


def scan(path):
    try:
        with path.open('rb') as stream:
            stream.seek(0, 2)
            size = stream.tell()
            stream.seek(max(0, size - MAX_TAIL))
            lines = stream.read(MAX_TAIL).splitlines()
        if size > MAX_TAIL:
            lines = lines[1:]  # first line may be partial
        hits = []
        for raw in lines:
            try:
                record = json.loads(raw)
                payload = record.get('payload') or {}
                if record.get('type') != 'event_msg' or not isinstance(payload, dict):
                    continue
                kind = payload.get('type')
                at = record.get('timestamp')
                if not isinstance(at, str):
                    continue
                parsed = datetime.fromisoformat(at.replace('Z', '+00:00'))
                if parsed.tzinfo is None:
                    continue
                marker = None
                if kind == 'goal_stopped':
                    marker = 'Possible goal stop'
                elif kind == 'usage_limit_reached':
                    marker = 'Possible usage limit'
                elif kind in ('error', 'warning', 'notice') and isinstance(payload.get('message'), str):
                    marker = next((name for name, pattern in PATTERNS if pattern.search(payload['message'])), None)
                if marker:
                    hits.append({'kind': marker, 'observedAt': at, 'source': 'Codex system event heuristic'})
            except (ValueError, TypeError, AttributeError):
                continue
        return hits[-10:]
    except OSError:
        return None


def admin_markers(database, sessions_root, project):
    """Only a unique active thread in the exact project and sessions tree is usable."""
    unknown = {'lead': 'Admin Center lead', 'coverage': 'Session marker coverage unknown', 'markers': []}
    try:
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
            rows = db.execute('SELECT rollout_path FROM threads WHERE cwd=? AND archived=0 LIMIT 2', (str(project),)).fetchall()
        if len(rows) != 1 or not isinstance(rows[0][0], str):
            return unknown
        path = Path(rows[0][0]).resolve(strict=True)
        path.relative_to(sessions_root.resolve(strict=True))
        markers = scan(path)
        if markers is None:
            return unknown
        return {'lead': 'Admin Center lead', 'coverage': 'Recent rollout tail only; no current goal-state guarantee', 'markers': markers}
    except (OSError, ValueError, TypeError, sqlite3.Error):
        return unknown
