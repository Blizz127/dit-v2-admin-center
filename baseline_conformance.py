"""Committed baseline-conformance tracker, never a live probe of any game's bots."""
from pathlib import Path
from local_evidence import read_json

FIXTURE = Path(__file__).resolve().parent / 'data/fixtures/baseline-conformance.json'
LIMIT = 256 * 1024
STATUSES = frozenset({'Reference', 'Sim-measured', 'Unit-tested', 'Designed', 'Not started', 'Unknown'})
GROUPS = frozenset({'forever', 'dit'})
MAX_TEXT = 300
MISSING = {'status': 'Unknown', 'evidence': 'No documented evidence'}


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= MAX_TEXT


def _cell(value):
    return (isinstance(value, dict) and set(value) == {'status', 'evidence'}
            and value['status'] in STATUSES and _text(value['evidence']))


def _parse(data):
    if not isinstance(data, dict) or data.get('kind') != 'baseline-conformance':
        return None
    if data.get('version') != 1 or isinstance(data.get('version'), bool):
        return None
    if not (_text(data.get('source')) and _text(data.get('asOf'))):
        return None
    rows, games = data.get('rows'), data.get('games')
    if not isinstance(rows, list) or not rows or not isinstance(games, list):
        return None
    ids, clean_rows = set(), []
    for row in rows:
        if not (isinstance(row, dict) and _text(row.get('id')) and _text(row.get('behavior'))
                and row.get('group') in GROUPS) or row['id'] in ids:
            return None
        ids.add(row['id'])
        clean_rows.append({'id': row['id'], 'group': row['group'], 'behavior': row['behavior']})
    names, clean_games = set(), []
    for game in games:
        if not (isinstance(game, dict) and _text(game.get('game')) and _text(game.get('owner'))
                and isinstance(game.get('cells'), dict)) or game['game'] in names:
            return None
        names.add(game['game'])
        cells = game['cells']
        if any(key not in ids or not _cell(cell) for key, cell in cells.items()):
            return None
        clean_games.append({'game': game['game'], 'owner': game['owner'], 'cells': {
            row['id']: dict(cells[row['id']]) if row['id'] in cells else dict(MISSING)
            for row in clean_rows}})
    return {'source': data['source'], 'asOf': data['asOf'], 'rows': clean_rows, 'games': clean_games}


def read(path=None):
    """Return the validated tracker with every cell filled, or None for any refusal."""
    try:
        return _parse(read_json(FIXTURE if path is None else path, LIMIT))
    except Exception:  # Callers render Unknown; no bad input may raise.
        return None
