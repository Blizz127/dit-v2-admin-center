"""Document inventory and temporary loopback mock only; no live collectors."""
import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from contextlib import ExitStack
from http.server import ThreadingHTTPServer

import project_issues
import server
from tools.build_inspector_playtest import snapshot


class ProjectIssuesTests(unittest.TestCase):
    def test_repository_inventory_has_provenance_and_no_live_claims(self):
        rows = project_issues.read()
        self.assertEqual(len(rows), 6)
        self.assertEqual(len({r['id'] for r in rows}), 6)
        self.assertTrue(all(r['updatedAt'] is None and r['documentIssue'] for r in rows))
        self.assertEqual({r['status'] for r in rows}, {'Documented gap', 'Verification pending'})
        self.assertEqual(len([r for r in rows if r['scope']=='FFXI']), 1)
        self.assertEqual(len([r for r in rows if r['scope']=='SWTOR']), 1)
        self.assertIn('NOT RUN', rows[-1]['detail'])
        self.assertEqual(snapshot()['issues'], rows)

    def test_bad_document_preserves_other_inventory_with_unknown_placeholder(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in project_issues.DOCUMENTS:
                (root/name).parent.mkdir(parents=True, exist_ok=True)
                (root/name).write_bytes((project_issues.ROOT/name).read_bytes())
            target = root/project_issues.DOCUMENTS[0]
            valid = target.read_text()
            invalid = ['', valid.replace('"status": "Documented gap"', '"status": "Healthy"',1),
                       valid.replace('"id": "ffxi-evidence"', '"id": "ffxi-evidence", "id":"hidden"',1),
                       valid + project_issues.START, 'x' * (256*1024+1)]
            for text in invalid:
                target.write_text(text)
                rows = project_issues.read(root)
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[0]['status'], 'Unknown')
                self.assertEqual(rows[1]['status'], 'Verification pending')
            target.write_text(project_issues.START + '\n```json\n[]\n```\n' + project_issues.END)
            self.assertEqual([r['status'] for r in project_issues.read(root)], ['Verification pending'])
            target.unlink()
            rows = project_issues.read(root)
            self.assertEqual(rows[0]['status'], 'Unknown')

    def test_localhost_mock_serves_document_issues_only_after_auth(self):
        data = snapshot()
        with ExitStack() as stack:
            for target in ('server.BRIDGE.read', 'server.HUB_VIEWS.get', 'server.HUB_HEALTH.get',
                           'server.HUB_INTERACTION.get', 'sqlite3.connect', 'subprocess.Popen'):
                stack.enter_context(patch(target, side_effect=AssertionError('Live dependency forbidden')))
            overview = stack.enter_context(patch('server.overview', side_effect=lambda *_: copy.deepcopy(data)))
            httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
            httpd.admin_token = 'synthetic-localhost-token'
            thread = threading.Thread(target=httpd.serve_forever, kwargs={'poll_interval':0.02}, daemon=True)
            thread.start()
            try:
                for authorized in (False, True):
                    conn = http.client.HTTPConnection('127.0.0.1', httpd.server_port, timeout=2)
                    try:
                        conn.request('GET', '/api/overview?source=mock', headers={'Authorization':'Bearer synthetic-localhost-token'} if authorized else {})
                        response = conn.getresponse()
                        body = json.loads(response.read())
                        self.assertEqual(response.status, 200 if authorized else 401)
                        self.assertEqual(response.getheader('Cache-Control'), 'no-store')
                        if authorized:
                            self.assertEqual(body['issues'], project_issues.read())
                            self.assertEqual(len(body['modelCalls']), 3)
                            self.assertEqual({r['model'] for r in body['modelCalls']}, {'Example model A','Example model B'})
                            self.assertTrue(all(r['quality'] is None for r in body['modelCalls']))
                        else:
                            overview.assert_not_called()
                    finally:
                        conn.close()
                overview.assert_called_once_with('mock')
                # The new editor is page-local; adding it must not create a write API.
                conn = http.client.HTTPConnection('127.0.0.1', httpd.server_port, timeout=2)
                try:
                    conn.request('GET', '/')
                    response = conn.getresponse()
                    markup = response.read().decode()
                    self.assertEqual(response.status, 200)
                    self.assertIn('id="bot-draft-fields" disabled', markup)
                    self.assertIn('Nothing is saved, applied or sent.', markup)
                    conn.request('POST', '/api/bots/one/draft', body=b'{"goal":"synthetic"}',
                                 headers={'Authorization':'Bearer synthetic-localhost-token'})
                    response = conn.getresponse()
                    self.assertEqual(response.status, 405)
                    self.assertEqual(response.getheader('Allow'), 'GET')
                    self.assertEqual(json.loads(response.read()), {'error':'method not allowed'})
                    overview.assert_called_once_with('mock')
                finally:
                    conn.close()
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=2)
                self.assertFalse(thread.is_alive())
