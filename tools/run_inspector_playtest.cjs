// Execute the generated inspector artifact in an installed, offline jsdom runtime.
// A missing dependency is an error, never a skipped/passing browser check.
const path = require('node:path');
const crypto = require('node:crypto');
const {performance} = require('node:perf_hooks');
const {execFileSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const runtime = process.env.DIT_JSDOM_MODULE || 'jsdom';
let runtimePath;
try {
  runtimePath = require.resolve(runtime);
} catch {
  console.error('BLOCKED: jsdom is not installed. Supply an existing module with DIT_JSDOM_MODULE. No download attempted.');
  process.exit(2);
}
const blocked = [];
const deny = label => function () { blocked.push(label); throw new Error('Network forbidden: ' + label); };
require('node:net').Socket.prototype.connect = deny('net.Socket.connect');
for (const [name, methods] of [
  ['node:http', ['request', 'get']], ['node:https', ['request', 'get']],
  ['node:tls', ['connect']], ['node:dns', ['lookup', 'resolve']],
]) {
  const module = require(name);
  for (const method of methods) module[method] = deny(name + '.' + method);
}
globalThis.fetch = deny('global fetch');
const {JSDOM, ResourceLoader, VirtualConsole} = require(runtimePath);
class OfflineResources extends ResourceLoader {
  fetch() { return deny('DOM resource')(); }
}
const errors = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', error => errors.push(error.message));
// Generate in memory; this imports only the pure projection, never server.py.
const html = execFileSync(process.env.PYTHON || 'python3', ['-c',
  'from tools.build_inspector_playtest import build; print(build(), end="")'],
  {cwd: root, encoding: 'utf8', timeout: 10000, maxBuffer: 2 * 1024 * 1024});
const objectUrls = new Set();
const constructionStarted = performance.now();
const dom = new JSDOM(html, {
  url: 'https://offline.invalid/', runScripts: 'dangerously',
  resources: new OfflineResources(), virtualConsole,
  beforeParse(window) {
    window.structuredClone = globalThis.structuredClone;
    // jsdom supplies a DOM engine, not these browser facilities. Use Node's
    // in-memory Blob implementation and make unsupported scrolling a no-op.
    // Receipt limitations explicitly exclude downloads, scrolling and layout.
    window.Blob = globalThis.Blob;
    window.URL.createObjectURL = blob => {
      const url = URL.createObjectURL(blob); objectUrls.add(url); return url;
    };
    window.URL.revokeObjectURL = url => {objectUrls.delete(url); URL.revokeObjectURL(url);};
    window.HTMLElement.prototype.scrollIntoView = function () {};
    window.fetch = deny('window.fetch');
    window.XMLHttpRequest = deny('XMLHttpRequest');
    window.WebSocket = deny('WebSocket');
    window.EventSource = deny('EventSource');
  },
});
const constructedAt = performance.now();
const artifactSha256 = crypto.createHash('sha256').update(html).digest('hex');
(async () => {
  const started = performance.now();
  try {
    const deadline = started + 5000;
    while (!dom.window.document.documentElement.dataset.playtest) {
      if (errors.length) throw new Error('DOM runtime errors: ' + errors.join('; '));
      if (performance.now() > deadline) throw Object.assign(new Error('Harness did not finish within five seconds'), {code:'DOM_COMPLETION_TIMEOUT'});
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    const doc = dom.window.document;
    if (doc.documentElement.dataset.playtest !== 'passed') throw new Error(doc.querySelector('#harness-status').textContent);
    if (blocked.length) throw new Error('Blocked transport attempts: ' + blocked.join(', '));
    if (errors.length) throw new Error('DOM runtime errors: ' + errors.join('; '));
    const checks = [...doc.querySelectorAll('#harness-checks li')];
    if (checks.length < 20 || checks.some(row => !row.textContent.startsWith('PASS — '))) throw new Error('Incomplete runtime assertions');
    const result = {status: 'passed', runtime: 'jsdom', checks: checks.length, transportAttempts: blocked.length,
      artifactSha256,
      timingMs: {construction: Math.round(constructedAt - constructionStarted), completionWait: Math.round(performance.now() - started)},
      shims: ['Node Blob/object URLs', 'scrollIntoView no-op'],
      nativeKeyboard: doc.documentElement.dataset.keyboardPlaytest || 'unknown',
      limitations: 'DOM execution only; no native keyboard activation, browser rendering, scrolling, file download, CSP enforcement, HTTP server or deployed-service verification'};
    console.log(JSON.stringify(result));
  } catch (error) {
    console.error('FAIL: ' + error.message);
    const checks = [...dom.window.document.querySelectorAll('#harness-checks li')];
    console.error('DIAGNOSTIC: ' + JSON.stringify({status:'failed',
      reason: error.code === 'DOM_COMPLETION_TIMEOUT' ? 'completion-timeout' : 'runtime-or-assertion',
      artifactSha256, completedChecks:checks.length,
      lastCheck:(checks.at(-1)?.textContent || '').slice(0, 240),
      constructionMs:Math.round(constructedAt - constructionStarted), completionWaitMs:Math.round(performance.now() - started),
      runtimeErrors:errors.length, transportAttempts:blocked.length}));
    process.exitCode = 1;
  } finally { dom.window.close(); for (const url of objectUrls) URL.revokeObjectURL(url); }
})();
