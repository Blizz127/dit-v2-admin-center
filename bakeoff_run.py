"""Offline import of one recorded bake-off run (docs/BAKEOFF-PRODUCER-PROPOSAL.md).

Off unless DIT_BAKEOFF_RUN_DIR names a local directory holding manifest.json and
attempts.jsonl. Never contacts the hub, spends AI budget or reads tokens. The
shape is the hub-lead-reviewed proposal (November 3), not an implemented hub
contract; no producer exists yet.

Review defaults enforced here:
- Only offline_fixture and recorded_replay runs are accepted; shadow_live needs an
  owner decision and is refused.
- inputSha256 is the producer's hash of a canonical request without per-call
  fields; it is named by inputCanonicalization and never recomputed here. A case
  whose candidates report different hashes is not comparable and is omitted.
- Latency is total (completed - sent). firstTokenAtUtc is not shown: no streaming
  path exists.
- Offline runs cannot claim delivery.
"""
from datetime import datetime
import json
import math
import os
import re
from pathlib import Path

from local_evidence import read_bytes

ENV = 'DIT_BAKEOFF_RUN_DIR'
SCHEMA = 'dit-bakeoff-run-v0'
MANIFEST_LIMIT = 64 * 1024
ATTEMPTS_LIMIT = 4 * 1024 * 1024
MAX_ATTEMPTS = 5000
ENVIRONMENTS = frozenset({'offline_fixture', 'recorded_replay'})
COMPLETION = frozenset({'succeeded', 'timed_out', 'unavailable', 'rate_limited', 'rejected',
                        'invalid_response', 'cancelled', 'provider_error', 'skipped'})
VALIDATION = frozenset({'not_run', 'accepted', 'rejected'})
SEMANTIC = frozenset({'not_evaluated', 'passed', 'failed'})
EVALUATOR_KINDS = frozenset({'rule', 'model', 'human'})
TOKEN = re.compile(r'[\x21-\x7e]{1,128}')
SHA256 = re.compile(r'[0-9a-f]{64}')
UTC = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,7})?Z')
REQUIRED = frozenset({'runId', 'caseId', 'inputSha256', 'provider', 'model', 'purpose',
                      'sentAtUtc', 'completedAtUtc', 'completionStatus'})
OPTIONAL = frozenset({'gameId', 'actorKey', 'reportedModel', 'firstTokenAtUtc', 'queuedMs',
                      'inputTokens', 'outputTokens', 'cacheHitTokens', 'costNusd', 'pricingBasis',
                      'attemptId', 'structuralValidation', 'semanticCompliance', 'fallbackEligible',
                      'fallbackUsed', 'delivery', 'scores'})
MANIFEST_FIELDS = frozenset({'schema', 'runId', 'startedAtUtc', 'completedAtUtc', 'environment', 'caseSet',
                             'inputCanonicalization', 'candidates', 'rubrics', 'hubRevision'})


class RunError(ValueError):
    """Fixed messages only; never echoes file contents."""


def _refuse(_):
    raise RunError('non-finite number')


def _unique(pairs):
    if len({k for k, _ in pairs}) != len(pairs):
        raise RunError('duplicate key')
    return dict(pairs)


def _json(raw):
    return json.loads(raw.decode('utf-8'), parse_constant=_refuse, object_pairs_hook=_unique)


def _token(value, field):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise RunError('invalid ' + field)
    return value


def _time(value, field):
    if not isinstance(value, str) or not UTC.fullmatch(value):
        raise RunError('invalid ' + field)
    return datetime.fromisoformat(value[:-1] + '+00:00')


def _count(value, field):
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise RunError('invalid ' + field)
    return value


def _number(value, field):
    try:
        valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise RunError('invalid ' + field)
    return value


def _enum(value, choices, field):
    if not isinstance(value, str) or value not in choices:
        raise RunError('invalid ' + field)
    return value


def _flag(value, field):
    if value is not None and type(value) is not bool:
        raise RunError('invalid ' + field)
    return value


