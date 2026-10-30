"""Serve synthetic in-memory handler responses and a parsed template manifest to Node.

This is a test adapter, not a listener. It reuses the offline handler suite's
socket/subprocess/database/read guards and projected fixture collector.
"""
import json
import hashlib
import subprocess
from html.parser import HTMLParser
from pathlib import Path
import sys
from types import SimpleNamespace
from urllib.parse import urlsplit
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from test_offline_inspector_handler import OfflineInspectorHandlerTests
from live_hub import HubReadError, project_hub_health
from interaction_projection import project_interaction
from bridge_status import BridgeObserver
from tools.build_inspector_playtest import snapshot


def coverage_fixture(scenario):
    """Projected learning plus fictional roster/metrics; no collection or live reads."""
    data = snapshot()
    data['bots'] = [dict(id='coverage-bot', name='Coverage fixture bot', game='FFXI', source='Synthetic')]
    data['botDetails'] = [dict(botId='coverage-bot', goals=[dict(text='Synthetic coverage goal')], memories=[])]
    data['modelCalls'] = [dict(model='Zero fixture', latencyMs=0, cost=0, quality=0),
                          dict(model='Partial fixture', latencyMs=12)]
    if scenario == 'coverage-partial':
        for key in ('bots', 'learning', 'modelCalls'):
            data[key] = [None, *data[key]]
    elif scenario == 'coverage-unavailable':
        for key in ('bots', 'learning', 'modelCalls'):
            data[key] = None
    elif scenario == 'coverage-identity-gaps':
        data['bots'].extend([
            dict(id='duplicate', name='Same name', game='FFXI', source='FIRST_GAP_SOURCE'),
            dict(id='duplicate', name='Same name', game='SWTOR', source='SECOND_GAP_SOURCE'),
            dict(name='Missing identity', game='FFXI'),
        ])
    elif scenario != 'coverage-loaded':
        raise AssertionError('Unknown coverage scenario')
    return data

INTERACTION_FIXTURES = ('contract-off-empty', 'contract-off-retained', 'contract-on-empty',
                        'fresh-snapshot', 'fresh-snapshot-superseded-view', 'fresh-mode-stale-snapshot',
                        'stale-mode-and-snapshot', 'same-actor-distinct-scopes', 'limit-50-truncated')


def health_fixture(scenario):
    if scenario == 'health-unavailable':
        raise HubReadError('OMIT_PRIVATE_HEALTH_FAILURE')
    data = {'utc': '2026-01-01T12:00:00Z', 'services': [
        {'game': 'ffxi', 'label': 'Fixture FFXI bridge', 'state': 'running',
         'log': 'OMIT_PRIVATE_HEALTH_LOG', 'environment': 'OMIT_PRIVATE_HEALTH_ENV'},
        {'game': 'swtor', 'label': 'Fixture SWTOR adapter', 'state': 'unrecognized'},
        {'game': 'other', 'label': 'OMIT_PRIVATE_OTHER_SERVICE', 'state': 'running'},
    ]}
    if scenario == 'health-empty':
        data['services'] = []
    elif scenario == 'health-malformed':
        data['services'] = 'OMIT_PRIVATE_HEALTH_INVALID'
    elif scenario != 'health-services':
        raise AssertionError('Unexpected health fixture request')
    return project_hub_health(data, 'fixture-health-fetch')


def bridge_runner(scenario):
    data = {'observedAt': '2026-01-01T12:00:00Z', 'unit': 'active', 'substate': 'running',
            'result': 'success', 'marker': 'absent', 'markerReason': 'unknown',
            'private': 'OMIT_PRIVATE_BRIDGE_PAYLOAD'}
    if scenario == 'bridge-fault':
        data.update(unit='failed', substate='failed', result='exit-code',
                    marker='present', markerReason='delayed_delivery_failed')
    runner = Mock(return_value=SimpleNamespace(stdout=json.dumps(data)))
    if scenario == 'bridge-empty':
        runner.return_value.stdout = ''
    elif scenario == 'bridge-malformed':
        runner.return_value.stdout = 'OMIT_PRIVATE_BRIDGE_INVALID'
    elif scenario == 'bridge-denied':
        runner.side_effect = PermissionError('OMIT_PRIVATE_BRIDGE_DENIAL')
    elif scenario == 'bridge-timeout':
        runner.side_effect = subprocess.TimeoutExpired(['fixture-ssh'], 8, stderr='OMIT_PRIVATE_BRIDGE_TIMEOUT')
    elif scenario not in ('bridge-active', 'bridge-fault'):
        raise AssertionError('Unexpected bridge fixture request')
    return runner


def interaction_fixture(scenario):
    if scenario == 'interaction-unavailable':
        raise HubReadError('OMIT_PRIVATE_INTERACTION_FAILURE')
    if scenario == 'interaction-malformed':
        return project_interaction({'scopes': 'OMIT_PRIVATE_INVALID'}, 'fixture-interaction-fetch')
    name = scenario.removeprefix('interaction:')
    if name not in INTERACTION_FIXTURES:
        raise AssertionError('Unexpected interaction fixture request')
    directory = ROOT / 'tests/fixtures/interaction-generated'
    manifest = json.loads((directory / 'MANIFEST.json').read_text())
    raw = (directory / (name + '.json')).read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest['files'][name + '.json']:
        raise AssertionError('Pinned interaction fixture changed')
    return project_interaction(json.loads(raw), 'fixture-interaction-fetch')


