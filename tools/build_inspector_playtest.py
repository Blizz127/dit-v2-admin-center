"""Build a synthetic, network-blocked inspector playtest without importing server.py."""
import argparse
import base64
import hashlib
import html as html_escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r10_projection import project_learning


def snapshot():
    payload = json.loads((ROOT / 'tests/fixtures/learning-evidence-e8c81be.json').read_text())
    rows = project_learning(payload)
    for row in rows:
        row['game'] = 'FFXI'
        row['source'] = 'Synthetic candidate fixture; offline runtime harness'
    result = {key: [] for key in (
        'bots', 'leads', 'leadActivity', 'leadMonitoring', 'leadTimeline', 'nudgeHistory',
        'sessionMarkers', 'quotaHistory', 'modelCalls', 'safetyRecords', 'botDetails',
        'replyEvents', 'assignmentHistory', 'audit', 'gameStatus', 'serviceHealth',
        'issues', 'ledger', 'learningArtifacts', 'learningPlan')}
    result.update(generatedAt='2026-01-01T12:00:00Z', learning=rows,
                  hubFeeds=[dict(game='All', view='hub', status='Not configured',
                                 note='Offline harness; no hub access', at=None)],
                  ownerAttention=dict(coverage='Synthetic empty fixture', items=[]),
                  spendExample=dict(month=None, settledUsd=None, reservedOpenUsd=None,
                                    budgetUsd=None, source='Synthetic fixture', attribution='Unknown'))
    return result


def source_fingerprints():
    paths = ('static/index.html', 'static/style.css', 'static/app.js',
             'r10_projection.py', 'tests/fixtures/learning-evidence-e8c81be.json',
             'tests/fixtures/assignment-pages.json',
             'tools/inspector_playtest.js', 'tools/build_inspector_playtest.py')
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}


def build():
    html = (ROOT / 'static/index.html').read_text()
    css = (ROOT / 'static/style.css').read_text()
    app = (ROOT / 'static/app.js').read_text()
    driver = (ROOT / 'tools/inspector_playtest.js').read_text()
    data = json.dumps(snapshot()).replace('<', '\\u003c')
    assignment_data = json.dumps(json.loads((ROOT / 'tests/fixtures/assignment-pages.json').read_text())).replace('<', '\\u003c')
    script = '(async function () {\nconst fixture = ' + data + ';\nconst assignmentFixtures = ' + assignment_data + ';\n' + driver.replace('/* APPLICATION */', app) + '\n})();'
    if '</script' in script.lower() or '</style' in css.lower():
        raise ValueError('Unsafe inline asset terminator')
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    csp = "default-src 'none'; script-src 'sha256-" + digest + "'; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'; base-uri 'none'"
    html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="' + csp + '">', 1)
    assert html.count('<script src="/app.js" defer></script>') == 1
    assert html.count('<link rel="stylesheet" href="/style.css">') == 1
    html = html.replace('<script src="/app.js" defer></script>', '')
    html = html.replace('<link rel="stylesheet" href="/style.css">', '<style>' + css + '</style>')
    html = html.replace('<body>', '<body><section class="panel" id="harness-results" aria-live="polite"><h1>Offline synthetic inspector playtest</h1><p id="harness-status">NOT RUN — waiting for browser JavaScript.</p><ol id="harness-checks"></ol><p>No server, token file, account or game is used. All data is synthetic. Browser results apply only to this artifact, not the running service. Reload this file to rerun.</p></section>', 1)
    fingerprints = html_escape.escape(json.dumps(source_fingerprints(), indent=2))
    provenance = '<details id="harness-provenance"><summary>Artifact source fingerprints</summary><p>SHA256 of local inputs at generation; not a deployment revision or browser result.</p><pre>' + fingerprints + '</pre></details>'
    html = html.replace('<ol id="harness-checks"></ol>', '<ol id="harness-checks"></ol>' + provenance, 1)
    html = html.replace('</body>', '<script>' + script + '</script></body>')
    return html


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/inspector-playtest.html')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build())
    print(f'Created {args.output}; open locally in a browser. Browser checks have NOT run.')
