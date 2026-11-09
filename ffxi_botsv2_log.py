"""Offline import of the FFXI regular-LSB Bots V2 log: exported [BOTS-V2] lines, c2.7 and later.

Off unless DIT_FFXI_BOTSV2_LOG names an absolute local file holding an exported log. Never reads a live
server log, never uses the network, never writes. Line shapes follow the frozen c2.7 and c2.8 Lua format
strings (banshee_bots_v2*.lua, banshee_bots_v2_exec.lua). Anything that is not one of those shapes is counted,
never guessed.

Rules enforced here:
- Only lines with the [BOTS-V2] marker are bot lines; other lines are ignored and counted.
- A line of a known shape that fails strict validation is omitted and counted. A line of an unknown shape is
  unrecognized and counted. Neither is repaired, and neither is echoed.
- A 'repeated N times' tail stands for N+1 occurrences: the printed line itself plus the N held repeats the
  producer suppressed. The per-bot counts add N+1; the event's repeated field keeps N (a plain line keeps 1).
- counts.stuck counts 'stuck' lines. A trip end tagged why=stuck is counted as tripEnd and keeps its reason.
- revived lines are events only; they are not in any count.
- c2.9 order lines ('order <bot> verb=... by=... channel=...') count as party, like the older form. by= must be the
  masked owner; a focusheal arg that is not '<owner>' is shown as '<member>'. levelsync lines are events counted as
  other.
- counts.mount counts 'mount <bot> why=' lines; dismount lines are events only; mount_blocked counts as other.
- P2b: an order line may end ' refused=<why>' (event result 'refused', still counted as party); 'advice <bot> release
  kind=party_tactic' lines are events only.
- C4.3/V2-Q1.1 (frozen, not live): 'group party' members/drop/off, 'slow eval', 'progression' and 'roe' lines count
  as other; a members line goes to every member and must start with its leader.
- C5 (frozen): 'bag full <bot> free=<n> (camping on, no sell path)' counts as other; group trip ends use why=group_<why>.
- J0a/J0b: profile lines count as other; advice answers count as advice (applied or not; the event result says
  which); requests are events only; a drop counts as other, and 'advice - drop' (no bot) is a system notice.
- counts.rest counts rest starts ('rest <bot> why=...'); a 'rest end' line is an event only.
- Lua's '%%' escape is unescaped to '%'. Output is printable ASCII; any other line is omitted.
- The owner is '<owner>' only. A line that names anyone else in an owner or speaker role is omitted, so no
  human name reaches the output.
- Timestamps (MM/DD/YY HH:MM:SS:mmm) are read as UTC and emitted as ISO 8601 with a Z suffix.
"""
import os
import re
from datetime import datetime, timezone

from local_evidence import read_bytes

ENV = 'DIT_FFXI_BOTSV2_LOG'
GAME = 'ffxi-lsb'
MARKER = '[BOTS-V2]'
MAX_BYTES = 8 * 1024 * 1024
MAX_LINES = 100000
MAX_LINE = 4096
MAX_DETAIL = 200
MAX_BOTS = 200
MAX_EVENTS = 200
MAX_REFUSALS = 50
MAX_DEATHS = 50
OWNER = '<owner>'
COUNT_KEYS = ('ok', 'refused', 'defend', 'tripStart', 'tripEnd', 'noTrip', 'stuck', 'dead', 'release', 'return',
              'weak', 'rest', 'mount', 'advice', 'party', 'other')

_BOT = r'([A-Za-z][A-Za-z0-9_]{0,23})'
_BOT_NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,23}')
_KV = re.compile(r'([A-Za-z][A-Za-z0-9_]{0,31})=(\S{1,128})')
_STAMP = re.compile(r'\[(\d{2})/(\d{2})/(\d{2}) (\d{2}):(\d{2}):(\d{2}):(\d{3})\]'
                    r'(?:\[[^\[\]\s]{1,32}\])*\s*\[BOTS-V2\]\s+(\S.*)')
_LUA_SUFFIX = re.compile(r' \(lua_print:\d{1,6}\)$')
_REPEAT = re.compile(r' \(repeated (\d{1,6}) times?(?: in the last \d{1,6}s)?\)$')


class _Malformed(ValueError):
    """A line of a known shape that fails validation: omitted and counted, never repaired."""


_SYSTEM = tuple(re.compile(pattern) for pattern in (
    r'on: tick host registered for \d{1,4} zone\(s\): .+',
    r'party chat orders wired( .*)?',
    r'tell orders wired( .*)?',
    r'off \(BANSHEE_BOTS_V2=0\): .+',
    r'tick host live in zone \d{1,6}',
    r'levelsync off: entity:levelRestriction is not bound \(gated off\)',
    r'mount_gate off: entity:botMount is not bound \(gated off\)',
    r'subjob off: entity:getSubLvl is not readable \(gated off\)',
    r'advice off: banshee_bots_v2_advice\.lua is not installed \(gated off\)',
    r'zone \d{1,6} has no known script name: no host',
    r'BANSHEE_BOTS_V2_ACTORS=all is refused in increment 1; .+',
    r'field_excursion is on without the V2 ownership skip \(fieldExcursionV2Aware unset\): V2 drives nothing',
    r'zone tick failed safely in .+: .+',
))
_BUDGET = re.compile(r'budget \d{1,6}s: windows=\d+ evals=\d+ deferred=\d+ maxMs=-?\d+\.\d+ avgMs=-?\d+\.\d+ '
                     r'budgetMs=-?\d+\.\d+')