def manifest(data):
    if not isinstance(data, dict) or not set(data) <= MANIFEST_FIELDS or data.get('schema') != SCHEMA:
        raise RunError('unsupported manifest')
    environment = data.get('environment')
    if environment == 'shadow_live':
        raise RunError('shadow_live runs need an owner decision and are not imported')
    _enum(environment, ENVIRONMENTS, 'environment')
    started, completed = _time(data.get('startedAtUtc'), 'start'), _time(data.get('completedAtUtc'), 'end')
    if completed < started:
        raise RunError('run ends before it starts')
    case_set = data.get('caseSet')
    if not isinstance(case_set, dict) or set(case_set) != {'name', 'version', 'sha256'} \
            or not isinstance(case_set['sha256'], str) or not SHA256.fullmatch(case_set['sha256']):
        raise RunError('invalid case set')
    candidates = data.get('candidates')
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 64:
        raise RunError('invalid candidates')
    keys = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != {'provider', 'model', 'purpose'}:
            raise RunError('invalid candidate')
        keys.add(tuple(_token(candidate[k], 'candidate') for k in ('provider', 'model', 'purpose')))
    if len(keys) != len(candidates):
        raise RunError('duplicate candidate')
    rubrics = data.get('rubrics')
    if not isinstance(rubrics, list) or len(rubrics) > 16:
        raise RunError('invalid rubrics')
    rubric_keys = set()
    for rubric in rubrics:
        if not isinstance(rubric, dict) or set(rubric) != {'name', 'version'}:
            raise RunError('invalid rubric')
        rubric_keys.add((_token(rubric['name'], 'rubric'), _token(rubric['version'], 'rubric version')))
    if len(rubric_keys) != len(rubrics):
        raise RunError('duplicate rubric')
    revision = data.get('hubRevision')
    return {
        'runId': _token(data.get('runId'), 'run id'), 'environment': environment,
        'caseSet': f"{_token(case_set['name'], 'case set')}@{_token(case_set['version'], 'case set version')}",
        'canonicalization': _token(data.get('inputCanonicalization'), 'canonicalization'),
        'candidates': keys, 'rubrics': rubric_keys,
        'hubRevision': _token(revision, 'hub revision') if revision is not None else None,
        'completedAtUtc': data['completedAtUtc'],
    }


def attempt(data, run):
    if not isinstance(data, dict) or not REQUIRED <= set(data) or not set(data) <= REQUIRED | OPTIONAL:
        raise RunError('unexpected attempt fields')
    if data['runId'] != run['runId']:
        raise RunError('attempt from another run')
    case = _token(data['caseId'], 'case id')
    key = tuple(_token(data[k], k) for k in ('provider', 'model', 'purpose'))
    if key not in run['candidates']:
        raise RunError('attempt for an undeclared candidate')
    if not isinstance(data['inputSha256'], str) or not SHA256.fullmatch(data['inputSha256']):
        raise RunError('invalid input hash')
    sent, completed = _time(data['sentAtUtc'], 'sent'), _time(data['completedAtUtc'], 'completed')
    if completed < sent:
        raise RunError('completed before sent')
    if 'firstTokenAtUtc' in data:
        _time(data['firstTokenAtUtc'], 'first token')  # Validated, never shown: no streaming path exists.
    status = data['completionStatus']
    _enum(status, COMPLETION, 'completion status')
    _enum(data.get('structuralValidation', 'not_run'), VALIDATION, 'structural validation')
    _enum(data.get('semanticCompliance', 'not_evaluated'), SEMANTIC, 'semantic compliance')
    delivery = data.get('delivery')
    if delivery is not None:
        if not isinstance(delivery, dict) or not {'status'} <= set(delivery) <= {'status', 'evidence'}:
            raise RunError('invalid delivery')
        if delivery['status'] != 'not_applicable':
            raise RunError('offline runs cannot claim delivery')
    scores = data.get('scores', [])
    if not isinstance(scores, list) or len(scores) > 16:
        raise RunError('invalid scores')
    parsed = []
    for score in scores:
        fields = {'rubric', 'rubricVersion', 'evaluator', 'evaluatorKind', 'evaluatorVersion', 'scaleMin', 'scaleMax', 'score'}
        if not isinstance(score, dict) or set(score) != fields:
            raise RunError('invalid score')
        rubric = (_token(score['rubric'], 'rubric'), _token(score['rubricVersion'], 'rubric version'))
        if rubric not in run['rubrics']:
            raise RunError('score for an undeclared rubric')
        _enum(score['evaluatorKind'], EVALUATOR_KINDS, 'evaluator kind')
        low, high, value = (_number(score[k], k) for k in ('scaleMin', 'scaleMax', 'score'))
        if not low < high or not low <= value <= high:
            raise RunError('score outside its scale')
        parsed.append({'rubric': f'{rubric[0]}@{rubric[1]}', 'evaluator':
                       f"{_token(score['evaluator'], 'evaluator')}@{_token(score['evaluatorVersion'], 'evaluator version')}",
                       'evaluatorKind': score['evaluatorKind'], 'scaleMin': low, 'scaleMax': high, 'score': value})
    for field in ('gameId', 'actorKey', 'reportedModel', 'pricingBasis', 'attemptId'):
        if field in data:
            _token(data[field], field)
    cost = _count(data.get('costNusd'), 'cost')
    if cost is not None:
        _number(cost, 'cost')
    for field in ('inputTokens', 'outputTokens', 'cacheHitTokens', 'queuedMs'):
        _count(data.get(field), field)
    _flag(data.get('fallbackEligible'), 'fallback eligibility')
    _flag(data.get('fallbackUsed'), 'fallback use')
    # Quality and the source string are set per run in load(), so every row of a
    # candidate shares one comparison group whether or not it was scored.
    source = f"Bake-off run {run['runId']} · {run['environment']} · cases {run['caseSet']}"
    return {
        'id': f"bakeoff:{run['runId']}:{case}:{'/'.join(key)}",
        'model': f'{key[0]} / {key[1]}', 'purpose': key[2],
        'latencyMs': round((completed - sent).total_seconds() * 1000, 3),
        'cost': cost / 1e9 if cost is not None else None,
        'quality': None, 'source': source, 'observedAt': data['completedAtUtc'],
        'bakeoff': {'caseId': case, 'inputSha256': data['inputSha256'],
                    'completionStatus': status, 'latency': 'Total (sent to completed); first-token time not available',
                    'costUnit': 'USD from costNusd', 'scores': parsed,
                    'fallbackEligible': data.get('fallbackEligible'), 'fallbackUsed': data.get('fallbackUsed'),
                    'delivery': 'Not applicable (offline run)', 'gameId': data.get('gameId'),
                    'actorKey': data.get('actorKey')},
    }


