"""Format: the 70450 predecessor Bots system's forever_botlog (bot, bot_event); PlayerbotV2 (70790) does not write it.

Offline import of an exported copy of the WoW Forever bot log (forever_botlog.bot_event).

Off unless DIT_FOREVER_BOTLOG_DIR names an absolute local directory holding
manifest.json, bots.jsonl and events.jsonl. Never opens a live database, never uses
the network. The Admin Center adopts Forever's log as its observability contract:
rows keep Forever's `bot` / `bot_event` column names, and the `details` shapes are the
ones pinned from Forever BotAI.cpp / BotEngine.cpp at fb754788894.

Rules enforced here:
- A malformed row is counted and omitted, never repaired. Duplicate JSON keys and
  NaN/Infinity are refused. Error text is fixed and never echoes file content.
- Event ids must be unique: every copy of a duplicated id is omitted.
- Bots with conflicting duplicate `bot` rows keep no identity (name/class/race/faction None).
- A `decision` or `death` row whose `details` do not match their pinned shape keeps its
  fixed columns; the structured part is Unknown: engine/trigger/action/band are the string
  "Unknown", numbers are None, alternatives and recentDecisions are empty, killer fields None.
- Timestamps without a zone (MySQL DATETIME) are read as UTC and normalised to ISO "Z".
"""
from datetime import datetime, timedelta, timezone
import json
import math
import os
import re
from pathlib import Path

from local_evidence import read_bytes

ENV = 'DIT_FOREVER_BOTLOG_DIR'
KIND = 'forever-botlog-export'
MANIFEST_LIMIT = 4 * 1024
BOTS_LIMIT = 1024 * 1024
EVENTS_LIMIT = 8 * 1024 * 1024
MAX_BOTS_LINES = 5000
MAX_EVENT_LINES = 50000
MAX_LINE = 64 * 1024
MAX_BOTS_SHOWN = 200
MAX_DECISIONS, MAX_DEATHS, MAX_QUESTS = 8, 3, 5
MAX_ALTERNATIVES = 64
MAX_FUTURE = timedelta(minutes=5)
MAX_ID = 2 ** 63 - 1

ENGINES = frozenset({'noncombat', 'combat', 'dead'})
FACTIONS = frozenset({'alliance', 'horde'})
QUEST_REASONS = frozenset({'QUEST_ACCEPTED', 'QUEST_PROGRESS', 'QUEST_COMPLETE',
                           'QUEST_REWARDED', 'QUEST_ABANDONED', 'QUEST_FAILED'})
REVISION = re.compile(r'[A-Za-z0-9._-]{1,64}')
MANIFEST_TIME = re.compile(r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{3}))?Z')
EVENT_TIME = re.compile(r'(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z?)')

BOT_REQUIRED = frozenset({'guid', 'name', 'class_id', 'race_id', 'faction'})
BOT_FIELDS = BOT_REQUIRED | {'first_seen'}
EVENT_REQUIRED = frozenset({'id', 'ts', 'bot_guid', 'event_type', 'severity'})
EVENT_INT_COLUMNS = ('level', 'map_id', 'zone_id', 'quest_id', 'target_entry', 'session_seq')
EVENT_POSITION_COLUMNS = ('pos_x', 'pos_y', 'pos_z')
# Generated columns of bot_event: accepted so an unedited export loads, never read.
GENERATED = frozenset({'killer_entry', 'killer_level', 'xp_amount', 'spell_id', 'outcome', 'lvl_diff', 'src'})
EVENT_FIELDS = (EVENT_REQUIRED | {'reason', 'summary', 'details'} | set(EVENT_INT_COLUMNS)
                | set(EVENT_POSITION_COLUMNS) | GENERATED)


class LogError(ValueError):
    """Fixed messages only; never echoes file contents."""


def _refuse(_):
    raise LogError('non-finite number')


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise LogError('non-finite number')
    return value


def _unique(pairs):
    if len({k for k, _ in pairs}) != len(pairs):
        raise LogError('duplicate key')
    return dict(pairs)


def _json(text):
    return json.loads(text, parse_constant=_refuse, parse_float=_finite_float, object_pairs_hook=_unique)


def _now():
    return datetime.now(timezone.utc)


def _int(value, low=0, high=MAX_ID):
    return type(value) is int and low <= value <= high


def _number(value):
    try:
        return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:  # An integer too large for a float is not a usable number.
        return False


def _text(value, limit, minimum=0):
    return isinstance(value, str) and minimum <= len(value) <= limit


