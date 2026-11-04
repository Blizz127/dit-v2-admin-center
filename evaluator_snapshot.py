"""Offline import of an exported DIT dialogue-wording evaluator snapshot.

Off by default. Reads one local JSON file only when DIT_EVALUATOR_SNAPSHOT_FILE is
set; never calls the hub, reads tokens or uses the network. The record shape is
pinned to DialogueProviderEvaluationRecord in the hub's DialogueWordingModels.cs
(worktree dit-ffxi-ls-replies-20261101 at 043bc4b1), as serialized by the
DialogueWordingHarness `compare-fixture` command.

Evaluator output is not bake-off data: it has no run ID or input hash, purpose,
game/actor attribution, time-to-first-token, rubric/evaluator version, delivery
outcome or fallback eligibility (FallbackEligible is on the provider result, not
this record). Those stay unknown here and are never inferred.
"""
import json
import math
import os
import re

from local_evidence import read_bytes

ENV = 'DIT_EVALUATOR_SNAPSHOT_FILE'
LIMIT = 1024 * 1024
MAX_RECORDS = 500
SOURCE = 'Offline evaluator snapshot; not live hub data or a bake-off'
FIELDS = frozenset({
    'RequestId', 'IntentionId', 'SemanticTopic', 'Provider', 'Model', 'Response',
    'CompletionStatus', 'StructuralValidation', 'SemanticCompliance', 'Latency',
    'TokenUsage', 'EstimatedCost', 'EvaluatorScores',
})
COMPLETION = frozenset({'Succeeded', 'TimedOut', 'Unavailable', 'RateLimited', 'Rejected',
                        'InvalidResponse', 'Cancelled', 'ProviderError', 'Skipped'})
SEMANTIC = frozenset({'NotEvaluated', 'Passed', 'Failed'})
VALIDATION = frozenset({'NotRun', 'Accepted', 'Rejected'})
# System.Text.Json TimeSpan: [-][d.]hh:mm:ss[.fffffff]; negative latency is refused.
TIMESPAN = re.compile(r'(?:(\d{1,8})\.)?(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,7}))?')
TOKEN = re.compile(r'[\x21-\x7e]{1,160}')
UNKNOWN = 'Unknown (not in evaluator record)'


class SnapshotError(ValueError):
    """A record that does not match the pinned shape; message never echoes input."""


def latency_ms(value):
    match = TIMESPAN.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise SnapshotError('invalid latency')
    days, hours, minutes, seconds, fraction = match.groups()
    if int(hours) > 23 or int(minutes) > 59 or int(seconds) > 59:
        raise SnapshotError('invalid latency')
    total = ((int(days or 0) * 24 + int(hours)) * 60 + int(minutes)) * 60 + int(seconds)
    return round(total * 1000 + int((fraction or '').ljust(7, '0')) / 10_000, 4)


def token(value, field):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise SnapshotError('invalid ' + field)
    return value


def count(value, field):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SnapshotError('invalid ' + field)
    return value


def number(value, field):
    if value is None:
        return None
    try:
        valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise SnapshotError('invalid ' + field)
    return value


def project(record):
    if not isinstance(record, dict) or set(record) != FIELDS:
        raise SnapshotError('unexpected record fields')
    status = record['CompletionStatus']
    if not isinstance(status, str) or status not in COMPLETION:
        raise SnapshotError('invalid completion status')
    if not isinstance(record['SemanticCompliance'], str) or record['SemanticCompliance'] not in SEMANTIC:
        raise SnapshotError('invalid semantic compliance')
    validation = record['StructuralValidation']
    if (not isinstance(validation, dict) or not isinstance(validation.get('Status'), str)
            or validation['Status'] not in VALIDATION):
        raise SnapshotError('invalid structural validation')
    usage = record['TokenUsage']
    if usage is not None and not isinstance(usage, dict):
        raise SnapshotError('invalid token usage')
    usage = usage or {}
    scores = record['EvaluatorScores']
    if not isinstance(scores, list) or len(scores) > 32:
        raise SnapshotError('invalid evaluator scores')
    parsed_scores = []
    for score in scores:
        if not isinstance(score, dict) or set(score) != {'Evaluator', 'Score'}:
            raise SnapshotError('invalid evaluator score')
        parsed_scores.append({'evaluator': token(score['Evaluator'], 'evaluator'),
                              'score': number(score['Score'], 'score')})
    provider, model = token(record['Provider'], 'provider'), token(record['Model'], 'model')
    return {
        'id': 'snapshot:' + token(record['RequestId'], 'request'),
        'model': f'{provider} / {model}',
        'purpose': None,
        'latencyMs': latency_ms(record['Latency']),
        'cost': number(record['EstimatedCost'], 'cost'),
        # Scores carry no rubric or evaluator version, so none becomes a quality value.
        'quality': None,
        'source': SOURCE,
        'observedAt': None,
        'evaluator': {
            'requestId': record['RequestId'],
            'intentionId': token(record['IntentionId'], 'intention'),
            'semanticTopic': token(record['SemanticTopic'], 'topic'),
            'completionStatus': status,
            'structuralValidation': validation['Status'],
            'semanticCompliance': record['SemanticCompliance'],
            'inputTokens': count(usage.get('InputTokens'), 'input tokens'),
            'outputTokens': count(usage.get('OutputTokens'), 'output tokens'),
            'scores': parsed_scores,
            'scoreRubric': UNKNOWN,
            'fallbackEligible': UNKNOWN,
            'delivery': UNKNOWN,
            'attribution': UNKNOWN,
            'runId': UNKNOWN,
        },
    }


def refuse_constant(_):
    raise SnapshotError('non-finite number')


def unique_object(pairs):
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise SnapshotError('duplicate key')
    return dict(pairs)


def load(path):
    """Return (rows, coverage). Malformed records are counted and omitted, never repaired."""
    try:
        raw = read_bytes(path, LIMIT)
        if len(raw) > LIMIT:
            raise SnapshotError('oversized snapshot')
        data = json.loads(raw.decode('utf-8'), parse_constant=refuse_constant, object_pairs_hook=unique_object)
        if not isinstance(data, list) or len(data) > MAX_RECORDS:
            raise SnapshotError('snapshot must be a bounded JSON array')
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as error:
        reason = str(error) if isinstance(error, SnapshotError) else type(error).__name__
        return [], {'status': 'Unavailable', 'records': 0, 'omitted': None,
                    'reason': f'Snapshot unreadable ({reason}); nothing imported.'}
    rows, omitted, seen = [], 0, set()
    for record in data:
        try:
            row = project(record)
            key = (row['id'], row['model'])
            if key in seen:
                raise SnapshotError('duplicate record')
            seen.add(key)
            rows.append(row)
        except SnapshotError:
            omitted += 1
    return rows, {'status': 'Loaded', 'records': len(rows), 'omitted': omitted,
                  'reason': 'Offline evaluator records only. Purpose, attribution, run identity, '
                            'rubric, delivery and fallback eligibility are not in the export.'}


def from_env(environ=None):
    path = (os.environ if environ is None else environ).get(ENV)
    if not path:
        return [], {'status': 'Not configured', 'records': 0, 'omitted': 0,
                    'reason': f'Set {ENV} to a local exported evaluator JSON file to import it.'}
    return load(path)
