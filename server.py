"""Local, synthetic-only DIT Admin Center development server."""
import hmac
import json
import os
import sqlite3
import math
import time
import subprocess
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from lead_timeline import add_current_evidence, monitoring_issues, timeline
from quota_history import collect, history
from owner_attention import pending_owner_decisions
from session_markers import admin_markers, binding_issues, claude_markers, handoff_codex_markers
from r10_projection import project_health, project_learning, project_learning_attention, project_roster

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT / "static"
LOCAL_DATA = PROJECT / "data" / "local"
QUOTA_SOURCE = Path.home() / ".local/share/devbox-codex-accounts/state.json"
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8")}


def lead_inventory():
    """Read only the DIT hub's latest coordinator task; absence is not idleness."""
    db = Path.home() / ".local/share/devbox-coordinator-state/tasks.sqlite"
    leads = [
        {"name": "DIT v2 hub lead", "scope": "Human behavior platform", "status": "Unknown", "source": "Coordinator task board", "observedAt": None},
        {"name": "Admin Center lead", "scope": "Admin Center", "status": "Unknown", "source": "Coordinator task board", "observedAt": None},
    ]
    try:
        with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True, timeout=2) as connection:
            row = connection.execute(
                "SELECT status, updated FROM tasks WHERE project = ? AND agent = ? ORDER BY updated DESC LIMIT 1",
                ("claude-dit-human-behavior-platform", "claude"),
            ).fetchone()
        if row:
            leads[0]["status"] = "Latest tracked task: " + row[0]
            leads[0]["observedAt"] = datetime.fromtimestamp(row[1], timezone.utc).isoformat()
    except (OSError, sqlite3.Error, ValueError, OverflowError):
        pass
    return leads


def capacity_context(root, provider, now=None):
    """A shared provider estimate is context, not an individual lead's quota."""
    if not provider:
        return "Unknown", "Lead provider identity is not established"
    try:
        snapshot = json.loads((root / "routing-capacity.json").read_text())
        checked = snapshot["checked_at"]
        entry = snapshot["providers"][provider]
        if type(checked) not in (int, float) or not math.isfinite(checked):
            raise ValueError("invalid timestamp")
        age = (time.time() if now is None else now) - checked
        at = datetime.fromtimestamp(checked, timezone.utc).isoformat()
        if not 0 <= age <= 180:
            return "Unknown", "Coordinator provider pool estimate stale; checked " + at
        value = entry.get("remaining")
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            return "Unknown", "Coordinator provider pool estimate unavailable; checked " + at
        return f"{value * 100:.0f}%", "Coordinator provider pool estimate; checked " + at + "; not the lead's own quota"
    except (OSError, ValueError, KeyError, TypeError, OverflowError):
        return "Unknown", "Coordinator provider pool estimate unavailable"


def session_activity(session):
    if not session:
        return "Unknown"
    try:
        result = subprocess.run(["tmux", "display-message", "-p", "-t", "=" + session, "#{session_activity}"],
                                capture_output=True, text=True, timeout=1, check=True)
        timestamp = int(result.stdout.strip())
        return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError, subprocess.SubprocessError):
        return "Unknown"


def lead_monitoring():
    root = Path.home() / ".local/share/devbox-coordinator-state"
    targets = [("DIT v2 hub lead", "claude-dit-human-behavior-platform", "claude", "claude", "claude-dit-human-behavior-platform"),
               ("Admin Center lead", "claude-dit-v2-admin-center", "codex", None, None)]
    try:
        config = json.loads((root / "watch.json").read_text())
        state = json.loads((root / "watch-state.json").read_text())
        records = config["targets"]
        if not isinstance(records, list) or not isinstance(state, dict):
            raise ValueError("invalid watcher data")
    except (OSError, ValueError, KeyError, TypeError):
        records, state = [], {}
    result = []
    for name, project, agent, provider, session in targets:
        item = {"lead": name, "stall": "Unknown", "stallReason": "No available matching watcher classification", "quota": "Unknown", "quotaReason": "No per-lead quota source connected", "stallObservedAt": None}
        item["poolCapacity"], item["poolReason"] = capacity_context(root, provider)
        item["sessionActivity"] = session_activity(session)
        matches = [t for t in records if isinstance(t, dict) and t.get("project") == project and t.get("agent") == agent and t.get("enabled", True)]
        if len(matches) == 1:
            entry = state.get(matches[0].get("name"), {})
            if isinstance(entry, dict) and entry.get("kind") in ("STALLED", "STOPPED", "OFF-TRACK", "OK") and isinstance(entry.get("checked"), (int, float)):
                try:
                    at = datetime.fromtimestamp(entry["checked"], timezone.utc).isoformat()
                    item["stallObservedAt"] = at
                    item["stall"] = entry["kind"]
                    item["stallReason"] = "Coordinator watcher classification checked " + at + "; may be stale"
                except (ValueError, OverflowError, OSError):
                    pass
        result.append(item)
    return result


