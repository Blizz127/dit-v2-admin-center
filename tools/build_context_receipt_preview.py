"""Inspect synthetic receipts captured by the offline hub context tests.

No hub access, provider request or runtime configuration is performed.
"""
import argparse
import hashlib
import html
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_evidence import read_json


def utf16_length(value):
    return len(value.encode('utf-16-le')) // 2


def validate(data):
    if not isinstance(data, dict) or data.get('synthetic') is not True or data.get('schema') != 'dit.context-preview.v1':
        raise ValueError('Synthetic context receipt required')
    if data.get('game') not in ('ffxi', 'swtor') or type(data.get('rewrite')) is not bool:
        raise ValueError('Invalid fixture scope')
    if data.get('status') != 'not implemented' or data.get('delivery') != 'not attempted' or data.get('tokens') is not None:
        raise ValueError('Fixture must retain its verification limits')
    for key in ('systemMessage', 'userMessage', 'currentMessage'):
        if not isinstance(data.get(key), str) or not data[key] or utf16_length(data[key]) > 24576:
            raise ValueError('Invalid bounded prompt text')
    history, receipt = data.get('suppliedHistory'), data.get('receipt')
    if not isinstance(history, list) or len(history) > 32 or any(
            not isinstance(x, str) or not x.strip() or utf16_length(x) > 512 for x in history):
        raise ValueError('Invalid history')
    if utf16_length(data['currentMessage']) > 512 or not isinstance(receipt, dict):
        raise ValueError('Invalid receipt')
    for key in ('SuppliedHistoryTurns', 'IncludedHistoryTurns', 'OmittedHistoryTurns', 'SerializedCharacters', 'MaximumSerializedCharacters'):
        if type(receipt.get(key)) is not int or receipt[key] < 0:
            raise ValueError('Invalid coverage count')
    supplied, included, omitted = (receipt[k] for k in ('SuppliedHistoryTurns', 'IncludedHistoryTurns', 'OmittedHistoryTurns'))
    if supplied != len(history) or included + omitted != supplied or included > supplied:
        raise ValueError('Coverage counts disagree')
    system, user = data['systemMessage'], data['userMessage']
    size = utf16_length(system) + utf16_length(user)
    if receipt['MaximumSerializedCharacters'] != 24576 or receipt['SerializedCharacters'] != size or size > 24576:
        raise ValueError('Serialized size disagrees')
    encoded = f'{utf16_length(system)}:{system}{utf16_length(user)}:{user}'.encode()
    if receipt.get('PromptSha256') != hashlib.sha256(encoded).hexdigest():
        raise ValueError('Prompt digest disagrees')
    if not isinstance(receipt.get('RequestId'), str) or not re.fullmatch(r'dit-wording-[0-9a-f]{64}', receipt['RequestId']):
        raise ValueError('Invalid request identity')
    # Check the retained chronological suffix and explicit latest input in the
    # supplied prompt. This validates internal consistency, not authenticity.
    cursor = user.find('UNTRUSTED RECENT CONVERSATION\n')
    if cursor < 0:
        raise ValueError('Missing conversation section')
    for turn in history[omitted:]:
        normalized = ' '.join(turn.split())
        cursor = user.find('- ' + normalized, cursor)
        if cursor < 0:
            raise ValueError('Retained history missing or reordered')
        cursor += len(normalized) + 2
    if user.find('LATEST LINE, the one you are answering: ' + ' '.join(data['currentMessage'].split()), cursor) < 0:
        raise ValueError('Current input missing')
    return data


def build(records):
    if not 1 <= len(records) <= 8:
        raise ValueError('One to eight synthetic receipts required')
    sections = []
    for data in records:
        validate(data)
        r = data['receipt']
        esc = html.escape
        title = data['game'].upper() + (' · rewrite' if data['rewrite'] else ' · reply')
        turns = ''.join('<li>' + esc(x) + '</li>' for x in data['suppliedHistory'][r['OmittedHistoryTurns']:])
        sections.append(f'''<section><h2>{esc(title)}</h2>
<p><strong>{r['IncludedHistoryTurns']} of {r['SuppliedHistoryTurns']} supplied turns included</strong> · {r['OmittedHistoryTurns']} omitted</p>
<p>{r['SerializedCharacters']:,} / {r['MaximumSerializedCharacters']:,} UTF-16 characters in the serialized prompt. Token count: unknown.</p>
<h3>Retained conversation</h3><ol>{turns}</ol><p><strong>Current input:</strong> {esc(data['currentMessage'])}</p>
<details><summary>Exact provider-neutral prompt</summary><h3>System</h3><pre>{esc(data['systemMessage'])}</pre><h3>User</h3><pre>{esc(data['userMessage'])}</pre></details>
<details><summary>Receipt identity</summary><p>Request: <code>{esc(r['RequestId'])}</code></p><p>Prompt SHA-256: <code>{esc(r['PromptSha256'])}</code></p></details></section>''')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>DIT · Context receipt preview</title><style>body{max-width:1100px;margin:40px auto;padding:0 22px;background:#0b1220;color:#eff5ff;font:18px/1.5 system-ui}h1,h2{color:#57e0d1}section{background:#152338;border:1px solid #2c405c;border-radius:14px;padding:24px;margin:26px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:15px}code{overflow-wrap:anywhere}summary{cursor:pointer}aside{color:#ffd27b}</style>
<h1>What reached the reply prompt</h1><p>Offline synthetic captures from the shared hub request builder and provider JSON serializer.</p>
<aside>These are supplied test artifacts. Digest equality checks consistency, not authenticity, model understanding or live delivery. Shared status projection: not implemented. Native delivery: not attempted.</aside>
''' + ''.join(sections) + '</html>\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipts', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if len(args.receipts) > 8:
            raise ValueError('Too many receipts')
        result = build([read_json(p, 262144) for p in args.receipts])
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        parser.exit(2, 'Invalid or unavailable synthetic context receipt; no preview written.\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result)
    print('Created synthetic context preview: ' + str(args.output))


if __name__ == '__main__':
    main()