def _clip(text):
    return text[:MAX_DETAIL]


def _part(bots, kind, count=None, rule=None, apl=None, op=None, result=None, reason=None, detail='',
          char=None, zone=None):
    # kind is the record category (bot lines carry bots; budget and system lines carry none); type is the event kind.
    return {'kind': 'bot' if bots else kind, 'bots': bots, 'type': kind, 'count': count, 'rule': rule, 'apl': apl,
            'op': op,
            'result': result, 'reason': reason, 'detail': _clip(detail), 'char': char, 'zone': zone}


def _bot(token):
    if token == 'nil' or not _BOT_NAME.fullmatch(token):
        raise _Malformed('bot name')
    return token


def _num(token):
    if token == 'nil':
        return None
    if not token.isdigit() or len(token) > 12:
        raise _Malformed('number')
    return int(token)


def _pairs(tokens):
    pairs = {}
    for token in tokens:
        match = _KV.fullmatch(token)
        if match is None or match.group(1) in pairs:
            raise _Malformed('key=value')
        pairs[match.group(1)] = match.group(2)
    return pairs


def _owner(token):
    if token != OWNER:
        raise _Malformed('owner must be masked')


def _act(body):
    head, separator, right = body.partition(' -> ')
    words = head.split(' ')
    parts = right.split()
    if not separator or len(words) < 4 or words[0] != 'act' or len(parts) < 2 or parts[0] not in ('ok', 'refused'):
        raise _Malformed('act')
    bot = _bot(words[1])
    fields = _pairs(words[2:])
    if 'rule' not in fields or 'op' not in fields:
        raise _Malformed('act fields')
    apl = fields.get('apl')
    detail = ' '.join([f'{k}={v}' for k, v in fields.items() if k not in ('rule', 'apl', 'op')] + parts[2:])
    return _part([bot], 'act', count=parts[0], rule=fields['rule'], apl=None if apl in (None, '-') else apl,
                 op=fields['op'], result=parts[0], reason=parts[1], detail=detail)


_DEFEND = re.compile(r'defend ' + _BOT + r' hp=(-?\d{1,3})pct attacker=(.+?) why=(\S+)')


def _defend(body):
    match = _DEFEND.fullmatch(body)
    if match is None:
        raise _Malformed('defend')
    hp = int(match.group(2))
    if not -1 <= hp <= 100:
        raise _Malformed('hp')
    return _part([_bot(match.group(1))], 'defend', count='defend', reason=match.group(4),
                 detail=f'hp={hp}pct attacker={match.group(3)}')


_TRIP_START = re.compile(r'trip start group (\S+) camp=(\S+)( \(attached on its first pick\))?')


def _trip_start(body):
    match = _TRIP_START.fullmatch(body)
    if match is None:
        raise _Malformed('trip start')
    bots = [_bot(name) for name in match.group(1).split('+')]
    if len(set(bots)) != len(bots):
        raise _Malformed('duplicate group member')
    detail = f"group={'+'.join(bots)} camp={match.group(2)}" + (' attached' if match.group(3) else '')
    return _part(bots, 'tripStart', count='tripStart', detail=detail)


_TRIP_END = re.compile(r'trip end ' + _BOT + r' camp=(\S+) (\S+)->(\S+) zone=(\S+) why=(\S+)')


def _trip_end(body):
    match = _TRIP_END.fullmatch(body)
    if match is None:
        raise _Malformed('trip end')
    detail = f'camp={match.group(2)} {match.group(3)}->{match.group(4)} zone={match.group(5)}'
    return _part([_bot(match.group(1))], 'tripEnd', count='tripEnd', reason=match.group(6), detail=detail,
                 zone=_num(match.group(5)))


_NO_TRIP = re.compile(r'no trip ' + _BOT + r' why=(\S+) zone=(\S+)')


def _no_trip(body):
    match = _NO_TRIP.fullmatch(body)
    if match is None:
        raise _Malformed('no trip')
    return _part([_bot(match.group(1))], 'noTrip', count='noTrip', reason=match.group(2),
                 detail=f'zone={match.group(3)}', zone=_num(match.group(3)))


_OWNS = re.compile(r'owns ' + _BOT + r' charid=(\S+) zone=(\S+)')


def _owns(body):
    match = _OWNS.fullmatch(body)
    if match is None:
        raise _Malformed('owns')
    return _part([_bot(match.group(1))], 'owns', count='other',
                 detail=f'charid={match.group(2)} zone={match.group(3)}',
                 char=_num(match.group(2)), zone=_num(match.group(3)))


