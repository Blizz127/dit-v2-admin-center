"""Build a synthetic, network-blocked inspector playtest without importing server.py."""
import argparse
import base64
import copy
import hashlib
import html as html_escape
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r10_projection import project_learning
from operation_sources import read as read_operation_sources
from tools.review_party_greeting import decode_metadata, review
from project_issues import read as read_project_issues
from routing_audit import examples as routing_audit_examples
from presence_examples import examples as presence_examples
from baseline_conformance import read as baseline_conformance
from forever_botlog import load as forever_botlog
from ffxi_botsv2_log import read as read_ffxi_botsv2
from bot_event_v1 import read as read_bot_event
from vanilla_botlog import read as read_vanilla_botlog
from local_evidence import read_bytes, read_json


def fixture_json(path, expected):
    try:
        value = read_json(path, 256 * 1024)
        if not isinstance(value, expected):
            raise ValueError('Unexpected fixture type')
        return value
    except (OSError, ValueError, RecursionError) as error:
        raise ValueError('Synthetic preview fixture unavailable') from error


def bot_activity_preview():
    """Committed offline fixtures for the four bot-activity sources; mirrors server.bot_activity() labels and notes."""
    wow = dict(zip(('bots', 'coverage'), forever_botlog(ROOT / 'tests/fixtures/forever-botlog')))
    sources = [
        dict(id='wow-70450-export', label='WoW Forever (70450 predecessor export)',
             note='Exported WoW Forever bot log (70450 predecessor Bots format); not live, not DIT bots, not PlayerbotV2.', **wow),
    ]
    for source_id, label, note, read, path in (
            ('ffxi-lsb', 'FFXI (LSB) Bots V2 log export',
             'Exported [BOTS-V2] map-log lines from the live J1-J4 run (11-09 13:37Z-17:10Z, no human interaction: group trips, chocobos, BLM nukes, three deaths and releases, full-bag returns); offline import (DIT_FFXI_BOTSV2_LOG).',
             read_ffxi_botsv2, ROOT / 'tests/fixtures/ffxi-botsv2/bots-v2-j1234-20261109.log'),
            ('dit-bot-event-v1', 'DIT bot_event v1 (SWTOR, FFXI Forever, other DIT games)',
             'Offline import of dit.bot_event.v1 JSONL (DIT_BOT_EVENT_DIR); includes AI advice rows.',
             read_bot_event, ROOT / 'tests/fixtures/bot-event-v1'),
            ('wow-vanilla-playerbots', 'WoW Vanilla / Benilla playerbots (cmangos-classic event log)',
             'Release-20261109k exported playerbot CSV, 11-09 22:20Z-22:52Z, 473 bots. In 32 min 8 s each (j → k), same-name runs of 10+ pulls without recorded XP or loot fell from 2 to 1; pull share 4.3% → 0.9%; longest 37 → 14; pulls per XP-gain row 1.39 → 1.28. The remaining run spans a respawn. Populations differ; kills with neither signal are invisible. Offline import (DIT_VANILLA_BOTLOG_CSV).',
             read_vanilla_botlog, ROOT / 'tests/fixtures/vanilla-botlog/vanilla-bot_events-release-k-20261109T2219Z.csv')):
        bots, coverage = read(str(path))  # Both readers take an absolute path string, not a Path.
        sources.append(dict(id=source_id, label=label, note=note, bots=bots, coverage=coverage))
    return dict(wow, sources=sources)


def parity_readiness_sources():
    """Separate fictional feeds for import/display readiness, never live parity evidence."""
    sources = []
    for source_id, label, note, read, path in (
            ('ffxi-lsb', 'FFXI post-H1 readiness (synthetic stub)',
             'Fictional post-H1 readiness sample using accepted BOTS-V2 log shapes. Varied timing exercises the reader; '
             'this is not an H1 capture or proof of human-like behavior. Real post-H1 export still required.',
             read_ffxi_botsv2, ROOT / 'tests/fixtures/ffxi-botsv2/synthetic-post-h1-readiness.log'),
            ('dit-bot-event-v1', 'SWTOR readiness (synthetic writer samples)',
             'Existing release kf writer test samples with synthetic actors and timestamps. Covers rotation, refusal, '
             'advice, chat and death shapes; not a real day of play. Real bot-event export still required.',
             read_bot_event, ROOT / 'tests/fixtures/bot-event-swtor')):
        bots, coverage = read(str(path))
        if coverage['status'] != 'Loaded':
            raise ValueError('Synthetic parity readiness fixture unavailable')
        coverage = dict(coverage, reason='Synthetic readiness sample; not live evidence. ' + coverage['reason'])
        sources.append(dict(id=source_id, label=label, note=note, bots=bots, coverage=coverage))
    return sources


