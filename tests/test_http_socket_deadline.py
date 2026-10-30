"""Measured HTTP acquisition limits over local socket pairs, without listeners."""
import json
import socket
import threading
import time
import unittest
from email.parser import BytesParser
from types import SimpleNamespace
from unittest.mock import patch

from server import Handler


class SocketDeadlineTests(unittest.TestCase):
    def exchange(self, handler_type, prefix, trickle=False):
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
            while not stopped.wait(0.04):
                try:
                    client.sendall(b'x')
                    sent.append(time.monotonic())
                except OSError:
                    return

        worker = threading.Thread(target=serve, daemon=True)
        sender = threading.Thread(target=feed, daemon=True) if trickle else None
        try:
            client.settimeout(handler_type.request_timeout + 3)
            client.sendall(prefix)
            started = time.monotonic()
            with patch('server.overview', side_effect=AssertionError('Collection forbidden')) as overview:
                worker.start()
                self.assertTrue(ready.wait(1))
                if sender:
                    sender.start()
                wire = bytearray()
                while True:
                    chunk = client.recv(4096)
                    if not chunk:
                        break
                    wire.extend(chunk)
                elapsed = time.monotonic() - started
                overview.assert_not_called()
            head, body = bytes(wire).split(b'\r\n\r\n', 1)
            status, raw_headers = head.split(b'\r\n', 1)
            headers = BytesParser().parsebytes(raw_headers)
            self.assertEqual(int(status.split()[1]), 408)
            self.assertEqual(json.loads(body), {'error': 'request rejected'})
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


if __name__ == '__main__':
    unittest.main()
