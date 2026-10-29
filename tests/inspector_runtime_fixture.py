"""Serve synthetic in-memory handler responses and a parsed template manifest to Node.

This is a test adapter, not a listener. It reuses the offline handler suite's
socket/subprocess/database/read guards and projected fixture collector.
"""
import json
from html.parser import HTMLParser
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from test_offline_inspector_handler import OfflineInspectorHandlerTests


class Template(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = {}
        self.select = None
        self.first_option = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        identity = attrs.get('id')
        if identity:
            if identity in self.elements:
                raise ValueError('Duplicate template ID')
            self.elements[identity] = {'tag': tag, 'attrs': attrs, 'value': attrs.get('value', '')}
        if tag == 'select':
            self.select, self.first_option = identity, True
        if tag == 'option' and self.select:
            if self.first_option or 'selected' in attrs:
                self.elements[self.select]['value'] = attrs.get('value', '')
            self.first_option = False

    def handle_endtag(self, tag):
        if tag == 'select':
            self.select = None


def exchange(request):
    if request.get('path') not in ('/api/overview?source=mock', '/api/bridge-status'):
        raise ValueError('Only synthetic inspector fixture routes are allowed')
    case = OfflineInspectorHandlerTests()
    case.setUp()
    try:
        # The UI starts a bridge read on overview success; return only unknown fixture state.
        unknown = dict(unit='unknown', substate='unknown', result='unknown', marker='unknown',
                       markerReason='unknown', source='Synthetic offline fixture', observedAt=None)
        with patch('server.BRIDGE.read', return_value=unknown):
            status, headers, body = case.request(path=request['path'], token=request.get('token'))
        return {'status': status, 'headers': dict(headers.items()), 'body': body.decode()}
    finally:
        case.doCleanups()


if __name__ == '__main__':
    if sys.argv[1:] == ['--template']:
        parser = Template()
        parser.feed((ROOT / 'static/index.html').read_text())
        print(json.dumps(parser.elements))
    else:
        raw = sys.stdin.read(4097)
        if len(raw) > 4096:
            raise ValueError('Fixture request too large')
        print(json.dumps(exchange(json.loads(raw))))
