import base64
import hashlib
import json
from html.parser import HTMLParser
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.build_context_capture_playtest import build, ROOT


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.scripts = []
        self.inline = False
        self.csp = ''
        self.sources = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self.inline = True
            self.scripts.append('')
        if 'src' in attrs:
            self.sources.append(attrs['src'])
        if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy':
            self.csp = attrs['content']

    def handle_data(self, text):
        if self.inline:
            self.scripts[-1] += text

    def handle_endtag(self, tag):
        if tag == 'script':
            self.inline = False


class ContextPanelPlaytestTests(unittest.TestCase):
    def test_artifact_binds_actual_application_and_all_twelve_validated_captures(self):
        page = Page(build())
        self.assertEqual(len(page.scripts), 1)
        script = page.scripts[0]
        self.assertIn((ROOT / 'static/app.js').read_text(), script)
        payload = script.split('const fixtures = ', 1)[1].split(';\nconst sessionStorage', 1)[0]
        data = json.loads(payload)
        self.assertEqual(len(data['captures']), 12)
        self.assertEqual(set(data['delivery']), {'ffxi', 'swtor'})
        for game, report in data['delivery'].items():
            self.assertEqual(report['scope']['game'], game)
            self.assertEqual(report['counts']['publicationMatched'], 2)
            self.assertEqual(report['counts']['syntheticConfirmed'], 0)
            self.assertFalse(report['nativeDeliveryVerified'])
            self.assertIsNone(report['deliveredInGame'])
        for name, capture in data['captures'].items():
            folder = 'context-status-unavailable' if name in ('ffxi-missing', 'ffxi-error', 'ffxi-binding', 'ffxi-gap') else 'context-status-integration'
            if name.endswith('-empty-intent'):
                folder = 'context-status-empty'
            self.assertEqual(capture, json.loads((ROOT / 'tests/fixtures' / folder / (name + '.json')).read_text()))

    def test_artifact_blocks_network_and_script_is_valid_without_launching_browser(self):
        page = Page(build())
        self.assertEqual(page.sources, [])
        self.assertIn("connect-src 'none'", page.csp)
        self.assertIn("default-src 'none'", page.csp)
        digest = base64.b64encode(hashlib.sha256(page.scripts[0].encode()).digest()).decode()
        self.assertIn("script-src 'sha256-" + digest + "'", page.csp)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture.js'
            path.write_text(page.scripts[0])
            result = subprocess.run(['node', '--check', str(path)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_presence_conflict_uses_response_copies_without_network_or_delivery_changes(self):
        artifact = build()
        page = Page(artifact)
        self.assertIn('<option value="presence-conflict">Synthetic presence conflict</option>', artifact)
        self.assertIn('Presence conflict should show the context capture as unavailable', artifact)
        self.assertIn("connect-src 'none'", page.csp)
        self.assertEqual(page.sources, [])
        app = (ROOT / 'static/app.js').read_text()
        self.assertIn(app, page.scripts[0])
        # Exercise the exact embedded fetch wrapper, without running unrelated
        # application startup or granting the VM a network-capable fetch.
        driver = page.scripts[0].split(app, 1)[0] + '\nglobalThis.fixtureFetch = fetch; globalThis.originalFixtures = fixtures;})();'
        check = '''const assert = require('node:assert/strict');
const vm = require('node:vm');
const controls = {'fixture-scenario':{value:'presence-conflict'}, 'fixture-capture':{value:'ffxi-companion'}};
let networkCalls = 0;
const context = vm.createContext({
  document:{getElementById:id=>controls[id]}, structuredClone,
  fetch:()=>{networkCalls++; throw new Error('Network forbidden');}
});
vm.runInContext(DRIVER, context);
(async () => {
  const original = JSON.stringify(context.originalFixtures);
  const fetchFixture = async url => (await context.fixtureFetch(url)).json();
  for (const game of ['ffxi', 'swtor']) {
    controls['fixture-capture'].value = game + '-companion';
    const conflict = await fetchFixture('/api/context-capture');
    assert.equal(conflict.status, 'Loaded');
    assert.equal(conflict.capture.game, game);
    assert.equal(conflict.capture.statusBinding.View.Fields[0].State, 'Known');
    assert.equal(conflict.capture.statusBinding.View.Fields[0].Value, 'offline');
    assert.equal(conflict.capture.statusBinding.View.Fields[1].State, 'Known');
    assert.equal(conflict.capture.statusBinding.View.Fields[1].Value, 'Synthetic native west entrance');
    assert.equal(JSON.stringify(context.originalFixtures), original);
    const delivery = await fetchFixture('/api/delivery-capture');
    assert.equal(JSON.stringify(delivery), JSON.stringify(context.originalFixtures.delivery[game]));
    assert.equal(delivery.nativeDeliveryVerified, false);
    assert.equal(delivery.deliveredInGame, null);
  }
  for (const name of ['ffxi-missing', 'ffxi-gap', 'ffxi-empty-intent', 'swtor-empty-intent']) {
    controls['fixture-capture'].value = name;
    const rejected = (await fetchFixture('/api/context-capture')).capture;
    assert.equal(rejected.statusBinding.State, 'synthetic conflict: no projected body');
    assert.equal(JSON.stringify(rejected.statusBinding.View), JSON.stringify(context.originalFixtures.captures[name].statusBinding.View));
  }
  controls['fixture-capture'].value = 'ffxi-companion';
  controls['fixture-scenario'].value = 'loaded';
  assert.equal(JSON.stringify((await fetchFixture('/api/context-capture')).capture), JSON.stringify(context.originalFixtures.captures['ffxi-companion']));
  controls['fixture-scenario'].value = 'invalid';
  assert.equal((await fetchFixture('/api/delivery-capture')).nativeDeliveryVerified, true);
  await assert.rejects(context.fixtureFetch('https://example.invalid'), /network forbidden/);
  await assert.rejects(context.fixtureFetch('/api/context-capture', {method:'POST'}), /Only fixture GETs allowed/);
  assert.equal(networkCalls, 0);
  assert.equal(JSON.stringify(context.originalFixtures), original);
})().catch(error=>{console.error(error);process.exitCode=1;});
'''.replace('DRIVER', json.dumps(driver), 1)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture-fetch-check.cjs'
            path.write_text(check)
            result = subprocess.run(['node', str(path)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_scope_conflict_mutates_only_body_or_lookup_game_in_response_copies(self):
        artifact = build()
        page = Page(artifact)
        self.assertIn('<option value="scope-conflict">Synthetic scope conflict</option>', artifact)
        self.assertIn('<option value="presence-conflict">Synthetic presence conflict</option>', artifact)
        self.assertIn("connect-src 'none'", page.csp)
        self.assertEqual(page.sources, [])
        app = (ROOT / 'static/app.js').read_text()
        self.assertIn(app, page.scripts[0])
        driver = page.scripts[0].split(app, 1)[0] + '\nglobalThis.fixtureFetch = fetch; globalThis.originalFixtures = fixtures;})();'
        check = '''const assert = require('node:assert/strict');
const vm = require('node:vm');
const controls = {'fixture-scenario':{value:'scope-conflict'}, 'fixture-capture':{value:'ffxi-companion'}};
let networkCalls = 0;
const context = vm.createContext({
  document:{getElementById:id=>controls[id]}, structuredClone,
  fetch:()=>{networkCalls++; throw new Error('Network forbidden');}
});
vm.runInContext(DRIVER, context);
(async () => {
  const original = JSON.stringify(context.originalFixtures);
  const fetchFixture = async url => (await context.fixtureFetch(url)).json();
  for (const name of ['ffxi-companion', 'swtor-companion', 'ffxi-gap', 'ffxi-missing', 'ffxi-empty-intent', 'swtor-empty-intent']) {
    controls['fixture-scenario'].value = 'scope-conflict';
    controls['fixture-capture'].value = name;
    const source = context.originalFixtures.captures[name];
    const expected = structuredClone(source);
    const otherGame = source.game === 'ffxi' ? 'swtor' : 'ffxi';
    if (expected.statusBinding.View) expected.statusBinding.View.Body.Game = otherGame;
    else expected.statusBinding.Lookup.Game = otherGame;
    const response = await fetchFixture('/api/context-capture');
    assert.equal(response.status, 'Loaded');
    assert.equal(response.capture.game, source.game);
    assert.equal(JSON.stringify(response.capture), JSON.stringify(expected));
    assert.equal(JSON.stringify(context.originalFixtures), original);
    const delivery = await fetchFixture('/api/delivery-capture');
    assert.equal(JSON.stringify(delivery), JSON.stringify(context.originalFixtures.delivery[source.game]));
    assert.equal(delivery.nativeDeliveryVerified, false);
    assert.equal(delivery.deliveredInGame, null);
    controls['fixture-scenario'].value = 'loaded';
    assert.equal(JSON.stringify((await fetchFixture('/api/context-capture')).capture), JSON.stringify(source));
  }
  await assert.rejects(context.fixtureFetch('https://example.invalid'), /network forbidden/);
  await assert.rejects(context.fixtureFetch('/api/context-capture', {method:'POST'}), /Only fixture GETs allowed/);
  assert.equal(networkCalls, 0);
  assert.equal(JSON.stringify(context.originalFixtures), original);
})().catch(error=>{console.error(error);process.exitCode=1;});
'''.replace('DRIVER', json.dumps(driver), 1)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture-scope-fetch-check.cjs'
            path.write_text(check)
            result = subprocess.run(['node', str(path)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_coverage_conflict_changes_only_retained_count_and_recovers_loaded_capture(self):
        artifact = build()
        page = Page(artifact)
        for name, label in (('coverage-conflict', 'Synthetic coverage conflict'),
                            ('presence-conflict', 'Synthetic presence conflict'),
                            ('scope-conflict', 'Synthetic scope conflict')):
            self.assertIn(f'<option value="{name}">{label}</option>', artifact)
        self.assertIn("connect-src 'none'", page.csp)
        self.assertEqual(page.sources, [])
        app = (ROOT / 'static/app.js').read_text()
        self.assertIn(app, page.scripts[0])
        driver = page.scripts[0].split(app, 1)[0] + '\nglobalThis.fixtureFetch = fetch; globalThis.originalFixtures = fixtures;})();'
        check = '''const assert = require('node:assert/strict');
const vm = require('node:vm');
const controls = {'fixture-scenario':{value:'coverage-conflict'}, 'fixture-capture':{value:'ffxi-companion'}};
let networkCalls = 0;
const context = vm.createContext({
  document:{getElementById:id=>controls[id]}, structuredClone,
  fetch:()=>{networkCalls++; throw new Error('Network forbidden');}
});
vm.runInContext(DRIVER, context);
(async () => {
  const original = JSON.stringify(context.originalFixtures);
  const fetchFixture = async url => (await context.fixtureFetch(url)).json();
  for (const name of ['ffxi-companion', 'swtor-companion', 'ffxi-empty-intent', 'swtor-empty-intent']) {
    controls['fixture-scenario'].value = 'coverage-conflict';
    controls['fixture-capture'].value = name;
    const source = context.originalFixtures.captures[name];
    const expected = structuredClone(source);
    expected.contextReceipt.IncludedHistoryTurns = source.contextReceipt.SuppliedHistoryTurns + 1;
    if (name.endsWith('-empty-intent')) {
      assert.equal(source.contextReceipt.SuppliedHistoryTurns, 0);
      assert.equal(expected.contextReceipt.IncludedHistoryTurns, 1);
    }
    const response = await fetchFixture('/api/context-capture');
    assert.equal(response.status, 'Loaded');
    assert.equal(JSON.stringify(response.capture), JSON.stringify(expected));
    assert.equal(response.capture.systemMessage, source.systemMessage);
    assert.equal(response.capture.userMessage, source.userMessage);
    assert.equal(JSON.stringify(context.originalFixtures), original);
    const delivery = await fetchFixture('/api/delivery-capture');
    assert.equal(JSON.stringify(delivery), JSON.stringify(context.originalFixtures.delivery[source.game]));
    assert.equal(delivery.nativeDeliveryVerified, false);
    assert.equal(delivery.deliveredInGame, null);
    controls['fixture-scenario'].value = 'loaded';
    assert.equal(JSON.stringify((await fetchFixture('/api/context-capture')).capture), JSON.stringify(source));
  }
  await assert.rejects(context.fixtureFetch('https://example.invalid'), /network forbidden/);
  await assert.rejects(context.fixtureFetch('/api/context-capture', {method:'POST'}), /Only fixture GETs allowed/);
  assert.equal(networkCalls, 0);
  assert.equal(JSON.stringify(context.originalFixtures), original);
})().catch(error=>{console.error(error);process.exitCode=1;});
'''.replace('DRIVER', json.dumps(driver), 1)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture-coverage-fetch-check.cjs'
            path.write_text(check)
            result = subprocess.run(['node', str(path)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