def overview():
    # Synthetic r10 light/task-only shape; never fetched from the hub.
    projected = project_learning({'gameId': 'ffxi', 'tasks': [{
        'id': 'fixture-learning-1', 'gameId': 'ffxi', 'topic': 'Example route evidence',
        'status': 'unverified', 'reason': 'Example evidence needs review',
        'updatedAtUtc': '2026-01-01T12:00:00Z',
    }]})
    for row in projected:
        row['game'] = 'FFXI'
    home = Path.home()
    hub_project = home / 'dev/dit-human-behavior-platform'
    hub_report = claude_markers(home / '.claude', hub_project,
                                'claude-dit-human-behavior-platform', 'DIT v2 hub / behavior-platform lead')
    if hub_report['coverage'].startswith('Session marker coverage unknown'):
        takeover = handoff_codex_markers(home / '.codex/state_5.sqlite', home / '.codex/sessions', hub_project,
                                        home / '.local/share/devbox-failover/claude-dit-human-behavior-platform.json', hub_report['lead'])
        hub_report = takeover
    marker_reports = [admin_markers(home / '.codex/state_5.sqlite', home / '.codex/sessions', PROJECT), hub_report]
    marker_issues = [{'title': f"{report['lead']}: {m['kind']}",
                      'detail': 'Historical heuristic from a native system event; current goal and quota state remain unknown.',
                      'scope': 'Leads', 'status': 'Heuristic', 'source': m['source'], 'updatedAt': m['observedAt']}
                     for report in marker_reports for m in report['markers']]
    monitoring = lead_monitoring()
    lead_history = add_current_evidence(timeline(Path.home() / '.local/share/devbox-coordinator-state'), monitoring)
    return {
        "mode": "mock", "generatedAt": datetime.now(timezone.utc).isoformat(),
        "ownerAttention": pending_owner_decisions(home / ".local/share/devbox-coordinator-state/tasks.sqlite"),
        "bots": [
            {"id": "demo-1", "name": "Aster", "game": "FFXI", "status": "Paused", "source": "Synthetic fixture", "observedAt": "2026-01-01T12:00:00Z", "routing": {"purpose": "conversation", "requested": "Example provider / example model", "effective": None, "version": "example-1", "source": "Synthetic routing example", "observedAt": "2026-01-01T12:00:00Z", "availability": "Unavailable", "reason": "Example identity has not been verified"}},
            {"id": "demo-2", "name": "Vale", "game": "SWTOR", "status": "Unknown", "source": "Synthetic fixture", "observedAt": None},
        ] + project_roster("ffxi", [{"key": "example", "name": "Example roster bot"}]),
        "serviceHealth": project_health({'utc': '2026-01-01T12:00:00Z', 'services': [
            {'id': 'fixture-feed', 'game': 'ffxi', 'label': 'Example adapter feed', 'state': 'quiet', 'detail': 'Example only'}]}),
        "leads": lead_inventory(),
        "leadMonitoring": monitoring,
        "leadTimeline": lead_history,
        "sessionMarkers": marker_reports,
        "quotaHistory": history(LOCAL_DATA),
        "assignmentHistory": [
            {"botId": "demo-1", "purpose": "conversation", "requested": "Example provider / example model",
             "effective": None, "version": "example-1", "at": "2026-01-01T12:00:00Z", "source": "Synthetic assignment fixture"},
        ],
        "modelCalls": [
            {"id": "example-call-1", "model": "Example model", "purpose": "conversation", "latencyMs": 240,
             "cost": None, "quality": None, "source": "Synthetic example", "observedAt": "2026-01-01T12:00:00Z"},
        ],
        "audit": [
            {"actor": "Example operator", "action": "Simulated model selection", "scope": "Example FFXI bot",
             "result": "Example only; no change applied", "at": "2026-01-01T12:00:00Z", "source": "Synthetic audit fixture"},
        ],
        "ledger": [
            {"correlationId": "demo-episode-1", "botId": "demo-1", "bot": "Aster", "request": "Observe surroundings", "result": "Accepted", "verification": "Pending"},
            {"correlationId": "demo-episode-2", "botId": "demo-1", "bot": "Aster", "request": "Move to camp", "result": "Rejected: gate disabled", "verification": "Not applicable"},
        ],
        "learning": [
            {"id": "fixture-need-1", "game": "FFXI", "topic": "Navigation, party behavior and grounded social memory", "status": "Needs evidence", "evidence": "Not instrumented", "datasets": "Unknown", "policy": "Unknown", "source": "Synthetic planning example"},
            {"id": "fixture-need-2", "game": "FFXI", "topic": "Mission progression and current quest evidence", "status": "Needs inventory", "evidence": "Unknown", "datasets": "Unknown", "policy": "Unknown", "source": "Synthetic planning example"},
            {"id": "fixture-need-3", "game": "SWTOR", "topic": "Adapter coverage, missions and social behavior", "status": "Needs inventory", "evidence": "Unknown", "datasets": "Unknown", "policy": "Unknown", "source": "Synthetic planning example"},
        ] + projected,
        "issues": [
            {"title": "Hub contract awaiting coordination", "detail": "This view uses fixtures; no hub connection is configured.", "status": "Open", "scope": "Network", "source": "Synthetic planning example"},
            {"title": "Controls unavailable", "detail": "Bot commands, gates and model changes are not connected.", "status": "Open", "scope": "Network", "source": "Synthetic planning example"},
            {"title": "Example routing identity is unverified", "detail": "The synthetic routing record cannot select a model.", "status": "Open", "scope": "Bots", "source": "Synthetic routing example", "updatedAt": "2026-01-01T12:00:00Z"},
            {"title": "Bot presence lacks current evidence", "detail": "Mock bot statuses cannot establish current game presence.", "status": "Open", "scope": "Bots", "source": "Synthetic planning example"},
        ] + project_learning_attention(projected) + monitoring_issues(monitoring) + marker_issues + binding_issues(hub_report),
    }