_ZONE_DANGER = re.compile(r'zone danger ' + _BOT + r' zone=(\d{1,6}) lv=(\S+) aggro=(\S+) median=(\S+) '
                          r'night=(true|false): (\S.*)')


def _zone_danger(body):
    match = _ZONE_DANGER.fullmatch(body)
    if match is None:
        raise _Malformed('zone danger')
    zone = match.group(2)
    detail = (f'zone={zone} lv={match.group(3)} aggro={match.group(4)} median={match.group(5)} '
              f'night={match.group(6)}: {match.group(7)}')
    return _part([_bot(match.group(1))], 'zone', count='other', detail=detail, zone=int(zone))


_STUCK_RESOLVED = re.compile(r'stuck ' + _BOT + r' resolved (\S.*?) after (\d{1,6})s attempts=(\d{1,6})')
_STUCK_WAITING = re.compile(r'stuck ' + _BOT + r' waiting: human in view \((\d{1,4}) min, no teleport while seen\)')
_STUCK_HOMEPOINT = re.compile(r'stuck ' + _BOT + r' homepoint gave no move \(3 accepted\), left as is')
_STUCK_UNRESOLVED = re.compile(r'stuck ' + _BOT + r' unresolved zone=(\d{1,6}|nil) at \(([-0-9.]{1,16}), '
                               r'([-0-9.]{1,16})\) humans_in_view=(\d{1,4})')


def _stuck(body):
    """The four c2.7/c2.8 stuck shapes. The reason is a fixed code: the first word of 'resolved <why>', or a code
    for the free-text messages. Any other stuck text is malformed and omitted."""
    match = _STUCK_RESOLVED.fullmatch(body)
    if match:
        why = match.group(2)
        return _part([_bot(match.group(1))], 'stuck', count='stuck', reason=why.split()[0],
                     detail=f'resolved {why} after {match.group(3)}s attempts={match.group(4)}')
    match = _STUCK_WAITING.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'stuck', count='stuck', reason='human_in_view',
                     detail=f'waiting: human in view {match.group(2)} min, no teleport while seen')
    match = _STUCK_HOMEPOINT.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'stuck', count='stuck', reason='homepoint_no_move',
                     detail='homepoint gave no move (3 accepted), left as is')
    match = _STUCK_UNRESOLVED.fullmatch(body)
    if match:
        zone = _num(match.group(2))
        return _part([_bot(match.group(1))], 'stuck', count='stuck', reason='unresolved',
                     detail=f'unresolved zone={match.group(2)} humans_in_view={match.group(5)}', zone=zone)
    raise _Malformed('stuck')


_ORDER = re.compile(r'order ([a-z_]{1,32}) from (\S+) -> ' + _BOT)
# c2.9 (banshee_bots_v2.lua:1426): 'order %s verb=%s%s by=%s channel=%s', the middle %s being '' or ' arg=<arg>'.
# P2b (banshee_bots_v2.lua:1683) adds an optional ' refused=<why>' suffix; spaces in the arg are logged as '_'.
_ORDER_C29 = re.compile(r'order ' + _BOT + r' verb=([a-z_]{1,32})(?: arg=(\S{1,64}))? by=(\S+) channel=([a-z_]{1,16})'
                        r'(?: refused=([a-z_]{1,32}))?')
# focusheal's arg is a party member's name, which may be a human: only the masked owner is shown.
_NAME_ARG_VERBS = frozenset({'focusheal'})


def _order(body):
    match = _ORDER.fullmatch(body)
    if match:
        _owner(match.group(2))
        return _part([_bot(match.group(3))], 'party', count='party', reason=match.group(1), detail=f'from={OWNER}')
    match = _ORDER_C29.fullmatch(body)
    if match is None:
        raise _Malformed('order')
    _owner(match.group(4))
    verb, arg = match.group(2), match.group(3)
    if arg is not None and verb in _NAME_ARG_VERBS and arg not in (OWNER, 'off'):
        arg = '<member>'
    detail = (f'arg={arg} ' if arg is not None else '') + f'by={OWNER} channel={match.group(5)}'
    refused = match.group(6)
    if refused is not None:
        detail += f' refused={refused}'
    return _part([_bot(match.group(1))], 'party', count='party', reason=verb,
                 result='refused' if refused is not None else None, detail=detail)


# c2.9 level sync (banshee_bots_v2.lua and exec E.revertSync). Events only, counted as other.
_LEVELSYNC_ON = re.compile(r'levelsync ' + _BOT + r' to=(\d{1,3}) from=(\d{1,3})')
_LEVELSYNC_EXTERNAL = re.compile(r'levelsync ' + _BOT + r' off why=external cur=(-?\d{1,3})')
_LEVELSYNC_OFF = re.compile(r'levelsync ' + _BOT + r' off why=([a-z_]{1,32})')


def _levelsync(body):
    match = _LEVELSYNC_ON.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'levelsync', count='other', reason='on',
                     detail=f'to={match.group(2)} from={match.group(3)}')
    match = _LEVELSYNC_EXTERNAL.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'levelsync', count='other', reason='off_external',
                     detail=f'cur={match.group(2)}')
    match = _LEVELSYNC_OFF.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'levelsync', count='other', reason='off', detail=f'why={match.group(2)}')
    raise _Malformed('levelsync')


