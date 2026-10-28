"""In-memory synthetic routing exercise; never connected to the web server or hub.

This is an offline example, not a hub contract, authorization layer, or audit system.
"""
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class BotKey:
    game: str
    realm: str
    native_bot: str
    purpose: str


class MockRouting:
    def __init__(self, verified_keys, allowed_models):
        self._keys = frozenset(verified_keys)
        self._models = frozenset(allowed_models)
        self._policies = {}
        self._version = 0
        self._audit = []
        self._lock = Lock()

    def snapshot(self):
        with self._lock:
            return {'version': self._version, 'policies': dict(self._policies), 'audit': list(self._audit)}

    def apply(self, keys, model, expected_version, actor, reason):
        """Atomically update explicit fixture keys, once, with compare-and-set."""
        with self._lock:
            keys = tuple(keys)
            if type(expected_version) is not int or expected_version != self._version:
                raise ValueError('stale version')
            if not keys or len(set(keys)) != len(keys) or any(key not in self._keys for key in keys):
                raise ValueError('unknown or duplicate synthetic bot identity')
            if model not in self._models or not isinstance(actor, str) or not actor.strip() or not isinstance(reason, str) or not reason.strip():
                raise ValueError('model, actor, and reason must be supplied')
            before = {key: self._policies.get(key) for key in keys}
            self._version += 1
            for key in keys:
                self._policies[key] = model
            self._audit.append({'version': self._version, 'actor': actor, 'reason': reason,
                                'changes': tuple((key, before[key], model) for key in keys)})
            return self._version
