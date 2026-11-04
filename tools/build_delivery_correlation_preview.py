"""Create a standalone synthetic delivery-evidence preview; never launch a browser."""
import argparse
import copy
import hashlib
import html
import json
from pathlib import Path

from delivery_correlation import LIMIT, correlate
from local_evidence import read_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/delivery-correlation'


def scenarios():
    ffxi, swtor = (read_json(FIXTURES / (game + '.json'), LIMIT) for game in ('ffxi', 'swtor'))
    conflict = copy.deepcopy(ffxi)
    conflict['receipts'][1]['observationId'] = conflict['receipts'][0]['observationId']
    publication_conflict = copy.deepcopy(ffxi)
    publication_conflict['inbox'].append(publication_conflict['inbox'][0] | {'text': 'A conflicting synthetic line'})
    repeated = copy.deepcopy(ffxi)
    repeated['receipts'].append(repeated['receipts'][0] | dict(receiptId='later-fixture-receipt', receivedAtUtc='2030-01-01T00:00:30Z'))
    verify_fixture = lambda _: True
    return [
        ('FFXI publication only', correlate(ffxi, enabled=True)),
        ('FFXI synthetic native matches', correlate(ffxi, enabled=True, native_verifier=verify_fixture)),
        ('FFXI conflicting native observation IDs', correlate(conflict, enabled=True, native_verifier=verify_fixture)),
        ('FFXI conflicting publication records', correlate(publication_conflict, enabled=True, native_verifier=verify_fixture)),
        ('SWTOR synthetic native matches', correlate(swtor, enabled=True, native_verifier=verify_fixture)),
        ('Disabled reader', correlate()),
        ('Unavailable capture', correlate({}, enabled=True)),
        ('FFXI repeated observation receipts', correlate(repeated, enabled=True, native_verifier=verify_fixture)),
    ]


def build():
    esc, sections = html.escape, []
    for name, report in scenarios():
        if report['deliveredInGame'] is not None or report['nativeDeliveryVerified'] is not False or report['replayAuthorized'] is not False:
            raise ValueError('Offline report cannot assert actual delivery or replay authority')
        scope = report['scope']
        identity = 'No scoped records loaded.' if scope is None else ' / '.join(scope.values())
        counts = report['counts']
        coverage = 'Counts unavailable.' if counts is None else (
            f"{counts['recordedAttempts']} recorded attempts; {counts['publicationMatched']} publication matches; "
            f"{counts['syntheticConfirmed']} synthetic native matches; {counts['conflicted']} conflicts. "
            f"{report['rejectedReceipts']} receipts rejected or unverified.")
        rows = []
        for record in report['records']:
            wording = 'Wording withheld: publication conflict' if record['publication'] == 'Conflict' else record['text'] or 'No final text'
            cells = [str(record['inboxSeq']) if record['inboxSeq'] is not None else 'No sequence',
                     wording, record['publication'], record['fixtureConfirmation'],
                     record['actualDelivery'], record['observedAtUtc'] or 'Unknown', record['receivedAtUtc'] or 'Unknown', record['reason']]
            rows.append('<tr>' + ''.join('<td>' + esc(cell) + '</td>' for cell in cells) + '</tr>')
        table = ('<div class="scroll" tabindex="0" role="region" aria-label="' + esc(name) + ' records"><table><thead><tr>'
                 '<th>Inbox sequence</th><th>Final wording</th><th>Publication</th><th>Fixture confirmation</th>'
                 '<th>Actual game delivery</th><th>Native observation time (fixture)</th><th>Receipt time (fixture; earliest supplied)</th><th>Reason</th>'
                 '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>') if rows else '<p>No records displayed.</p>'
        sections.append('<section><h2>' + esc(name) + '</h2><p>Status: ' + esc(report['status']) + '</p><p>' + esc(identity) +
                        '</p><p>' + esc(coverage) + '</p>' + table + '<p>' + esc(report['coverage']) + '</p>' +
                        '<details><summary>Exact synthetic correlation report</summary><pre>' +
                        esc(json.dumps(report, indent=2)) + '</pre></details></section>')
    sources = [ROOT / 'delivery_correlation.py', ROOT / 'tools/build_delivery_correlation_preview.py',
               FIXTURES / 'ffxi.json', FIXTURES / 'swtor.json']
    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>DIT · Offline delivery evidence</title><style>
body{font:17px/1.5 system-ui;background:#0c1524;color:#eff5ff;max-width:1300px;margin:32px auto;padding:0 18px}h1,h2{color:#62e6d4}
section{padding:18px;background:#17273d;margin:24px 0;border-radius:12px}aside{padding:18px;border:2px solid #ffd27b;color:#ffe1a1}
.scroll{overflow:auto;max-width:100%}table{border-collapse:collapse;min-width:1000px}td,th{border:1px solid #52667e;padding:10px;text-align:left;vertical-align:top}
td{overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer;padding:8px}:focus-visible{outline:3px solid #ffd27b;outline-offset:3px}
</style></head><body><h1>Which replies have delivery evidence?</h1>
<aside><strong>Actual in-game delivery: Unknown.</strong> This entire preview uses synthetic records. Inbox publication is not speech.
Even a synthetic native match is not a real receipt. No game, model, inbox writer or replay is connected. Native browser: NOT RUN.</aside>
<p>FFXI records follow inspected decision/inbox field shapes. SWTOR uses the same shape only as a synthetic cross-game example; no native SWTOR log contract is established.</p>
''' + ''.join(sections) + '<details><summary>Input SHA-256 fingerprints</summary><pre>' + esc(json.dumps(hashes, indent=2)) + '</pre></details></body></html>\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/context-slice/Delivery-Evidence-Preview.html')
    args = parser.parse_args()
    page = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page)
    print(f'Created {args.output}; synthetic only, native browser NOT RUN')