_NOT_HOSTED = re.compile(r'owned bot ' + _BOT + r' is in zone (\d{1,6}), which has no V2 tick host: not driven')


def _not_hosted(body):
    match = _NOT_HOSTED.fullmatch(body)
    if match is None:
        raise _Malformed('not hosted')
    return _part([_bot(match.group(1))], 'notHosted', count='other', reason='no_tick_host',
                 detail=f'zone={match.group(2)}', zone=int(match.group(2)))


_REFUSE = re.compile(r'refuse ' + _BOT + r': (\S.*) \(never driven by V2\)')


def _refuse(body):
    match = _REFUSE.fullmatch(body)
    if match is None:
        raise _Malformed('refuse')
    return _part([_bot(match.group(1))], 'refuse', count='other', reason='never_driven',
                 detail=f'why={match.group(2)}')


_OWNER_LEFT = re.compile(_BOT + r': owner (\S+) left zone (\d{1,6}) for (\d{1,6})( \(exit unknown: waits\))?')


def _owner_left(body):
    match = _OWNER_LEFT.fullmatch(body)
    if match is None:
        raise _Malformed('owner left')
    _owner(match.group(2))
    detail = f'owner={OWNER} zone={match.group(3)} to={match.group(4)}'
    if match.group(5):
        detail += ' exit unknown, waits'
    return _part([_bot(match.group(1))], 'party', count='party', reason='owner_left_zone', detail=detail)


_OWNED_BY = re.compile(_BOT + r' owned by (\S+) \(joined their party\)')


def _owned_by(body):
    match = _OWNED_BY.fullmatch(body)
    if match is None:
        raise _Malformed('owned by')
    _owner(match.group(2))
    return _part([_bot(match.group(1))], 'party', count='party', reason='joined_party', detail=f'owner={OWNER}')


_OWNERSHIP = re.compile(_BOT + r' ownership by (\S+) ended: (\S.*)')
_OWNERSHIP_WHY = re.compile(r'[a-z_]{1,32}|dismissed by <owner>')


def _ownership_ended(body):
    match = _OWNERSHIP.fullmatch(body)
    if match is None or _OWNERSHIP_WHY.fullmatch(match.group(3)) is None:
        raise _Malformed('ownership ended')
    _owner(match.group(2))
    return _part([_bot(match.group(1))], 'party', count='party', reason='ownership_ended',
                 detail=f'owner={OWNER} why={match.group(3)}')


_FOLLOWED = re.compile(_BOT + r' followed its owner into zone (\d{1,6})')


def _followed(body):
    match = _FOLLOWED.fullmatch(body)
    if match is None:
        raise _Malformed('followed')
    return _part([_bot(match.group(1))], 'party', count='party', reason='followed_owner',
                 detail=f'zone={match.group(2)}')


_NOT_DRIVEN = re.compile(_BOT + r' not driven: (\S.*)')


def _not_driven(body):
    match = _NOT_DRIVEN.fullmatch(body)
    if match is None:
        raise _Malformed('not driven')
    return _part([_bot(match.group(1))], 'notDriven', count='other', reason='not_driven', detail=match.group(2))


_EVAL_FAILED = re.compile(_BOT + r' evaluation failed safely: (\S.*)')


def _eval_failed(body):
    match = _EVAL_FAILED.fullmatch(body)
    if match is None:
        raise _Malformed('evaluation failed')
    return _part([_bot(match.group(1))], 'error', count='other', reason='evaluation_failed',
                 detail=match.group(2))


_DEAD_END = re.compile(_BOT + r': dead end on (\S+) leg (\S+) at \(([-0-9., ]+)\): blackspot \((\d{1,6})\)')


def _dead_end(body):
    match = _DEAD_END.fullmatch(body)
    if match is None:
        raise _Malformed('dead end')
    detail = f'camp={match.group(2)} leg={match.group(3)} blackspot={match.group(5)}'
    return _part([_bot(match.group(1))], 'deadEnd', count='other', reason='dead_end', detail=detail)


# c2.8 kinds. Each regex is the exact producer format string (banshee_bots_v2.lua, c2.8), with %s/%d as \S/digits
# and Lua's tostring(nil) as 'nil'. Anything else in these heads is malformed and omitted.
_DEAD = re.compile(r'dead ' + _BOT + r' wait_raise=(\d{1,6}) raisers=(\d{1,3}) zone=(\d{1,6}|nil)')
_RELEASE = re.compile(r'release ' + _BOT + r' why=(\S+) zone=(\d{1,6}|nil) after (\d{1,6})s')
_WEAK = re.compile(r'weak ' + _BOT + r' resting')
_RETURN_GAVE_UP = re.compile(r'return ' + _BOT + r' gave up why=(\S+) after (\d{1,6})s')
_RETURN_ARRIVED = re.compile(r'return ' + _BOT + r' arrived zone=(\d{1,6}) after (\d{1,6})s')
_RETURN_OWNER = re.compile(r'return ' + _BOT + r' to owner zone=(\d{1,6}) from=(\d{1,6})')
_REVIVED = re.compile(r'revived ' + _BOT + r' (at its home point|raised) zone=(\d{1,6}|nil) after (\d{1,6})s')


