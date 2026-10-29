// Invoked only by run_keyboard_playtest.py inside its isolated namespace.
// Chromium's anonymous debugging pipes avoid a TCP listener or WebSocket library.
const {spawn} = require('node:child_process');
const {pathToFileURL} = require('node:url');

function keyEvents(key, shift = false) {
  const mapping = {Tab: ['Tab', 9], Enter: ['Enter', 13], ' ': ['Space', 32], Escape: ['Escape', 27]};
  if (!mapping[key]) throw Error('Unsupported fixture key');
  const [code, value] = mapping[key];
  const base = {key, code, windowsVirtualKeyCode: value, modifiers: shift ? 8 : 0};
  // CDP modifiers: Alt=1, Control=2, Meta=4, Shift=8.
  return [{...base, type: 'keyDown', ...(key === 'Enter' ? {text: '\r'} : key === ' ' ? {text: ' '} : {})},
    {...base, type: 'keyUp'}];
}

function connection(child) {
  let nextId = 0, buffer = '';
  const pending = new Map();
  const fail = () => { for (const item of pending.values()) { clearTimeout(item.timer); item.reject(Error('Browser pipe closed')); } pending.clear(); };
  child.on('error', fail); child.on('exit', fail);
  child.stdio[3].on('error', fail); child.stdio[4].on('error', fail);
  child.stdio[4].setEncoding('utf8');
  child.stdio[4].on('data', data => {
    buffer += data;
    if (buffer.length > 4 * 1024 * 1024) { fail(); child.kill(); return; }
    let end;
    while ((end = buffer.indexOf('\0')) >= 0) {
      const raw = buffer.slice(0, end); buffer = buffer.slice(end + 1);
      let message;
      try { message = JSON.parse(raw); } catch { fail(); child.kill(); return; }
      const item = pending.get(message.id);
      if (!item) continue;
      pending.delete(message.id); clearTimeout(item.timer);
      if (message.error) item.reject(Error('Browser protocol command failed'));
      else item.resolve(message.result);
    }
  });
  return (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const id = ++nextId;
    const timer = setTimeout(() => { pending.delete(id); reject(Error('Browser command timed out')); }, 4000);
    pending.set(id, {resolve, reject, timer});
    child.stdio[3].write(JSON.stringify({id, method, params, ...(sessionId ? {sessionId} : {})}) + '\0');
  });
}

async function run(browser, artifact, profile) {
  const child = spawn(browser, ['--headless', '--disable-gpu', '--disable-background-networking',
    '--no-first-run', '--no-default-browser-check', '--user-data-dir=' + profile,
    '--remote-debugging-pipe', 'about:blank'], {stdio: ['ignore', 'ignore', 'ignore', 'pipe', 'pipe']});
  const deadline = setTimeout(() => child.kill('SIGKILL'), 25000);
  const send = connection(child);
  try {
    const {targetId} = await send('Target.createTarget', {url: 'about:blank'});
    const {sessionId} = await send('Target.attachToTarget', {targetId, flatten: true});
    const command = (method, params) => send(method, params, sessionId);
    const evaluate = async expression => {
      const response = await command('Runtime.evaluate', {expression, returnByValue: true});
      if (response.exceptionDetails) throw Error('Artifact evaluation failed');
      return response.result.value;
    };
    const waitFor = async expression => {
      const end = Date.now() + 4000;
      do {
        if (await evaluate(expression)) return;
        await new Promise(resolve => setTimeout(resolve, 20));
      } while (Date.now() < end);
      throw Error('Expected artifact state did not arrive');
    };
    const press = async (key, shift = false) => {
      for (const event of keyEvents(key, shift)) await command('Input.dispatchKeyEvent', event);
    };
    await command('Page.enable');
    await command('Page.navigate', {url: pathToFileURL(artifact).href});
    await command('Page.bringToFront');
    await waitFor("document.documentElement.dataset.playtest === 'passed'");
    // Position initial focus only; all activation and subsequent focus traversal
    // use native browser input, never dispatched DOM events or element.click().
    await evaluate("document.getElementById('keyboard-start').focus(); true");
    await press('Enter');
    await waitFor("document.documentElement.dataset.keyboardPlaytest === 'running'");
    const beforeCancel = await evaluate("document.getElementById('assignment-count').textContent");
    await press('Escape');
    await waitFor("document.documentElement.dataset.keyboardPlaytest === 'cancelled' && document.activeElement.id === 'keyboard-start'");
    if (beforeCancel !== await evaluate("document.getElementById('assignment-count').textContent")) throw Error('Cancel changed the page');
    await press('Enter');
    await waitFor("document.documentElement.dataset.keyboardPlaytest === 'running'");
    const keys = [['Tab'], ['Enter'], [' '], ['Tab'], ['Enter'], [' '], ['Enter'], [' '], ['Tab', true], ['Enter'], [' '], ['Tab', true]];
    for (let index = 0; index < keys.length; index++) {
      await press(...keys[index]);
      await waitFor(index === keys.length - 1
        ? "document.documentElement.dataset.keyboardPlaytest === 'passed'"
        : "document.documentElement.dataset.keyboardPlaytest === 'running' && document.getElementById('keyboard-status').textContent.startsWith('Step " + (index + 2) + "/12:')");
    }
    return {status: 'passed', nativeKeyboard: 'passed', steps: keys.length, escapeCancellation: 'passed',
      automaticDOM: 'passed', transport: 'anonymous debugging pipes',
      limitations: 'Synthetic artifact only; no visual or screen-reader review, live service or game verification'};
  } finally { clearTimeout(deadline); child.kill('SIGKILL'); }
}

module.exports = {keyEvents, connection};
if (require.main === module) {
  const [browser, artifact, profile] = process.argv.slice(2);
  if (!browser || !artifact || !profile) { console.error('Use run_keyboard_playtest.py'); process.exitCode = 2; }
  else run(browser, artifact, profile).then(result => console.log(JSON.stringify(result)))
    .catch(() => { console.error('FAIL: native keyboard check could not complete; no success claimed.'); process.exitCode = 1; });
}
