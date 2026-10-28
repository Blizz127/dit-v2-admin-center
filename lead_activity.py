"""Read-only coordinator task summaries and project checkout commit timestamps."""
from contextlib import closing
from datetime import datetime, timezone
import re
import sqlite3
import subprocess

# Suppress an entire summary if it resembles credential material; never return the match.
SENSITIVE = re.compile(r'(?i)(?:\b(?:bearer|basic)\s+\S+|\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|token|secret|password|passwd|authorization|cookie|client[_-]?secret)\s*["\']?\s*[:=]|\b(?:sk|xai|pk|rk)-[A-Za-z0-9_-]{16,}|\bAIza[0-9A-Za-z_-]{30,}|\bgh[pousr]_[A-Za-z0-9]{30,}|\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.|-----BEGIN [A-Z ]*PRIVATE KEY-----)')


def project_commit(project):
    try:
        result = subprocess.run(['git', '-C', str(project), 'log', '-1', '--format=%cI', 'HEAD'],
                                capture_output=True, text=True, timeout=2, check=True)
        value = result.stdout.strip()
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return stamp.astimezone(timezone.utc).isoformat() if stamp.tzinfo else None
    except (OSError, subprocess.SubprocessError, ValueError, OverflowError):
        return None


def lead_activity(database, leads):
    """`leads` is a list of (name, project ID, agent, checkout path)."""
    result = []
    try:
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
            for name, project_id, agent, project_path in leads:
                row = db.execute('SELECT status, summary, updated FROM tasks WHERE project=? AND agent=? ORDER BY updated DESC LIMIT 1', (project_id, agent)).fetchone()
                summary = 'Unknown'
                status = 'Unknown'
                updated = None
                if row:
                    status, raw, updated_at = row
                    updated = datetime.fromtimestamp(updated_at, timezone.utc).isoformat()
                    if isinstance(raw, str) and raw.strip():
                        summary = '[Summary withheld: possible sensitive material]' if SENSITIVE.search(raw) else raw[:1000] + ('…' if len(raw) > 1000 else '')
                result.append({'lead': name, 'taskStatus': status, 'taskSummary': summary,
                               'taskUpdatedAt': updated, 'commitAt': project_commit(project_path),
                               'taskSource': 'Coordinator task board', 'commitSource': 'Project checkout HEAD; not attributed to a lead'})
        return result
    except (OSError, sqlite3.Error, ValueError, TypeError, OverflowError):
        return [{'lead': name, 'taskStatus': 'Unknown', 'taskSummary': 'Unknown', 'taskUpdatedAt': None,
                 'commitAt': project_commit(path), 'taskSource': 'Coordinator task board unavailable',
                 'commitSource': 'Project checkout HEAD; not attributed to a lead'} for name, _, _, path in leads]