def _dead(body):
    match = _DEAD.fullmatch(body)
    if match is None:
        raise _Malformed('dead')
    detail = f'wait_raise={match.group(2)} raisers={match.group(3)} zone={match.group(4)}'
    return _part([_bot(match.group(1))], 'dead', count='dead', detail=detail, zone=_num(match.group(4)))


def _release(body):
    match = _RELEASE.fullmatch(body)
    if match is None:
        raise _Malformed('release')
    why = None if match.group(2) == 'nil' else match.group(2)
    detail = f'zone={match.group(3)} after={match.group(4)}s'
    return _part([_bot(match.group(1))], 'release', count='release', reason=why, detail=detail,
                 zone=_num(match.group(3)))


def _weak(body):
    match = _WEAK.fullmatch(body)
    if match is None:
        raise _Malformed('weak')
    return _part([_bot(match.group(1))], 'weak', count='weak', detail='resting')


def _return(body):
    match = _RETURN_GAVE_UP.fullmatch(body)
    if match:
        why = None if match.group(2) == 'nil' else match.group(2)
        return _part([_bot(match.group(1))], 'return', count='return', reason=why,
                     detail=f'gave up after={match.group(3)}s')
    match = _RETURN_ARRIVED.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'return', count='return', reason='arrived',
                     detail=f'zone={match.group(2)} after={match.group(3)}s', zone=int(match.group(2)))
    match = _RETURN_OWNER.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'return', count='return', reason='to_owner',
                     detail=f'zone={match.group(2)} from={match.group(3)}', zone=int(match.group(2)))
    raise _Malformed('return')


def _revived(body):
    match = _REVIVED.fullmatch(body)
    if match is None:
        raise _Malformed('revived')
    reason = 'home_point' if match.group(2).startswith('at its') else 'raised'
    return _part([_bot(match.group(1))], 'revived', reason=reason,
                 detail=f'zone={match.group(3)} after={match.group(4)}s', zone=_num(match.group(3)))


_REST_START = re.compile(r'rest ' + _BOT + r' why=(\S+) mp=(-?\d{1,3}) hp=(-?\d{1,3})')
_REST_END = re.compile(r'rest end ' + _BOT + r' mp=(-?\d{1,3}) hp=(-?\d{1,3}) why=(\S+)')


def _rest(body):
    # c2.8 V.restLog: 'rest %s why=%s mp=%d hp=%d' and 'rest end %s mp=%d hp=%d why=%s'. The shapes cannot both match.
    match = _REST_START.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'rest', count='rest', reason=match.group(2),
                     detail=f'mp={match.group(3)} hp={match.group(4)}')
    match = _REST_END.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'restEnd', reason=match.group(4),
                     detail=f'mp={match.group(2)} hp={match.group(3)}')
    raise _Malformed('rest')


# c2.10 mounts (banshee_bots_v2_exec.lua:59/300/309, banshee_bots_v2.lua:780/803/814).
_MOUNT = re.compile(r'(mount|dismount) ' + _BOT + r' why=([a-z_]{1,32})')
_MOUNT_BLOCKED = re.compile(r'mount_blocked ' + _BOT + r' why=([a-z_]{1,32}) ki=(\d{1,6}) \(V2 grants none\)')


def _mount(body):
    match = _MOUNT.fullmatch(body)
    if match is None:
        raise _Malformed('mount')
    mounting = match.group(1) == 'mount'
    return _part([_bot(match.group(2))], 'mount' if mounting else 'dismount', count='mount' if mounting else None,
                 reason=match.group(3))


def _mount_blocked(body):
    match = _MOUNT_BLOCKED.fullmatch(body)
    if match is None:
        raise _Malformed('mount blocked')
    return _part([_bot(match.group(1))], 'mountBlocked', count='other', reason=match.group(2),
                 detail=f'ki={match.group(3)}')


# J0a profile line (banshee_bots_v2.lua:849) and J0b advice seam (banshee_bots_v2_advice.lua:97-199).
_PROFILE = re.compile(r'profile ' + _BOT + r' to=(\S{1,64}) from=(\S{1,64}) why=([a-z_]{1,32})')
_ADVICE_REQ = re.compile(r'advice ' + _BOT + r' req kind=([a-z_]{1,32}) id=(\S{1,128}) options=(\d{1,3}) default=(\S{1,64})')
_ADVICE_ANSWER = re.compile(r'advice ' + _BOT + r' answer kind=([a-z_]{1,32}) choice=(\S{1,64}) applied=(yes|no) '
                            r'why=([a-z_0-9]{1,32})')
_ADVICE_RELEASE = re.compile(r'advice ' + _BOT + r' release kind=(party_tactic) choice=(\S{1,64}) why=(ttl|replaced)')
_ADVICE_DROP = re.compile(r'advice (?:-|' + _BOT + r') drop why=(unknown_id|bad_choice|expired|cap)')


