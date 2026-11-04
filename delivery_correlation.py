"""Read-only correlation of bounded synthetic decision, inbox and receipt records.

Legacy `sent` is inbox publication only. No real native receipt authority exists
here: even an injected fixture verifier cannot assert actual game delivery.
"""
import hashlib
import json
import re
from types import MappingProxyType

from local_evidence import read_json
from tools.build_integrated_context_preview import timestamp

SCHEMA = 'dit.delivery-correlation-fixture.v1'
SCOPE_KEYS = ('game', 'realm', 'instance', 'thread', 'channel', 'actorKey', 'nativeActorId', 'epoch')
LIMIT = 262144
MAX_ROWS = 256


def text(value, maximum=128):
    if (not isinstance(value, str) or not value.strip() or len(value.encode('utf-8')) > maximum
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError('Invalid bounded text')
    return value


def integer(value):
    if type(value) is not int or not 0 <= value <= 2**53 - 1:
        raise ValueError('Invalid bounded integer')
    return value


def scope_of(value):
    scope = {key: text(value[key]) for key in SCOPE_KEYS}
    if scope['game'] not in ('ffxi', 'swtor'):
        raise ValueError('Unsupported game')
    return scope


def rows(value):
    if not isinstance(value, list) or len(value) > MAX_ROWS:
        raise ValueError('Invalid record list')
    return value


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def base(status):
    return dict(schema='dit.delivery-correlation-report.v1', status=status, evidenceKind='synthetic',
                nativeDeliveryVerified=False, deliveredInGame=None, replayAuthorized=False,
                coverage='Supplied decision replies only; missing or rotated records do not prove silence.',
                scope=None, records=[], counts=None, rejectedReceipts=None)


def correlate(data=None, *, enabled=False, native_verifier=None):
    if type(enabled) is not bool:
        raise ValueError('Explicit boolean switch required')
    if not enabled:
        return base('Disabled')
    try:
        return _correlate(data, native_verifier)
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError, OverflowError):
        return base('Unavailable')


def from_file(path=None, *, enabled=False, native_verifier=None):
    if type(enabled) is not bool:
        raise ValueError('Explicit boolean switch required')
    if not enabled:
        return correlate(enabled=enabled)
    try:
        return correlate(read_json(path, LIMIT), enabled=enabled, native_verifier=native_verifier)
    except (OSError, ValueError, TypeError, RecursionError):
        return base('Unavailable')


