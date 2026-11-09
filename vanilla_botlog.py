"""Offline importer for the cmangos-classic (WoW Vanilla / Benilla) playerbot event log.

Off unless DIT_VANILLA_BOTLOG_CSV names an absolute local CSV file. Never opens a live path and never uses
the network. The server truncates this log at every start, so one file is one server run.

Format (cmangos-classic lane, 2026-11-09): CSV, no header, 9 fields.
  1 timestamp "YYYY-MM-DD HH:MM:SS+00" (UTC, one-second resolution)
  2 bot character name      3 playerbot action class, e.g. AttackAnythingAction
  4 "POINT(a b)" position   5 race id   6 class id   7 level as a float (level plus xp fraction)
  8 info1 (a creature, item, quest or guild name, or a player name on group actions)   9 info2

Rules enforced here:
- A row is checked field by field against exact patterns. A failing row is counted as omitted, never repaired.
- info1 is shown only for actions where it is a game object (TARGET_ACTIONS). For every other action it is
  dropped, because on group and guild actions it can hold a character or guild name.
- A pull is an AttackAnythingAction row; a kill is an XpGainAction row. A stall is the longest run of pulls on
  one target name with no kill between them. A bot that re-pulls one mob for an hour without a kill is stuck,
  and it is the clearest non-human tell this log can show.
- Hearthstone escapes are counted by their reason ("move long stuck", "combat long stuck").
- Output caps: MAX_BOTS bots (longest stall first, then most rows) and MAX_EVENTS events per bot. The
  coverage totals cover every bot in the file, shown or not.
- Errors carry fixed reason text and never echo file content. Nothing in this module raises.

read(path=None) returns (bots, coverage). With path=None the env var is read; unset is Off.
"""
import csv
import os
import re
from datetime import datetime, timezone

import human_feel
from local_evidence import read_bytes

ENV = 'DIT_VANILLA_BOTLOG_CSV'
GAME = 'wow_vanilla'
MAX_BYTES = 8 * 1024 * 1024
MAX_LINES = 100000
MAX_LINE = 1024
MAX_BOTS = 40
MAX_EVENTS = 25
MAX_DEATHS = 20
STALL_MIN = 10          # A run of this many pulls on one target with no kill is called a stall.
PULL, KILL, HEARTH = 'AttackAnythingAction', 'XpGainAction', 'UseHearthStoneAction'
DEATHS = frozenset({'RepopAction', 'AutoReleaseSpiritAction', 'ReviveFromSpiritHealerAction'})
# Actions whose info1 is a creature, item, quest, spell or recipe name: safe to show.
TARGET_ACTIONS = frozenset({
    PULL, KILL, 'StoreLootAction', 'EquipAction', 'SellAction', 'BuyAction', 'AhAction', 'AhBidAction',
    'AcceptQuestAction', 'TalkToQuestGiverAction', 'QuestUpdateAddItemAction', 'QuestUpdateAddKillAction',
    'TrainerAction'})
HEARTH_REASONS = frozenset({'move long stuck', 'combat long stuck'})

_TS = re.compile(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})\+00')
_NAME = re.compile(r'[A-Za-z]{2,12}')
_ACTION = re.compile(r'[A-Z][A-Za-z0-9]{1,62}Action')
_POINT = re.compile(r'POINT\((-?\d{1,6}(?:\.\d{1,6})?) (-?\d{1,6}(?:\.\d{1,6})?)\)')
_LEVEL = re.compile(r'\d{1,3}(?:\.\d{1,6})?')
_INFO = re.compile(r"[A-Za-z0-9][A-Za-z0-9 :,.'()\-]{0,63}")


class _Bad(ValueError):
    """A row that fails a check: omitted and counted."""


def _row(line):
    if len(line) > MAX_LINE:
        raise _Bad('oversized')
    text = line.decode('ascii')  # The format is ASCII; anything else is refused by the decode error.
    if not text.isprintable():
        raise _Bad('control character')
    fields = next(csv.reader([text], strict=True))
    if len(fields) != 9:
        raise _Bad('field count')
    stamp, name, action, point, race, klass, level, info1, info2 = fields
    match = _TS.fullmatch(stamp)
    if match is None or not _NAME.fullmatch(name) or not _ACTION.fullmatch(action) or not _POINT.fullmatch(point):
        raise _Bad('shape')
    moment = datetime(*(int(part) for part in match.groups()), tzinfo=timezone.utc)
    if not (race.isdigit() and klass.isdigit() and 1 <= int(race) <= 255 and 1 <= int(klass) <= 255):
        raise _Bad('race or class')
    if not _LEVEL.fullmatch(level) or not 1 <= float(level) < 256:
        raise _Bad('level')
    target = info1 if action in TARGET_ACTIONS and _INFO.fullmatch(info1) else None
    reason = info2 if action == HEARTH and info2 in HEARTH_REASONS else None
    return {'moment': moment, 'ts': f'{moment:%Y-%m-%dT%H:%M:%SZ}', 'name': name, 'action': action,
            'point': point, 'level': float(level), 'target': target, 'reason': reason}


def _stalls(rows):
    """Runs of pulls on one target with no kill between, as dicts; a kill or a new target ends a run."""
    runs, current = [], None
    for row in rows:
        if row['action'] == PULL:
            if current is not None and current['target'] == row['target']:
                current['pulls'] += 1
                current['end'] = row['moment']
                current['points'].add(row['point'])
            else:
                if current is not None:
                    runs.append(current)
                current = {'target': row['target'], 'pulls': 1, 'start': row['moment'], 'end': row['moment'],
                           'points': {row['point']}}
        elif row['action'] == KILL and current is not None:
            runs.append(current)
            current = None
    if current is not None:
        runs.append(current)
    return runs


