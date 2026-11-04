"""Build the actual context panel with embedded fixtures and network disabled."""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path

from tools.build_inspector_playtest import ROOT, snapshot, fixture_json
from tools.build_integrated_context_preview import validate


def build():
    paths = sorted((ROOT / 'tests/fixtures/context-status-integration').glob('*.json'))
    if len(paths) != 6:
        raise ValueError('Expected six synthetic integration captures')
    captures = {p.stem: validate(fixture_json(p, dict)) for p in paths}
    sources = [ROOT / name for name in ('static/index.html', 'static/app.js', 'static/style.css',
                                       'tools/build_context_capture_playtest.py')]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources + paths}
    payload = json.dumps({'overview': snapshot(), 'captures': captures}).replace('<', '\\u003c')
    app = (ROOT / 'static/app.js').read_text()
    script = '''(function () {
const fixtures = PAYLOAD;
const sessionStorage = {getItem: () => 'synthetic-fixture-token', setItem() {}, removeItem() {}};
const setInterval = () => 0;
let releaseResponse = null;
const fetch = async (url, options = {}) => {
  if (options.method && options.method !== 'GET') throw new Error('Only fixture GETs allowed');
  if (url === '/api/overview?source=mock' || url === '/api/overview?source=hub')
    return {ok:true, json:async()=>structuredClone(fixtures.overview)};
  if (url === '/api/bridge-status') return {ok:true, json:async()=>({unit:'Unknown', source:'Synthetic fixture'})};
  if (url !== '/api/context-capture') throw new Error('No fixture: network forbidden');
  const scenario = document.getElementById('fixture-scenario').value;
  let result;
  if (scenario === 'unconfigured') result = {status:'Not configured', capture:null};
  else if (scenario === 'unavailable') result = {status:'Unavailable', capture:null};
  else if (scenario === 'auth-error') return {ok:false, status:401};
  else {
    const selected = document.getElementById('fixture-capture').value;
    const capture = structuredClone(fixtures.captures[selected]);
    if (scenario === 'invalid') { capture.statusBinding.View.Fields[0].State = 'Unknown'; capture.statusBinding.View.Fields[0].Value = 'BAD_WITHHELD_VALUE'; }
    result = {status:'Loaded', capture};
  }
  if (scenario === 'delayed') return new Promise(resolve => { releaseResponse = () => resolve({ok:true, json:async()=>result}); });
  return {ok:true, json:async()=>result};
};
/* APPLICATION */
document.getElementById('fixture-reset').addEventListener('click', () => resetPanelSession());
document.getElementById('fixture-release').addEventListener('click', () => { releaseResponse?.(); releaseResponse = null; });
document.querySelectorAll('a').forEach(a => { if (!a.getAttribute('href')?.startsWith('#')) a.href = '#context-fixture'; });
})();'''.replace('PAYLOAD', payload, 1).replace('/* APPLICATION */', app)
    css = (ROOT / 'static/style.css').read_text()
    if '</script' in script.lower() or '</style' in css.lower():
        raise ValueError('Unsafe inline terminator')
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    csp = f"default-src 'none'; script-src 'sha256-{digest}'; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'; base-uri 'none'"
    page = (ROOT / 'static/index.html').read_text()
    page = page.replace('<meta charset="utf-8">', '<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="' + csp + '">', 1)
    page = page.replace('<link rel="stylesheet" href="/style.css">', '<style>' + css + '</style>')
    page = page.replace('<script src="/app.js" defer></script>', '')
    options = ''.join(f'<option value="{html.escape(key)}">{html.escape(key)}</option>' for key in captures)
    controls = ('<section class="panel" id="context-fixture"><h2>Offline conversation panel preview</h2>'
                '<p>Native browser validation: NOT RUN. All responses are synthetic and embedded. '
                'No authentication, file read, model call or delivery is tested by this file.</p>'
                '<label>Capture <select id="fixture-capture">' + options + '</select></label>'
                '<label>Response <select id="fixture-scenario"><option value="loaded">Loaded</option>'
                '<option value="unconfigured">Not configured</option><option value="unavailable">Unavailable</option>'
                '<option value="invalid">Invalid field</option><option value="auth-error">HTTP error fixture</option>'
                '<option value="delayed">Delayed response</option></select></label>'
                '<p>Choose a response, then use “Load configured offline capture” in Bots. '
                'Switching this selector alone does not reload.</p><button id="fixture-reset" type="button">Reset panel session</button>'
                '<button id="fixture-release" type="button">Release delayed response</button>'
                '<details><summary>Input SHA-256 fingerprints</summary><pre>' + html.escape(json.dumps(hashes, indent=2)) + '</pre></details></section>')
    page = page.replace('<main', controls + '<main', 1)
    page = page.replace('LOCAL · MIXED SOURCES', 'OFFLINE · SYNTHETIC', 1)
    page = page.replace('</body>', '<script>' + script + '</script></body>')
    return page


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/context-slice/Context-Panel-Playtest.html')
    args = parser.parse_args()
    page = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page)
    print(f'Created {args.output}; native browser NOT RUN')
