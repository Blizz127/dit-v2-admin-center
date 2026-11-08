// Actual click/session code; simulated DOM, no native browser or live request.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {createHash} = require('node:crypto');
const {get, refresh, context} = require('./overview_snapshot_harness.cjs');
const capture = JSON.parse(fs.readFileSync('tests/fixtures/context-status-integration/ffxi-companion.json', 'utf8'));
function presenceCapture(original, state, value, withholdBody) {
  const result = structuredClone(original), view = result.statusBinding.View;
  Object.assign(view.Fields[0], {State:state, Value:value, Reason:'synthetic presence case'});
  if (state === 'Unknown') Object.assign(view.Fields[0], {ObservedAtUtc:null, ValidUntilUtc:null});
  if (state === 'Stale') view.Fields[0].ValidUntilUtc = view.ReadAtUtc;
  if (withholdBody) for (const field of view.Fields.slice(1))
    Object.assign(field, {State:'Unknown', Value:null, Reason:'presence unconfirmed', ObservedAtUtc:null, ValidUntilUtc:null});
  view.ApprovedFacts = view.Fields.filter(field => field.State === 'Known')
    .map(field => ({Key:'native_status_' + field.Field.toLowerCase(), Value:field.Value}));
  const native = view.Fields.flatMap(field => {
    const key = 'native_status_' + field.Field.toLowerCase();
    return [`- ${key}_state: ${field.State.toLowerCase()}: ${field.Reason}`,
      ...(field.State === 'Known' ? [`- ${key}: ${field.Value}`] : [])];
  });
  native.push('- native_status_revision: ' + view.RevisionSha256, '- native_status_policy: ' + view.FreshnessPolicyVersion);
  result.userMessage = result.userMessage.split('\n\n').map(block => block.startsWith('APPROVED FACTS\n')
    ? ['APPROVED FACTS', ...native, ...block.split('\n').slice(1).filter(line => !line.startsWith('- native_status_'))].join('\n') : block).join('\n\n');
  const system = result.systemMessage, user = result.userMessage;
  result.contextReceipt.SerializedCharacters = system.length + user.length;
  result.contextReceipt.PromptSha256 = createHash('sha256').update(`${system.length}:${system}${user.length}:${user}`).digest('hex');
  return result;
}
(async () => {
  await refresh({});
  const panel = get('context-capture'), button = get('context-capture-load');
  let response = {status:'Loaded', capture};
  context.fetch = async (path, options) => {
    assert.equal(path, '/api/context-capture');
    assert.equal(options.method || 'GET', 'GET');
    assert.equal(options.headers.Authorization, 'Bearer synthetic-test-token');
    assert.equal(options.cache, 'no-store');
    return {ok:true, json:async()=>response};
  };
  await button.listeners.click();
  assert.match(panel.textContent, /12 \/ 12 captured input turns retained/);
  assert.ok(panel.textContent.includes(capture.userMessage));
  assert.ok(panel.textContent.includes(capture.statusBinding.View.RevisionSha256));
  assert.match(panel.textContent, /independent of roster selection/);
  assert.equal(button.disabled, false);
  for (const game of ['ffxi', 'swtor']) {
    const original = JSON.parse(fs.readFileSync(`tests/fixtures/context-status-integration/${game}-companion.json`, 'utf8'));
    for (const [state, value] of [['Known', 'offline'], ['Known', 'busy'], ['Unknown', null], ['Stale', null]]) {
      response = {status:'Loaded', capture:presenceCapture(original, state, value, false)};
      await button.listeners.click();
      assert.match(panel.textContent, /Offline capture unavailable/, `${game}: ${state}/${value} cannot authorize body facts`);
      assert.ok(!panel.textContent.includes(original.userMessage));
      assert.ok(!panel.textContent.includes('Synthetic native west entrance'));
      assert.equal(button.disabled, false);
      if (value === 'busy') continue;
      response = {status:'Loaded', capture:presenceCapture(original, state, value, true)};
      await button.listeners.click();
      assert.match(panel.textContent, /12 \/ 12 captured input turns retained/);
      assert.ok(panel.textContent.includes(response.capture.userMessage));
      assert.match(panel.textContent, /Unknown · Value withheld/);
      assert.ok(!panel.textContent.includes('Synthetic native west entrance'));
    }
    for (const mutate of [
      fields => { fields[0] = structuredClone(fields[1]); },
      fields => { fields[1].Field = 'Presence'; },
      fields => { [fields[0], fields[1]] = [fields[1], fields[0]]; },
    ]) {
      response = {status:'Loaded', capture:structuredClone(original)};
      mutate(response.capture.statusBinding.View.Fields);
      await button.listeners.click();
      assert.match(panel.textContent, /Offline capture unavailable/, 'Malformed field identity must not bypass presence checks');
    }
    response = {status:'Loaded', capture:original};
    await button.listeners.click();
    assert.ok(panel.textContent.includes(original.userMessage), 'Corrected online capture must recover without losing history');
  }
  for (const failure of ['missing', 'error', 'binding', 'gap']) {
    const unavailable = JSON.parse(fs.readFileSync(`tests/fixtures/context-status-unavailable/ffxi-${failure}.json`, 'utf8'));
    response = {status:'Loaded', capture:unavailable};
    await button.listeners.click();
    assert.match(panel.textContent, /12 \/ 12 captured input turns retained/);
    assert.ok(panel.textContent.includes(unavailable.userMessage));
    assert.ok(!panel.textContent.includes('Synthetic native west entrance'));
    assert.ok(panel.textContent.includes(failure === 'gap' ? 'sequence gap: snapshot required' : unavailable.statusBinding.State));
    assert.match(panel.textContent, /Unknown · Value withheld/);
  }
  for (const game of ['ffxi', 'swtor']) {
    const empty = JSON.parse(fs.readFileSync(`tests/fixtures/context-status-empty/${game}-empty-intent.json`, 'utf8'));
    response = {status:'Loaded', capture:empty};
    await button.listeners.click();
    assert.match(panel.textContent, /0 \/ 0 captured input turns retained/);
    assert.ok(panel.textContent.includes(empty.userMessage));
    assert.match(panel.textContent, /Native status unavailable/);
  }
  response = {status:'Loaded', capture:structuredClone(capture)};
  response.capture.statusBinding.View = null;
  response.capture.statusBinding.State = 'source unavailable';
  await button.listeners.click();
  assert.match(panel.textContent, /Offline capture unavailable/);
  assert.ok(!panel.textContent.includes('Synthetic native west entrance'));
  response = {status:'Not configured', capture:null};
  await button.listeners.click();
  assert.equal(panel.textContent, 'No offline capture configured.');
  response = {status:'Unavailable', capture:null};
  await button.listeners.click();
  assert.match(panel.textContent, /Offline capture unavailable/);
  assert.ok(!panel.textContent.includes(capture.userMessage));
  response = {status:'Loaded', capture:structuredClone(capture)};
  response.capture.statusBinding.View.Fields[3].Value = 'leaked unavailable value';
  await button.listeners.click();
  assert.ok(!panel.textContent.includes('leaked unavailable value'));
  assert.match(panel.textContent, /Offline capture unavailable/);
  let resolve;
  context.fetch = () => new Promise(done => {resolve=done;});
  const pending = button.listeners.click();
  assert.equal(button.disabled, true);
  vm.runInContext('resetPanelSession()', context);
  resolve({ok:true, json:async()=>({status:'Loaded', capture})});
  await pending;
  assert.equal(panel.textContent, 'Not requested in this session.');
  assert.equal(button.disabled, false);
  console.log('PASS: authenticated capture click, presence/body consistency, exact field identities, unavailable clearing and session-race suppression; native browser NOT RUN.');
})().catch(error => {console.error(error); process.exitCode=1;});
