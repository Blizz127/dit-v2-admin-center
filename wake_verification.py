"""Project an owning-lead supplied local receipt; never probe or control a game."""
from datetime import datetime, timezone
import json
import re

GAMES = ('wow-vanilla', 'wow-forever', 'firefall', 'eden', 'blacklight',
         'tabula-rasa', 'ffxi', 'war', 'enb', 'planetside', 'marvel-heroes', 'rose')
HELD = {'war', 'marvel-heroes'}
SCHEMA = 'dit-admin-wake-readback-v1'
LIMIT = 65536


def timestamp(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError('Invalid time')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('Timezone required')
    return result


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9._-]{1,96}', value) is not None


def project(data, now=None):
    result = {'schema': SCHEMA, 'coverage': 'No valid local cutover receipt', 'cutover': None, 'rows': [
        {'game': game, 'status': 'Held' if game in HELD else 'Unverified',
         'observedAt': None, 'receipt': None} for game in GAMES]}
    now = now or datetime.now(timezone.utc)
    try:
        cutover = data['cutover']
        at = timestamp(cutover['completedAt'])
        if (data['schema'] != SCHEMA or cutover['completed'] is not True
                or cutover['destination'] != 'banshee:8450' or at > now
                or not identifier(cutover['id']) or not identifier(cutover['receipt'])
                or not isinstance(data['games'], list) or len(data['games']) > 24):
            return result
        rows = data['games']
        result['coverage'] = 'Local owning-lead receipt; dated reported readbacks, not live observations'
        result['cutover'] = {'id': cutover['id'], 'destination': 'banshee:8450',
                             'completedAt': at.isoformat(), 'receipt': cutover['receipt']}
        for output in result['rows']:
            if output['game'] in HELD:
                continue  # A readback receipt cannot lift the retained owner hold.
            matches = [row for row in rows if isinstance(row, dict) and row.get('game') == output['game']]
            if len(matches) != 1:
                continue  # Exact canonical ID; duplicate claims are ambiguous.
            row = matches[0]
            try:
                observed = timestamp(row.get('observedAt'))
            except (ValueError, TypeError, OverflowError):
                continue
            if (row.get('cutoverId') == cutover['id'] and row.get('authenticated') is True
                    and row.get('result') == 'ready' and at <= observed <= now
                    and identifier(row.get('receipt'))):
                output.update(status='Verified readback (reported)', observedAt=observed.isoformat(),
                              receipt=row['receipt'])
    except (KeyError, TypeError, ValueError, OverflowError):
        return result
    return result


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate field')
            result[key] = value
        return result

    def reject(_value):
        raise ValueError('Invalid JSON number')

    try:
        with path.open('rb') as source:
            raw = source.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError('Receipt too large')
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=unique, parse_constant=reject)
        return project(data)
    except (OSError, ValueError, RecursionError):
        return project(None)  # No retained verified state or private error details.
