"""Local, synthetic-only DIT Admin Center development server."""
import hmac
import http.client
import json
import os
import sqlite3
import math
import time
import subprocess
import threading
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from lead_timeline import add_checkout_history, add_current_evidence, monitoring_issues, timeline
from lead_activity import lead_activity
from lead_binding import current_codex_binding
from interaction_projection import project_interaction
from live_hub import CORRELATION, HubReadError, HubReader, merge_views, project_hub_health, project_spend, project_trace, read_views
from hub_cache import HubViewsCache
from bridge_status import BridgeObserver
from project_issues import read as read_project_issues
from issue_evidence import bridge_fault_issue, pending_decision_issues
from quota_history import collect, history
from owner_attention import pending_owner_decisions
from nudge_history import nudge_history
from session_markers import admin_markers, binding_issues, claude_markers, handoff_codex_markers
from r10_projection import project_health, project_learning, project_learning_attention, project_roster
from routing_audit import examples as routing_audit_examples
from presence_examples import examples as presence_examples
from evaluator_snapshot import from_env as evaluator_snapshot
from hub_snapshot import ENV as HUB_SNAPSHOT_ENV, SnapshotReader
from bakeoff_run import from_env as bakeoff_run
from baseline_conformance import read as baseline_conformance
from wake_verification import read as read_wake_verification
from operation_sources import read as read_operation_sources
from local_evidence import read_json
from context_capture import from_env as context_capture
from delivery_correlation import from_env as delivery_capture

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT / "static"
LOCAL_DATA = PROJECT / "data" / "local"
BRIDGE = BridgeObserver()
HUB_VIEWS = HubViewsCache(lambda url, token_file: read_views(HubReader(url, token_file)))
HUB_HEALTH = HubViewsCache(lambda url, token_file: project_hub_health(*HubReader(url, token_file).health()))
HUB_INTERACTION = HubViewsCache(lambda url, token_file: project_interaction(*HubReader(url, token_file).interaction()))


def hub_source():
    """Return ('live', (url, token_file)), ('snapshot', directory), ('none', None) or ('conflict', None).

    Exported snapshots and a live tunnel are mutually exclusive so a view is never
    silently mixed or mislabeled; both configured is refused.
    """
    url, token_file = os.environ.get('HUB_READONLY_URL'), os.environ.get('HUB_TOKEN_FILE')
    directory = os.environ.get(HUB_SNAPSHOT_ENV)
    if directory and (url or token_file):
        return 'conflict', None
    if directory:
        return 'snapshot', directory
    if url and token_file:
        return 'live', (url, token_file)
    return 'none', None
QUOTA_SOURCE = Path.home() / ".local/share/devbox-codex-accounts/state.json"
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"), "/playtest": ("playtest.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8")}


def lead_inventory():
    """Read only the DIT hub's latest coordinator task; absence is not idleness."""
    db = Path.home() / ".local/share/devbox-coordinator-state/tasks.sqlite"
    leads = [
        {"name": "DIT v2 hub lead", "scope": "Human behavior platform", "status": "Unknown", "source": "Coordinator task board", "observedAt": None},
        {"name": "Admin Center lead", "scope": "Admin Center", "status": "Unknown", "source": "Coordinator task board", "observedAt": None},
    ]
    try:
        with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True, timeout=2)) as connection:
            row = connection.execute(
                "SELECT status, updated FROM tasks WHERE project = ? AND agent = ? ORDER BY updated DESC LIMIT 1",
                ("claude-dit-human-behavior-platform", "claude"),
            ).fetchone()
        if row:
            leads[0]["status"] = "Latest tracked Claude-routed task (current lead unverified): " + row[0]
            leads[0]["observedAt"] = datetime.fromtimestamp(row[1], timezone.utc).isoformat()
    except (OSError, sqlite3.Error, ValueError, OverflowError):
        pass
    return leads


