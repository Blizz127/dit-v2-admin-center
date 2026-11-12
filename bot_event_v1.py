"""Offline importer for dit.bot_event.v1, the DIT per-game bot observability envelope (BOT_BRAIN_STANDARD 6.3, 6.5).

Off unless DIT_BOT_EVENT_DIR names an absolute local directory of *.jsonl files, one row per line.
Non-recursive, files read in name order. Never opens a live path and never uses the network.
Producers: SWTOR bot-event exports, the hub's Forever owner-party driver, and any DIT game that
writes the envelope.

The schema pinned at commit ea92d35a is copied to tests/fixtures/bot-event-v1/ (see SOURCE.txt).
The checks here are written out explicitly, and the tests cross-check every constant against
that file, so a drift in either place fails.

Rules enforced here:
- Each row is checked against the schema's required fields, types, enums, length limits and
  patterns. A failing row is counted by a fixed reason code and omitted, never repaired.
- Stricter than the schema, by design: ts must be UTC millisecond form ending in Z and be a real
  date; integers must be JSON integers (1.0 is refused, and so is True); level is 0..255;
  session_seq is 0..2**63-1; an advice row must carry details (its outcome cannot be classified
  without them); death.details.recent_decisions, when present, must be a list of at most 8.
- A row whose details hold `text` or `chat_text` is refused. Free-form chat never enters the output.
- A chat row must carry details.channel, origin and voiced (6.6). A voiced row whose origin is not "ai" is refused
  as chat_voiced_not_ai (the AI-or-silence rule); any other origin must be voiced false with drop_reason NOT_AI.
  Each bot's output has chat totals: voiced, dropped, and drops by reason.
- Each bot's output has feel.cadence: the share of identical gaps between repeats of one decision action
  (human_feel.py); None with too few samples.
- Only the summary and the structured decision, death, advice and chat fields are returned, plus four
  labels when they fully match a strict pattern: details.actor_key (the bot's name), area_name, ability and
  discipline. Other details keys, including free-form ones, are never returned.
  The displayed area name must come from a row with the last observed area ID; an older area's name
  cannot label a newer area. Without any supplied area ID, a standalone area name keeps the ID unknown.
- A refused row with details.intent "chat", voiced false and a known drop_reason (SWTOR's shape for a dropped
  non-AI line) counts in the bot's chat drops.
- An error/LOG_DROPPED row exposes a safe nonnegative integer details.dropped as reportedDropped, or None
  when missing/invalid. Counts are per report, never summed or added to reader omissions; reports may overlap.
- Events, deaths and advice retain supplied correlation_id, target and session_seq. Login generation is
  projected as an exact decimal string because the accepted 64-bit range exceeds JavaScript's safe integers.
  These are record context, not identity joins, action verification or a life/death counter.
- Duplicate keys, NaN and Infinity are refused. Lines over MAX_LINE are refused unparsed.
- Symlinked files and directories are refused. Only regular files are opened, and a FIFO is never
  waited on. A refused file is skipped, and the other files still load.
- Limits: MAX_DIR_ENTRIES, MAX_FILES, MAX_FILE_BYTES, MAX_TOTAL_BYTES, MAX_LINE, MAX_ROWS. When a
  limit bites, the newest data is kept: the last MAX_FILES files by name, with the byte and row
  budgets spent newest file and newest line first. A file that does not fit the total byte budget ends the read,
  so the older files are not read either: only a contiguous newest run is kept. Files are named by date, so the
  oldest go. A file over MAX_FILE_BYTES is skipped as oversized whatever budget is left and does not end the read.
  A directory that mixes games is still capped by name order, so the games that sort last win.
- Output caps: MAX_BOTS bots (the most recently active), MAX_EVENTS events, MAX_ADVICE advice items
  and MAX_DEATHS deaths per bot.
- Errors carry fixed reason codes and never echo file content.

read(directory=None) returns (bots, coverage). With directory=None the env var is read; if it is
unset, bots is [] and coverage status is 'Off'. Nothing in this module raises.
"""
from datetime import datetime, timezone
import json
import math
import os
import re
import stat

import human_feel
from local_evidence import read_bytes

