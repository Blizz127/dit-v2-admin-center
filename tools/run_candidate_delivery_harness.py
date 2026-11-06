"""Exercise candidate decisions through an in-memory synthetic receipt channel.

No native adapter, model, network, persistent ledger or replay path is used.
The local verifier recognizes only receipts issued AND received in this run.
"""
import argparse
import copy
from datetime import timedelta
import hashlib
import json
from pathlib import Path
from queue import Empty, Queue
import re
from threading import Event, Thread
from uuid import uuid4

from delivery_correlation import SCHEMA, correlate, fingerprint, text
from local_evidence import read_json
from tools.build_integrated_context_preview import timestamp, validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/candidate-delivery'
CASES = ('delivered', 'withheld', 'duplicate', 'tampered', 'wrong-session')
DEADLINE = 5
RUNTIME_BASE = 'e55c7dc75d01d88c8fbc6866ff9aca04eed52055'


def base(status):
    return dict(schema='dit.synthetic-delivery-harness.v1', status=status,
                evidenceKind='synthetic', nativeDeliveryVerified=False,
                deliveredInGame=None, replayAuthorized=False, results=[])


def packet(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    if len(raw) > 262144:
        raise ValueError('Oversized synthetic packet')
    return raw


def receipt_key(value):
    return fingerprint(dict(value) | {'scope': dict(value['scope'])})


def checked(result):
    expired = result['candidateScenario'] == 'expired-during-generation'
    case = result['transportCase']
    expected_matches = int(not expired and case in ('delivered', 'duplicate'))
    expected_received = 0 if expired or case == 'withheld' else 2 if case == 'duplicate' else 1
    before, after = result['beforeReceipt'], result['afterReceipt']
    conditions = [result['retainedTurns'] == 12,
                  result['emittedPackets'] == int(not expired), result['receivedPackets'] == expected_received,
                  before['counts']['syntheticConfirmed'] == 0,
                  after['counts']['syntheticConfirmed'] == expected_matches,
                  after['counts']['recordedAttempts'] == int(not expired),
                  after['counts']['publicationMatched'] == int(not expired),
                  after['counts']['duplicateReceiptRecords'] == int(not expired and case == 'duplicate'),
                  after['rejectedReceipts'] == int(not expired and case in ('tampered', 'wrong-session'))]
    if not expired:
        premature = result['issuedBeforeReceive']
        conditions.extend([premature['counts']['syntheticConfirmed'] == 0, premature['rejectedReceipts'] == 1])
    for report in (before, after, *([result['issuedBeforeReceive']] if not expired else [])):
        conditions.extend([report['status'] == 'Loaded', report['nativeDeliveryVerified'] is False,
                           report['deliveredInGame'] is None, report['replayAuthorized'] is False,
                           all(row['actualDelivery'] == 'Unknown' for row in report['records'])])
    if not all(conditions):
        raise RuntimeError('Synthetic harness invariant failed')
    result['check'] = 'Passed'
    return base('Passed') | {'results': [result]}


def publication(data):
    if (data['schema'] != 'dit.candidate-delivery-export.v1' or data['synthetic'] is not True
            or data['scenario'] not in ('fresh', 'expired-during-generation')
            or data['candidateStage'] != 'response prepared or withheld; no native publication'):
        raise ValueError('Synthetic candidate export required')
    capture = validate(data['capture'])
    if data['game'] != capture['game']:
        raise ValueError('Candidate/capture game mismatch')
    binding = capture['statusBinding']
    view = binding['View']
    if view is None or binding['State'] != 'snapshot projected':
        raise ValueError('Expected the captured synthetic status projection')
    published_at = timestamp(data['publishedAtUtc'])
    thread, channel = text(data['thread']), text(data['channel'])
    reply = data['reply']
    if reply['Mode'] != 'live' or reply['LineId'] != 'synthetic-input':
        raise ValueError('Unexpected synthetic candidate route')
    decisions = reply['Decisions']
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise ValueError('Expected one candidate decision')
    decision = decisions[0]
    if (decision['ActorKey'] != binding['Lookup']['ActorKey'] or decision['Channel'] != channel
            or decision['Action'] is not None or decision['Recipient'] is not None):
        raise ValueError('Decision scope or action mismatch')
    scope = dict(game=data['game'], realm=view['Body']['Realm'], instance=view['Body']['Instance'],
                 thread=thread, channel=channel, actorKey=decision['ActorKey'],
                 nativeActorId=view['Body']['NativeActorId'], epoch=view['Epoch'])
    bundle = dict(schema=SCHEMA, synthetic=True, scope=scope, bridgeSession='synthetic-harness-session',
                  decisions=[], inbox=[], receipts=[])
    if data['scenario'] == 'expired-during-generation':
        if (decision['Kind'] != 'silence' or decision['Text'] is not None
                or 'shared status changed' not in decision['Note']):
            raise ValueError('Withheld output must not become a publication')
        return bundle, capture
    if decision['Kind'] != 'say':
        raise ValueError('Expected candidate wording')
    wording, bot = text(decision['Text'], 2048), text(decision['DisplayName'])
    # This sequence/publication is invented by the harness, not emitted by the hub or a game.
    bundle['decisions'] = [dict(schema='dit.chat.decision.v2', game=data['game'], scope=thread,
        channel=channel, replies=[dict(actor_key=scope['actorKey'], bot=bot,
                                       text_final=wording, verdict='sent', inbox_seq=1)])]
    bundle['inbox'] = [dict(seq=1, ts=int(published_at.timestamp()), channel=channel,
                           actorKey=scope['actorKey'], bot=bot, text=wording)]
    return bundle, capture


def exercise(data, case='delivered', *, enabled=False):
    if type(enabled) is not bool:
        raise ValueError('Explicit boolean switch required')
    if not enabled:
        return base('Disabled')
    if case not in CASES:
        raise ValueError('Unknown synthetic transport case')
    bundle, capture = publication(data)
    # A fresh observer run is a distinct synthetic session even when all source
    # bytes and fictional timestamps repeat. Old receipts must not certify it.
    if bundle['inbox']:
        bundle['bridgeSession'] = 'synthetic-harness-' + uuid4().hex
    source_hash = hashlib.sha256(packet(data)).hexdigest()
    result = dict(game=data['game'], candidateScenario=data['scenario'], transportCase=case,
                  exportContentSha256=source_hash, requestId=capture['contextReceipt']['RequestId'],
                  promptSha256=capture['contextReceipt']['PromptSha256'],
                  retainedTurns=capture['contextReceipt']['IncludedHistoryTurns'],
                  syntheticSession=bundle['bridgeSession'] if bundle['inbox'] else None,
                  publicationOrigin='synthetic harness', emittedPackets=0, receivedPackets=0)
    result['beforeReceipt'] = correlate(bundle, enabled=True)
    if not bundle['inbox']:
        result['afterReceipt'] = result['beforeReceipt']
        result['candidateWithheld'] = True
        return checked(result)

    publications, returned = Queue(maxsize=1), Queue(maxsize=2)
    observed, release = Event(), Event()
    issued, received, errors = set(), set(), []
    observed_receipts = []

    def observe():
        try:
            # The worker receives serialized bytes through its own queue, not the producer's object.
            raw = publications.get(timeout=DEADLINE)
            item = json.loads(raw)
            expected = bundle['inbox'][0]
            if item != expected:
                raise ValueError('Publication changed across synthetic transport')
            instant = timestamp(data['publishedAtUtc'])
            receipt = dict(schema='dit.synthetic-chat-receipt.v1', receiptId='synthetic-receipt-1',
                           observationId='synthetic-observation-1', scope=copy.deepcopy(bundle['scope']),
                           bridgeSession=bundle['bridgeSession'], inboxSeq=item['seq'],
                           textSha256=hashlib.sha256(item['text'].encode()).hexdigest(),
                           observedAtUtc=(instant + timedelta(seconds=1)).isoformat(),
                           receivedAtUtc=(instant + timedelta(seconds=2)).isoformat())
            # Times are fictional event labels; this test does not measure native latency.
            issued.add(receipt_key(receipt))
            observed_receipts.append(receipt)
            observed.set()
            if not release.wait(DEADLINE):
                raise TimeoutError('Synthetic receipt release timed out')
            if case == 'withheld':
                return
            outgoing = copy.deepcopy(receipt)
            if case == 'tampered':
                outgoing['textSha256'] = '0' * 64
            if case == 'wrong-session':
                outgoing['bridgeSession'] = 'different-synthetic-session'
            returned.put(packet(outgoing), timeout=DEADLINE)
            if case == 'duplicate':
                returned.put(packet(outgoing), timeout=DEADLINE)
        except Exception as error:
            errors.append(type(error).__name__)
            observed.set()

    def verifier(receipt):
        key = receipt_key(receipt)
        return key in issued and key in received

    worker = Thread(target=observe, name='synthetic-receipt-observer', daemon=True)
    worker.start()
    try:
        publications.put(packet(bundle['inbox'][0]), timeout=DEADLINE)
        result['emittedPackets'] = 1
        if not observed.wait(DEADLINE) or errors:
            raise RuntimeError('Synthetic observer did not complete')
        # Even the exact issued receipt cannot pass until the receiver gets it.
        premature = bundle | {'receipts': copy.deepcopy(observed_receipts)}
        result['issuedBeforeReceive'] = correlate(premature, enabled=True, native_verifier=verifier)
        release.set()
        worker.join(DEADLINE)
        if worker.is_alive() or errors:
            raise RuntimeError('Synthetic receipt transport did not complete')
        receipt_rows = []
        while True:
            try:
                row = json.loads(returned.get_nowait())
            except Empty:
                break
            received.add(receipt_key(row))
            receipt_rows.append(row)
        result['receivedPackets'] = len(receipt_rows)
        result['afterReceipt'] = correlate(bundle | {'receipts': receipt_rows}, enabled=True,
                                           native_verifier=verifier)
        return checked(result)
    finally:
        release.set()
        worker.join(DEADLINE)


def run(*, enabled=False):
    if type(enabled) is not bool:
        raise ValueError('Explicit boolean switch required')
    if not enabled:
        return base('Disabled')
    names = {f'{game}-{state}.json' for game in ('ffxi', 'swtor') for state in ('fresh', 'expired')}
    manifest = read_json(FIXTURES / 'manifest.json', 4096)
    if (manifest['schema'] != 'dit.candidate-delivery-manifest.v1'
            or manifest['runtimeCandidateRevision'] != RUNTIME_BASE
            or not re.fullmatch('[0-9a-f]{40}', manifest['exporterRevision'])
            or not isinstance(manifest['contentSha256'], dict)
            or set(manifest['contentSha256']) != names):
        raise ValueError('Unexpected synthetic export manifest')
    exports = {}
    for name in sorted(names):
        data = read_json(FIXTURES / name, 262144)
        if hashlib.sha256(packet(data)).hexdigest() != manifest['contentSha256'][name]:
            raise ValueError('Synthetic export content changed')
        exports[name] = data
    results = []
    for game in ('ffxi', 'swtor'):
        fresh = exports[game + '-fresh.json']
        for case in CASES:
            results.extend(exercise(fresh, case, enabled=True)['results'])
        expired = exports[game + '-expired.json']
        results.extend(exercise(expired, enabled=True)['results'])
    return base('Passed') | {'runtimeCandidateRevision': RUNTIME_BASE,
                             'exporterRevision': manifest['exporterRevision'], 'results': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enable-offline', action='store_true')
    args = parser.parse_args()
    try:
        report = run(enabled=args.enable_offline)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError, RuntimeError):
        report = base('Unavailable')
    print(json.dumps(report, sort_keys=True))
    return 2 if report['status'] == 'Unavailable' else 0


if __name__ == '__main__':
    raise SystemExit(main())
