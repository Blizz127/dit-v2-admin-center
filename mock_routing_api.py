"""In-process synthetic write-contract proposal; NOT an HTTP handler or hub API.

No sockets, storage, provider calls, credential handling or production imports.
Actor and allowed identities/models come from the test fixture, never the body.
"""
from copy import deepcopy
import json
import re
from threading import Lock

from mock_routing import BotKey, MockRouting

PATH = '/mock/v1/routing'
CONTRACT = 'dit-admin-mock-routing-v1'
MAX_BODY = 16 * 1024
MAX_REQUESTS = 256
TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}\Z')
FIELDS = {'contract', 'environment', 'requestId', 'expectedVersion', 'targets', 'model', 'reason'}
SCOPE = {'game', 'realm', 'nativeBot', 'purpose'}


def scope(key):
    return dict(game=key.game, realm=key.realm, nativeBot=key.native_bot, purpose=key.purpose)


def token(value):
    return isinstance(value, str) and TOKEN.fullmatch(value) is not None


def decode(body):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate field')
            result[key] = value
        return result

    def nonfinite(_value):
        raise ValueError('nonfinite')

    data = json.loads(body.decode('utf-8'), object_pairs_hook=unique, parse_constant=nonfinite)
    if not isinstance(data, dict) or set(data) != FIELDS:
        raise ValueError('fields')
    if data['contract'] != CONTRACT or data['environment'] != 'synthetic':
        raise ValueError('contract')
    if not token(data['requestId']) or not token(data['model']):
        raise ValueError('identity')
    if type(data['expectedVersion']) is not int or not 0 <= data['expectedVersion'] <= 2**53 - 1:
        raise ValueError('version')
    reason = data['reason']
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 256 or any(ord(c) < 32 or ord(c) == 127 for c in reason):
        raise ValueError('reason')
    targets = data['targets']
    if not isinstance(targets, list) or not 1 <= len(targets) <= 32:
        raise ValueError('targets')
    for target in targets:
        if not isinstance(target, dict) or set(target) != SCOPE or not all(token(value) for value in target.values()):
            raise ValueError('scope')
    keys = [BotKey(t['game'], t['realm'], t['nativeBot'], t['purpose']) for t in targets]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate target')
    return data, keys


class MockRoutingAPI:
    """Finite fixture lifetime; request IDs and state disappear with this object."""
    def __init__(self, fixture_keys, allowed_models, actor='synthetic-owner'):
        if not token(actor):
            raise ValueError('invalid fixture actor')
        self._store = MockRouting(fixture_keys, allowed_models)
        self._actor = actor
        self._requests = {}
        self._lock = Lock()

    @staticmethod
    def error(status, message):
        return status, {'kind': 'synthetic', 'error': message}

    def request(self, method, path, body=b''):
        if path != PATH:
            return self.error(404, 'unknown mock path')
        if method not in ('GET', 'POST'):
            return self.error(405, 'unsupported mock method')
        if not isinstance(body, bytes):
            return self.error(400, 'invalid mock body')
        if len(body) > MAX_BODY:
            return self.error(413, 'mock body too large')
        with self._lock:
            if method == 'GET':
                if body:
                    return self.error(400, 'mock read has no body')
                data = self._store.snapshot()
                return 200, {'kind': 'synthetic', 'contract': CONTRACT, 'version': data['version'],
                    'policies': [dict(scope=scope(key), model=model) for key, model in data['policies'].items()],
                    'audit': [dict(version=e['version'], actor=e['actor'], reason=e['reason'], at=e['at'],
                        changes=[dict(scope=scope(key), before=before, after=after) for key, before, after in e['changes']]) for e in data['audit']]}
            try:
                data, keys = decode(body)
            except (ValueError, UnicodeError, RecursionError):
                return self.error(400, 'invalid synthetic routing request')
            request_id = data['requestId']
            if request_id in self._requests:
                previous, response = self._requests[request_id]
                if data != previous:
                    return self.error(409, 'request ID reused with different content')
                return 200, deepcopy(response)
            if len(self._requests) >= MAX_REQUESTS:
                return self.error(429, 'mock request capacity reached')
            try:
                version = self._store.apply(keys, data['model'], data['expectedVersion'], self._actor, data['reason'])
            except ValueError as error:
                return self.error(409 if str(error) == 'stale version' else 422,
                                  'version conflict' if str(error) == 'stale version' else 'fixture scope or model not allowed')
            response = {'kind': 'synthetic', 'contract': CONTRACT, 'status': 'applied-synthetic',
                        'requestId': request_id, 'version': version, 'changedTargets': len(keys),
                        'liveEffect': False}
            self._requests[request_id] = (deepcopy(data), deepcopy(response))
            return 200, response