class Handler(BaseHTTPRequestHandler):
    def send_content(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path.startswith("/api/"):
            supplied = self.headers.get("Authorization", "")
            expected = "Bearer " + self.server.admin_token
            if not hmac.compare_digest(supplied.encode(), expected.encode()):
                self.send_content(401, "application/json", b'{"error":"unauthorized"}')
            elif path == "/api/overview":
                self.send_content(200, "application/json", json.dumps(overview()).encode())
            else:
                self.send_content(404, "application/json", b'{"error":"not found"}')
            return
        if path in ASSETS:
            filename, content_type = ASSETS[path]
            self.send_content(200, content_type, (ROOT / filename).read_bytes())
        else:
            self.send_content(404, "text/plain; charset=utf-8", b"Not found")

    def log_message(self, format, *args):
        # Avoid logging paths or credentials.
        pass


def make_server(port, token):
    if not token or not token.strip():
        raise ValueError("ADMIN_TOKEN must be set")
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.admin_token = token
    return server


def run_quota_collector(stop):
    while not stop.is_set():
        try:
            collect(QUOTA_SOURCE, LOCAL_DATA)
        except (OSError, sqlite3.Error):
            pass
        stop.wait(60)


if __name__ == "__main__":
    token = os.environ.get("ADMIN_TOKEN", "")
    if not token.strip():
        raise SystemExit("Set ADMIN_TOKEN to a private, non-empty token before starting.")
    port = int(os.environ.get("PORT", "7391"))
    with make_server(port, token) as server:
        stop = threading.Event()
        worker = threading.Thread(target=run_quota_collector, args=(stop,), daemon=True)
        worker.start()
        print(f"Mock Admin Center listening on http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        finally:
            stop.set()
            worker.join(timeout=3)
