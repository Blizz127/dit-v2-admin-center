// Execute the generated inspector artifact in an installed, offline jsdom runtime.
// A missing dependency is an error, never a skipped/passing browser check.
const path = require('node:path');
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
const dom = new JSDOM(html, {
  url: 'https://offline.invalid/', runScripts: 'dangerously',
  resources: new OfflineResources(), virtualConsole,
  beforeParse(window) {
    window.structuredClone = globalThis.structuredClone;
    window.fetch = deny('window.fetch');
    window.XMLHttpRequest = deny('XMLHttpRequest');
    window.WebSocket = deny('WebSocket');
    window.EventSource = deny('EventSource');
  },
});
(async () => {
  try {
    const deadline = Date.now() + 5000;
    while (!dom.window.document.documentElement.dataset.playtest) {
      if (Date.now() > deadline) throw new Error('Harness did not finish within five seconds');
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    const doc = dom.window.document;
    if (doc.documentElement.dataset.playtest !== 'passed') throw new Error(doc.querySelector('#harness-status').textContent);
    if (blocked.length) throw new Error('Blocked transport attempts: ' + blocked.join(', '));
    if (errors.length) throw new Error('DOM runtime errors: ' + errors.join('; '));
    const checks = [...doc.querySelectorAll('#harness-checks li')];
    if (checks.length < 20 || checks.some(row => !row.textContent.startsWith('PASS — '))) throw new Error('Incomplete runtime assertions');
    const result = {status: 'passed', runtime: 'jsdom', checks: checks.length, transportAttempts: blocked.length,
      limitations: 'DOM execution only; no browser rendering, CSP enforcement, HTTP server or deployed-service verification'};
    console.log(JSON.stringify(result));
  } catch (error) {
    console.error('FAIL: ' + error.message);
    process.exitCode = 1;
  } finally { dom.window.close(); }
})();
