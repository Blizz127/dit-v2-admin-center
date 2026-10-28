"""Local, synthetic-only DIT Admin Center development server."""
import hmac
import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent / "static"
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8")}


def overview():
    return {
        "mode": "mock", "generatedAt": datetime.now(timezone.utc).isoformat(),
        "bots": [
            {"id": "demo-1", "name": "Aster", "game": "FFXI", "status": "Paused", "source": "Synthetic fixture", "observedAt": "2026-01-01T12:00:00Z"},
            {"id": "demo-2", "name": "Vale", "game": "SWTOR", "status": "Unknown", "source": "Synthetic fixture", "observedAt": None},
        ],
        "leads": [
            {"name": "Mira", "scope": "FFXI learning", "status": "Unknown", "source": "Synthetic fixture", "observedAt": None},
            {"name": "Rowan", "scope": "SWTOR adapter", "status": "Unknown", "source": "Synthetic fixture", "observedAt": None},
        ],
        "ledger": [
            {"correlationId": "demo-episode-1", "bot": "Aster", "request": "Observe surroundings", "result": "Accepted", "verification": "Pending"},
            {"correlationId": "demo-episode-2", "bot": "Aster", "request": "Move to camp", "result": "Rejected: gate disabled", "verification": "Not applicable"},
        ],
        "learning": [
            {"game": "FFXI", "topic": "Navigation and grounded social memory", "status": "Needs evidence", "evidence": "Not instrumented"},
            {"game": "SWTOR", "topic": "Adapter and game-specific behavior", "status": "Not started", "evidence": "Unknown"},
        ],
        "issues": [
            {"title": "Hub contract awaiting coordination", "detail": "This view uses fixtures; no hub connection is configured."},
            {"title": "Controls unavailable", "detail": "Bot commands, gates and model changes are not connected."},
        ],
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


if __name__ == "__main__":
    token = os.environ.get("ADMIN_TOKEN", "")
    if not token.strip():
        raise SystemExit("Set ADMIN_TOKEN to a private, non-empty token before starting.")
    port = int(os.environ.get("PORT", "7391"))
    with make_server(port, token) as server:
        print(f"Mock Admin Center listening on http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()