ENV = 'DIT_BOT_EVENT_DIR'
SCHEMA = 'dit.bot_event.v1'
SUFFIX = '.jsonl'
MAX_DIR_ENTRIES = 4096
MAX_FILES = 64
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_LINE = 64 * 1024
MAX_ROWS = 200000
MAX_BOTS = 500
MAX_EVENTS = 200
MAX_ADVICE = 50
MAX_DEATHS = 50
MAX_RECENT = 8
MAX_LEVEL = 255
MAX_SESSION = 2 ** 63 - 1
MAX_REPORTED_DROPPED = 2 ** 53 - 1  # Preserve exact numeric display in JavaScript.
MAX_OPTIONS = 16

# Schema values, copied from dit.bot_event.v1.schema.json. tests/test_bot_event_v1.py checks each one.
GAME_PATTERN = '[a-z0-9_]{2,32}'
EVENT_TYPE_PATTERN = '[a-z_]{2,32}'
GAME_RE = re.compile(GAME_PATTERN)
EVENT_TYPE_RE = re.compile(EVENT_TYPE_PATTERN)
TIME_RE = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]{3})Z')
REQUIRED = frozenset({'schema', 'game', 'actor_id', 'ts', 'event_type', 'severity'})
FIELDS = REQUIRED | {'session_seq', 'reason', 'summary', 'level', 'area', 'pos', 'quest_id', 'target',
                     'correlation_id', 'details'}
SEVERITIES = frozenset({0, 1, 2, 3})
LIMITS = {'actor_id': 64, 'reason': 64, 'summary': 255, 'area': 64, 'quest_id': 64, 'target': 64,
          'correlation_id': 128}
ADVICE_KINDS = frozenset({'goal', 'party_tactic', 'rotation_profile'})
ADVICE_ROUTES = frozenset({'cheap', 'planning', 'rules'})  # The schema also allows null.
ADVICE_OUTCOMES = frozenset({'applied', 'NO_ADVICE', 'TIMEOUT', 'INVALID_OPTION', 'STALE', 'REVALIDATE_FAIL'})
ADVICE_REQUIRED = frozenset({'kind', 'options', 'default_option', 'choice', 'outcome'})
ADVICE_OPTION_ID = 64
ADVICE_REASON = 160
FORBIDDEN_DETAILS = frozenset({'text', 'chat_text'})
CHAT_REQUIRED = frozenset({'channel', 'origin', 'voiced'})
CHAT_DROP_REASONS = frozenset({'NOT_AI', 'NO_REPLY_ID', 'STALE', 'FILTERED', 'NO_LISTENER'})  # The schema also allows null.
CHAT_CHANNEL = 32
CHAT_ORIGIN = 32
CHAT_ROUTE = 64
CHAT_AI = 'ai'
# Structured labels a writer may put in details. Each is returned only when it fully matches its pattern, so
# a free-form sentence can never pass as one. actor_key is the DIT actor key (6.6); the others are SWTOR's.
NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_' -]{0,31}")
AREA_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_' -]{0,63}")
TOKEN_RE = re.compile(r'[a-z0-9][a-z0-9_.:]{0,63}')
SHORT_TEXT = 64


class RowRefused(Exception):
    """A row failed one check. Carries a fixed reason code, never row content."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _need(ok, reason):
    if not ok:
        raise RowRefused(reason)


def _refuse(_):
    raise ValueError('non-finite number')


def _finite(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError('non-finite number')
    return value


def _unique(pairs):
    keys = [key for key, _ in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate key')
    return dict(pairs)


def _json(text):
    return json.loads(text, parse_constant=_refuse, parse_float=_finite, object_pairs_hook=_unique)


def _int(value, low, high):
    return type(value) is int and low <= value <= high


def _optional_int(value, low, high):
    return value is None or _int(value, low, high)


def _number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:  # An integer too large for a float is not a usable number.
        return False


def _text(value, limit, minimum=0):
    return isinstance(value, str) and minimum <= len(value) <= limit


def _optional_text(value, limit):
    return value is None or _text(value, limit)


def _bounded(value, limit):
    """A string kept for display when it is a bounded string, otherwise None."""
    return value if _text(value, limit) else None


def _label(value, pattern):
    """A details label kept for display when it fully matches its pattern, otherwise None."""
    return value if isinstance(value, str) and pattern.fullmatch(value) else None


def _moment(value):
    """Validate the schema's UTC ms 'Z' form and return the normalised string."""
    match = TIME_RE.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise RowRefused('invalid_ts')
    parts = [int(part) for part in match.groups()]
    try:
        datetime(*parts[:6], parts[6] * 1000, tzinfo=timezone.utc)
    except ValueError:
        raise RowRefused('invalid_ts') from None
    return value


