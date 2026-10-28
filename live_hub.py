"""Optional bounded read-only hub client; only an explicitly configured loopback tunnel."""
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MAX_RESPONSE = 1_000_000
GAME = re.compile(r'^[a-z][a-z0-9_]{1,31}$')
CORRELATION = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HubReadError(Exception):
    pass


class HubReader:
    def __init__(self, url, token_file, timeout=3):
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.username is not None
                or parsed.password is not None or not parsed.port or parsed.path not in ('', '/')
                or parsed.query or parsed.fragment):
            raise ValueError('Hub URL must be an explicit HTTP 127.0.0.1 port')
        self.base = f'http://127.0.0.1:{parsed.port}'
        self.token_file = Path(token_file)
        self.timeout = timeout
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def get(self, view, game):
        if view not in ('bots', 'learning', 'server-status') or not GAME.fullmatch(game):
            raise ValueError('Unsupported read')
        query = {'gameId': game}
        if view == 'learning':
            query.update({'light': 'true', 'tasksOnly': 'true'})
        return self._request(view, query)

    def health(self):
        return self._request('health', {})

    def trace(self, game, correlation):
        if game not in ('ffxi', 'swtor') or not isinstance(correlation, str) or not CORRELATION.fullmatch(correlation):
            raise ValueError('Invalid trace scope')
        return self._request('trace', {'gameId': game, 'correlationId': correlation})

    def _request(self, view, query):
        try:
            if self.token_file.stat().st_size > 4096:
                raise HubReadError('Hub token unavailable')
            token = self.token_file.read_text().strip()
            if not token or '\n' in token or '\r' in token:
                raise HubReadError('Hub token unavailable')
            request = urllib.request.Request(self.base + '/v1/control/' + view + '?' + urllib.parse.urlencode(query),
                                             headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}, method='GET')
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise HubReadError('Hub response exceeded limit')
            result = json.loads(raw)
            return result, datetime.now(timezone.utc).isoformat()
        except (OSError, ValueError, urllib.error.URLError) as error:
            # Do not include paths, headers, response bodies, or credentials in errors.
            raise HubReadError('Hub read unavailable') from None


def read_views(reader, games=('ffxi', 'swtor')):
    """Project per-game roster and task-only learning reads; failures are isolated."""
    from r10_projection import project_learning, project_learning_attention
    result = {'bots': {}, 'learning': {}, 'issues': {}, 'gameStatus': {}, 'feeds': []}
    for game in games:
        for view in ('bots', 'learning', 'server-status'):
            try:
                data, fetched = reader.get(view, game)
                if view == 'bots':
                    if not isinstance(data, list):
                        raise ValueError('invalid roster')
                    rows = []
                    for row in data:
                        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k] for k in ('key', 'name')):
                            raise ValueError('invalid roster row')
                        def bounded(value, limit=128):
                            return value if isinstance(value, str) and 0 < len(value) <= limit and not any(ord(c) < 32 for c in value) else None
                        level = bounded(row.get('level'))
                        if level is not None and not re.fullmatch(r'[0-9]{1,4}', level):
                            level = None
                        rows.append({'id': f'live:{game}:{row["key"]}', 'name': row['name'], 'game': game.upper(),
                                     'character': bounded(row.get('character')), 'level': level, 'bodyKind': bounded(row.get('bodyKind')),
                                     'personalitySummary': bounded(row.get('summary'), 512),
                                     'status': 'Unknown', 'observedAt': None,
                                     'source': f'Hub roster (r10-shaped projection) · fetched {fetched} · registration is not presence'})
                    result['bots'][game] = rows
                elif view == 'learning':
                    rows = project_learning(data)
                    if data.get('gameId') != game:
                        raise ValueError('mismatched game')
                    for row in rows:
                        row['id'] = f'live:{game}:{row["id"]}'
                        row['game'] = game.upper()
                        row['source'] = f'Hub light learning tasks (r10-shaped projection) · fetched {fetched}'
                    result['learning'][game] = rows
                    result['issues'][game] = project_learning_attention(rows)
                else:
                    result['gameStatus'][game] = project_server_status(data, game, fetched)
                result['feeds'].append({'game': game.upper(), 'view': view, 'status': 'Live response', 'at': fetched,
                                        'note': {'learning': 'Light task list; curriculum and evidence omitted; deployed revision unverified', 'bots': 'Registration only; presence, coverage and deployed revision unverified', 'server-status': 'Stored settings snapshot; not server liveness; deployed revision unverified'}[view]})
            except (HubReadError, ValueError, TypeError, KeyError):
                result['feeds'].append({'game': game.upper(), 'view': view, 'status': 'Unavailable', 'at': None,
                                        'note': 'Synthetic fallback; no current hub data'})
    return result