def _profile(body):
    match = _PROFILE.fullmatch(body)
    if match is None:
        raise _Malformed('profile')
    return _part([_bot(match.group(1))], 'profile', count='other', reason=match.group(4),
                 detail=f'to={match.group(2)} from={match.group(3)}')


def _advice(body):
    # Requests are events; each answer counts as advice (applied or not); a drop counts as other, or is a
    # bot-less system notice when the key is '-'.
    match = _ADVICE_REQ.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'adviceRequest', reason=match.group(2),
                     detail=f'id={match.group(3)} options={match.group(4)} default={match.group(5)}')
    match = _ADVICE_ANSWER.fullmatch(body)
    if match:
        applied = match.group(4) == 'yes'
        return _part([_bot(match.group(1))], 'advice', count='advice', reason=match.group(5),
                     result='applied' if applied else 'not_applied',
                     detail=f'kind={match.group(2)} choice={match.group(3)} applied={match.group(4)}')
    match = _ADVICE_RELEASE.fullmatch(body)
    if match:
        # P2b (banshee_bots_v2_advice.lua:276): a party_tactic choice raised by this bot ends.
        return _part([_bot(match.group(1))], 'adviceRelease', reason=match.group(4),
                     detail=f'kind={match.group(2)} choice={match.group(3)}')
    match = _ADVICE_DROP.fullmatch(body)
    if match:
        if match.group(1) is None:
            return _part([], 'system')
        return _part([_bot(match.group(1))], 'adviceDrop', count='other', reason=match.group(2))
    raise _Malformed('advice')


_GP_MEMBERS = re.compile(r'group party ' + _BOT + r' members=(\S{1,160})')
_GP_DROP = re.compile(r'group party ' + _BOT + r' drop ' + _BOT + r' why=([a-z_]{1,32})')
_GP_OFF = re.compile(r'group party ' + _BOT + r' off why=([a-z_]{1,32})')


def _group_party(body):
    # C4 trip parties (ffxi C4.3 banshee_bots_v2.lua:1612/1629/1654/1774): bots in one real FFXI party.
    match = _GP_MEMBERS.fullmatch(body)
    if match:
        leader = _bot(match.group(1))
        bots = [_bot(name) for name in match.group(2).split('+')]
        if len(bots) < 2 or bots[0] != leader or len(set(bots)) != len(bots):
            raise _Malformed('group party members')
        return _part(bots, 'groupParty', count='other', reason='formed', detail=f"members={'+'.join(bots)}")
    match = _GP_DROP.fullmatch(body)
    if match:
        leader = _bot(match.group(1))
        return _part([_bot(match.group(2))], 'groupPartyDrop', count='other', reason=match.group(3),
                     detail=f'leader={leader}')
    match = _GP_OFF.fullmatch(body)
    if match:
        return _part([_bot(match.group(1))], 'groupPartyOff', count='other', reason=match.group(2))
    raise _Malformed('group party')


_SLOW_EVAL = re.compile(r'slow eval ' + _BOT + r' rule=([a-z_0-9]{1,32}) tier=([a-z_0-9]{1,16}) wallMs=(\d{1,7}\.\d\d)'
                        r' cpuMs=(\d{1,7}\.\d\d|n/a) atomic=(yes|no) heapKB=(\d{1,9})->(\d{1,9})')


def _slow_eval(body):
    # C4.3 diagnostic (banshee_bots_v2.lua:1884): one evaluation over BANSHEE_BOTS_V2_SLOW_EVAL_MS, at most 1 per 10 s.
    match = _SLOW_EVAL.fullmatch(body)
    if match is None:
        raise _Malformed('slow eval')
    return _part([_bot(match.group(1))], 'slowEval', count='other', reason=match.group(2),
                 detail=f'tier={match.group(3)} wallMs={match.group(4)} cpuMs={match.group(5)} atomic={match.group(6)} '
                        f'heapKB={match.group(7)}->{match.group(8)}')


_PROGRESSION = re.compile(r'progression ' + _BOT + r' level=(\d{1,3}) why=(levelup|spawn|periodic)'
                          r' -> (ok|refused ([a-z_]{1,40}))')
_ROE = re.compile(r'roe ' + _BOT + r' record=(\d{1,6}) -> (ok|refused)')


def _progression(body):
    # V2-Q1.1 (banshee_bots_v2.lua:608/1517), dark unless BANSHEE_BOTS_V2_PROGRESSION=1.
    match = _PROGRESSION.fullmatch(body)
    if match is None:
        raise _Malformed('progression')
    refused = match.group(5)
    return _part([_bot(match.group(1))], 'progression', count='other', result='refused' if refused else 'ok',
                 reason=match.group(3), detail=f'level={match.group(2)}' + (f' refused={refused}' if refused else ''))


def _roe(body):
    # V2-Q1.1 (banshee_bots_v2.lua:619): Records of Eminence step; the introduction also logs record=1.
    match = _ROE.fullmatch(body)
    if match is None:
        raise _Malformed('roe')
    return _part([_bot(match.group(1))], 'roe', count='other', result=match.group(3), detail=f'record={match.group(2)}')