def _short(action):
    return action[:-len('Action')]


def _bot(name, rows):
    pulls = sum(row['action'] == PULL for row in rows)
    kills = sum(row['action'] == KILL for row in rows)
    counts = {}
    for row in rows:
        counts[_short(row['action'])] = counts.get(_short(row['action']), 0) + 1
    hearth = {}
    for row in rows:
        if row['reason'] is not None:
            hearth[row['reason']] = hearth.get(row['reason'], 0) + 1
    runs = _stalls(rows)
    worst = max(runs, key=lambda run: (run['pulls'], run['end'] - run['start']), default=None)
    stall = None
    if worst is not None and worst['pulls'] >= STALL_MIN:
        stall = {'target': worst['target'], 'pulls': worst['pulls'],
                 'seconds': int((worst['end'] - worst['start']).total_seconds()), 'positions': len(worst['points']),
                 'from': f"{worst['start']:%Y-%m-%dT%H:%M:%SZ}", 'to': f"{worst['end']:%Y-%m-%dT%H:%M:%SZ}"}
    newest = list(reversed(rows))
    last = rows[-1]
    events = [{'ts': row['ts'], 'type': _short(row['action']), 'detail': row['target'] or row['reason']}
              for row in newest[:MAX_EVENTS]]
    return {'game': GAME, 'actorId': name.lower(), 'name': name, 'level': last['level'], 'lastEventAt': last['ts'],
            'doing': _short(last['action']) + (f" {last['target']}" if last['target'] else ''),
            'counts': dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))),
            'pulls': pulls, 'kills': kills, 'pullsPerKill': round(pulls / kills, 1) if kills else None,
            'stall': stall, 'stalledPulls': sum(run['pulls'] for run in runs if run['pulls'] >= STALL_MIN),
            'hearthStuck': dict(sorted(hearth.items())),
            'events': events,
            'deaths': [{'ts': row['ts'], 'type': _short(row['action'])} for row in newest
                       if row['action'] in DEATHS][:MAX_DEATHS],
            'feel': {'cadence': human_feel.cadence({'pull': [row['moment'] for row in rows if row['action'] == PULL]}),
                     'sync': None, 'schedule': None}}


def _unavailable(reason):
    return [], {'status': 'Unavailable', 'records': 0, 'omitted': None,
                'reason': f'Vanilla playerbot log unreadable ({reason}); nothing imported.', 'from': None, 'to': None}


def _off():
    return [], {'status': 'Off', 'records': 0, 'omitted': 0, 'from': None, 'to': None,
                'reason': f'Set {ENV} to a local exported cmangos-classic playerbot event CSV to import it.'}


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
    lines = raw.split(b'\n')
    if raw.endswith(b'\n'):
        lines.pop()
    if len(lines) > MAX_LINES:
        return _unavailable('too many lines')
    by_bot, omitted, records = {}, 0, 0
    first = last = None
    for line in lines:
        try:
            row = _row(line[:-1] if line.endswith(b'\r') else line)
        except Exception:  # Any failure omits the one row; no bad input may raise or echo.
            omitted += 1
            continue
        records += 1
        by_bot.setdefault(row['name'], []).append(row)
        first = row['moment'] if first is None or row['moment'] < first else first
        last = row['moment'] if last is None or row['moment'] > last else last
    bots = []
    for name, rows in by_bot.items():
        rows.sort(key=lambda row: row['moment'])  # Stable: rows of one second keep their file order.
        bots.append((_bot(name, rows), len(rows)))
    pulls = sum(bot['pulls'] for bot, _ in bots)
    kills = sum(bot['kills'] for bot, _ in bots)
    stalled = [bot for bot, _ in bots if bot['stall'] is not None]
    stalled_pulls = sum(bot['stalledPulls'] for bot, _ in bots)
    hearth = sum(sum(bot['hearthStuck'].values()) for bot, _ in bots)
    deaths = sum(bot['counts'].get('Repop', 0) for bot, _ in bots)
    bots.sort(key=lambda item: (-(item[0]['stall'] or {'pulls': 0})['pulls'], -item[1], item[0]['actorId']))
    shown = [bot for bot, _ in bots[:MAX_BOTS]]
    span = (None if first is None else f'{first:%Y-%m-%dT%H:%M:%SZ}', None if last is None else f'{last:%Y-%m-%dT%H:%M:%SZ}')
    reason = (f'cmangos-classic playerbot event log read offline (not live): {records} rows, {omitted} omitted '
              f'(malformed); {len(bots)} bots, showing {len(shown)} (longest stall first). Whole file: {pulls} pulls, '
              f'{kills} kills, {len(stalled)} bots with a stall of {STALL_MIN}+ pulls on one target and no kill '
              f'({stalled_pulls} pulls), {hearth} hearthstone escapes from being stuck, {deaths} deaths. '
              f'Timestamps are whole seconds, so short gaps are coarse.')
    return shown, {'status': 'Loaded', 'records': records, 'omitted': omitted, 'reason': reason, 'from': span[0],
                   'to': span[1], 'bots': len(bots), 'pulls': pulls, 'kills': kills, 'stalledBots': len(stalled),
                   'stalledPulls': stalled_pulls, 'hearthStuck': hearth, 'deaths': deaths}


def read(path=None):
    """(bots, coverage). path=None reads the file named by DIT_VANILLA_BOTLOG_CSV; unset or empty is Off."""
    try:
        return _read(path)
    except Exception:  # Callers render Unavailable; no input may raise.
        return _unavailable('unexpected error')
