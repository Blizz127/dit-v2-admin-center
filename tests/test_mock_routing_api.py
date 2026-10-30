"""Proposed in-process mock contract only; no HTTP write route is enabled."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from mock_routing import BotKey
from mock_routing_api import MockRoutingAPI, PATH, MAX_BODY, MAX_REQUESTS


class MockRoutingAPITests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parent/'fixtures/mock-routing-write.json').read_text())
        self.api = MockRoutingAPI([BotKey('example-game', 'example-realm', 'example-bot', 'conversation')], ['example-model'])
        for name in ('socket.socket', 'socket.create_connection', 'subprocess.Popen'):
            guard = patch(name, side_effect=AssertionError('External effect forbidden'))
            guard.start(); self.addCleanup(guard.stop)

    def post(self, data=None):
        return self.api.request('POST', PATH, json.dumps(self.data if data is None else data).encode())

    def snapshot(self):
        status, result = self.api.request('GET', PATH)
        self.assertEqual(status, 200)
        return result

    def test_write_read_audit_and_identical_retry(self):
        status, result = self.post()
        self.assertEqual(status, 200)
        self.assertEqual(result['status'], 'applied-synthetic')
        self.assertIs(result['liveEffect'], False)
        before = self.snapshot()
        self.assertEqual(before['version'], 1)
        self.assertEqual(before['audit'][0]['actor'], 'synthetic-owner')
        self.assertEqual(before['audit'][0]['changes'][0], {'scope':self.data['targets'][0], 'before':None, 'after':'example-model'})
        self.assertEqual(self.post(), (status, result))
        self.assertEqual(self.snapshot(), before)
        result['version'] = 99
        before['audit'][0]['changes'][0]['after'] = 'tampered'
        self.assertEqual(self.post()[1]['version'], 1)
        self.assertEqual(self.snapshot()['audit'][0]['changes'][0]['after'], 'example-model')

    def test_conflicts_and_rejected_batch_have_no_side_effects(self):
        before = self.snapshot()
        bad = deepcopy(self.data)
        bad['targets'].append({**bad['targets'][0], 'nativeBot':'unknown'})
        self.assertEqual(self.post(bad)[0], 422)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.post()[0], 200)
        before = self.snapshot()
        self.assertEqual(self.post({**self.data, 'reason':'different content'})[0], 409)
        self.assertEqual(self.post({**self.data, 'requestId':'second'})[0], 409)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.post({**self.data, 'requestId':'second', 'expectedVersion':1})[0], 200)

    def test_invalid_bodies_are_redacted_and_leave_state_unchanged(self):
        before = self.snapshot()
        invalid = [None, [], {**self.data, 'actor':'OMIT_PRIVATE'}, {**self.data, 'environment':'live'},
                   {**self.data, 'expectedVersion':True}, {**self.data, 'expectedVersion':-1},
                   {**self.data, 'expectedVersion':2**53}, {**self.data, 'targets':[]},
                   {**self.data, 'targets':self.data['targets']*2},
                   {**self.data, 'targets':[{**self.data['targets'][0], 'nativeBot':' '}]},
                   {**self.data, 'reason':'x'*257}, {**self.data, 'reason':'bad\x00'},
                   {**self.data, 'requestId':'../../OMIT_PRIVATE'}]
        bodies = [json.dumps(data).encode() for data in invalid]
        bodies += [b'\xff', b'{"contract":"OMIT_PRIVATE","contract":"duplicate"}',
                   b'{"x":NaN}', b'not JSON OMIT_PRIVATE']
        for body in bodies:
            with self.subTest(body=body[:32]):
                status, result = self.api.request('POST', PATH, body)
                self.assertEqual(status, 400)
                self.assertEqual(result, {'kind':'synthetic', 'error':'invalid synthetic routing request'})
                self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.api.request('POST', PATH, b'x'*(MAX_BODY+1))[0], 413)
        self.assertEqual(self.api.request('GET', PATH, b'{}')[0], 400)
        self.assertEqual(self.api.request('PUT', PATH)[0], 405)
        self.assertEqual(self.api.request('POST', '/api/routing', b'{}')[0], 404)
        self.assertEqual(self.snapshot(), before)

    def test_concurrent_identical_retries_apply_once(self):
        barrier = Barrier(2)
        def submit():
            barrier.wait(timeout=2)
            return self.post()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(submit) for _ in range(2)]
            results = [future.result(timeout=3) for future in futures]
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0][0], 200)
        self.assertEqual(len(self.snapshot()['audit']), 1)

    def test_capacity_is_bounded_but_existing_retry_still_works(self):
        for index in range(MAX_REQUESTS):
            self.assertEqual(self.post({**self.data, 'requestId':f'fixture-{index}', 'expectedVersion':index})[0], 200)
        before = self.snapshot()
        self.assertEqual(self.post({**self.data, 'requestId':'new', 'expectedVersion':MAX_REQUESTS})[0], 429)
        self.assertEqual(self.post({**self.data, 'requestId':'fixture-0'})[0], 200)
        self.assertEqual(self.snapshot(), before)

    def test_distinct_writers_at_same_version_have_one_winner(self):
        barrier = Barrier(2)
        def submit(request_id):
            barrier.wait(timeout=2)
            return request_id, self.post({**self.data, 'requestId':request_id})
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(submit, request_id) for request_id in ('writer-a', 'writer-b')]
            results = [future.result(timeout=3) for future in futures]
        self.assertEqual(sorted(result[0] for _, result in results), [200, 409])
        self.assertEqual(self.snapshot()['version'], 1)
        self.assertEqual(len(self.snapshot()['audit']), 1)
        loser = next(request_id for request_id, result in results if result[0] == 409)
        self.assertEqual(self.post({**self.data, 'requestId':loser, 'expectedVersion':1})[0], 200)
        self.assertEqual(len(self.snapshot()['audit']), 2)

    def test_real_http_handler_still_refuses_mock_write_path(self):
        import server
        from tests.test_offline_inspector_handler import MemoryConnection
        body = json.dumps(self.data).encode()
        wire = (f'POST {PATH} HTTP/1.1\r\nHost: fixture.invalid\r\nAuthorization: Bearer fixture-token\r\nContent-Length: {len(body)}\r\n\r\n').encode() + body
        connection = MemoryConnection(wire)
        with patch('server.overview', side_effect=AssertionError('No collector permitted')):
            server.Handler(connection, ('127.0.0.1', 0), SimpleNamespace(admin_token='fixture-token'))
        headers, response = bytes(connection.outgoing).split(b'\r\n\r\n', 1)
        self.assertIn(b'405 Method Not Allowed', headers)
        self.assertEqual(json.loads(response), {'error':'method not allowed'})
        self.assertEqual(self.snapshot()['version'], 0)