_BAG_FULL = re.compile(r'bag full ' + _BOT + r' free=(\d{1,3}) \(camping on, no sell path\)')


def _bag_full(body):
    # C5 (banshee_bots_v2.lua:797): once per trip, the bot camps on with a full bag instead of riding home.
    match = _BAG_FULL.fullmatch(body)
    if match is None:
        raise _Malformed('bag full')
    return _part([_bot(match.group(1))], 'bagFull', count='other', reason='camping_on', detail=f'free={match.group(2)}')


def _budget(body):
    if _BUDGET.fullmatch(body) is None:
        raise _Malformed('budget')
    return _part([], 'budget')


# (head, parser): the head only chooses a parser; the parser's fullmatch decides whether the line is that shape.
_RULES = (
    (re.compile(r'act '), _act),
    (re.compile(r'defend '), _defend),
    (re.compile(r'trip start group '), _trip_start),
    (re.compile(r'trip end '), _trip_end),
    (re.compile(r'no trip '), _no_trip),
    (re.compile(r'owns '), _owns),
    (re.compile(r'zone danger '), _zone_danger),
    (re.compile(r'stuck '), _stuck),
    (re.compile(r'order '), _order),
    (re.compile(r'levelsync (?!off: )'), _levelsync),
    (re.compile(r'owned bot '), _not_hosted),
    (re.compile(r'refuse '), _refuse),
    (re.compile(r'\S+: owner '), _owner_left),
    (re.compile(r'\S+ owned by '), _owned_by),
    (re.compile(r'\S+ ownership by '), _ownership_ended),
    (re.compile(r'\S+ followed its owner '), _followed),
    (re.compile(r'\S+ not driven: '), _not_driven),
    (re.compile(r'\S+ evaluation failed safely: '), _eval_failed),
    (re.compile(r'\S+: dead end on '), _dead_end),
    (re.compile(r'dead '), _dead),
    (re.compile(r'release '), _release),
    (re.compile(r'weak '), _weak),
    (re.compile(r'return '), _return),
    (re.compile(r'revived '), _revived),
    (re.compile(r'rest '), _rest),
    (re.compile(r'(?:mount|dismount) '), _mount),
    (re.compile(r'mount_blocked '), _mount_blocked),
    (re.compile(r'profile '), _profile),
    (re.compile(r'advice (?!off: )'), _advice),
    (re.compile(r'budget '), _budget),
    (re.compile(r'group party '), _group_party),
    (re.compile(r'slow eval '), _slow_eval),
    (re.compile(r'progression '), _progression),
    (re.compile(r'roe '), _roe),
    (re.compile(r'bag full '), _bag_full),
)


def _classify(body):
    """Part dict for a known shape, None when the line is of no known shape. Raises _Malformed for a known shape
    that fails validation."""
    for pattern in _SYSTEM:
        if pattern.fullmatch(body):
            return _part([], 'system')
    for head, parse in _RULES:
        if head.match(body):
            return parse(body)
    return None


def _tails(body):
    """Strip the Lua print suffix, then a repeated-count tail. Returns (body, held): held is N for a tail, else 0."""
    body = _LUA_SUFFIX.sub('', body, count=1)
    held = 0
    match = _REPEAT.search(body)
    if match:
        held = int(match.group(1))
        if held < 1:
            raise _Malformed('repeated')
        body = body[:match.start()]
    return body, held


def _stamp(groups):
    month, day, year, hour, minute, second, millis = (int(part) for part in groups)
    moment = datetime(2000 + year, month, day, hour, minute, second, millis * 1000, tzinfo=timezone.utc)
    return moment, f'{moment:%Y-%m-%dT%H:%M:%S}.{millis:03d}Z'


def _line(raw, lineno):
    """(status, record). status is 'record', 'ignored', 'unrecognized' or 'omitted'. Never raises."""
    if MARKER.encode('ascii') not in raw:
        return 'ignored', None
    try:
        if len(raw) > MAX_LINE:
            raise _Malformed('oversized line')
        text = raw.decode('ascii')
        if not text.isprintable():
            raise _Malformed('control character')
        match = _STAMP.fullmatch(text)
        if match is None:
            raise _Malformed('line shape')
        moment, ts = _stamp(match.groups()[:7])
        body, held = _tails(match.group(8).replace('%%', '%'))
        part = _classify(body)
    except Exception:  # Any failure omits the one line; no bad input may raise or echo.
        return 'omitted', None
    if part is None:
        return 'unrecognized', None
    # A tail line is the printed occurrence plus its held repeats; 'repeated' keeps N (1 for a plain line).
    return 'record', {'lineno': lineno, 'moment': moment, 'ts': ts, 'repeated': held or 1,
                      'occurrences': held + 1, **part}


def _split(raw):
    if not raw:
        return []
    lines = raw.split(b'\n')
    if raw.endswith(b'\n'):
        lines.pop()
    return [line[:-1] if line.endswith(b'\r') else line for line in lines]


