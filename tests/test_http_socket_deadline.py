"""Measured HTTP acquisition limits over local socket pairs, without listeners."""
import json
import socket
import threading
import time
import unittest
from contextlib import ExitStack
from email.parser import BytesParser
from types import SimpleNamespace
from unittest.mock import patch

from server import Handler


class SocketDeadlineTests(unittest.TestCase):
    def exchange(self, handler_type, prefix, trickle=False, expected_status=408,
                 trickle_chunk=b'x', chunks=None):
        client, peer = socket.socketpair()
        errors = []
        stopped = threading.Event()
        ready = threading.Event()
        sent = []

        def serve():
            try:
                with peer:
                    ready.set()
                    handler_type(peer, ('local-socket-pair', 0),
                                 SimpleNamespace(admin_token='fixture-token'))
            except BaseException as error:
                errors.append(error)

        def feed():
            sequence = iter(chunks) if chunks is not None else None
            while not stopped.wait(0.04):
                try:
                    chunk = next(sequence) if sequence is not None else trickle_chunk
                    client.sendall(chunk)
                    sent.append(time.monotonic())
                except StopIteration:
                    return
                except OSError:
                    return

        worker = threading.Thread(target=serve, daemon=True)
        sender = threading.Thread(target=feed, daemon=True) if trickle else None
        try:
            client.settimeout(handler_type.request_timeout + 3)
            client.sendall(prefix)
            started = time.monotonic()
            with ExitStack() as guards:
                readers = [guards.enter_context(patch(target, side_effect=AssertionError('Collection forbidden')))
                           for target in ('server.overview', 'server.BRIDGE.read', 'server.HubReader',
                                          'server.HUB_VIEWS.get', 'server.HUB_HEALTH.get', 'server.HUB_INTERACTION.get')]
                worker.start()
                self.assertTrue(ready.wait(1))
                if sender:
                    sender.start()
                wire = bytearray()
                while True:
                    try:
                        chunk = client.recv(4096)
                    except ConnectionResetError:
                        # Closing with deliberately unread bytes may reset the
                        # pair. Still require the complete refusal below.
                        if expected_status not in (405, 414, 431):
                            raise
                        break
                    if not chunk:
                        break
                    wire.extend(chunk)
                elapsed = time.monotonic() - started
                worker.join(timeout=2)
                self.assertFalse(worker.is_alive(), 'Handler did not exit after refusal')
                for reader in readers:
                    reader.assert_not_called()
            head, body = bytes(wire).split(b'\r\n\r\n', 1)
            status, raw_headers = head.split(b'\r\n', 1)
            headers = BytesParser().parsebytes(raw_headers)
            self.assertEqual(int(status.split()[1]), expected_status)
            error = {405: 'method not allowed', 401: 'unauthorized'}.get(expected_status, 'request rejected')
            self.assertEqual(json.loads(body), {'error': error})
            if expected_status == 405:
                self.assertEqual(headers['Allow'], 'GET')
                self.assertEqual(headers['Connection'], 'close')
                self.assertNotIn(b'100 Continue', wire)
            self.assertEqual(headers['Content-Type'], 'application/json')
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertEqual(int(headers['Content-Length']), len(body))
            self.assertNotIn(b'OMIT_PRIVATE', wire)
            self.assertEqual(bytes(wire).count(b'HTTP/1.0 '), 1)
            self.assertEqual(errors, [])
            return elapsed, sent
        finally:
            stopped.set()
            client.close()
            worker.join(timeout=2)
            if sender and sender.ident is not None:
                sender.join(timeout=2)
            self.assertFalse(worker.is_alive(), 'Handler did not exit')
            if sender:
                self.assertFalse(sender.is_alive(), 'Trickle sender did not exit')

    def test_default_five_second_idle_timeout_is_measured(self):
        elapsed, _ = self.exchange(Handler, b'GET /api/overview HTTP/1.1\r\nX-OMIT_PRIVATE: unfinished')
        self.assertGreaterEqual(elapsed, 4.5)
        self.assertLess(elapsed, 7.5)
        print(f'idle socket read: {elapsed:.3f}s (configured 5s)', flush=True)

    def test_trickled_request_line_and_header_hit_total_deadline(self):
        class ShortDeadline(Handler):
            timeout = 0.35
            request_timeout = 0.65

        for prefix in (b'GET /api/OMIT_PRIVATE_',
                       b'GET /api/overview HTTP/1.1\r\nX-OMIT_PRIVATE: '):
            with self.subTest(prefix=prefix):
                elapsed, sent = self.exchange(ShortDeadline, prefix, trickle=True)
                self.assertGreaterEqual(elapsed, 0.58)
                self.assertLess(elapsed, 2)
                self.assertGreaterEqual(len(sent), 5)
                print(f'trickled socket read: {elapsed:.3f}s (deadline 0.65s, {len(sent)} bytes)', flush=True)

    def test_write_headers_refused_before_a_withheld_body_arrives(self):
        framing_cases = (
            'Content-Length: 1',
            'Content-Length: 999999999999999999999999999',
            'Transfer-Encoding: chunked',
            'Content-Length: 1\r\nTransfer-Encoding: chunked',
            'Content-Length: 1\r\ncontent-length: 9999999',
            'Content-Length: OMIT_PRIVATE_INVALID',
        )
        elapsed_times = []
        for method in ('POST', 'PUT'):
            for route in ('/api/overview', '/api/bridge-status'):
                for framing in framing_cases:
                    with self.subTest(method=method, route=route, framing=framing):
                        prefix = (f'{method} {route} HTTP/1.1\r\nHost: offline.invalid\r\n'
                                  'Authorization: Bearer fixture-token\r\nConnection: keep-alive\r\n'
                                  'Expect: 100-continue\r\n' + framing + '\r\n\r\n').encode()
                        # Keep the sending side open but send no promised body.
                        # A parser/drain would wait for the idle timeout instead.
                        elapsed, _ = self.exchange(Handler, prefix, expected_status=405)
                        self.assertLess(elapsed, 1.5)
                        elapsed_times.append(elapsed)
        print(f'24 withheld-body refusals: max {max(elapsed_times):.3f}s (idle timeout 5s)', flush=True)

    def test_oversized_request_and_header_refusal_timing(self):
        cases = (
            ('request line', 414, b'GET /OMIT_PRIVATE_' + b'x' * 65536 + b' HTTP/1.1\r\n\r\n'),
            ('header line', 431, b'GET /api/overview HTTP/1.1\r\nX-OMIT_PRIVATE: ' + b'x' * 65536 + b'\r\n\r\n'),
            ('aggregate headers', 431, b'GET /api/overview HTTP/1.1\r\n' +
             (b'X-OMIT_PRIVATE: ' + b'x' * 32768 + b'\r\n') * 2 + b'\r\n'),
            ('header count', 431, b'GET /api/overview HTTP/1.1\r\n' + b'X-OMIT_PRIVATE: x\r\n' * 101 + b'\r\n'),
        )
        for label, expected, prefix in cases:
            with self.subTest(limit=label):
                elapsed, _ = self.exchange(Handler, prefix, expected_status=expected)
                self.assertLess(elapsed, 2)
                print(f'{label} refusal: {elapsed:.3f}s, status {expected}', flush=True)

    def test_completed_header_lines_do_not_reset_total_deadline(self):
        class ShortDeadline(Handler):
            timeout = 0.35
            request_timeout = 0.65

        elapsed, sent = self.exchange(ShortDeadline, b'GET /api/overview HTTP/1.1\r\n',
                                      trickle=True, trickle_chunk=b'X-Probe: completed\r\n')
        self.assertGreaterEqual(elapsed, 0.58)
        self.assertLess(elapsed, 2)
        self.assertGreaterEqual(len(sent), 5)
        print(f'completed-header trickle: {elapsed:.3f}s, {len(sent)} lines (total 0.65s)', flush=True)

    def test_headers_completed_in_time_reach_normal_authentication(self):
        class ShortDeadline(Handler):
            timeout = 0.25
            request_timeout = 0.8

        # Total acquisition exceeds the idle interval, but each arrival is
        # timely and the terminating blank line arrives before the total limit.
        chunks = [b'X-Probe: completed\r\n'] * 8 + [b'\r\n']
        elapsed, sent = self.exchange(ShortDeadline, b'GET /api/overview HTTP/1.1\r\n',
                                      trickle=True, expected_status=401, chunks=chunks)
        self.assertEqual(len(sent), len(chunks))
        self.assertGreater(elapsed, ShortDeadline.timeout)
        self.assertLess(elapsed, ShortDeadline.request_timeout)
        print(f'completed within budget: {elapsed:.3f}s, ordinary 401 (idle 0.25s / total 0.8s)', flush=True)

    def test_partial_chunk_and_pipelined_request_cannot_reach_readers(self):
        for framing, body in ((b'Content-Length: 1', b'x'),
                              (b'Transfer-Encoding: chunked', b'ffffff\r\nx')):
            with self.subTest(framing=framing):
                prefix = (b'POST /api/bridge-status HTTP/1.1\r\nConnection: keep-alive\r\n'
                          + framing + b'\r\n\r\n' + body +
                          b'GET /api/overview HTTP/1.1\r\nAuthorization: Bearer fixture-token\r\n\r\n')
                elapsed, _ = self.exchange(Handler, prefix, expected_status=405)
                self.assertLess(elapsed, 1.5)


if __name__ == '__main__':
    unittest.main()