def parity_partial_readiness_source():
    """Run a deliberately damaged synthetic copy through the normal SWTOR reader."""
    raw = read_bytes(ROOT / 'tests/fixtures/bot-event-swtor/swtor-kf-writer-samples.jsonl', 256 * 1024)
    if len(raw) > 256 * 1024:
        raise ValueError('Synthetic parity readiness fixture oversized')
    # Keep the original writer sample untouched. The unfinished JSON line is
    # intentional and must never be interpreted as a bot or a producer drop.
    with tempfile.TemporaryDirectory(prefix='dit-parity-readiness-') as temp:
        path = Path(temp) / 'synthetic-partial.jsonl'
        path.write_bytes(raw + b'\n{"synthetic_partial_marker": "OMITTED_SYNTHETIC_ROW",\n')
        bots, coverage = read_bot_event(temp)
    if coverage['status'] != 'Loaded' or coverage['omittedByReason'] != {'invalid_json': 1}:
        raise ValueError('Synthetic partial readiness fixture unavailable')
    coverage = dict(coverage, reason='Synthetic incomplete readiness sample; not live evidence. ' + coverage['reason'])
    return dict(id='dit-bot-event-v1', label='SWTOR readiness (synthetic incomplete export)',
                note='Fictional incomplete SWTOR export: valid events remain visible while one malformed row is rejected. '
                     'Reader omissions and producer-reported loss are separate. '
                     'Real bot-event export still required.', bots=bots, coverage=coverage)


def parity_partial_ffxi_readiness_source():
    """Exercise all three non-imported FFXI line categories without altering the fixture."""
    raw = read_bytes(ROOT / 'tests/fixtures/ffxi-botsv2/synthetic-post-h1-readiness.log', 256 * 1024)
    if len(raw) > 256 * 1024:
        raise ValueError('Synthetic parity readiness fixture oversized')
    # No blank separator: an extra blank line would itself count as ignored.
    extra = (b'[01/01/26 10:15:00:000][map][lua] [BOTS-V2] act readya rule=combat -> ok cast (lua_print:228)\n'
             b'[01/01/26 10:15:01:000][map][lua] [BOTS-V2] synthetic_unknown readya (lua_print:228)\n'
             b'[01/01/26 10:15:02:000][map][lua] synthetic unrelated fixture line (lua_print:228)\n')
    with tempfile.TemporaryDirectory(prefix='dit-parity-readiness-') as temp:
        path = Path(temp) / 'synthetic-partial.log'
        path.write_bytes(raw + (b'' if raw.endswith(b'\n') else b'\n') + extra)
        bots, coverage = read_ffxi_botsv2(str(path))
    if (coverage['status'] != 'Loaded'
            or tuple(coverage[key] for key in ('omitted', 'unrecognized', 'ignored')) != (1, 1, 1)):
        raise ValueError('Synthetic partial FFXI readiness fixture unavailable')
    coverage = dict(coverage, reason='Synthetic incomplete readiness sample; not live evidence. ' + coverage['reason'])
    return dict(id='ffxi-lsb', label='FFXI readiness (synthetic incomplete export)',
                note='Fictional incomplete FFXI export: one malformed bot line, one unrecognized bot line and one '
                     'unrelated log line are counted separately. Valid events remain visible. '
                     'Real post-H1 export still required.', bots=bots, coverage=coverage)