def _project(records):
    """Per-bot state from the records in (moment, line) order, newest first on output."""
    bots = {}
    for record in sorted(records, key=lambda r: (r['moment'], r['lineno'])):
        for name in record['bots']:
            key = name.lower()
            state = bots.get(key)
            if state is None:
                state = bots[key] = {'name': name, 'charId': None, 'zoneId': None,
                                     'counts': dict.fromkeys(COUNT_KEYS, 0), 'events': []}
            state['events'].append({'ts': record['ts'], 'type': record['type'], 'rule': record['rule'],
                                    'apl': record['apl'], 'op': record['op'], 'result': record['result'],
                                    'reason': record['reason'], 'detail': record['detail'],
                                    'repeated': record['repeated']})
            if record['count']:
                state['counts'][record['count']] += record['occurrences']
            if record['char'] is not None:
                state['charId'] = record['char']
            if record['zone'] is not None:
                state['zoneId'] = record['zone']
    shown = []
    for key in sorted(bots)[:MAX_BOTS]:
        state = bots[key]
        events = state['events']
        last = events[-1]
        if last['type'] == 'act':
            doing = f"{last['rule']} {last['op']}"
        else:
            doing = last['type'] if not last['reason'] else f"{last['type']} {last['reason']}"
        newest = list(reversed(events))
        shown.append({'game': GAME, 'actorId': key, 'name': state['name'], 'charId': state['charId'],
                      'zoneId': state['zoneId'], 'lastEventAt': last['ts'], 'doing': doing,
                      'counts': state['counts'], 'events': newest[:MAX_EVENTS],
                      'refusals': [e for e in newest if e['result'] == 'refused'][:MAX_REFUSALS],
                      'deaths': [e for e in newest if e['type'] == 'dead'][:MAX_DEATHS]})
    return shown, len(bots)


def _unavailable(reason):
    return [], {'status': 'Unavailable', 'records': 0, 'omitted': None,
                'reason': f'Bots V2 log unreadable ({reason}); nothing imported.', 'from': None, 'to': None,
                'unrecognized': None, 'ignored': None, 'budget': None, 'system': None}


def _off():
    return [], {'status': 'Off', 'records': 0, 'omitted': 0,
                'reason': f'Set {ENV} to a local exported FFXI Bots V2 log file to import it.', 'from': None,
                'to': None, 'unrecognized': 0, 'ignored': 0, 'budget': 0, 'system': 0}


def _read(path):
    if path is None:
        path = os.environ.get(ENV, '')
        if not path:
            return _off()
    try:
        text = os.fspath(path)
    except TypeError:
        return _unavailable('path must be a file path')
    if not isinstance(text, str) or not os.path.isabs(text):
        return _unavailable('path must be an absolute local file')
    if os.path.islink(text):
        return _unavailable('symlink refused')
    try:
        raw = read_bytes(text, MAX_BYTES)
    except FileNotFoundError:
        return _unavailable('missing file')
    except OSError:
        return _unavailable('not a readable regular file')
    if len(raw) > MAX_BYTES:
        return _unavailable('oversized file')
    lines = _split(raw)
    if len(lines) > MAX_LINES:
        return _unavailable('too many lines')
    records, omitted, unrecognized, ignored = [], 0, 0, 0
    budget = system = 0
    for lineno, line in enumerate(lines, 1):
        status, record = _line(line, lineno)
        if status == 'record':
            records.append(record)
            budget += record['kind'] == 'budget'
            system += record['kind'] == 'system'
        elif status == 'omitted':
            omitted += 1
        elif status == 'unrecognized':
            unrecognized += 1
        else:
            ignored += 1
    shown, bot_count = [], 0
    if records:
        bot_records = [r for r in records if r['kind'] == 'bot']
        shown, bot_count = _project(bot_records)
    first = min(records, key=lambda r: r['moment'])['ts'] if records else None
    last = max(records, key=lambda r: r['moment'])['ts'] if records else None
    notes = f' Showing the first {MAX_BOTS} of {bot_count} bots by name.' if bot_count > MAX_BOTS else ''
    reason = (f'FFXI regular-LSB Bots V2 log export read offline (not live): {len(records)} recognized lines '
              f'({budget} budget, {system} system), {omitted} omitted (malformed, oversized or non-ASCII), '
              f'{unrecognized} unrecognized, {ignored} ignored (no [BOTS-V2] marker); {bot_count} bots. '
              f'Timestamps are read as UTC. Stuck counts are stuck lines; a trip end with why=stuck counts as a '
              f'trip end.{notes}')
    return shown, {'status': 'Loaded', 'records': len(records), 'omitted': omitted, 'reason': reason,
                   'from': first, 'to': last, 'unrecognized': unrecognized, 'ignored': ignored,
                   'budget': budget, 'system': system}


def read(path=None):
    """(bots, coverage). path=None reads the file named by DIT_FFXI_BOTSV2_LOG; unset or empty is Off."""
    try:
        return _read(path)
    except Exception:  # Callers render Unavailable; no input may raise.
        return _unavailable('unexpected error')
