"""Offline reference reviewer for a proposed synthetic assessment contract.

Not imported by the server/UI. A consistent report is not authenticated evidence.
"""
import math
import re
from datetime import datetime, timezone


VERSION = 'dit-learning-assessment-draft-v1'
KINDS = ('nativeIdentity', 'navigationAndMissions', 'partyAndSocial',
         'groundedMemory', 'measuredPolicyBenefit')
SCOPE_KEYS = {'gameId', 'realmId', 'callerId', 'serverInstanceId', 'nativeBotId', 'taskId'}
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}\Z')


def _identifier(value):
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def _scope(value):
    return (isinstance(value, dict) and set(value) == SCOPE_KEYS and
            value['gameId'] in ('ffxi', 'swtor') and all(_identifier(v) for v in value.values()))


def _timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
        raise ValueError('timestamp')
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def review(payload, expected_scope, *, now, max_age_seconds):
    """Review supplied synthetic data against an exact caller-supplied scope.

    Freshness is an explicit caller policy, not a proposed authoritative hub TTL.
    Unknown/invalid input never produces a supported or verified game outcome.
    """
    result = {
        'contractStatus': 'draft', 'environment': 'synthetic',
        'sourceAuthenticity': 'unverified', 'status': 'unavailable',
        'assessments': [{'kind': kind, 'state': 'Unknown', 'evidenceIds': []} for kind in KINDS],
        'policyAdoption': 'Unknown',
    }
    try:
        if (not _scope(expected_scope) or not isinstance(now, datetime) or
                now.tzinfo is None or now.utcoffset() is None or
                type(max_age_seconds) not in (int, float) or
                not math.isfinite(max_age_seconds) or not 0 < max_age_seconds <= 86400):
            return result
        if not isinstance(payload, dict) or set(payload) != {
                'schema', 'contractStatus', 'environment', 'generatedAt',
                'scope', 'assessments', 'evidence'}:
            return result
        if (payload['schema'] != VERSION or payload['contractStatus'] != 'draft' or
                payload['environment'] != 'synthetic' or not _scope(payload['scope']) or
                payload['scope'] != expected_scope):
            return result
        generated = _timestamp(payload['generatedAt'])
        if not 0 <= (now - generated).total_seconds() <= max_age_seconds:
            return result
        evidence = payload['evidence']
        assessments = payload['assessments']
        if (not isinstance(evidence, list) or len(evidence) > 32 or
                not isinstance(assessments, list) or len(assessments) > len(KINDS)):
            return result
        indexed = {}
        for item in evidence:
            if not isinstance(item, dict) or set(item) != {'id', 'scope', 'sourceId', 'receiptId', 'observedAt'}:
                return result
            if (not all(_identifier(item[key]) for key in ('id', 'sourceId', 'receiptId')) or
                    item['id'] in indexed or not _scope(item['scope']) or item['scope'] != expected_scope):
                return result
            observed = _timestamp(item['observedAt'])
            if not 0 <= (now - observed).total_seconds() <= max_age_seconds or observed > generated:
                return result
            indexed[item['id']] = item
        projected = {}
        for item in assessments:
            if not isinstance(item, dict) or set(item) != {'kind', 'claim', 'evidenceIds'}:
                return result
            kind, claim, refs = item['kind'], item['claim'], item['evidenceIds']
            if (not isinstance(kind, str) or kind not in KINDS or kind in projected or
                    claim not in ('unknown', 'supported', 'contradicted') or
                    not isinstance(refs, list) or len(refs) > 32 or
                    not all(_identifier(ref) for ref in refs) or len(set(refs)) != len(refs) or
                    any(ref not in indexed for ref in refs)):
                return result
            if (claim == 'unknown' and refs) or (claim != 'unknown' and not refs):
                return result
            state = {'unknown': 'Unknown', 'supported': 'Reported support (synthetic)',
                     'contradicted': 'Reported contradiction (synthetic)'}[claim]
            projected[kind] = {'kind': kind, 'state': state, 'evidenceIds': list(refs)}
        result['assessments'] = [projected.get(row['kind'], row) for row in result['assessments']]
        result['status'] = 'reviewed-synthetic'
    except (ValueError, TypeError, OverflowError):
        # Deliberately fixed output: no paths, raw evidence or exception details.
        pass
    return result