def _stamp(match):
    """(datetime, normalised ISO 'Z' string) from an EVENT_TIME/MANIFEST_TIME match, or LogError."""
    parts = match.groups()
    fraction = parts[6]
    try:
        moment = datetime(*(int(p) for p in parts[:6]), int(fraction.ljust(6, '0')) if fraction else 0,
                          tzinfo=timezone.utc)
    except ValueError:
        raise LogError('invalid time') from None
    iso = moment.strftime('%Y-%m-%dT%H:%M:%S') + ('.' + fraction if fraction else '') + 'Z'
    return moment, iso


def _event_time(value):
    match = EVENT_TIME.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise LogError('invalid time')
    if (value[10] == 'T') != bool(match.group(8)):  # ISO form needs its Z; the DATETIME form has none.
        raise LogError('invalid time')
    return _stamp(match)


def manifest(data):
    fields = {'kind', 'version', 'exportedAtUtc'}
    if not isinstance(data, dict) or not fields <= set(data) <= fields | {'sourceRevision'}:
        raise LogError('unsupported manifest')
    if data['kind'] != KIND or type(data['version']) is not int or data['version'] != 1:
        raise LogError('unsupported manifest')
    match = MANIFEST_TIME.fullmatch(data['exportedAtUtc']) if isinstance(data['exportedAtUtc'], str) else None
    if match is None:
        raise LogError('invalid export time')
    exported, iso = _stamp(match)
    if exported > _now() + MAX_FUTURE:
        raise LogError('export time is in the future')
    revision = data.get('sourceRevision')
    if 'sourceRevision' in data and (not isinstance(revision, str) or not REVISION.fullmatch(revision)):
        raise LogError('invalid source revision')
    return {'exportedAt': iso, 'sourceRevision': revision}


def bot(data):
    if not isinstance(data, dict) or not BOT_REQUIRED <= set(data) <= BOT_FIELDS:
        raise LogError('unexpected bot fields')
    if not _int(data['guid']) or not _text(data['name'], 24, 1) or not _int(data['class_id'], 0, 255) \
            or not _int(data['race_id'], 0, 255) \
            or not isinstance(data['faction'], str) or data['faction'] not in FACTIONS:
        raise LogError('invalid bot')
    if 'first_seen' in data:
        _event_time(data['first_seen'])
    return {'guid': data['guid'], 'name': data['name'], 'classId': data['class_id'],
            'raceId': data['race_id'], 'faction': data['faction']}


def event(data):
    if not isinstance(data, dict) or not EVENT_REQUIRED <= set(data) <= EVENT_FIELDS:
        raise LogError('unexpected event fields')
    if not _int(data['id']) or not _int(data['bot_guid']) or not _text(data['event_type'], 32, 1) \
            or not _int(data['severity'], 0, 3):
        raise LogError('invalid event')
    moment, iso = _event_time(data['ts'])
    for field, limit in (('reason', 64), ('summary', 255)):
        value = data.get(field)
        if value is not None and not _text(value, limit):
            raise LogError('invalid ' + field)
    columns = {}
    for field in EVENT_INT_COLUMNS:
        value = data.get(field)
        if value is not None and not _int(value, 0, 255 if field == 'level' else MAX_ID):
            raise LogError('invalid ' + field)
        columns[field] = value
    for field in EVENT_POSITION_COLUMNS:
        value = data.get(field)
        if value is not None and not _number(value):
            raise LogError('invalid ' + field)
    details = data.get('details')
    if isinstance(details, str):
        if len(details) > MAX_LINE:
            raise LogError('invalid details')
        try:
            details = _json(details)
        except (ValueError, RecursionError):
            raise LogError('invalid details') from None
        if not isinstance(details, dict):  # A string must hold an object; "null" is not one.
            raise LogError('invalid details')
    if details is not None and not isinstance(details, dict):
        raise LogError('invalid details')
    return {'id': data['id'], 'moment': moment, 'ts': iso, 'guid': data['bot_guid'],
            'type': data['event_type'], 'severity': data['severity'], 'reason': data.get('reason'),
            'summary': data.get('summary'), 'level': columns['level'], 'zoneId': columns['zone_id'],
            'questId': columns['quest_id'], 'details': details}


