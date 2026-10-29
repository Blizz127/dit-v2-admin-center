// Observer logic only. Fake trusted events below are NOT native browser evidence.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = {};
vm.runInNewContext(fs.readFileSync('tools/assignment_keyboard_playtest.js', 'utf8'), context);
function fixture({prepareFails = false} = {}) {
  const events = {}, timers = [], elements = new Map();
  const document = {documentElement: {dataset: {}}, activeElement: null,
    getElementById: id => elements.get(id), addEventListener: (type, listener) => { events[type] = listener; }};
  for (const id of ['keyboard-start', 'keyboard-status', 'assignment-prev', 'assignment-next']) {
    elements.set(id, {id, listeners: {}, textContent: '',
      addEventListener(type, callback) { this.listeners[type] = callback; },
      focus() { document.activeElement = this; }});
  }
  let page = 1, requests = 0;
  context.installAssignmentKeyboardCheck({document,
    prepare: async () => { if (prepareFails) throw Error('private fixture detail'); page = 1; },
    page: () => page, requests: () => requests, schedule: callback => timers.push(callback)});
  const key = (type, value, extra = {}) => events[type]({key: value, isTrusted: true, shiftKey: false, ...extra,
    preventDefault() { throw Error('Observer must never intercept native behavior'); }});
  const flush = () => { while (timers.length) timers.shift()(); };
  return {document, elements, key, flush,
    start: () => elements.get('keyboard-start').listeners.click(),
    state: () => document.documentElement.dataset.keyboardPlaytest,
    status: () => elements.get('keyboard-status').textContent,
    setPage: value => { page = value; }, request: () => { requests++; },
    press(value, target, after, shiftKey = false) {
      key('keydown', value, {shiftKey});
      // A fake default action, deliberately separate from the observer.
      document.activeElement = elements.get(target); page = after;
      key('keyup', value, {shiftKey}); flush();
    },
  };
}
(async () => {
  const f = fixture();
  assert.equal(f.state(), 'not-run');
  await f.start(); assert.equal(f.state(), 'running');
  f.key('keydown', 'Tab', {isTrusted: false}); f.key('keyup', 'Tab', {isTrusted: false}); f.flush();
  assert.match(f.status(), /Step 1\/12/);
  f.press('Tab', 'assignment-prev', 1);
  f.press('Enter', 'assignment-prev', 1);
  f.press(' ', 'assignment-prev', 1);
  f.press('Tab', 'assignment-next', 1);
  f.press('Enter', 'assignment-next', 2);
  // Space must be verified after keyup's default action, not on keydown.
  f.key('keydown', ' '); assert.match(f.status(), /Step 6\/12/);
  f.key('keyup', ' '); f.setPage(3); f.flush();
  f.press('Enter', 'assignment-next', 3);
  f.press(' ', 'assignment-next', 3);
  f.press('Tab', 'assignment-prev', 3, true);
  f.press('Enter', 'assignment-prev', 2);
  f.press(' ', 'assignment-prev', 1);
  assert.equal(f.state(), 'running'); // An incomplete sequence cannot pass.
  f.press('Tab', 'keyboard-start', 1, true);
  assert.equal(f.state(), 'passed');

  for (const mode of ['wrong-tab', 'lost-focus', 'missing-enter', 'extra-request']) {
    const bad = fixture(); await bad.start();
    if (mode === 'wrong-tab') bad.press('Tab', 'assignment-next', 1);
    else {
      bad.press('Tab', 'assignment-prev', 1);
      if (mode === 'lost-focus') bad.press('Enter', 'keyboard-start', 1);
      if (mode === 'extra-request') { bad.request(); bad.press('Enter', 'assignment-prev', 1); }
      if (mode === 'missing-enter') {
        bad.press('Enter', 'assignment-prev', 1); bad.press(' ', 'assignment-prev', 1);
        bad.press('Tab', 'assignment-next', 1); bad.press('Enter', 'assignment-next', 1);
      }
    }
    assert.equal(bad.state(), 'failed', mode);
  }
  const restarted = fixture(); await restarted.start();
  restarted.key('keydown', 'Tab'); restarted.key('keyup', 'Tab');
  await restarted.start(); restarted.flush();
  assert.equal(restarted.state(), 'running'); assert.match(restarted.status(), /Step 1\/12/);
  const unavailable = fixture({prepareFails: true}); await unavailable.start();
  assert.equal(unavailable.state(), 'failed'); assert.doesNotMatch(unavailable.status(), /private fixture detail/);
  assert.equal(unavailable.elements.get('keyboard-start').disabled, false);
  console.log('Keyboard observer logic passed with fake events: trust gating, sequence/default observations, failure and restart handling. Native browser keys NOT executed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
