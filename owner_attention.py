"""Read-only, bounded view of explicit coordinator owner approval records."""
from contextlib import closing
from datetime import datetime, timezone
import sqlite3
import time

PROJECTS = ('claude-dit-v2-admin-center', 'claude-dit-human-behavior-platform')


def pending_owner_decisions(database, now=None):
    now = time.time() if now is None else now
    try:
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
            rows = db.execute('''SELECT a.project, a.title, a.created, a.expires
                FROM approvals a LEFT JOIN overnight_decisions n ON n.id=a.id
                WHERE a.status='pending' AND a.expires>? AND n.id IS NULL AND a.project IN (?, ?)
                ORDER BY a.created DESC LIMIT 20''', (now, *PROJECTS)).fetchall()
        return {'coverage': 'Unexpired pending owner approvals for the two DIT projects; other requests may exist',
                'items': [{'project': project, 'title': title,
                           'createdAt': datetime.fromtimestamp(created, timezone.utc).isoformat(),
                           'expiresAt': datetime.fromtimestamp(expires, timezone.utc).isoformat()}
                          for project, title, created, expires in rows]}
    except (OSError, sqlite3.Error, ValueError, TypeError, OverflowError):
        return {'coverage': 'Coordinator approval records unavailable', 'items': []}
