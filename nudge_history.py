"""Read-only nudge/reply metadata for the two explicitly scoped DIT projects."""
from contextlib import closing
from datetime import datetime, timezone
import sqlite3

PROJECTS = (('DIT v2 hub / behavior-platform lead', 'claude-dit-human-behavior-platform'),
            ('Admin Center lead', 'claude-dit-v2-admin-center'))


def timestamp(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


def nudge_history(database):
    result = [{'lead': lead, 'coverage': 'Coordinator nudge history unavailable', 'nudges': []} for lead, _ in PROJECTS]
    try:
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
            for item, (_, project) in zip(result, PROJECTS):
                # Coordinator watcher origin is explicit. Owner-relayed stall-watch messages
                # use a text marker; the marker is only a heuristic and text is never returned.
                rows = db.execute('''SELECT m.created, m.delivered, m.status,
                    (SELECT MIN(r.time) FROM replies r WHERE r.message_id=m.id AND r.time>=m.created),
                    CASE WHEN m.origin='watcher' THEN 'watcher' ELSE 'stall-watch text match' END
                    FROM messages m WHERE m.project=? AND
                    (m.origin='watcher' OR (m.origin LIKE 'coordinator%' AND lower(m.text) LIKE '%stall watch%'))
                    ORDER BY m.created DESC LIMIT 20''', (project,)).fetchall()
                item['coverage'] = 'Latest 20 matching coordinator records; text matches are heuristic; other nudges may be absent'
                for created, delivered, status, reply, source in rows:
                    item['nudges'].append({
                        'createdAt': timestamp(created), 'deliveredAt': timestamp(delivered),
                        'messageStatus': status, 'repliedAt': timestamp(reply),
                        'replySeconds': round(reply-created, 1) if reply is not None else None,
                        'resumeSeconds': None, 'source': source,
                    })
        return result
    except (OSError, sqlite3.Error, ValueError, OverflowError, TypeError):
        return [{'lead': lead, 'coverage': 'Coordinator nudge history unavailable', 'nudges': []} for lead, _ in PROJECTS]