def snapshot():
    payload = fixture_json(ROOT / 'tests/fixtures/learning-evidence-e8c81be.json', dict)
    rows = project_learning(payload)
    for row in rows:
        row['game'] = 'FFXI'
        row['source'] = 'Synthetic candidate fixture; offline runtime harness'
    result = {key: [] for key in (
        'bots', 'leads', 'leadActivity', 'leadMonitoring', 'leadTimeline', 'nudgeHistory',
        'sessionMarkers', 'quotaHistory', 'modelCalls', 'safetyRecords', 'botDetails',
        'replyEvents', 'assignmentHistory', 'audit', 'gameStatus', 'serviceHealth',
        'issues', 'ledger', 'learningArtifacts', 'learningPlan')}
    result.update(presenceExamples=presence_examples(), modelCalls=fixture_json(ROOT / 'data/fixtures/model-comparison.json', list), issues=read_project_issues(), operationSources=read_operation_sources(), generatedAt='2026-01-01T12:00:00Z', learning=rows, routingAudit=routing_audit_examples(),
                  hubFeeds=[dict(game='All', view='hub', status='Not configured',
                                 note='Offline harness; no hub access', at=None)],
                  ownerAttention=dict(coverage='Synthetic empty fixture', items=[]),
                  # Synthetic exported Forever bot log and the committed baseline tracker.
                  botActivity=bot_activity_preview(),
                  baselineConformance=baseline_conformance(),
                  spendExample=dict(month=None, settledUsd=None, reservedOpenUsd=None,
                                    budgetUsd=None, source='Synthetic fixture', attribution='Unknown'))
    return result


def source_fingerprints():
    paths = ('static/index.html', 'static/style.css', 'static/app.js', 'routing_audit.py', 'presence_examples.py', 'data/fixtures/presence-examples.json', 'operation_sources.py', 'local_evidence.py',
             'data/fixtures/routing-audit.json', 'data/fixtures/model-comparison.json', 'project_issues.py', 'docs/LEARNING-AND-ISSUES.md', 'docs/NATIVE-VERIFICATION-GAP.md',
             'r10_projection.py', 'tests/fixtures/learning-evidence-e8c81be.json',
             'tests/fixtures/assignment-pages.json',
             'tests/fixtures/party-greeting-review.json', 'tools/review_party_greeting.py',
             'tools/inspector_playtest.js', 'tools/preview_progress.js', 'tools/assignment_keyboard_playtest.js', 'tools/build_inspector_playtest.py',
             'forever_botlog.py', 'tests/fixtures/forever-botlog/manifest.json', 'tests/fixtures/forever-botlog/bots.jsonl',
             'tests/fixtures/forever-botlog/events.jsonl', 'baseline_conformance.py', 'data/fixtures/baseline-conformance.json',
             'ffxi_botsv2_log.py', 'tests/fixtures/ffxi-botsv2/bots-v2-j1234-20261109.log', 'bot_event_v1.py', 'human_feel.py', 'vanilla_botlog.py',
             'tests/fixtures/vanilla-botlog/vanilla-bot_events-release-k-20261109T2219Z.csv',
             'tests/fixtures/bot-event-v1/EXAMPLES.jsonl',
             'tests/fixtures/ffxi-botsv2/synthetic-post-h1-readiness.log',
             'tests/fixtures/ffxi-botsv2/README.md',
             'tests/fixtures/bot-event-swtor/swtor-kf-writer-samples.jsonl',
             'tests/fixtures/bot-event-swtor/README.md')
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}


def party_review_examples():
    raw = read_bytes(ROOT / 'tests/fixtures/party-greeting-review.json', 256 * 1024)
    if len(raw) > 256 * 1024:
        raise ValueError('Synthetic preview fixture unavailable')
    base = decode_metadata(raw)
    if not isinstance(base, dict):
        raise ValueError('Synthetic preview fixture unavailable')
    owner = copy.deepcopy(base)
    owner['queuedReplies'] = []
    owner['ownerSpeech'] = dict(scope=copy.deepcopy(base['scope']), correlationId=base['greeting']['correlationId'],
                                reporter='owner', confirmed=True, heardAt='2026-01-01T12:01:06Z',
                                reportedAt='2026-01-01T12:01:30Z')
    mixed = copy.deepcopy(base)
    mixed['queuedReplies'].append({**mixed['queuedReplies'][0], 'enqueued': False})
    stale = copy.deepcopy(base)
    stale['queuedReplies'][0]['observedAt'] = '2025-12-31T23:59:00Z'
    return [(label, review(data)) for label, data in (
        ('Queue report only', base), ('Owner report without queue telemetry', owner),
        ('Mixed enqueue claims', mixed), ('Old retained queue row', stale))]


