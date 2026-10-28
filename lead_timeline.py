"""Bounded, read-only coordinator task history for the two DIT leads."""
from contextlib import closing
from datetime import datetime, timezone
import sqlite3

LEADS = (
    ('DIT v2 hub lead', 'claude-dit-human-behavior-platform', 'claude'),
    ('Admin Center lead', 'claude-dit-v2-admin-center', 'codex'),
)


def timeline(root):
    result = [{'lead': name, 'events': [], 'coverage': 'Unknown'} for name, _, _ in LEADS]
    try:
        with closing(sqlite3.connect((root / 'tasks.sqlite').as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
            for item, (_, project, agent) in zip(result, LEADS):
                rows = db.execute('''SELECT e.status, e.time FROM events e JOIN tasks t ON t.id=e.task
                    WHERE t.project=? AND t.agent=? ORDER BY e.time DESC LIMIT 10''', (project, agent)).fetchall()
                item['events'] = [
                    {'kind': 'Task status', 'status': status, 'at': datetime.fromtimestamp(at, timezone.utc).isoformat(),
                     'source': 'Coordinator task board'} for status, at in rows
                ]
                item['coverage'] = 'Recent tracked task events only' if rows else 'No matching task events; current state unknown'
    except (OSError, sqlite3.Error, ValueError, OverflowError, TypeError):
        # Never present partial history as a successful complete query.
        return [{'lead': name, 'events': [], 'coverage': 'Coordinator history unavailable'} for name, _, _ in LEADS]
    return result