def _pos(value):
    if value is None:
        return
    _need(isinstance(value, dict) and set(value) == {'x', 'y', 'z'}
          and all(_number(value[axis]) for axis in ('x', 'y', 'z')), 'invalid_pos')


def _advice(data, details):
    """Advice rows: the pinned details shape (BOT_BRAIN_STANDARD 6.5 rule 5), or RowRefused."""
    _need('details' in data, 'missing_details')
    _need(ADVICE_REQUIRED <= set(details), 'invalid_advice')
    kind, outcome, route = details['kind'], details['outcome'], details.get('route')
    _need(isinstance(kind, str) and kind in ADVICE_KINDS, 'invalid_advice')
    _need(_int(details['options'], 0, MAX_OPTIONS), 'invalid_advice')
    _need(_text(details['default_option'], ADVICE_OPTION_ID), 'invalid_advice')
    _need(_optional_text(details['choice'], ADVICE_OPTION_ID), 'invalid_advice')
    _need(_optional_text(details.get('reason'), ADVICE_REASON), 'invalid_advice')
    _need(route is None or (isinstance(route, str) and route in ADVICE_ROUTES), 'invalid_advice')
    _need(isinstance(outcome, str) and outcome in ADVICE_OUTCOMES, 'invalid_advice')
    _need(_text(data.get('correlation_id'), LIMITS['correlation_id']), 'invalid_correlation_id')
    return {'kind': kind, 'choice': details['choice'], 'outcome': outcome, 'reason': details.get('reason')}


def _chat(data, details):
    """Chat rows: the pinned details shape (BOT_BRAIN_STANDARD 6.6, AI or silence), or RowRefused.

    A voiced line whose origin is not "ai" breaks the owner's rule (no canned lines). It gets its own reason code,
    chat_voiced_not_ai, so the coverage shows it apart from a merely malformed row."""
    _need('details' in data, 'missing_details')
    _need(CHAT_REQUIRED <= set(details), 'invalid_chat')
    origin, voiced, drop = details['origin'], details['voiced'], details.get('drop_reason')
    _need(_text(details['channel'], CHAT_CHANNEL), 'invalid_chat')
    _need(_text(origin, CHAT_ORIGIN), 'invalid_chat')
    _need(_optional_text(details.get('route'), CHAT_ROUTE), 'invalid_chat')
    _need(type(voiced) is bool, 'invalid_chat')
    _need(drop is None or (isinstance(drop, str) and drop in CHAT_DROP_REASONS), 'invalid_chat')
    _need('correlation_id' not in data or isinstance(data['correlation_id'], str), 'invalid_correlation_id')
    if origin != CHAT_AI:
        _need(not voiced, 'chat_voiced_not_ai')
        _need(drop == 'NOT_AI', 'invalid_chat')
    return {'channel': details['channel'], 'voiced': voiced, 'dropReason': drop}


def _recent(items):
    """Recent decisions as {action, reason}. One malformed item empties the whole list, never a partial one."""
    parsed = []
    for item in items:
        if not isinstance(item, dict):
            return []
        action = item.get('action', item.get('intent'))
        if not _text(action, SHORT_TEXT, 1) or not _optional_text(item.get('reason'), LIMITS['reason']):
            return []
        parsed.append({'action': action, 'reason': item.get('reason')})
    return parsed


def _death(details):
    """(killer, recent_decisions) for a death row. The schema caps recent_decisions at 8 items."""
    recent = details.get('recent_decisions', [])
    _need(isinstance(recent, list) and len(recent) <= MAX_RECENT, 'invalid_death')
    killer = details.get('killer')
    if isinstance(killer, dict):
        killer = killer.get('name')
    return _bounded(killer, SHORT_TEXT), _recent(recent)