def _unavailable(reason):
    return [], {'status': 'Unavailable', 'records': 0, 'omitted': None, 'reason': reason + '; nothing imported.'}


def load(directory):
    root = Path(directory)
    if not root.is_absolute():
        return _unavailable('Run directory must be an absolute path')
    try:
        raw = read_bytes(root / 'manifest.json', MANIFEST_LIMIT)
        if len(raw) > MANIFEST_LIMIT:
            raise RunError('oversized manifest')
        run = manifest(_json(raw))
        raw = read_bytes(root / 'attempts.jsonl', ATTEMPTS_LIMIT)
        if len(raw) > ATTEMPTS_LIMIT:
            raise RunError('oversized attempts')
        lines = [line for line in raw.split(b'\n') if line.strip()]
        if len(lines) > MAX_ATTEMPTS:
            raise RunError('too many attempts')
    except RunError as error:
        return _unavailable(f'Run unreadable ({error})')
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as error:
        return _unavailable(f'Run unreadable ({type(error).__name__})')
    rows, omitted = [], 0
    for line in lines:
        try:
            rows.append(attempt(_json(line), run))
        except (RunError, UnicodeDecodeError, ValueError, RecursionError):
            omitted += 1
    # Exact duplicates of a case × candidate are ambiguous: drop every copy.
    counts = {}
    for row in rows:
        counts[row['id']] = counts.get(row['id'], 0) + 1
    # A case is comparable only if all its attempts hash the same input.
    hashes = {}
    for row in rows:
        hashes.setdefault(row['bakeoff']['caseId'], set()).add(row['bakeoff']['inputSha256'])
    kept = [r for r in rows if counts[r['id']] == 1 and len(hashes[r['bakeoff']['caseId']]) == 1]
    omitted += len(rows) - len(kept)
    # Quality only if the run declares one rubric and every scored attempt has exactly
    # one score with the same rubric, evaluator, version and scale; otherwise none.
    scored = [r for r in kept if r['bakeoff']['scores']]
    descriptors = {(sc['rubric'], sc['evaluator'], sc['scaleMin'], sc['scaleMax'])
                   for r in scored for sc in r['bakeoff']['scores']}
    if len(run['rubrics']) == 1 and len(descriptors) == 1 and all(len(r['bakeoff']['scores']) == 1 for r in scored):
        rubric, evaluator, low, high = descriptors.pop()
        quality_note = f'quality: {rubric} by {evaluator} on {low}–{high}; unscored attempts are unknown.'
        for row in kept:
            row['source'] += f' · {rubric} by {evaluator} on {low}–{high}'
            if row['bakeoff']['scores']:
                row['quality'] = row['bakeoff']['scores'][0]['score']
    else:
        quality_note = ('no quality shown: scores are absent or mix rubrics, evaluators or scales.'
                        if scored else 'no quality shown: no attempt was scored.')
    cases = {r['bakeoff']['caseId'] for r in kept}
    expected = len(cases) * len(run['candidates'])
    revision = f"reported hub revision {run['hubRevision']}" if run['hubRevision'] else 'hub revision not reported'
    return kept, {'status': 'Loaded', 'records': len(kept), 'omitted': omitted,
                  'reason': f"Run {run['runId']} ({run['environment']}, cases {run['caseSet']}, input hash "
                            f"{run['canonicalization']}, {revision}). {len(kept)} of {expected} case × candidate "
                            f'attempts present (means include partial cases; disclosed, not filtered). Total latency only; {quality_note} Offline runs have no delivery. '
                            'Proposal shape, not an implemented hub contract.'}


def from_env(environ=None):
    directory = (os.environ if environ is None else environ).get(ENV)
    if not directory:
        return [], {'status': 'Not configured', 'records': 0, 'omitted': 0,
                    'reason': f'Set {ENV} to a local recorded bake-off run directory to import it.'}
    return load(directory)