def merge_views(snapshot, live):
    """Replace only successful game/view slices; leave explicit synthetic fallback elsewhere."""
    for game, bots in live['bots'].items():
        snapshot['bots'] = [b for b in snapshot['bots'] if b.get('game', '').lower() != game] + bots
    for game, learning in live['learning'].items():
        snapshot['learning'] = [r for r in snapshot['learning'] if r.get('game', '').lower() != game] + learning
        snapshot['issues'] = [i for i in snapshot['issues'] if not (i.get('learningId') and i.get('scope', '').lower() == game)] + live['issues'][game]
    for game, status in live.get('gameStatus', {}).items():
        snapshot['gameStatus'] = [s for s in snapshot['gameStatus'] if s.get('game', '').lower() != game] + [status]
    snapshot['hubFeeds'] = live['feeds']
    snapshot['mode'] = 'mixed' if live['bots'] or live['learning'] or live.get('gameStatus') else 'mock'
    return snapshot


def project_trace(data):
    """Keep bounded envelope metadata only; never expose the original body."""
    if not isinstance(data, list) or len(data) > 250:
        raise ValueError('invalid trace response')
    rows = []
    for record in data:
        if not isinstance(record, dict):
            raise ValueError('invalid envelope')
        kind, event_type = record.get('kind'), record.get('type')
        if not isinstance(kind, str) or not kind or not isinstance(event_type, str) or not event_type:
            raise ValueError('invalid envelope metadata')
        body = record.get('body')
        try:
            body = json.loads(body) if isinstance(body, str) else {}
        except ValueError:
            body = {}
        body = body if isinstance(body, dict) and kind.lower() == 'outcome' else {}
        def safe(value):
            return value if isinstance(value, str) and 0 < len(value) <= 128 else None
        rows.append({'kind': safe(kind), 'type': safe(event_type), 'occurredAt': safe(record.get('occurredAtUtc')),
                     'classification': safe(body.get('classification')), 'disposition': safe(body.get('disposition')),
                     'isFinal': body.get('isFinal') if type(body.get('isFinal')) is bool else None})
    return rows


def project_server_status(data, game, fetched):
    """Only a stored configuration snapshot, never an assertion of liveness."""
    if not isinstance(data, dict) or data.get('gameId') != game:
        raise ValueError('invalid game status scope')
    status = data.get('status')
    if status is not None and not isinstance(status, dict):
        raise ValueError('invalid game status')
    status = status or {}
    rate = status.get('xpRate')
    if type(rate) not in (int, float) or not math.isfinite(rate) or rate < 0:
        rate = None
    checked = status.get('checkedAtUtc')
    if not isinstance(checked, str) or len(checked) > 64:
        checked = None
    return {'game': game.upper(), 'xpRate': rate, 'checkedAt': checked,
            'source': f'Hub stored server settings (r10-shaped projection) · fetched {fetched}',
            'liveness': 'Unknown'}


def project_spend(data, fetched):
    """One hub's aggregate ledger; no provider, account or per-bot attribution."""
    if not isinstance(data, dict):
        raise ValueError('invalid spend response')
    configured = data.get('configured') if type(data.get('configured')) is bool else None
    readable = configured is True and not data.get('error')
    def money(field, requires_pricing=False):
        value = data.get(field)
        if not readable or (requires_pricing and data.get('pricingError')):
            return None
        return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None
    month = data.get('month')
    if not isinstance(month, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}', month):
        month = None
    return {'configured': configured, 'month': month, 'settledUsd': money('settledUsd'),
            'reservedOpenUsd': money('reservedOpenUsd'), 'budgetUsd': money('budgetUsd', True),
            'source': 'Single hub ledger (r10-shaped projection); revision and environment unverified',
            'fetchedAt': fetched, 'attribution': 'Not available per game, bot, party or call'}


def project_hub_health(data, fetched):
    """Project only FFXI/SWTOR service states; no paths, environment or logs."""
    if not isinstance(data, dict) or not isinstance(data.get('services'), list) or len(data['services']) > 500:
        raise ValueError('invalid health response')
    observed = data.get('utc')
    if not isinstance(observed, str) or len(observed) > 64:
        observed = None
    states = {'running', 'stopped', 'failed', 'restarting', 'degraded', 'missing', 'live', 'quiet', 'log', 'done'}
    rows = []
    for service in data['services']:
        if not isinstance(service, dict):
            raise ValueError('invalid health record')
        game = service.get('game')
        if not isinstance(game, str) or game.lower() not in ('ffxi', 'swtor'):
            continue
        label = service.get('label')
        if not isinstance(label, str) or not 0 < len(label) <= 128 or any(ord(c) < 32 for c in label):
            label = 'Unknown service'
        state = service.get('state')
        state = state if isinstance(state, str) and state in states else 'Unknown'
        rows.append({'game': game.upper(), 'label': label, 'state': state, 'observedAt': observed})
        if len(rows) >= 50:
            break
    return {'services': rows, 'fetchedAt': fetched,
            'coverage': 'FFXI/SWTOR services only; maximum 50 records. Service state does not establish bot presence or delivery.',
            'source': 'Hub service-health response (r10-shaped projection); revision unverified'}