def party_review_html():
    columns = [('queuedReply', 'Queue evidence'), ('queueReview', 'Queue caveat'),
               ('nativeSpeech', 'Owner-reported speech'), ('modelOrigin', 'Model origin')]
    header = '<tr><th scope="col">Synthetic scenario</th>' + ''.join(
        '<th scope="col">' + title + '</th>' for _, title in columns) + '</tr>'
    rows = ''.join('<tr><th scope="row">' + html_escape.escape(label) + '</th>' + ''.join(
        '<td style="padding:8px;vertical-align:top">' + html_escape.escape(result[key]) + '</td>'
        for key, _ in columns) + '</tr>' for label, result in party_review_examples())
    return ('<details class="panel" id="party-review-examples"><summary>Synthetic party-evidence comparisons</summary>'
            '<p>Four fictional summaries, assessed by the offline reviewer at build time. These are not live results '
            'or a browser test pass. Expand this panel to compare; no requests or game messages occur.</p>'
            '<div tabindex="0" role="region" aria-label="Synthetic party evidence table" style="overflow-x:auto">'
            '<table style="min-width:760px;text-align:left"><caption>Queue evidence, owner reports and model origin remain separate</caption>'
            '<thead>' + header + '</thead><tbody>' + rows + '</tbody></table></div>'
            '<p>Reported means supplied metadata, not authenticated observation. Mixed claims may describe a transition; '
            'old rows do not prove a new reply. All four model-origin results remain Unknown.</p></details>')