def _decision(details):
    """The pinned decision shape, or None (structure Unknown)."""
    if details is None or not isinstance(details.get('engine'), str) or details['engine'] not in ENGINES:
        return None
    for key in ('trigger', 'action', 'band'):
        if not _text(details.get(key), 128, 1):
            return None
    if not _number(details.get('relevance')) or not _number(details.get('effective')):
        return None
    alternatives = details.get('alternatives')
    if not isinstance(alternatives, list) or len(alternatives) > MAX_ALTERNATIVES:
        return None
    parsed = []
    for alternative in alternatives:
        if not isinstance(alternative, dict) or not _text(alternative.get('action'), 128, 1) \
                or not _number(alternative.get('relevance')) or not _text(alternative.get('result'), 64, 1):
            return None
        parsed.append({'action': alternative['action'], 'relevance': alternative['relevance'],
                       'result': alternative['result']})
    if 'detail' in details and not isinstance(details['detail'], dict):
        return None
    return {'engine': details['engine'], 'trigger': details['trigger'], 'action': details['action'],
            'relevance': details['relevance'], 'band': details['band'], 'effective': details['effective'],
            'alternatives': parsed}


def _killer(details):
    killer = None if details is None else details.get('killer')
    if not isinstance(killer, dict):
        return None, None, None
    values = [killer.get(key) for key in ('entry', 'level', 'lvl_diff')]
    if any(value is not None and not _int(value, -MAX_ID, MAX_ID) for value in values):
        return None, None, None
    return tuple(values)


def _recent(details):
    recent = None if details is None else details.get('recent_decisions')
    if not isinstance(recent, list) or len(recent) > MAX_ALTERNATIVES:
        return []
    parsed = []
    for item in recent:
        if not isinstance(item, dict) or not _int(item.get('ms_ago')) or not _text(item.get('action'), 128, 1) \
                or not _text(item.get('reason'), 128):
            return []  # One bad element makes the whole list Unknown; never keep a partial history.
        parsed.append({'msAgo': item['ms_ago'], 'action': item['action'], 'reason': item['reason']})
    return parsed


def _engine_change(details):
    """The 'to' engine of an engine state_change; 'Unknown' if the row does not name a valid one."""
    to = None if details is None else details.get('to')
    return to if isinstance(to, str) and to in ENGINES else 'Unknown'


def _project(guid, rows, identity):
    rows = sorted(rows, key=lambda r: (r['moment'], r['id']))
    counts = {}
    for row in rows:
        counts[row['type']] = counts.get(row['type'], 0) + 1
    decisions, deaths, quests = [], [], []
    last_change = last_decision_engine = None
    for row in rows:
        kind, details = row['type'], row['details']
        if kind == 'decision':
            parsed = _decision(details)
            decisions.append((row, parsed))
            if parsed is not None:
                last_decision_engine = parsed['engine']
        elif kind == 'death':
            deaths.append(row)
        elif kind == 'quest' and row['reason'] in QUEST_REASONS:
            quests.append(row)
        elif kind == 'state_change' and details is not None and details.get('kind') == 'engine':
            last_change = _engine_change(details)
    engine = last_change or last_decision_engine or 'Unknown'
    doing = 'Unknown'
    if decisions:
        row, parsed = decisions[-1]
        if row['summary']:
            doing = row['summary']
        elif parsed is not None:
            doing = f"{parsed['action']} via {parsed['trigger']}"
    latest = rows[-1]
    level = next((r['level'] for r in reversed(rows) if r['level'] is not None), None)
    zone = next((r['zoneId'] for r in reversed(rows) if r['zoneId'] is not None), None)
    shown_decisions = []
    for row, parsed in reversed(decisions[-MAX_DECISIONS:]):
        base = parsed or {'engine': 'Unknown', 'trigger': 'Unknown', 'action': 'Unknown', 'relevance': None,
                          'band': 'Unknown', 'effective': None, 'alternatives': []}
        shown_decisions.append({'ts': row['ts'], 'engine': base['engine'], 'trigger': base['trigger'],
                                'action': base['action'], 'reason': row['reason'], 'relevance': base['relevance'],
                                'band': base['band'], 'effective': base['effective'],
                                'alternatives': base['alternatives']})
    shown_deaths = []
    for row in reversed(deaths[-MAX_DEATHS:]):
        entry, killer_level, gap = _killer(row['details'])
        shown_deaths.append({'ts': row['ts'], 'reason': row['reason'], 'summary': row['summary'],
                             'killerEntry': entry, 'killerLevel': killer_level, 'levelGap': gap,
                             'recentDecisions': _recent(row['details'])})
    return {'botGuid': str(guid), 'name': identity['name'], 'classId': identity['classId'],
            'raceId': identity['raceId'], 'faction': identity['faction'], 'engine': engine,
            'lastEventAt': latest['ts'], 'level': level, 'zoneId': zone, 'doing': doing,
            'decisions': shown_decisions, 'deaths': shown_deaths,
            'quests': [{'ts': r['ts'], 'reason': r['reason'], 'questId': r['questId'], 'summary': r['summary']}
                       for r in reversed(quests[-MAX_QUESTS:])],
            'counts': counts}