def capacity_context(root, provider, now=None):
    """A shared provider estimate is context, not an individual lead's quota."""
    if not provider:
        return "Unknown", "Lead provider identity is not established"
    try:
        snapshot = read_json(root / "routing-capacity.json", 1024 * 1024)
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
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError, RecursionError):
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
    home = Path.home()
    root = home / ".local/share/devbox-coordinator-state"
    targets = [("DIT v2 hub lead", "claude-dit-human-behavior-platform", home / 'dev/dit-human-behavior-platform'),
               ("Admin Center lead", "claude-dit-v2-admin-center", PROJECT)]
    try:
        config = read_json(root / "watch.json", 1024 * 1024)
        state = read_json(root / "watch-state.json", 1024 * 1024)
        records = config["targets"]
        if not isinstance(records, list) or not isinstance(state, dict):
            raise ValueError("invalid watcher data")
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        records, state = [], {}
    result = []
    for name, project, workspace_path in targets:
        binding = current_codex_binding(home / '.local/share/devbox-failover' / (project + '.json'),
                                        home / '.codex/state_5.sqlite', workspace_path)
        provider, thread = binding['provider'], binding['thread']
        item = {"lead": name, "stall": "Unknown", "stallReason": "No available matching watcher classification", "quota": "Unknown", "quotaReason": "No per-lead quota source connected", "stallObservedAt": None}
        item.update(provider=provider, binding=binding['coverage'], bindingObservedAt=datetime.now(timezone.utc).isoformat())
        if provider is None:
            item["stallReason"] = "Watcher-to-current-lead binding is unverified after provider rotation"
        item["poolCapacity"], item["poolReason"] = capacity_context(root, provider)
        item["sessionActivity"] = session_activity(project) if provider else "Unknown"
        matches = [t for t in records if isinstance(t, dict) and t.get("project") == project
                   and t.get("agent") == provider and t.get('session') == thread and t.get("enabled", True)]
        if provider is not None and len(matches) == 1 and isinstance(matches[0].get('name'), str):
            entry = state.get(matches[0].get("name"), {})
            if isinstance(entry, dict) and entry.get("kind") in ("STALLED", "STOPPED", "OFF-TRACK", "OK") and type(entry.get("checked")) in (int, float):
                try:
                    at = datetime.fromtimestamp(entry["checked"], timezone.utc).isoformat()
                    item["stallObservedAt"] = at
                    if 0 <= time.time() - entry['checked'] <= 180:
                        item["stall"] = entry["kind"]
                        item["stallReason"] = "Coordinator watcher for the bound thread checked " + at + "; observation only"
                    else:
                        item["stallReason"] = "Bound-thread watcher observation stale or future-dated; checked " + at
                except (ValueError, OverflowError, OSError):
                    pass
        result.append(item)
    return result


def model_call_examples():
    try:
        rows = read_json(PROJECT / 'data/fixtures/model-comparison.json', 256 * 1024)
        return rows if isinstance(rows, list) else None
    except (OSError, ValueError, RecursionError):
        return None


