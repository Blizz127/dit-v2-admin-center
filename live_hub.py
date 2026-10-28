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
