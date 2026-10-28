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
            'reason': task.get('reason'),
            # Light responses omit evidence, and a verified task is not a verified policy.
            'evidence': 'Not included' if 'evidence' not in task else 'Present' if task['evidence'] is not None else 'Unknown',
            'datasets': 'Unknown', 'policy': 'Unknown',
            'source': 'Synthetic r10 task-only fixture; offline projection',
        })
    return rows


def project_learning_attention(rows):
    """Expose task states needing attention without calling them incidents."""
    return [{
        'scope': row['game'], 'title': row['topic'], 'status': row['status'],
        'detail': row['reason'] or 'No reason reported', 'updatedAt': row['updatedAt'],
        'source': row['source'],
    } for row in rows if row['status'] in ('unverified', 'failed', 'canceled', 'cancelled')]
