"""Bounded heuristic: first observed tool work item after a delivered nudge."""
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3

MAX_TAIL = 256 * 1024


def parse_time(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.timestamp() if parsed.tzinfo else None
    except (ValueError, TypeError, AttributeError, OverflowError):
        return None


def work_items(path):
    try:
        with path.open('rb') as stream:
            stream.seek(0, 2); size = stream.tell()
            stream.seek(max(0, size - MAX_TAIL)); lines = stream.read(MAX_TAIL).splitlines()
        truncated = size > MAX_TAIL
        if truncated:
            lines = lines[1:]
        times, items = [], []
        for line in lines:
            try:
                record = json.loads(line)
                at = parse_time(record.get('timestamp'))
                if at is None:
                    continue
                times.append(at)
                payload = record.get('payload') or {}
                if record.get('type') == 'response_item' and isinstance(payload, dict) and payload.get('type') in ('function_call', 'custom_tool_call'):
                    items.append(at)
            except (ValueError, TypeError, AttributeError):
                continue
        return {'truncated': truncated, 'earliest': min(times) if times else None, 'items': sorted(items)}
    except OSError:
        return None


def resolve_rollout(database, sessions_root, project, session):
    """The message must name the unique active Codex thread in the configured cwd."""
    try:
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
            rows = db.execute('SELECT id, rollout_path FROM threads WHERE cwd=? AND archived=0 LIMIT 2', (str(project),)).fetchall()
        if len(rows) != 1 or rows[0][0] != session or not isinstance(rows[0][1], str):
            return None
        path = Path(rows[0][1]).resolve(strict=True)
        path.relative_to(sessions_root.resolve(strict=True))
        return path
    except (OSError, sqlite3.Error, ValueError, TypeError):
        return None


def first_signal(observed, delivered, next_delivery=None):
    if observed is None or delivered is None:
        return None
    if observed['truncated'] and (observed['earliest'] is None or observed['earliest'] > delivered):
        return None
    for at in observed['items']:
        if at >= delivered and (next_delivery is None or at < next_delivery):
            return {'observedAt': datetime.fromtimestamp(at, timezone.utc).isoformat(),
                    'seconds': round(at - delivered, 1), 'label': 'First observed tool request after delivery (heuristic; causality unverified)'}
    return None
