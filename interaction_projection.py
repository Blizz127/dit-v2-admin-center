"""Minimal read-only projection of candidate e8c81be's interaction snapshot.

No roster joins: its scoped actor keys are not a verified native roster identity.
Raw orders, receipts, requesters and message content are deliberately omitted.
"""
import math

ACTIVITIES = {'unknown', 'idle', 'walking', 'traveling', 'fighting', 'leveling', 'resting',
              'crafting', 'gathering', 'fishing', 'questing', 'shopping', 'following', 'waiting'}


def _text(value, limit=128):
    return value if isinstance(value, str) and 0 < len(value) <= limit and not any(ord(c) < 32 for c in value) else None


def _boolean(value):
    return value if type(value) is bool else None


def _number(value):
    return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None


def project_interaction(data, fetched):
    if not isinstance(data, dict) or not isinstance(data.get('scopes'), list) or len(data['scopes']) > 50:
        raise ValueError('invalid interaction response')
    switches = data.get('switches')
    if not isinstance(switches, dict):
        raise ValueError('missing interaction switches')
    switches = {key: _boolean(switches.get(key)) for key in ('contract', 'naturalOrders', 'selfClaims')}
    rows, identities, count = [], set(), 0
    for scope in data['scopes']:
        if not isinstance(scope, dict) or not isinstance(scope.get('bots'), list):
            raise ValueError('invalid interaction scope')
        count += len(scope['bots'])
        if count > 50:
            raise ValueError('interaction limit exceeded')
        if scope.get('gameId') != 'ffxi':
            continue
        caller, instance = _text(scope.get('caller')), _text(scope.get('serverInstanceId'))
        if caller is None or instance is None:
            raise ValueError('missing interaction identity')
        for bot in scope['bots']:
            if not isinstance(bot, dict) or _text(bot.get('actorKey')) is None:
                raise ValueError('invalid interaction bot')
            identity = (caller, instance, bot['actorKey'])
            if identity in identities:
                raise ValueError('ambiguous interaction actor')
            identities.add(identity)
            fresh, snapshot_fresh = _boolean(bot.get('fresh')), _boolean(bot.get('snapshotFresh'))
            enabled = switches['contract'] is True
            # Treat reported activity as unknown unless the hub explicitly certifies a current view.
            reported_activity = _text(bot.get('activity'))
            activity = reported_activity if enabled and fresh is True and reported_activity in ACTIVITIES else None
            rows.append({'actorKey': bot['actorKey'], 'caller': caller, 'serverInstanceId': instance,
                         'fresh': fresh if enabled else None, 'snapshotFresh': snapshot_fresh if enabled else None,
                         'activity': activity, 'observedAt': _text(bot.get('observedAtUtc'), 64),
                         'ageSeconds': _number(bot.get('ageSeconds')),
                         'source': bot.get('source') if bot.get('source') in ('native snapshot', 'native report', 'no state yet') else None})
    if switches['contract'] is not True:
        rows = []  # Disabled or unknown collection must never masquerade as a current bot inventory.
    return {'switches': switches, 'freshForSeconds': _number(data.get('freshForSeconds')),
            'truncated': _boolean(data.get('truncated')), 'bots': rows, 'fetchedAt': fetched,
            'coverage': 'Candidate FFXI interaction view; at most 50 hub bots, deployed revision unverified. No roster identity join or delivery inference.'}
