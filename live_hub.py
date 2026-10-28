"""Optional bounded read-only hub client; only an explicitly configured loopback tunnel."""
import json
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
        if view not in ('bots', 'learning') or not GAME.fullmatch(game):
            raise ValueError('Unsupported read')
        query = {'gameId': game}
        if view == 'learning':
            query.update({'light': 'true', 'tasksOnly': 'true'})
        return self._request(view, query)

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
    result = {'bots': {}, 'learning': {}, 'issues': {}, 'feeds': []}
    for game in games:
        for view in ('bots', 'learning'):
            try:
                data, fetched = reader.get(view, game)
                if view == 'bots':
                    if not isinstance(data, list):
                        raise ValueError('invalid roster')
                    rows = []
                    for row in data:
                        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k] for k in ('key', 'name')):
                            raise ValueError('invalid roster row')
                        rows.append({'id': f'live:{game}:{row["key"]}', 'name': row['name'], 'game': game.upper(),
                                     'status': 'Unknown', 'observedAt': None,
                                     'source': f'Hub roster (r10-shaped projection) · fetched {fetched} · registration is not presence'})
                    result['bots'][game] = rows
                else:
                    rows = project_learning(data)
                    if data.get('gameId') != game:
                        raise ValueError('mismatched game')
                    for row in rows:
                        row['id'] = f'live:{game}:{row["id"]}'
                        row['game'] = game.upper()
                        row['source'] = f'Hub light learning tasks (r10-shaped projection) · fetched {fetched}'
                    result['learning'][game] = rows
                    result['issues'][game] = project_learning_attention(rows)
                result['feeds'].append({'game': game.upper(), 'view': view, 'status': 'Live response', 'at': fetched,
                                        'note': 'Light task list; curriculum and evidence omitted; deployed revision unverified' if view == 'learning' else 'Registration only; presence, coverage and deployed revision unverified'})
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
    snapshot['hubFeeds'] = live['feeds']
    snapshot['mode'] = 'mixed' if live['bots'] or live['learning'] else 'mock'
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
        body = body if isinstance(body, dict) else {}
        def safe(value):
            return value if isinstance(value, str) and 0 < len(value) <= 128 else None
        rows.append({'kind': safe(kind), 'type': safe(event_type), 'occurredAt': safe(record.get('occurredAtUtc')),
                     'classification': safe(body.get('classification')), 'disposition': safe(body.get('disposition')),
                     'isFinal': body.get('isFinal') if type(body.get('isFinal')) is bool else None})
    return rows
