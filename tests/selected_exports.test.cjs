// Exact generated selected-export artifact in the installed DOM runtime.
// No native browser, live server, network, or private input is used.
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {performance} = require('node:perf_hooks');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = execFileSync('python3', ['-c',
  'from tools.build_inspector_playtest import build, ROOT; print(build(ffxi_log=ROOT / "tests/fixtures/ffxi-botsv2/synthetic-post-h1-readiness.log"), end="")'],
  {cwd: root, encoding: 'utf8', timeout: 10000, maxBuffer: 4 * 1024 * 1024});
const attempts = [];
const deny = label => () => { attempts.push(label); throw new Error('Network forbidden: ' + label); };
require('node:net').Socket.prototype.connect = deny('socket');
for (const name of ['node:http', 'node:https']) {
  require(name).request = deny(name); require(name).get = deny(name);
}
require('node:tls').connect = deny('tls');
globalThis.fetch = deny('fetch');
const {JSDOM, ResourceLoader, VirtualConsole} = require(process.env.DIT_JSDOM_MODULE || 'jsdom');
class OfflineResources extends ResourceLoader { fetch() { return deny('resource')(); } }
const errors = [], urls = new Set(), virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', error => errors.push(error.message));
const dom = new JSDOM(html, {
  url: 'https://offline.invalid/', runScripts: 'dangerously', resources: new OfflineResources(), virtualConsole,
  beforeParse(window) {
    window.structuredClone = structuredClone;
    window.Blob = Blob;
    window.URL.createObjectURL = blob => { const url = URL.createObjectURL(blob); urls.add(url); return url; };
    window.URL.revokeObjectURL = url => { urls.delete(url); URL.revokeObjectURL(url); };
    window.HTMLElement.prototype.scrollIntoView = function () {};
    window.fetch = deny('window.fetch'); window.XMLHttpRequest = deny('XHR');
    window.WebSocket = deny('WebSocket'); window.EventSource = deny('EventSource');
  },
});
const doc = dom.window.document;
const waitFor = async condition => {
  const deadline = performance.now() + 15000;
  while (!condition()) {
    assert.equal(errors.length, 0, errors.join('; '));
    assert.ok(performance.now() < deadline, 'DOM check timed out');
    await new Promise(resolve => setTimeout(resolve, 10));
  }
};
(async () => {
  await waitFor(() => doc.documentElement.dataset.playtest);
  assert.equal(doc.documentElement.dataset.playtest, 'passed', doc.getElementById('harness-status').textContent);
  const selector = doc.getElementById('parity-sample');
  assert.equal(selector.value, 'selected');
  const parity = doc.getElementById('baseline-conformance').textContent;
  const selectedText = () => doc.getElementById('bot-activity-sources').textContent;
  const verifySelected = () => {
    assert.match(doc.getElementById('bot-activity-coverage').textContent, /Coverage: Off/);
    const sources = [...doc.querySelectorAll('#bot-activity-sources .bot-source')];
    assert.match(sources[0].textContent, /Imported log rows: 52/);
    assert.match(sources[0].textContent, /readya/);
    assert.doesNotMatch(sources[0].textContent, /Tomoe|Fumika/);
    assert.match(sources[1].textContent, /Coverage: Off/);
    assert.match(sources[2].textContent, /Coverage: Off/);
    assert.equal(doc.getElementById('baseline-conformance').textContent, parity);
  };
  verifySelected();
  const original = selectedText();
  const select = value => { selector.value = value; selector.dispatchEvent(new dom.window.Event('change', {bubbles: true})); };
  select('exports');
  assert.notEqual(selectedText(), original);
  select('selected'); verifySelected(); assert.equal(selectedText(), original);
  select('readiness');
  assert.match(selectedText(), /SWTOR readiness/);
  select('selected'); verifySelected(); assert.equal(selectedText(), original);
  doc.getElementById('updated').textContent = '';
  doc.getElementById('refresh').click();
  await waitFor(() => doc.getElementById('updated').textContent.startsWith('Snapshot generated'));
  verifySelected(); assert.equal(selector.value, 'selected');
  assert.equal(errors.length, 0, errors.join('; '));
  assert.equal(attempts.length, 0, 'No network transports');
  assert.equal(doc.documentElement.dataset.keyboardPlaytest, 'not-run');
  console.log('PASS: selected exports start selected, omit unselected sources, recover after sample switches and refresh, preserve parity evidence; zero transports. Simulated DOM only.');
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => {
  dom.window.close(); for (const url of urls) URL.revokeObjectURL(url);
});
