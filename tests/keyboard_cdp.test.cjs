// Protocol/key encoding checks with fake pipes; no Chromium or native input.
const assert = require('node:assert/strict');
const {EventEmitter} = require('node:events');
const {keyEvents, connection} = require('../tools/keyboard_cdp.cjs');
function fake() {
  const child = new EventEmitter();
  child.stdio = [null, null, null, new EventEmitter(), new EventEmitter()];
  child.stdio[4].setEncoding = () => {};
  const writes = [];
  child.stdio[3].write = data => writes.push(JSON.parse(data.slice(0, -1)));
  child.kill = () => child.emit('exit');
  return {child, writes, send: connection(child)};
}
(async () => {
  for (const [key, code, value] of [['Tab', 'Tab', 9], ['Enter', 'Enter', 13], [' ', 'Space', 32], ['Escape', 'Escape', 27]]) {
    const [down, up] = keyEvents(key);
    assert.equal(down.type, 'keyDown'); assert.equal(up.type, 'keyUp');
    assert.equal(down.key, key); assert.equal(down.code, code);
    assert.equal(down.windowsVirtualKeyCode, value);
    assert.equal(up.text, undefined);
  }
  assert.equal(keyEvents('Tab', true)[0].modifiers, 8);
  assert.equal(keyEvents('Tab')[0].text, undefined);
  assert.equal(keyEvents('Enter')[0].text, '\r');
  assert.equal(keyEvents(' ')[0].text, ' ');
  assert.throws(() => keyEvents('F12'), /Unsupported/);
  const f = fake();
  const first = f.send('Runtime.evaluate', {expression: 'true'}, 'synthetic-session');
  assert.deepEqual(f.writes[0], {id: 1, method: 'Runtime.evaluate', params: {expression: 'true'}, sessionId: 'synthetic-session'});
  // Events and fragmented null-delimited replies must not steal the request.
  f.child.stdio[4].emit('data', '{"method":"Page.event"}\0{"id":1,"res');
  f.child.stdio[4].emit('data', 'ult":{"value":true}}\0');
  assert.deepEqual(await first, {value: true});
  const bad = f.send('Input.dispatchKeyEvent', keyEvents('Enter')[0]);
  f.child.stdio[4].emit('data', '{"id":2,"error":{"message":"PRIVATE_BROWSER_DETAIL"}}\0');
  await assert.rejects(bad, error => error.message === 'Browser protocol command failed');
  const closed = f.send('Page.enable'); f.child.emit('exit');
  await assert.rejects(closed, /Browser pipe closed/);
  const malformed = fake(); const request = malformed.send('Page.enable');
  malformed.child.stdio[4].emit('data', 'PRIVATE_NOT_JSON\0');
  await assert.rejects(request, /Browser pipe closed/);
  console.log('CDP key/pipe contracts passed with fake pipes. Native keyboard execution NOT performed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