class Template(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = {}
        self.select = None
        self.first_option = False
        self.sections = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        identity = attrs.get('id')
        if tag == 'section':
            self.sections.append(identity if 'workspace-section' in attrs.get('class', '').split() else None)
        if identity:
            if identity in self.elements:
                raise ValueError('Duplicate template ID')
            self.elements[identity] = {'tag': tag, 'attrs': attrs, 'value': attrs.get('value', ''),
                                       'section': next((s for s in reversed(self.sections) if s), None)}
        if tag == 'select':
            self.select, self.first_option = identity, True
        if tag == 'option' and self.select:
            if self.first_option or 'selected' in attrs:
                self.elements[self.select]['value'] = attrs.get('value', '')
            self.first_option = False

    def handle_endtag(self, tag):
        if tag == 'section':
            self.sections.pop()
        if tag == 'select':
            self.select = None


def exchange(request):
    path = request.get('path', '')
    if '\r' in path or '\n' in path:
        raise ValueError('Invalid fixture request path')
    if path not in ('/api/overview?source=mock', '/api/overview?source=hub', '/api/bridge-status', '/api/interaction', '/api/hub-health') and urlsplit(path).path != '/api/trace':
        raise ValueError('Only synthetic inspector fixture routes are allowed')
    scenario = request.get('scenario', 'trace-pending')
    allowed = {'trace-pending', 'trace-empty', 'trace-malformed', 'trace-unavailable', 'trace-unconfigured',
               'interaction-malformed', 'interaction-unavailable', 'interaction-unconfigured',
               'health-services', 'health-empty', 'health-malformed', 'health-unavailable', 'health-unconfigured',
               'bridge-active', 'bridge-fault', 'bridge-empty', 'bridge-malformed', 'bridge-denied', 'bridge-timeout'}
    allowed.update('interaction:' + name for name in INTERACTION_FIXTURES)
    allowed.update(('coverage-loaded', 'coverage-partial', 'coverage-unavailable', 'coverage-identity-gaps'))
    if scenario not in allowed:
        raise ValueError('Unknown fixture scenario')
    case = OfflineInspectorHandlerTests()
    case.setUp()
    try:
        if scenario.startswith('coverage-'):
            case.overview.side_effect = lambda source: coverage_fixture(scenario)
        # The UI starts a bridge read on overview success; return only unknown fixture state.
        unknown = dict(unit='unknown', substate='unknown', result='unknown', marker='unknown',
                       markerReason='unknown', source='Synthetic offline fixture', observedAt=None)
        runner = bridge_runner(scenario) if scenario.startswith('bridge-') else Mock()
        bridge = BridgeObserver(runner, lambda: 0) if scenario.startswith('bridge-') else SimpleNamespace(read=lambda: unknown)
        records = [{'kind': 'outcome', 'type': 'fixture.outcome', 'occurredAtUtc': '2026-01-01T12:00:00Z',
                    'body': json.dumps({'classification': 'queued_for_native_delivery', 'disposition': 'pending',
                                        'isFinal': False, 'message': 'OMIT_RAW_TRACE_BODY'})}]
        if scenario == 'trace-empty':
            records = []
        elif scenario == 'trace-malformed':
            records = {'private': 'OMIT_RAW_TRACE_BODY'}
        trace = Mock(return_value=(records, 'fixture-trace-fetch'))
        if scenario == 'trace-unavailable':
            trace.side_effect = HubReadError('OMIT_PRIVATE_READ_FAILURE')
        interaction = Mock(side_effect=lambda *args: interaction_fixture(scenario))
        health = Mock(side_effect=lambda *args: health_fixture(scenario))
        config = {} if scenario in ('trace-unconfigured', 'interaction-unconfigured', 'health-unconfigured') else {
            'HUB_READONLY_URL': 'http://127.0.0.1:1', 'HUB_TOKEN_FILE': '/fixture/not-read'}
        with patch('server.BRIDGE', bridge), patch.dict('os.environ', config, clear=True), \
                patch('server.HubReader', return_value=SimpleNamespace(trace=trace)), \
                patch('server.HUB_INTERACTION.get', interaction), patch('server.HUB_HEALTH.get', health):
            status, headers, body = case.request(path=path, token=request.get('token'))
        return {'status': status, 'headers': dict(headers.items()), 'body': body.decode(),
                'traceCalls': trace.call_count, 'interactionCalls': interaction.call_count,
                'healthCalls': health.call_count, 'bridgeRunnerCalls': runner.call_count}
    finally:
        case.doCleanups()


if __name__ == '__main__':
    if len(sys.argv) in (2, 3) and sys.argv[1] == '--template':
        parser = Template()
        parser.feed((Path(sys.argv[2]) if len(sys.argv) == 3 else ROOT / 'static/index.html').read_text())
        print(json.dumps(parser.elements))
    else:
        raw = sys.stdin.read(4097)
        if len(raw) > 4096:
            raise ValueError('Fixture request too large')
        print(json.dumps(exchange(json.loads(raw))))