def _row(data):
    """One validated dit.bot_event.v1 row as the fields this module surfaces, or RowRefused."""
    if not isinstance(data, dict):
        raise RowRefused('not_object')
    if data.get('schema') != SCHEMA:
        raise RowRefused('not_bot_event')
    missing = sorted(REQUIRED - set(data))
    if missing:
        raise RowRefused('missing_' + missing[0])
    if set(data) - FIELDS:
        raise RowRefused('unknown_field')
    _need(isinstance(data['game'], str) and GAME_RE.fullmatch(data['game']) is not None, 'invalid_game')
    _need(_text(data['actor_id'], LIMITS['actor_id'], 1), 'invalid_actor_id')
    _moment(data['ts'])
    _need(_optional_int(data.get('session_seq'), 0, MAX_SESSION), 'invalid_session_seq')
    _need(isinstance(data['event_type'], str) and EVENT_TYPE_RE.fullmatch(data['event_type']) is not None,
          'invalid_event_type')
    _need(type(data['severity']) is int and data['severity'] in SEVERITIES, 'invalid_severity')
    _need(_optional_text(data.get('reason'), LIMITS['reason']), 'invalid_reason')
    _need(_optional_text(data.get('summary'), LIMITS['summary']), 'invalid_summary')
    _need(_optional_int(data.get('level'), 0, MAX_LEVEL), 'invalid_level')
    _need(_optional_text(data.get('area'), LIMITS['area']), 'invalid_area')
    _pos(data.get('pos'))
    _need(_optional_text(data.get('quest_id'), LIMITS['quest_id']), 'invalid_quest_id')
    _need(_optional_text(data.get('target'), LIMITS['target']), 'invalid_target')
    _need(_optional_text(data.get('correlation_id'), LIMITS['correlation_id']), 'invalid_correlation_id')
    details = data.get('details', {})
    _need(isinstance(details, dict), 'invalid_details')
    _need(not FORBIDDEN_DETAILS & set(details), 'forbidden_text')

    kind = data['event_type']
    action = _bounded(details.get('action'), SHORT_TEXT)
    if action is None:
        action = _bounded(details.get('intent'), SHORT_TEXT)
    result = _bounded(details.get('result'), SHORT_TEXT)
    advice = killer = chat = None
    recent = []
    if kind == 'advice':
        advice = _advice(data, details)
        action, result = advice['choice'], advice['outcome']
    elif kind == 'death':
        killer, recent = _death(details)
    elif kind == 'chat':
        chat = _chat(data, details)
        action, result = chat['channel'], 'voiced' if chat['voiced'] else (chat['dropReason'] or 'not_voiced')
    elif (kind == 'refused' and details.get('intent') == 'chat' and details.get('voiced') is False
          and isinstance(details.get('drop_reason'), str) and details['drop_reason'] in CHAT_DROP_REASONS):
        # SWTOR logs a dropped non-AI line as a refused row with intent chat; it counts as a chat drop.
        chat = {'channel': _bounded(details.get('channel'), CHAT_CHANNEL), 'voiced': False,
                'dropReason': details['drop_reason']}
    reported_dropped = details.get('dropped') if kind == 'error' and data.get('reason') == 'LOG_DROPPED' else None
    if not _int(reported_dropped, 0, MAX_REPORTED_DROPPED):
        reported_dropped = None
    return {'game': data['game'], 'actorId': data['actor_id'], 'ts': data['ts'], 'type': kind,
            'severity': data['severity'], 'reason': data.get('reason'), 'summary': data.get('summary'),
            'correlationId': data.get('correlation_id'), 'target': data.get('target'),
            'sessionSeq': str(data['session_seq']) if data.get('session_seq') is not None else None,
            'level': data.get('level'), 'area': data.get('area'), 'action': action, 'result': result,
            'advice': advice, 'killer': killer, 'recent': recent, 'chat': chat,
            'name': _label(details.get('actor_key'), NAME_RE), 'areaName': _label(details.get('area_name'), AREA_NAME_RE),
            'ability': _label(details.get('ability'), TOKEN_RE), 'discipline': _label(details.get('discipline'), TOKEN_RE),
            'reportedDropped': reported_dropped}


def _parse(line):
    if len(line) > MAX_LINE:
        raise RowRefused('oversized_line')
    try:
        data = _json(line.decode('utf-8'))
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise RowRefused('invalid_json') from None
    return _row(data)