def overview(source='mock'):
    # Synthetic r10 light/task-only shape; never fetched from the hub.
    projected = project_learning({'gameId': 'ffxi', 'tasks': [{
        'id': 'fixture-learning-1', 'gameId': 'ffxi', 'topic': 'Example route evidence',
        'status': 'unverified', 'hasModelAnswer': True, 'reason': 'Example evidence needs review', 'phase': 'example review', 'escalation': 'needs-info',
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
    owner_attention = pending_owner_decisions(home / '.local/share/devbox-coordinator-state/tasks.sqlite')
    synthetic_spend = project_spend({'configured': True, 'month': '2026-01', 'settledUsd': 0.42,
                                     'reservedOpenUsd': 0.10, 'pricingError': 'example unknown'}, '2026-01-01T12:00:00Z')
    synthetic_spend['source'] = 'Synthetic ledger fixture; no live spend read'
    monitoring = lead_monitoring()
    # Off unless DIT_EVALUATOR_SNAPSHOT_FILE names a local export; never a hub read.
    evaluator_rows, evaluator_coverage = evaluator_snapshot()
    # Off unless DIT_BAKEOFF_RUN_DIR names a recorded offline run; no hub read or AI spend.
    bakeoff_rows, bakeoff_coverage = bakeoff_run()
    example_calls = model_call_examples()
    lead_history = add_current_evidence(timeline(Path.home() / '.local/share/devbox-coordinator-state'), monitoring)
    add_checkout_history(lead_history, {'DIT v2 hub lead': hub_project, 'Admin Center lead': PROJECT})
    snapshot = {
        "mode": "mock", "generatedAt": datetime.now(timezone.utc).isoformat(),
        "operationSources": read_operation_sources(home),
        "wakeVerification": read_wake_verification(LOCAL_DATA / 'wake-verification.json'),
        "ownerAttention": owner_attention,
        "ffxiFocus": {
            "closest": "DIT activation receipt 9ba4ccb reports model-only bridge r2 ready on October 29 at 22:53:01 UTC, superseding the earlier r5 baseline; post-rollout speech remains unverified.",
            "whatToLookFor": "Per the DIT lead's retest request, try a greeting, question and follow-up in linkshell, then party with a present companion. Correlate generation, queue and native delivery separately; Admin sends no test message.",
            "toggle": "No behavior or model toggle is connected in this Admin Center. Gate state is unknown.",
            "unverified": "Owner conversation acceptance is not observed; post-rollout generation, queue delivery and native speech remain unverified here. Retirement counters were not exercised by the empty bridge readback. Coordinator reports native scripts retired in 6ad8732c at 22:56:51 UTC with ALIVE_CHATTER=1; that rollout is not conversation acceptance.",
            "source": "DIT 9ba4ccb execution receipt: ready October 29, 2026 at 22:53:01 UTC; auditErrors 0, one poll, zero input/hub/queue rows. Dated evidence, not a current poll; the provider route was unchanged.",
        },
        "bots": [
            {"id": "demo-1", "name": "Aster", "game": "FFXI", "status": "Paused", "character": "Example job", "level": "12", "bodyKind": "Example body", "personalitySummary": "Example: patient and curious", "source": "Synthetic fixture", "observedAt": "2026-01-01T12:00:00Z", "routing": {"purpose": "conversation", "requested": "Example provider / example model", "effective": None, "version": "example-1", "source": "Synthetic routing example", "observedAt": "2026-01-01T12:00:00Z", "availability": "Unavailable", "reason": "Example identity has not been verified"}},
            {"id": "demo-2", "name": "Vale", "game": "SWTOR", "status": "Unknown", "source": "Synthetic fixture", "observedAt": None},
        ] + project_roster("ffxi", [{"key": "example", "name": "Example roster bot"}]),
        "gameStatus": [
            {"game": "FFXI", "xpRate": None, "checkedAt": None, "liveness": "Unknown", "source": "Synthetic fallback"},
            {"game": "SWTOR", "xpRate": None, "checkedAt": None, "liveness": "Unknown", "source": "Synthetic fallback"},
        ],
        "serviceHealth": project_health({'utc': '2026-01-01T12:00:00Z', 'services': [
            {'id': 'fixture-feed', 'game': 'ffxi', 'label': 'Example adapter feed', 'state': 'quiet', 'detail': 'Example only'}]}),
        "leads": lead_inventory(),
        "leadMonitoring": monitoring,
        "leadActivity": lead_activity(home / '.local/share/devbox-coordinator-state/tasks.sqlite', [
            ('DIT v2 hub lead', 'claude-dit-human-behavior-platform', 'claude', hub_project),
            ('Admin Center lead', 'claude-dit-v2-admin-center', 'codex', PROJECT),
        ]),
        "leadTimeline": lead_history,
        "nudgeHistory": nudge_history(home / ".local/share/devbox-coordinator-state/tasks.sqlite", home / '.codex/state_5.sqlite',
                                      home / '.codex/sessions', {'claude-dit-v2-admin-center': PROJECT,
                                      'claude-dit-human-behavior-platform': home / 'dev/dit-human-behavior-platform'}),
        "sessionMarkers": marker_reports,
        "quotaHistory": history(LOCAL_DATA),
        "safetyRecords": [
            {"scope": "Network example", "botId": None, "gate": "Off", "killSwitch": "Unknown", "source": "Synthetic safety fixture", "observedAt": "2026-01-01T12:00:00Z"},
            {"scope": "Bot example", "botId": "demo-1", "gate": "Off", "killSwitch": "Unknown", "source": "Synthetic safety fixture", "observedAt": "2026-01-01T12:00:00Z"},
        ],
        "botDetails": [
            {"botId": "demo-1", "source": "Synthetic bot detail fixture", "observedAt": "2026-01-01T12:00:00Z",
             "goals": [{"text": "Example: explore a safe area", "status": "Proposed", "evidence": "Not verified"}],
             "memories": [{"text": "Example: greeting a nearby traveler", "grounding": "Not verified"}]},
        ],
        "replyEvents": [
            {"botId": "demo-1", "correlationId": "demo-reply-1", "wordingOrigin": "Fallback",
             "fallbackPolicy": "Deterministic wording", "fallbackReason": "Example provider timeout",
             "generationStatus": "Timed out", "delivery": "Unknown", "verification": "Pending",
             "observedAt": "2026-01-01T12:00:00Z", "source": "Synthetic reply example"},
        ],
        "assignmentHistory": [
            {"botId": "demo-1", "purpose": "conversation", "requested": "Example provider / example model",
             "effective": None, "version": "example-1", "at": "2026-01-01T12:00:00Z", "source": "Synthetic assignment fixture"},
        ],
        "spendExample": synthetic_spend,
        "routingAudit": routing_audit_examples(),
        "presenceExamples": presence_examples(),
        "modelCalls": None if example_calls is None else example_calls + evaluator_rows + bakeoff_rows,
        "evaluatorSnapshot": evaluator_coverage,
        "bakeoffRun": bakeoff_coverage,
        # Committed tracker of the Forever-style baseline per game; None renders Unknown.
        "baselineConformance": baseline_conformance(),
        "audit": [
            {"actor": "Example operator", "action": "Simulated model selection", "scope": "Example FFXI bot",
             "result": "Example only; no change applied", "at": "2026-01-01T12:00:00Z", "source": "Synthetic audit fixture"},
        ],
        "ledger": [
            {"correlationId": "demo-episode-1", "botId": "demo-1", "bot": "Aster", "request": "Observe surroundings", "result": "Accepted", "verification": "Pending"},
            {"correlationId": "demo-episode-2", "botId": "demo-1", "bot": "Aster", "request": "Move to camp", "result": "Rejected: gate disabled", "verification": "Not applicable"},
        ],
        "learningArtifacts": [
            {"game": "FFXI", "kind": "Dataset", "name": "Example observation dataset", "version": "example-1", "validation": "Unknown", "adoption": "Not applicable", "outcome": "Unknown", "source": "Synthetic learning artifact", "observedAt": "2026-01-01T12:00:00Z"},
            {"game": "FFXI", "kind": "Policy", "name": "Example navigation policy", "version": "example-1", "validation": "Not evaluated", "adoption": "Unknown", "outcome": "Unknown", "source": "Synthetic learning artifact", "observedAt": "2026-01-01T12:00:00Z"},
            {"game": "SWTOR", "kind": "Dataset", "name": "Example dataset placeholder", "version": None, "validation": "Unknown", "adoption": "Not applicable", "outcome": "Unknown", "source": "Synthetic learning artifact", "observedAt": None},
        ],
        "learningPlan": [
            {"game": "FFXI", "topic": "Navigation, camps and zones", "next": "Inventory observations and outcome coverage", "evidence": "Unknown", "datasets": "Unknown", "policy": "Unknown", "source": "Project planning; not a live finding"},
            {"game": "FFXI", "topic": "Party, jobs, combat and missions", "next": "Identify game-specific examples and native validation coverage", "evidence": "Unknown", "datasets": "Unknown", "policy": "Unknown", "source": "Project planning; not a live finding"},
            {"game": "FFXI", "topic": "Grounded social memory", "next": "Identify verified facts and memory evaluation coverage", "evidence": "Unknown", "datasets": "Unknown", "policy": "Unknown", "source": "Project planning; not a live finding"},
            {"game": "SWTOR", "topic": "Adapter and observation coverage", "next": "Inventory native identity and available evidence", "evidence": "Unknown", "datasets": "Unknown", "policy": "Unknown", "source": "Project planning; not a live finding"},
            {"game": "SWTOR", "topic": "Missions, classes, parties and social behavior", "next": "Identify game-specific data and evaluation needs", "evidence": "Unknown", "datasets": "Unknown", "policy": "Unknown", "source": "Project planning; not a live finding"},
        ],
        "learning": [
            {"id": "fixture-need-1", "game": "FFXI", "topic": "Navigation, party behavior and grounded social memory", "status": "Needs evidence", "evidence": "Not instrumented", "datasets": "Unknown", "policy": "Unknown", "source": "Synthetic planning example"},
            {"id": "fixture-need-2", "game": "FFXI", "topic": "Mission progression and current quest evidence", "status": "Needs inventory", "evidence": "Unknown", "datasets": "Unknown", "policy": "Unknown", "source": "Synthetic planning example"},
            {"id": "fixture-need-3", "game": "SWTOR", "topic": "Adapter coverage, missions and social behavior", "status": "Needs inventory", "evidence": "Unknown", "datasets": "Unknown", "policy": "Unknown", "source": "Synthetic planning example"},
        ] + projected,
        "issues": [
            {"title": "Hub contract awaiting coordination", "detail": "Hub contract remains under review; each data source is labeled separately.", "status": "Open", "scope": "Network", "source": "Synthetic planning example"},
            {"title": "Controls unavailable", "detail": "Bot commands, gates and model changes are not connected.", "status": "Open", "scope": "Network", "source": "Synthetic planning example"},
            {"title": "Example routing identity is unverified", "botId": "demo-1", "detail": "The synthetic routing record cannot select a model.", "status": "Open", "scope": "Bots", "source": "Synthetic routing example", "updatedAt": "2026-01-01T12:00:00Z"},
            {"title": "Bot presence lacks current evidence", "detail": "Mock bot statuses cannot establish current game presence.", "status": "Open", "scope": "Bots", "source": "Synthetic planning example"},
        ] + read_project_issues() + project_learning_attention(projected) + monitoring_issues(monitoring) + marker_issues + binding_issues(hub_report) + [bridge_fault_issue()] + pending_decision_issues(owner_attention),
    }
    kind, config = hub_source()
    if kind == 'conflict':
        snapshot['hubFeeds'] = [{'game': 'All', 'view': 'hub', 'status': 'Invalid configuration', 'at': None,
                                 'note': 'Synthetic fallback; set either an exported snapshot directory or a live hub, not both'}]
        return snapshot
    if kind == 'none':
        snapshot['hubFeeds'] = [{'game': 'All', 'view': 'hub', 'status': 'Not configured', 'at': None,
                                 'note': 'Synthetic fallback; no live hub connection'}]
        return snapshot
    if source == 'mock':
        snapshot['hubFeeds'] = [{'game': 'All', 'view': 'hub', 'status': 'Mock selected', 'at': None,
                                 'note': 'Synthetic data selected; no hub read attempted'}]
        return snapshot
    try:
        if kind == 'snapshot':
            return merge_views(snapshot, read_views(SnapshotReader(config)))
        return merge_views(snapshot, HUB_VIEWS.get(*config))
    except ValueError:
        snapshot['hubFeeds'] = [{'game': 'All', 'view': 'hub', 'status': 'Invalid configuration', 'at': None,
                                 'note': 'Synthetic fallback; loopback tunnel required'}]
        return snapshot


class _RequestDeadline:
    """Enforce one deadline even within a buffered readline receiving trickles."""
    def __init__(self, stream, connection, idle_timeout, deadline):
        self.stream = stream
        self.connection = connection
        self.idle_timeout = idle_timeout
        self.deadline = deadline

    def readline(self, size=-1):
        line = bytearray()
        while size < 0 or len(line) < size:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Request acquisition deadline')
            self.connection.settimeout(min(self.idle_timeout, remaining))
            # readline(size) can do many socket reads internally. A one-byte
            # buffered read returns control between bytes without consuming a
            # following body; the socket buffer still amortizes actual recv calls.
            byte = self.stream.readline(1)
            if time.monotonic() >= self.deadline:
                raise TimeoutError('Request acquisition deadline')
            if not byte:
                break
            line.extend(byte)
            if byte == b'\n':
                break
        return bytes(line)


class _IncompleteHeaders(Exception):
    pass


class _HeaderBudget:
    """Bound aggregate header acquisition, not just each individual line."""
    def __init__(self, stream, limit=65536):
        self.stream = stream
        self.remaining = limit

    def readline(self, size=-1):
        limit = self.remaining + 1
        if size >= 0:
            limit = min(limit, size)
        line = self.stream.readline(limit)
        self.remaining -= len(line)
        if self.remaining < 0:
            # The stdlib parser maps this to 431; send_error redacts its text.
            raise http.client.LineTooLong('request headers')
        if not line.endswith(b'\n'):
            # EOF cannot substitute for the blank line terminating headers.
            raise _IncompleteHeaders
        return line


class Handler(BaseHTTPRequestHandler):
    # Idle I/O timeout plus one total request-line/header acquisition deadline.
    timeout = 5
    request_timeout = 10

    def handle_one_request(self):
        # Keep stdlib dispatch/size limits, but distinguish a read timeout from
        # a timeout after a response may have started (never append a second one).
        self.command = None
        self.requestline = ''
        self.request_version = 'HTTP/1.0'
        self._response_started = False
        reading = True
        original = self.rfile
        self.rfile = _RequestDeadline(original, self.connection, self.timeout,
                                      time.monotonic() + self.request_timeout)
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                return
            reading = False
            self.connection.settimeout(self.timeout)
            method = getattr(self, 'do_' + self.command, None)
            if method is None:
                self.send_error(501)
                return
            method()
            self.wfile.flush()
        except TimeoutError:
            self.close_connection = True
            if reading and not getattr(self, '_response_started', False):
                try:
                    self.send_error(408)
                except OSError:
                    # A stalled/disconnected peer may not accept the refusal.
                    pass
        except (BrokenPipeError, ConnectionResetError):
            # An aborted upload may disconnect before receiving its refusal.
            # Do not retry a response or bubble a normal peer failure to the server.
            self.close_connection = True
        finally:
            self.rfile = original

    def parse_request(self):
        original = self.rfile
        self.rfile = _HeaderBudget(original)
        try:
            parsed = super().parse_request()
        except _IncompleteHeaders:
            self.send_error(400)
            parsed = False
        finally:
            self.rfile = original
        if not parsed:
            return False
        # Mutation methods are already refused without consuming their bodies.
        # Validate framing before read routes can authenticate or collect data.
        if self.command == 'GET':
            singleton = ('Host', 'Authorization', 'Content-Length', 'Transfer-Encoding')
            ambiguous = any(len(self.headers.get_all(name, [])) > 1 for name in singleton)
            length = self.headers.get('Content-Length')
            invalid_length = length is not None and (
                not length or not length.isascii() or not length.isdecimal() or
                any(digit != '0' for digit in length))
            if (ambiguous or self.headers.defects or invalid_length or
                    'Transfer-Encoding' in self.headers):
                self.send_error(400)
                return False
        return True

    def send_content(self, status, content_type, body, *, allow=None):
        self._response_started = True
        # A near-expired acquisition deadline must not shrink the response's
        # write allowance, including the attempt to report a timeout itself.
        self.connection.settimeout(self.timeout)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.send_header("Content-Length", str(len(body)))
        if allow is not None:
            self.send_header('Allow', allow)
            self.send_header('Connection', 'close')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def send_error(self, code, message=None, explain=None):
        # Parser errors can precede path assignment or use absolute-form targets.
        # Redact uniformly rather than relying on an already-parsed API path.
        self.close_connection = True
        error = 'method not supported' if code == 501 else 'request rejected'
        self.send_content(code, 'application/json', json.dumps({'error': error}).encode())

    def reject_write(self):
        # No write routes exist. Do not read, decode or drain any request body,
        # including unbounded/chunked input; close so it cannot become a request.
        self.close_connection = True
        self.send_content(405, 'application/json', b'{"error":"method not allowed"}', allow='GET')

    do_POST = reject_write
    do_PUT = reject_write
    do_PATCH = reject_write
    do_DELETE = reject_write

    def do_GET(self):
        try:
            target = urlsplit(self.path)
        except ValueError:
            # Malformed authorities can fail before a route can be identified.
            # Do not expose parser exception text or attempt any collection.
            self.close_connection = True
            self.send_content(400, 'application/json', b'{"error":"invalid request target"}')
            return
        path = target.path
        if path.startswith("/api/"):
            supplied = self.headers.get("Authorization", "")
            expected = "Bearer " + self.server.admin_token
            if not hmac.compare_digest(supplied.encode(), expected.encode()):
                self.send_content(401, "application/json", b'{"error":"unauthorized"}')
            elif path == "/api/context-capture":
                if target.query:
                    self.send_content(400, "application/json", b'{"error":"context capture takes no parameters"}')
                    return
                self.send_content(200, "application/json", json.dumps(context_capture()).encode())
            elif path == "/api/delivery-capture":
                if target.query:
                    self.send_content(400, "application/json", b'{"error":"delivery capture takes no parameters"}')
                    return
                self.send_content(200, "application/json", json.dumps(delivery_capture()).encode())
            elif path == "/api/hub-health":
                if target.query:
                    self.send_content(400, "application/json", b'{"error":"invalid query"}')
                    return
                kind, config = hub_source()
                if kind in ('none', 'conflict'):
                    self.send_content(503, "application/json", b'{"error":"hub not configured"}')
                    return
                try:
                    result = project_hub_health(*SnapshotReader(config).health()) if kind == 'snapshot' else HUB_HEALTH.get(*config)
                except ValueError:
                    self.send_content(502, "application/json", b'{"error":"invalid health response or configuration"}')
                    return
                except HubReadError:
                    self.send_content(503, "application/json", b'{"error":"hub read unavailable"}')
                    return
                self.send_content(200, "application/json", json.dumps(result).encode())
            elif path == "/api/interaction":
                if target.query:
                    self.send_content(400, "application/json", b'{"error":"interaction takes no parameters"}')
                    return
                kind, config = hub_source()
                if kind in ('none', 'conflict'):
                    self.send_content(503, "application/json", b'{"error":"hub not configured"}')
                    return
                try:
                    result = project_interaction(*SnapshotReader(config).interaction()) if kind == 'snapshot' else HUB_INTERACTION.get(*config)
                except ValueError:
                    self.send_content(502, "application/json", b'{"error":"invalid interaction response or configuration"}')
                    return
                except HubReadError:
                    self.send_content(503, "application/json", b'{"error":"interaction read unavailable"}')
                    return
                self.send_content(200, "application/json", json.dumps(result).encode())
            elif path == "/api/trace":
                try:
                    query = parse_qs(target.query, keep_blank_values=True,
                                     strict_parsing=True, errors='strict', max_num_fields=2)
                except ValueError:
                    self.send_content(400, "application/json", b'{"error":"invalid trace scope"}')
                    return
                if set(query) != {'gameId', 'correlationId'} or any(len(v) != 1 for v in query.values()):
                    self.send_content(400, "application/json", b'{"error":"invalid trace scope"}')
                    return
                if query['gameId'][0] not in ('ffxi', 'swtor') or not CORRELATION.fullmatch(query['correlationId'][0]):
                    self.send_content(400, "application/json", b'{"error":"invalid trace scope"}')
                    return
                kind, config = hub_source()
                if kind in ('none', 'conflict'):
                    self.send_content(503, "application/json", b'{"error":"hub not configured"}')
                    return
                if kind == 'snapshot':
                    self.send_content(503, "application/json", b'{"error":"trace unavailable from exported snapshot"}')
                    return
                url, token_file = config
                try:
                    result, fetched = HubReader(url, token_file).trace(query['gameId'][0], query['correlationId'][0])
                except ValueError:
                    self.send_content(400, "application/json", b'{"error":"invalid trace scope or configuration"}')
                    return
                except HubReadError:
                    self.send_content(503, "application/json", b'{"error":"hub read unavailable"}')
                    return
                try:
                    records = project_trace(result)
                except ValueError:
                    self.send_content(502, "application/json", b'{"error":"invalid hub trace response"}')
                    return
                body = {'records': records, 'fetchedAt': fetched,
                        'coverage': 'Recent hub trace window, maximum 250 records; missing records do not prove no action.'}
                self.send_content(200, "application/json", json.dumps(body).encode())
            elif path == "/api/bridge-status":
                if target.query:
                    self.send_content(400, "application/json", b'{"error":"bridge status takes no parameters"}')
                    return
                self.send_content(200, "application/json", json.dumps(BRIDGE.read()).encode())
            elif path == "/api/overview":
                try:
                    query = parse_qs(target.query, keep_blank_values=True,
                                     strict_parsing=True, errors='strict', max_num_fields=1)
                except ValueError:
                    self.send_content(400, "application/json", b'{"error":"invalid source"}')
                    return
                values = query.get('source', ['mock'])
                if set(query) - {'source'} or len(values) != 1 or values[0] not in ('mock', 'hub'):
                    self.send_content(400, "application/json", b'{"error":"invalid source"}')
                else:
                    self.send_content(200, "application/json", json.dumps(overview(values[0])).encode())
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


class BoundedHTTPServer(ThreadingHTTPServer):
    """Bound active handlers; excess accepted connections are closed immediately."""
    max_handlers = 16

    def __init__(self, *args, **kwargs):
        self._handler_slots = threading.BoundedSemaphore(self.max_handlers)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self._handler_slots.acquire(blocking=False):
            # Do not read a request, start a rejection thread or block the
            # accept loop writing to an already saturated set of clients.
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            # Thread creation/start failed; no worker will release this slot.
            self._handler_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._handler_slots.release()


def make_server(port, token):
    if not token or not token.strip():
        raise ValueError("ADMIN_TOKEN must be set")
    server = BoundedHTTPServer(("127.0.0.1", port), Handler)
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
