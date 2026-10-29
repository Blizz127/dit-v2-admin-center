"""Review supplied, redacted party-test metadata offline; never collect live data.

This local review format is not a hub/inbox schema or an authenticity verifier.
Reported states describe supplied evidence only, not independently verified facts.
"""
import argparse
from datetime import datetime
import json
import math
from pathlib import Path


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return result if result.utcoffset() is not None else None
    except (ValueError, OverflowError):
        return None


def review(data):
    result = dict(eligibility='Unknown', greeting='Unknown', queuedReply='Unknown', queueReview='Unknown',
                  nativeSpeech='Unknown', modelOrigin='Unknown',
                  coverage='Supplied metadata only; not authenticated or independently observed. No live data read.',
                  nextStep='Review missing evidence with the DIT lead; do not replay chat or restart automatically.')
    if not isinstance(data, dict):
        return result
    scope = data.get('scope')
    if (not isinstance(scope, dict) or scope.get('game') != 'ffxi'
            or any(not isinstance(scope.get(key), str) or not scope[key].strip()
                   for key in ('realm', 'party', 'botId'))):
        return result
    eligible = data.get('eligibility')
    if not isinstance(eligible, dict):
        return result
    restart, through = timestamp(data.get('restartAt')), timestamp(data.get('observedThrough'))
    checked = timestamp(eligible.get('observedAt'))
    greeting = data.get('greeting')
    if not isinstance(greeting, dict):
        return result
    sent = timestamp(greeting.get('observedAt'))
    correlation = greeting.get('correlationId')
    if (not restart or not through or not checked or not sent
            or not restart <= checked <= sent <= through
            or eligible.get('identityVerified') is not True or eligible.get('partyMember') is not True
            or eligible.get('scope') != scope):
        return result
    result['eligibility'] = 'Reported for this scoped attempt; not a continuing presence guarantee'
    if (not restart < sent or greeting.get('scope') != scope
            or greeting.get('ownerGenerated') is not True
            or not isinstance(correlation, str) or not correlation.strip()):
        return result
    result['greeting'] = 'Reported after restart with explicit scope and correlation'

    def matching(record):
        return (isinstance(record, dict) and record.get('scope') == scope
                and record.get('correlationId') == correlation)

    queue = data.get('queuedReplies')
    if isinstance(queue, list):
        positive = negative = 0
        for row in queue:
            at = timestamp(row.get('observedAt')) if isinstance(row, dict) else None
            if matching(row) and at and sent <= at <= through:
                positive += row.get('enqueued') is True
                negative += row.get('enqueued') is False
        if positive:
            result['queuedReply'] = 'Reported matching new queue entry; not native speech'
            result['queueReview'] = ('Multiple positive reports; distinct replies are not established'
                                     if positive > 1 else 'One positive report; complete queue coverage is not established')
        if negative:
            result['queueReview'] = ('Mixed enqueue claims; review chronology and record identity before concluding an outcome'
                                     if positive else 'Non-enqueue reports only; these do not prove no reply occurred')
    speech = data.get('ownerSpeech')
    if matching(speech):
        heard, reported = timestamp(speech.get('heardAt')), timestamp(speech.get('reportedAt'))
        if (speech.get('confirmed') is True and speech.get('reporter') == 'owner'
                and heard and reported and sent <= heard <= reported <= through):
            result['nativeSpeech'] = 'Owner-reported visible party reply for this attempt; not proof of AI'
    # Service state, final trace labels, queue counts and claimed model tags are
    # deliberately not promoted into speech or model-origin evidence.
    return result


def decode_metadata(raw):
    def object_fields(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('ambiguous metadata')
            result[key] = value
        return result

    def invalid_constant(_):
        raise ValueError('invalid metadata number')

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('invalid metadata number')
        return result

    return json.loads(raw, object_pairs_hook=object_fields, parse_constant=invalid_constant,
                      parse_float=finite_float)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('metadata', type=Path, help='Explicit local redacted review JSON; no live collection')
    args = parser.parse_args()
    try:
        with args.metadata.open('rb') as source:
            raw = source.read(65537)
        if len(raw) > 65536:
            raise ValueError('oversized')
        data = decode_metadata(raw)
    except (OSError, ValueError, RecursionError):
        parser.exit(2, 'Unavailable or invalid review metadata; no evidence assessed.\n')
    print(json.dumps(review(data), indent=2))


if __name__ == '__main__':
    main()
