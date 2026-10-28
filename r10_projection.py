"""Offline projection of synthetic r10 task-only learning responses.

No networking, credential access or mutation. Not wired to a live hub.
"""


def project_learning(payload):
    """Preserve task state and scope; do not infer policy verification or presence."""
    if not isinstance(payload, dict) or not isinstance(payload.get('gameId'), str) or not payload['gameId']:
        raise ValueError('gameId is required')
    if not isinstance(payload.get('tasks'), list):
        raise ValueError('tasks must be a list')
    game = payload['gameId']
    rows = []
    for task in payload['tasks']:
        if not isinstance(task, dict) or task.get('gameId') != game:
            raise ValueError('task gameId must match response scope')
        if not all(isinstance(task.get(k), str) and task[k] for k in ('id', 'topic', 'status')):
            raise ValueError('task id, topic and status are required')
        rows.append({
            'id': task['id'], 'game': game, 'topic': task['topic'],
            'status': task['status'], 'updatedAt': task.get('updatedAtUtc'),
            'reason': task.get('reason') if isinstance(task.get('reason'), str) else None,
            'phase': task.get('phase') if isinstance(task.get('phase'), str) else None,
            'retryAt': task.get('retryAtUtc') if isinstance(task.get('retryAtUtc'), str) else None,
            'escalation': task.get('escalation') if isinstance(task.get('escalation'), str) else None,
            # Light responses omit evidence, and a verified task is not a verified policy.
            'evidence': 'Not included' if 'evidence' not in task else 'Present' if task['evidence'] is not None else 'Unknown',
            'datasets': 'Unknown', 'policy': 'Unknown',
            'source': 'Synthetic r10 task-only fixture; offline projection',
        })
    return rows


def project_learning_attention(rows):
    """Expose task states needing attention without calling them incidents."""
    return [{
        'scope': row['game'], 'title': row['topic'], 'status': row['status'], 'learningId': row['id'],
        'detail': row['reason'] or 'No reason reported', 'updatedAt': row['updatedAt'],
        'source': row['source'],
    } for row in rows if row['status'] in ('unverified', 'failed', 'canceled', 'cancelled')]


def project_roster(game, rows):
    """r10 persona/body listing: never infer online status from registration."""
    if not isinstance(game, str) or not game or not isinstance(rows, list):
        raise ValueError('game and roster list required')
    result = []
    for row in rows:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k] for k in ('key', 'name')):
            raise ValueError('roster key and name required')
        result.append({'id': f'fixture:{game}:{row["key"]}', 'name': row['name'], 'game': game.upper(),
                       'status': 'Unknown', 'source': 'Synthetic r10 roster fixture; registration is not presence',
                       'observedAt': None, 'identityNote': 'Fixture key; native identity is not verified'})
    return result


def project_health(payload):
    """Project service health only, preserving time and raw state; omit paths."""
    if not isinstance(payload, dict) or not isinstance(payload.get('services'), list):
        raise ValueError('services list required')
    result = []
    for service in payload['services']:
        if not isinstance(service, dict) or not all(isinstance(service.get(k), str) and service[k] for k in ('id', 'label', 'state')):
            raise ValueError('service id, label and state required')
        result.append({'label': service['label'], 'game': service.get('game') or 'Unknown',
                       'status': service['state'], 'detail': service.get('detail') or 'Not reported',
                       'observedAt': payload.get('utc'), 'source': 'Synthetic r10 health fixture'})
    return result
