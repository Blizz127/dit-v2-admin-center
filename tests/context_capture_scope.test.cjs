// Actual application handlers with synthetic captures; no browser or live reads.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {get, refresh, context} = require('./overview_snapshot_harness.cjs');
const fixture = name => JSON.parse(fs.readFileSync(`tests/fixtures/${name}.json`, 'utf8'));
(async () => {
  await refresh({});
  const panel = get('context-capture'), button = get('context-capture-load');
  let capture;
  context.fetch = async (path, options) => {
    assert.equal(path, '/api/context-capture');
    assert.equal(options.method || 'GET', 'GET');
    assert.equal(options.headers.Authorization, 'Bearer synthetic-test-token');
    return {ok:true, json:async()=>({status:'Loaded', capture})};
  };
  const row = title => {
    const rows = panel.children.filter(child => child.children?.[0]?.textContent === title);
    assert.equal(rows.length, 1, `Missing or duplicate ${title}`);
    return rows[0].textContent;
  };
  for (const game of ['ffxi', 'swtor']) {
    const original = fixture(`context-status-integration/${game}-companion`);
    const other = game === 'ffxi' ? 'swtor' : 'ffxi';
    for (const [label, change] of [
      ['body game mismatch', data => { data.statusBinding.View.Body.Game = other; }],
      ['lookup game mismatch', data => { data.statusBinding.Lookup.Game = other; }],
      ['instance mismatch', data => { data.statusBinding.View.Body.Instance = 'different-instance'; }],
      ['case-distinct instance', data => { data.statusBinding.View.Body.Instance = data.statusBinding.Lookup.ServerInstance.toUpperCase(); }],
      ['missing lookup', data => { delete data.statusBinding.Lookup; }],
      ['blank requested actor', data => { data.statusBinding.Lookup.ActorKey = ' '; }],
      ['oversized requested actor', data => { data.statusBinding.Lookup.ActorKey = 'x'.repeat(129); }],
      ['missing body', data => { data.statusBinding.View.Body = null; }],
      ['blank native actor', data => { data.statusBinding.View.Body.NativeActorId = ''; }],
      ['invalid realm', data => { data.statusBinding.View.Body.Realm = 123; }],
      ['missing epoch', data => { delete data.statusBinding.View.Epoch; }],
    ]) {
      capture = structuredClone(original);
      await button.listeners.click();
      assert.match(panel.textContent, /12 \/ 12 captured input turns retained/);
      change(capture);
      await button.listeners.click();
      assert.match(panel.textContent, /Offline capture unavailable/, `${game}: ${label}`);
      assert.ok(!panel.textContent.includes(original.userMessage));
      assert.ok(!panel.textContent.includes('Synthetic native west entrance'));
      assert.equal(button.disabled, false);
    }
    capture = original;
    await button.listeners.click();
    assert.ok(row('Requested bot scope').includes(`Game ${game}`));
    assert.ok(row('Requested bot scope').includes('actor key fixture'));
    assert.ok(row('Requested bot scope').includes('instance synthetic-instance'));
    assert.ok(row('Native body in capture').includes('native actor native-fixture-id'));
    assert.ok(row('Native body in capture').includes('realm synthetic-realm'));
    assert.ok(row('Native body in capture').includes('epoch synthetic-epoch'));
    assert.ok(panel.textContent.includes(original.userMessage));
  }
  for (const name of ['missing', 'error', 'binding', 'gap']) {
    capture = fixture(`context-status-unavailable/ffxi-${name}`);
    await button.listeners.click();
    assert.ok(row('Requested bot scope').includes('actor key fixture'));
    assert.match(panel.textContent, /12 \/ 12 captured input turns retained/);
    assert.match(panel.textContent, /Unknown · Value withheld/);
    if (name === 'gap') assert.ok(row('Native body in capture').includes('native-fixture-id'));
    else assert.ok(!panel.textContent.includes('Native body in capture'));
    capture.statusBinding.Lookup.Game = 'swtor';
    await button.listeners.click();
    assert.match(panel.textContent, /Offline capture unavailable/);
  }
  console.log('PASS: exact captured lookup/body scope, separate identities, mismatch clearing and missing-source history; native browser NOT RUN.');
})().catch(error => {console.error(error); process.exitCode=1;});
