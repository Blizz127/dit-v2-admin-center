"""Bounded, read-only heuristic for explicit native Codex system markers.

Never return rollout text, inspect prompts, or equate missing markers with a running goal.
"""
from contextlib import closing
from datetime import datetime
import json
from pathlib import Path
import re
import os
import uuid
import sqlite3
from local_evidence import read_json, read_tail

MAX_TAIL = 256 * 1024
PATTERNS = (
    ('Possible goal stop', re.compile(r'\bgoal (?:has )?(?:been )?stopped\b', re.I)),
    ('Possible usage limit', re.compile(r'\b(?:usage limit (?:reached|exceeded)|(?:hit|reached) (?:your |the )?usage limit)\b', re.I)),
)


def scan(path, source='Codex system event heuristic'):
    try:
        size, raw = read_tail(path, MAX_TAIL)
        lines = raw.splitlines()
        if size > MAX_TAIL:
            if len(lines) <= 1:
                return None  # No complete bounded line is available.
            lines = lines[1:]  # first line may be partial
        hits = []
        for raw in lines:
            try:
                record = json.loads(raw)
                payload = record.get('payload') or {}
                if record.get('type') == 'event_msg' and isinstance(payload, dict):
                    kind, message = payload.get('type'), payload.get('message')
                elif record.get('type') == 'system':
                    kind, message = record.get('subtype'), record.get('content')
                else:
                    continue
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
                elif kind in ('error', 'api_error', 'warning', 'notice') and isinstance(message, str):
                    marker = next((name for name, pattern in PATTERNS if pattern.search(message)), None)
                if marker:
                    hits.append({'kind': marker, 'observedAt': at, 'source': source})
            except (ValueError, TypeError, AttributeError, RecursionError):
                return None  # Incomplete tail cannot establish marker coverage.
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


def claude_markers(native_root, project, tmux_session, lead):
    """Accept one live native binding whose tmux, cwd and protocol match exactly."""
    def unknown(reason):
        return {'lead': lead, 'coverage': 'Session marker coverage unknown: ' + reason, 'markers': []}
    try:
        candidates = []
        for file in (native_root / 'sessions').glob('*.json'):
            try:
                data = read_json(file, 256 * 1024)
                pid, session = data.get('pid'), data.get('sessionId')
                if type(pid) is not int or pid <= 1 or not data.get('messagingSocketPath') or data.get('peerProtocol') != 1:
                    continue
                os.kill(pid, 0)
                if data.get('cwd') != str(project) or (data.get('tmux') or '').split(':', 1)[0] != tmux_session:
                    continue
                uuid.UUID(session)
                candidates.append(session)
            except (OSError, ValueError, TypeError, AttributeError, RecursionError):
                continue
        if len(candidates) != 1:
            return unknown('no unique live native Claude session matching configured cwd and tmux')
        slug = re.sub(r'[^A-Za-z0-9]', '-', str(project))
        projects = (native_root / 'projects').resolve(strict=True)
        path = (projects / slug / (candidates[0] + '.jsonl')).resolve(strict=True)
        path.relative_to(projects)
        markers = scan(path, 'Claude system event heuristic')
        if markers is None:
            return unknown('bound transcript is unreadable')
        return {'lead': lead, 'coverage': 'Recent rollout tail only; no current goal-state guarantee', 'markers': markers}
    except (OSError, ValueError, TypeError):
        return unknown('native session metadata or transcript is unavailable')


def handoff_codex_markers(database, sessions_root, project, lane_path, lead):
    """Use a unique coordinator handoff marker in exact native thread metadata.

    This establishes a historical thread binding, not a live process binding.
    """
    def unknown(reason):
        return {'lead': lead, 'coverage': 'Session marker coverage unknown: ' + reason, 'markers': []}
    try:
        lane = read_json(lane_path, 256 * 1024)
        marker = lane.get('marker')
        if lane.get('provider') != 'codex' or lane.get('cwd') != str(project) or not isinstance(marker, str) or not marker:
            return unknown('handoff provider, project, or marker is missing or mismatched')
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
            rows = db.execute('SELECT id, rollout_path, first_user_message FROM threads WHERE cwd=? AND archived=0', (str(project),)).fetchall()
        matches = [r for r in rows if isinstance(r[2], str) and marker in r[2]]
        if len(matches) != 1 or (lane.get('thread') and lane['thread'] != matches[0][0]):
            return unknown('handoff marker does not identify exactly one matching native thread')
        path = Path(matches[0][1]).resolve(strict=True)
        path.relative_to(sessions_root.resolve(strict=True))
        markers = scan(path)
        if markers is None:
            return unknown('bound rollout is unavailable')
        return {'lead': lead, 'coverage': 'Coordinator handoff binds one thread; live process unverified. Recent rollout tail only.', 'markers': markers}
    except (OSError, ValueError, TypeError, AttributeError, RecursionError, sqlite3.Error):
        return unknown('handoff metadata or bound rollout is unavailable')


def binding_issues(report):
    """Report coverage ambiguity without suggesting recovery actions."""
    coverage = report.get('coverage')
    if not isinstance(coverage, str) or not coverage.startswith('Session marker coverage unknown'):
        return []
    return [{'title': 'Hub lead session marker binding unavailable',
             'detail': coverage,
             'suggestedFix': 'Ask the coordinator to verify the configured project, handoff marker and native thread identity read-only; do not infer a match from activity alone.',
             'scope': 'Leads', 'status': 'Unknown', 'source': 'Coordinator handoff and native thread metadata',
             'updatedAt': None}]
