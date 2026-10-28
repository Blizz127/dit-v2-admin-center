"""Bounded, read-only coordinator task history for the two DIT leads."""
from contextlib import closing
from datetime import datetime, timezone
import sqlite3
import json

LEADS = (
    ('DIT v2 hub lead', 'claude-dit-human-behavior-platform', 'claude'),
    ('Admin Center lead', 'claude-dit-v2-admin-center', 'codex'),
)


def timeline(root):
    result = [{'lead': name, 'events': [], 'coverage': 'Unknown', 'watchCoverage': 'Unknown'} for name, _, _ in LEADS]
    try:
        config = json.loads((root / 'watch.json').read_text())
        targets = config['targets'] if isinstance(config['targets'], list) else []
    except (OSError, ValueError, TypeError, KeyError):
        targets = []
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
                matches = [t.get('name') for t in targets if isinstance(t, dict) and t.get('project') == project and t.get('agent') == agent and isinstance(t.get('name'), str)]
                item['watchCoverage'] = 'Unknown: no unambiguous watcher target'
                if len(matches) == 1:
                    alerts = db.execute('SELECT kind, time FROM watch_alerts WHERE target=? ORDER BY time DESC LIMIT 10', (matches[0],)).fetchall()
                    item['watchCoverage'] = 'Recent watcher alerts only' if alerts else 'No matching watcher alerts; current stall state unknown'
                    item['events'].extend({'kind': 'Watcher alert', 'status': kind, 'at': datetime.fromtimestamp(at, timezone.utc).isoformat(), 'source': 'Coordinator watcher'} for kind, at in alerts)
                    item['events'].sort(key=lambda event: event['at'], reverse=True)
    except (OSError, sqlite3.Error, ValueError, OverflowError, TypeError):
        # Never present partial history as a successful complete query.
        return [{'lead': name, 'events': [], 'coverage': 'Coordinator history unavailable', 'watchCoverage': 'Unknown'} for name, _, _ in LEADS]
    return result


def add_current_evidence(history_rows, monitoring):
    """Add session activity and watcher snapshots, not inferred idle or goal state."""
    by_lead = {item['lead']: item for item in monitoring}
    for row in history_rows:
        info = by_lead.get(row['lead'], {})
        activity = info.get('sessionActivity')
        if isinstance(activity, str) and activity != 'Unknown':
            row['events'].append({'kind': 'Session activity', 'status': 'Activity observed; idle state unknown',
                                  'at': activity, 'source': 'tmux session activity'})
        checked = info.get('stallObservedAt')
        classification = info.get('stall')
        if checked and classification in ('STALLED', 'STOPPED', 'OFF-TRACK', 'OK'):
            row['events'].append({'kind': 'Watcher classification', 'status': classification,
                                  'at': checked, 'source': 'Coordinator watcher; may be stale'})
        row['events'].sort(key=lambda event: event['at'], reverse=True)
    return history_rows


def monitoring_issues(monitoring):
    """Flag reported stopped sessions without claiming their goal has stopped."""
    issues = [{'title': 'Lead goal status unavailable',
               'detail': 'Coordinator task and watcher data do not report goal status; stopped goals cannot be determined.',
               'scope': 'Leads', 'status': 'Unknown', 'source': 'Coordinator coverage', 'updatedAt': None}]
    for info in monitoring:
        if info.get('stall') == 'STOPPED' and info.get('stallObservedAt'):
            issues.append({'title': f"{info['lead']}: watcher reported a stopped session",
                           'detail': 'This is a session classification, not a stopped-goal report; it may be stale.',
                           'scope': 'Leads', 'status': 'Reported', 'source': 'Coordinator watcher',
                           'updatedAt': info['stallObservedAt']})
    return issues


def add_checkout_history(history_rows, projects):
    """Add bounded checkout HEAD ancestry, not commits attributed to a lead."""
    import re
    import subprocess

    for row in history_rows:
        project = projects.get(row['lead'])
        row['commitCoverage'] = 'Checkout commit history unavailable'
        if project is None:
            continue
        try:
            output = subprocess.run(['git', '-C', str(project), 'log', '-10', '--format=%H%x09%cI', 'HEAD'],
                                    capture_output=True, text=True, timeout=2, check=True).stdout
            events = []
            for line in output.splitlines():
                parts = line.split('\t')
                if len(parts) != 2 or not re.fullmatch(r'[0-9a-f]{40,64}', parts[0]):
                    raise ValueError('invalid git output')
                stamp = datetime.fromisoformat(parts[1].replace('Z', '+00:00'))
                if stamp.tzinfo is None:
                    raise ValueError('missing timezone')
                events.append({'kind': 'Checkout commit', 'status': parts[0][:12],
                               'at': stamp.astimezone(timezone.utc).isoformat(),
                               'source': 'Checkout HEAD ancestry; not attributed to lead'})
            row['events'].extend(events)
            row['events'].sort(key=lambda event: datetime.fromisoformat(event['at'].replace('Z', '+00:00')).timestamp(), reverse=True)
            row['commitCoverage'] = 'Up to 10 checkout HEAD commits; other branches and authors are not covered'
        except (OSError, subprocess.SubprocessError, ValueError, OverflowError):
            continue
    return history_rows