def _project(key, entries):
    """One bot's output: events newest first (capped), counts over every kept row."""
    game, actor = key
    rows = [parsed for _, parsed in entries]
    counts = {}
    for row in rows:
        counts[row['type']] = counts.get(row['type'], 0) + 1
    newest = list(reversed(rows))
    decisions = [row for row in rows if row['type'] == 'decision']
    doing = None
    if decisions:
        doing = decisions[-1]['action'] or decisions[-1]['summary'] or None
        if decisions[-1]['action'] and decisions[-1]['ability']:
            doing = f"{decisions[-1]['action']} {decisions[-1]['ability']}"
    name = next((row['name'] for row in newest if row['name'] is not None), None)
    discipline = next((row['discipline'] for row in newest if row['discipline'] is not None), None)
    level = next((row['level'] for row in newest if row['level'] is not None), None)
    area = next((row['area'] for row in newest if row['area'] is not None), None)
    area_name = next((row['areaName'] for row in newest if row['area'] == area and row['areaName'] is not None), None)
    events = [{'ts': row['ts'], 'type': row['type'], 'severity': row['severity'], 'reason': row['reason'],
               'summary': row['summary'], 'action': row['action'], 'result': row['result'], 'ability': row['ability'],
               'correlationId': row['correlationId'], 'sessionSeq': row['sessionSeq'], 'target': row['target'],
               'reportedDropped': row['reportedDropped']}
              for row in newest[:MAX_EVENTS]]
    deaths = [{'ts': row['ts'], 'killer': row['killer'], 'recentDecisions': row['recent'],
               'correlationId': row['correlationId'], 'sessionSeq': row['sessionSeq'], 'target': row['target']}
              for row in newest if row['type'] == 'death'][:MAX_DEATHS]
    advice = [{'ts': row['ts'], 'kind': row['advice']['kind'], 'chosen': row['advice']['choice'],
               'correlationId': row['correlationId'], 'sessionSeq': row['sessionSeq'], 'target': row['target'],
               'outcome': row['advice']['outcome'], 'reason': row['advice']['reason']}
              for row in newest if row['type'] == 'advice'][:MAX_ADVICE]
    # Chat totals over every kept chat row: lines voiced, lines dropped, and the drops by reason. Never the text.
    chat = {'voiced': 0, 'dropped': 0, 'byReason': {}}
    for row in rows:
        if row['chat'] is None:
            continue
        if row['chat']['voiced']:
            chat['voiced'] += 1
        else:
            reason = row['chat']['dropReason'] or 'not_voiced'
            chat['dropped'] += 1
            chat['byReason'][reason] = chat['byReason'].get(reason, 0) + 1
    chat['byReason'] = dict(sorted(chat['byReason'].items()))
    # Human-feel cadence (human_feel.py): how many gaps between repeats of one decision action are identical.
    moments = {}
    for row in decisions:
        if row['action']:
            moments.setdefault(row['action'], []).append(datetime.strptime(row['ts'], '%Y-%m-%dT%H:%M:%S.%fZ'))
    feel = {'cadence': human_feel.cadence(moments)}
    return {'game': game, 'actorId': actor, 'lastEventAt': rows[-1]['ts'], 'level': level, 'area': area,
            'doing': doing, 'counts': counts, 'events': events, 'deaths': deaths, 'advice': advice, 'chat': chat,
            'feel': feel, 'name': name, 'areaName': area_name, 'discipline': discipline}


def _coverage(status, records, omitted, reason, files=0, games=(), span=(None, None), by_reason=None):
    return {'status': status, 'records': records, 'omitted': omitted, 'reason': reason, 'files': files,
            'games': sorted(games), 'from': span[0], 'to': span[1],
            'omittedByReason': dict(sorted((by_reason or {}).items()))}


def _off():
    return [], _coverage('Off', 0, 0, f'Set {ENV} to a local directory of dit.bot_event.v1 JSONL files to import it.')


def _unavailable(reason):
    return [], _coverage('Unavailable', 0, None, reason + '; nothing imported.')


class ListingTooLarge(Exception):
    """The directory holds more entries than MAX_DIR_ENTRIES."""


def _names(directory):
    names = []
    with os.scandir(directory) as entries:
        for index, entry in enumerate(entries):
            if index >= MAX_DIR_ENTRIES:
                raise ListingTooLarge()
            if entry.name.endswith(SUFFIX):
                names.append(entry.name)
    return sorted(names)


