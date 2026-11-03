"""Read exported hub control-view snapshots from a local directory.

Off unless HUB_SNAPSHOT_DIR is set. Exposes the same read interface as
live_hub.HubReader (get/health/interaction/trace) so the existing response
validation and projections apply unchanged. It never contacts the hub, reads a
token or uses the network. Snapshot data is as of its export time and is never
labeled live.

Layout (each file is the exact JSON body of the named hub GET at 043bc4b1):
    manifest.json                {"kind": "dit-hub-control-export", "version": 1,
                                  "exportedAtUtc": "...Z", "hubRevision": optional}
    <game>/bots.json             GET /v1/control/bots?gameId=<game>
    <game>/learning.json         GET /v1/control/learning?gameId=<game>&light=true&tasksOnly=true
    <game>/server-status.json    GET /v1/control/server-status?gameId=<game>
    health.json                  GET /v1/control/health
    interaction.json             GET /v1/control/interaction?limit=50
Trace lookups are per correlation ID and are not served from snapshots.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

from live_hub import GAME, MAX_RESPONSE, HubReadError, HubResponseTooLarge, _decode_response
from local_evidence import read_bytes

ENV = 'HUB_SNAPSHOT_DIR'
KIND = 'dit-hub-control-export'
MANIFEST_LIMIT = 4096
REVISION = re.compile(r'[0-9A-Za-z][0-9A-Za-z._-]{0,63}')
UTC = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,7})?Z')
VIEWS = ('bots', 'learning', 'server-status')


class SnapshotReader:
    feed_status = 'Exported snapshot'

    def __init__(self, directory, now=None):
        self.root = Path(directory)
        if not self.root.is_absolute():
            raise ValueError('Snapshot directory must be absolute')
        self.now = now or (lambda: datetime.now(timezone.utc))

    def label(self):
        """Validate the manifest on every read so a replaced export is never mislabeled."""
        try:
            raw = read_bytes(self.root / 'manifest.json', MANIFEST_LIMIT)
            if len(raw) > MANIFEST_LIMIT:
                raise ValueError('oversized manifest')
            manifest = _decode_response(raw)
            if not isinstance(manifest, dict) or set(manifest) - {'kind', 'version', 'exportedAtUtc', 'hubRevision'}:
                raise ValueError('unexpected manifest fields')
            if manifest.get('kind') != KIND or manifest.get('version') != 1 or type(manifest.get('version')) is not int:
                raise ValueError('unsupported manifest')
            exported = manifest.get('exportedAtUtc')
            if not isinstance(exported, str) or not UTC.fullmatch(exported):
                raise ValueError('invalid export time')
            moment = datetime.fromisoformat(exported[:-1] + '+00:00')
            if moment > self.now() + timedelta(minutes=5):
                raise ValueError('export time is in the future')
            revision = manifest.get('hubRevision')
            if revision is not None and (not isinstance(revision, str) or not REVISION.fullmatch(revision)):
                raise ValueError('invalid hub revision')
        except (OSError, ValueError, RecursionError):
            raise HubReadError('Snapshot unavailable') from None
        claimed = f'reported hub revision {revision}' if revision else 'hub revision not reported'
        return f'{exported} (exported snapshot, not live; {claimed})'

    def _read(self, relative):
        fetched = self.label()
        try:
            raw = read_bytes(self.root / relative, MAX_RESPONSE)
            if len(raw) > MAX_RESPONSE:
                raise HubResponseTooLarge('Snapshot exceeded limit')
            return _decode_response(raw), fetched
        except HubReadError:
            raise
        except (OSError, ValueError, RecursionError):
            # Paths and file contents are never included in errors.
            raise HubReadError('Snapshot view unavailable') from None

    def get(self, view, game):
        if view not in VIEWS or not GAME.fullmatch(game):
            raise ValueError('Unsupported read')
        return self._read(f'{game}/{view}.json')

    def health(self):
        return self._read('health.json')

    def interaction(self):
        return self._read('interaction.json')

    def trace(self, game, correlation):
        raise HubReadError('Trace lookups are not served from exported snapshots')