def build():
    html = (ROOT / 'static/index.html').read_text()
    css = (ROOT / 'static/style.css').read_text()
    app = (ROOT / 'static/app.js').read_text()
    driver = (ROOT / 'tools/preview_progress.js').read_text() + '\n' + (ROOT / 'tools/assignment_keyboard_playtest.js').read_text() + '\n' + (ROOT / 'tools/inspector_playtest.js').read_text()
    data = json.dumps(snapshot()).replace('<', '\\u003c')
    assignment_data = json.dumps(fixture_json(ROOT / 'tests/fixtures/assignment-pages.json', dict)).replace('<', '\\u003c')
    readiness_data = json.dumps(parity_readiness_sources()).replace('<', '\\u003c')
    partial_readiness_data = json.dumps(parity_partial_readiness_source()).replace('<', '\\u003c')
    partial_ffxi_data = json.dumps(parity_partial_ffxi_readiness_source()).replace('<', '\\u003c')
    script = ('(async function () {\nconst fixture = ' + data + ';\nconst assignmentFixtures = ' + assignment_data
              + ';\nconst parityReadinessSources = ' + readiness_data
              + ';\nconst parityPartialReadinessSource = ' + partial_readiness_data
              + ';\nconst parityPartialFfxiReadinessSource = ' + partial_ffxi_data
              + ';\n' + driver.replace('/* APPLICATION */', app) + '\n})();')
    if '</script' in script.lower() or '</style' in css.lower():
        raise ValueError('Unsafe inline asset terminator')
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    csp = "default-src 'none'; script-src 'sha256-" + digest + "'; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'; base-uri 'none'"
    html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="' + csp + '">', 1)
    assert html.count('<script src="/app.js" defer></script>') == 1
    assert html.count('<link rel="stylesheet" href="/style.css">') == 1
    html = html.replace('<script src="/app.js" defer></script>', '')
    html = html.replace('<link rel="stylesheet" href="/style.css">', '<style>' + css + '</style>')
    # Keep the preview recognizably the product. Verification detail is still available,
    # but does not occupy the first screen or imply that synthetic rows are live.
    html = html.replace('LOCAL · MIXED SOURCES', 'OFFLINE · SYNTHETIC', 1)
    html = html.replace('<strong>Local workspace.</strong> Check each data source below; synthetic fallback is labeled. Hub access is read-only, and model controls are unavailable.',
                        '<strong>Synthetic preview.</strong> Explore the layout with fictional records. No live connection or token is used. Model controls stay disabled. <a href="#harness-results">Preview checks ↓</a>', 1)
    html = html.replace('<form id="login" class="login-panel">', '<form id="login" class="login-panel" hidden>', 1)
    html = html.replace('Try configured read-only hub', 'Simulated hub responses (offline)', 1)
    html = html.replace('Select the hub to request read-only roster and learning data. Missing feeds fall back to examples. Model controls remain disabled.',
                        'Both sources use only embedded fictional records in this file. No network requests are made.', 1)
    readiness = ('<div class="filter-field"><label for="parity-sample">Bot activity sample</label>'
                 '<select id="parity-sample" aria-describedby="parity-sample-note" disabled>'
                 '<option value="exports">Recorded exports and schema examples</option>'
                 '<option value="readiness">Synthetic FFXI + SWTOR readiness</option>'
                 '<option value="partial">Synthetic SWTOR import with a malformed row</option>'
                 '<option value="partial-ffxi">Synthetic FFXI import with skipped lines</option></select>'
                 '<p id="parity-sample-note" class="muted" role="status">Readiness samples are fictional; '
                 'they do not verify live bot behavior. Parity tracker evidence is unchanged.</p></div>')
    html = html.replace('<div class="bot-source" id="bot-source-wow">', readiness + '<div class="bot-source" id="bot-source-wow">', 1)
    report = ('<details class="panel preview-report" id="harness-results"><summary>Preview verification &amp; source details</summary>'
              '<h2>Offline synthetic inspector playtest</h2><p id="harness-status" role="status" aria-live="polite">NOT RUN — waiting for browser JavaScript.</p>'
              '<ol id="harness-checks"></ol><p>No server, token file, account or game is used. Runtime test data is synthetic. Dated deployment handoffs are labeled separately and are not live observations. Browser results apply only to this artifact, not the running service. Reload this file to rerun.</p></details>')
    html = html.replace('</main>', party_review_html() + report + '</main>', 1)
    keyboard = '<p id="keyboard-status" role="status" aria-live="polite">NOT RUN — native keyboard check. Automatic DOM checks do not verify keyboard defaults.</p><button id="keyboard-start" type="button" disabled aria-describedby="keyboard-status">Start native assignment keyboard check</button>'
    html = html.replace('<p id="assignment-count"', keyboard + '<p id="assignment-count"', 1)
    for location, marker in [('overview', '<div id="data-coverage"'), ('assignment', '<p id="assignment-count"')]:
        progress = ('<details class="preview-report"><summary id="preview-progress-label-' + location + '">Local preview checks: NOT RUN</summary>'
                    '<p>5-second no-progress limit; 10-second total limit. This observes preview checks, not bots or services. '
                    'Reload this file to start a new check run.</p>'
                    '<p id="preview-progress-' + location + '" data-state="not-run">NOT RUN</p>'
                    '<button type="button" id="preview-progress-log-' + location + '">Open check log</button></details>')
        html = html.replace(marker, progress + marker, 1)
    fingerprints = html_escape.escape(json.dumps(source_fingerprints(), indent=2))
    provenance = '<details id="harness-provenance"><summary>Artifact source fingerprints</summary><p>SHA256 of local inputs at generation; not a deployment revision or browser result.</p><pre>' + fingerprints + '</pre></details>'
    html = html.replace('<ol id="harness-checks"></ol>', '<ol id="harness-checks"></ol>' + provenance, 1)
    html = html.replace('</body>', '<script>' + script + '</script></body>')
    return html


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/inspector-playtest.html')
    args = parser.parse_args()
    try:
        content = build()
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        parser.exit(1, 'Synthetic preview inputs unavailable; no artifact written.\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content)
    print(f'Created {args.output}; open locally in a browser. Browser checks have NOT run.')