def _read(directory):
    if directory is None:
        directory = os.environ.get(ENV, '')
    if directory == '':
        return _off()
    if not isinstance(directory, str) or not os.path.isabs(directory):
        return _unavailable('Directory must be an absolute path string')
    try:
        info = os.lstat(directory)
    except (OSError, ValueError):
        return _unavailable('Directory cannot be read')
    if stat.S_ISLNK(info.st_mode):
        return _unavailable('Directory is a symbolic link and is refused')
    if not stat.S_ISDIR(info.st_mode):
        return _unavailable('Path is not a directory')
    try:
        names = _names(directory)
    except ListingTooLarge:
        return _unavailable('Directory has too many entries')
    except (OSError, ValueError):
        return _unavailable('Directory cannot be listed')

    total_found = len(names)
    refused = {}
    if total_found > MAX_FILES:
        # Names are date-stamped, so the last names are the newest files. The oldest are refused.
        refused['over the file limit'] = total_found - MAX_FILES
        names = names[-MAX_FILES:]
    by_reason, used, read_count, chunks = {}, 0, 0, []

    def omit(reason):
        by_reason[reason] = by_reason.get(reason, 0) + 1

    for index in reversed(range(len(names))):  # Newest file first, so the byte budget keeps the newest data.
        path = os.path.join(directory, names[index])
        try:
            info = os.lstat(path)
        except OSError:
            refused['unreadable'] = refused.get('unreadable', 0) + 1
            continue
        why = None
        if stat.S_ISLNK(info.st_mode):
            why = 'symlink'
        elif not stat.S_ISREG(info.st_mode):
            why = 'not a regular file'
        elif info.st_size > MAX_FILE_BYTES:
            # Too large for any budget: skipped as oversized, so it never ends the read for older files that fit.
            why = 'oversized'
        limit = min(MAX_FILE_BYTES, MAX_TOTAL_BYTES - used)
        if why is None and limit <= 0:
            why = 'over the total byte limit'
        if why == 'over the total byte limit':
            # The total budget ends the read at the first file that does not fit, so only a newest run is kept.
            # This file and every older one are counted as refused and left unread.
            refused[why] = refused.get(why, 0) + index + 1
            break
        if why is not None:
            refused[why] = refused.get(why, 0) + 1
            continue
        try:
            raw = read_bytes(path, limit)
        except (OSError, ValueError):
            refused['unreadable'] = refused.get('unreadable', 0) + 1
            continue
        if len(raw) > limit:
            if limit != MAX_FILE_BYTES:
                refused['over the total byte limit'] = refused.get('over the total byte limit', 0) + index + 1
                break
            refused['oversized'] = refused.get('oversized', 0) + 1
            continue
        used += len(raw)
        read_count += 1
        chunks.append((index, raw))

    rows, attempted = [], 0
    for index, raw in chunks:  # Newest file and newest line first, so the row limit drops the oldest rows.
        lines = raw.split(b'\n')
        for line_no in reversed(range(len(lines))):
            line = lines[line_no]
            if not line.strip():
                continue
            attempted += 1
            if attempted > MAX_ROWS:
                omit('row_limit')
                continue
            try:
                parsed = _parse(line)
            except RowRefused as error:
                omit(error.reason)
                continue
            except Exception:  # One row can never fail the whole import.
                omit('invalid_row')
                continue
            rows.append(((parsed['ts'], index, line_no), parsed))
    rows.sort(key=lambda item: item[0])
    groups = {}
    for key, parsed in rows:
        groups.setdefault((parsed['game'], parsed['actorId']), []).append((key, parsed))
    chosen = sorted(groups, key=lambda key: groups[key][-1][0], reverse=True)[:MAX_BOTS]
    bots = [_project(key, groups[key]) for key in sorted(chosen)]

    omitted = sum(by_reason.values())
    games = {parsed['game'] for _, parsed in rows}
    span = (rows[0][1]['ts'], rows[-1][1]['ts']) if rows else (None, None)
    parts = [f'Export directory read: {read_count} of {total_found} .jsonl file(s); an exported log, not live; '
             'timestamps are UTC.',
             f'{len(rows)} rows kept and {omitted} omitted, counted by reason; {len(groups)} bots with events, '
             f'showing {len(bots)}.']
    if refused:
        parts.append('Files refused: ' + ', '.join(f'{count} {why}' for why, count in sorted(refused.items())) + '.')
    if len(groups) > len(bots):
        parts.append(f'Showing the {len(bots)} most recently active of {len(groups)} bots.')
    loss_reports = sum(parsed['type'] == 'error' and parsed['reason'] == 'LOG_DROPPED' for _, parsed in rows)
    if loss_reports:
        parts.append(f'Producer-reported log loss: {loss_reports} LOG_DROPPED rows. '
                     'Counts are per report and may overlap; reader omissions are separate.')
    parts.append('Rows are checked against dit.bot_event.v1 (BOT_BRAIN_STANDARD 6.3, 6.5). Details beyond the '
                 'summary, decision, death, advice, chat, label and reported log-loss fields are not shown.')
    return bots, _coverage('Loaded', len(rows), omitted, ' '.join(parts), read_count, games, span, by_reason)


def read(directory=None):
    """(bots, coverage) for a directory of dit.bot_event.v1 JSONL files, or the env var's directory."""
    try:
        return _read(directory)
    except Exception:  # Callers render Unknown; no input may raise.
        return _unavailable('Import failed')