def _correlate(data, verifier):
    if data['schema'] != SCHEMA or data['synthetic'] is not True:
        raise ValueError('Synthetic capture required')
    scope, session = scope_of(data['scope']), text(data['bridgeSession'])
    inbox = {}
    inbox_conflicts = set()
    for row in rows(data['inbox']):
        seq = integer(row['seq'])
        normalized = dict(seq=seq, ts=integer(row['ts']), channel=text(row['channel']),
                          bot=text(row['bot']), actorKey=text(row['actorKey']), text=text(row['text'], 2048),
                          replyTo=text(row['replyTo']) if row.get('replyTo') is not None else None)
        if seq in inbox and inbox[seq] != normalized:
            inbox_conflicts.add(seq)
        inbox[seq] = normalized

    attempts, duplicates = {}, 0
    for row_index, row in enumerate(rows(data['decisions'])):
        if (row['schema'] not in ('dit.chat.decision.v1', 'dit.chat.decision.v2')
                or row['game'] != scope['game'] or row['scope'] != scope['thread']
                or row['channel'] != scope['channel']):
            raise ValueError('Decision scope mismatch')
        for reply_index, reply in enumerate(rows(row['replies'])):
            if reply['actor_key'] != scope['actorKey']:
                raise ValueError('Decision actor mismatch')
            bot = text(reply['bot'])
            final = reply.get('text_final')
            if final is not None:
                text(final, 2048)
            verdict = reply.get('verdict')
            if verdict not in ('sent', 'trimmed', 'blocked', 'dropped', None):
                raise ValueError('Unknown decision verdict')
            seq = reply.get('inbox_seq')
            if seq is not None:
                integer(seq)
            # Positions label unbound draft evidence; they are not native event IDs.
            key = ('inbox', seq) if seq is not None else ('decision', row_index, reply_index)
            candidate = dict(inboxSeq=seq, bot=bot, text=final, verdict=verdict,
                             publication='Uncorroborated', fixtureConfirmation='Unknown',
                             actualDelivery='Unknown', reason='No matching publication identity.',
                             nativeObservationId=None, observedAtUtc=None, receivedAtUtc=None)
            if key in attempts:
                prior = attempts[key]
                if (prior['bot'], prior['text'], prior['verdict']) != (bot, final, verdict):
                    prior.update(publication='Conflict', reason='Decision records disagree for one inbox sequence.')
                duplicates += 1
                continue
            if len(attempts) >= MAX_ROWS:
                raise ValueError('Too many replies')
            attempts[key] = candidate
            if seq is None:
                candidate.update(publication='Not evidenced', reason='No inbox sequence; this does not prove no speech occurred.')
            elif seq in inbox_conflicts or verdict not in ('sent', 'trimmed') or final is None:
                candidate.update(publication='Conflict', reason='Publication records conflict.')
            elif seq in inbox:
                published = inbox[seq]
                if (published['actorKey'], published['channel'], published['bot'], published['text']) != (scope['actorKey'], scope['channel'], bot, final):
                    candidate.update(publication='Conflict', reason='Decision and inbox content or identity differ.')
                else:
                    candidate.update(publication='Matched', reason='Inbox publication matches; native speech is unconfirmed.')

    # Receipt authority is injected by the offline caller, never a trusted flag
    # in a file. Scope and IDs still have to match after fixture verification.
    receipts, rejected, receipt_duplicates = [], 0, 0
    by_receipt, by_observation, by_attempt = {}, {}, {}
    conflicts = set()
    for raw in rows(data['receipts']):
        try:
            receipt = dict(schema=raw['schema'], receiptId=text(raw['receiptId']),
                           observationId=text(raw['observationId']), scope=scope_of(raw['scope']),
                           bridgeSession=text(raw['bridgeSession']), inboxSeq=integer(raw['inboxSeq']),
                           textSha256=text(raw['textSha256'], 64), observedAtUtc=raw['observedAtUtc'],
                           receivedAtUtc=raw['receivedAtUtc'])
            if (receipt['schema'] != 'dit.synthetic-chat-receipt.v1' or receipt['scope'] != scope
                    or receipt['bridgeSession'] != session or re.fullmatch('[0-9a-f]{64}', receipt['textSha256']) is None):
                raise ValueError('Receipt binding mismatch')
            observed, received = timestamp(receipt['observedAtUtc']), timestamp(receipt['receivedAtUtc'])
            seq = receipt['inboxSeq']
            attempt, published = attempts.get(('inbox', seq)), inbox.get(seq)
            if (attempt is None or published is None or attempt['publication'] != 'Matched'
                    or receipt['textSha256'] != hashlib.sha256(published['text'].encode()).hexdigest()
                    or observed > received or observed.timestamp() < published['ts']):
                raise ValueError('Receipt does not match publication')
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            rejected += 1
            continue
        immutable = MappingProxyType(receipt | {'scope': MappingProxyType(dict(scope))})
        try:
            verified = callable(verifier) and verifier(immutable) is True
        except Exception:
            verified = False
        if not verified:
            rejected += 1
            continue
        identity = fingerprint(receipt)
        old = by_receipt.get(receipt['receiptId'])
        if old is not None:
            if old[0] == identity:
                receipt_duplicates += 1
                continue
            conflicts.update((old[1], seq))
        by_receipt[receipt['receiptId']] = (identity, seq)
        # Native observation IDs are unique within the explicit body/session.
        observation = (seq, receipt['textSha256'], receipt['observedAtUtc'])
        old = by_observation.get(receipt['observationId'])
        if old is not None and old != observation:
            conflicts.update((old[0], seq))
        by_observation[receipt['observationId']] = observation
        old = by_attempt.get(seq)
        if old is not None and old != receipt['observationId']:
            conflicts.add(seq)
        by_attempt[seq] = receipt['observationId']
        receipts.append(receipt)
    for receipt in receipts:
        attempt = attempts[('inbox', receipt['inboxSeq'])]
        if receipt['inboxSeq'] in conflicts:
            attempt.update(fixtureConfirmation='Conflict', reason='Verified fixture receipts disagree; no unique delivery conclusion.')
        else:
            attempt.update(fixtureConfirmation='Synthetic match', reason='Fixture evidence matches; actual game delivery remains unknown.',
                           nativeObservationId=receipt['observationId'], observedAtUtc=receipt['observedAtUtc'],
                           receivedAtUtc=receipt['receivedAtUtc'])
    records = []
    for key, attempt in attempts.items():
        records.append({'correlationId': fingerprint([scope, session, key]), **attempt})
    return base('Loaded') | dict(scope=scope, records=records, rejectedReceipts=rejected,
        counts=dict(recordedAttempts=len(records), publicationMatched=sum(r['publication'] == 'Matched' for r in records),
                    syntheticConfirmed=sum(r['fixtureConfirmation'] == 'Synthetic match' for r in records),
                    conflicted=sum(r['publication'] == 'Conflict' or r['fixtureConfirmation'] == 'Conflict' for r in records),
                    duplicateDecisionRecords=duplicates, duplicateReceiptRecords=receipt_duplicates))