def _unavailable(reason):
    return [], {'status': 'Unavailable', 'records': 0, 'omitted': None, 'reason': reason + '; nothing imported.'}


def _lines(raw, limit, field):
    lines = [line for line in raw.split(b'\n') if line.strip()]
    if len(lines) > limit:
        raise LogError('too many ' + field)
    return lines


def _rows(lines, parse):
    rows, omitted = [], 0
    for line in lines:
        try:
            if len(line) > MAX_LINE:
                raise LogError('oversized row')
            rows.append(parse(_json(line.decode('utf-8'))))
        except (LogError, UnicodeDecodeError, ValueError, RecursionError):
            omitted += 1
    return rows, omitted


def load(directory):
    root = Path(directory)
    if not root.is_absolute():
        return _unavailable('Export directory must be an absolute path')
    try:
        raw = read_bytes(root / 'manifest.json', MANIFEST_LIMIT)
        if len(raw) > MANIFEST_LIMIT:
            raise LogError('oversized manifest')
        meta = manifest(_json(raw.decode('utf-8')))
        raw = read_bytes(root / 'bots.jsonl', BOTS_LIMIT)
        if len(raw) > BOTS_LIMIT:
            raise LogError('oversized bots')
        bot_lines = _lines(raw, MAX_BOTS_LINES, 'bots')
        raw = read_bytes(root / 'events.jsonl', EVENTS_LIMIT)
        if len(raw) > EVENTS_LIMIT:
            raise LogError('oversized events')
        event_lines = _lines(raw, MAX_EVENT_LINES, 'events')
    except LogError as error:
        return _unavailable(f'Export unreadable ({error})')
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as error:
        return _unavailable(f'Export unreadable ({type(error).__name__})')
    bot_rows, bots_omitted = _rows(bot_lines, bot)
    identities, ambiguous = {}, set()
    for row in bot_rows:
        known = identities.setdefault(row['guid'], row)
        if known != row:
            ambiguous.add(row['guid'])
    rows, events_omitted = _rows(event_lines, event)
    seen = {}
    for row in rows:
        seen[row['id']] = seen.get(row['id'], 0) + 1
    kept = [row for row in rows if seen[row['id']] == 1]
    duplicate_omitted = len(rows) - len(kept)
    by_bot = {}
    for row in kept:
        by_bot.setdefault(row['guid'], []).append(row)
    nameless = {'name': None, 'classId': None, 'raceId': None, 'faction': None}
    # Most recently active first (stable, so ties keep ascending guid order); only the shown bots are projected.
    order = sorted(by_bot)
    order.sort(key=lambda guid: max((r['moment'], r['id']) for r in by_bot[guid]), reverse=True)
    shown = [_project(guid, by_bot[guid], identities[guid] if guid in identities and guid not in ambiguous else nameless)
             for guid in order[:MAX_BOTS_SHOWN]]
    omitted = bots_omitted + events_omitted + duplicate_omitted
    revision = f"source revision {meta['sourceRevision']}" if meta['sourceRevision'] else 'source revision not reported'
    notes = []
    if len(by_bot) > len(shown):
        notes.append(f'Showing the {len(shown)} most recently active of {len(by_bot)} bots.')
    clash = sorted(guid for guid in by_bot if guid in ambiguous)
    if clash:
        notes.append(f'{len(clash)} bot guid(s) have conflicting rows in bots.jsonl; their identity is withheld.')
    if duplicate_omitted:
        notes.append(f'{duplicate_omitted} event rows share an id with another row and were all omitted.')
    return shown, {'status': 'Loaded', 'records': len(kept), 'omitted': omitted,
                   'reason': ' '.join([
                       f"Forever bot log export taken {meta['exportedAt']} ({revision}): an exported log, not live; "
                       'timestamps are read as UTC.',
                       f'{len(by_bot)} bots with events; {len(kept)} event rows retained and {omitted} omitted '
                       f'(malformed, duplicate id or unknown field; {bots_omitted} of them bot rows).',
                       "Rows follow Forever's log shape (bot, bot_event); decision and death structure is shown "
                       'only where it matches the pinned shape, otherwise Unknown.'] + notes)}


def from_env(environ=None):
    directory = (os.environ if environ is None else environ).get(ENV)
    if not directory:
        return [], {'status': 'Not configured', 'records': 0, 'omitted': 0,
                    'reason': f"Set {ENV} to a local exported Forever bot log directory to import it."}
    return load(directory)
