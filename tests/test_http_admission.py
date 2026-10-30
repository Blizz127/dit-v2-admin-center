"""Request admission using real worker threads/socket pairs, never a listener."""
import queue
import socket
import threading
import unittest
from unittest.mock import patch

from server import BoundedHTTPServer, Handler


class ObservedServer(BoundedHTTPServer):
    max_handlers = 2

    def __init__(self, handler):
        self.finished = queue.Queue()
        self.failures = queue.Queue()
        super().__init__(('127.0.0.1', 0), handler, bind_and_activate=False)

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            # A completion here means the production finally released the slot.
            self.finished.put(address)

    def handle_error(self, request, address):
        self.failures.put(address)


class HTTPAdmissionTests(unittest.TestCase):
    def pair(self):
        client, peer = socket.socketpair()
        client.settimeout(1)
        self.addCleanup(client.close)
        self.addCleanup(peer.close)
        return client, peer

    def test_capacity_closes_excess_without_queue_and_recovers_after_completion(self):
        started = queue.Queue()
        release = threading.Semaphore(0)

        def handler(request, address, server):
            started.put(address)
            if not release.acquire(timeout=3):
                raise AssertionError('Test handler was not released')

        with ObservedServer(handler) as server:
            try:
                for number in range(2):
                    _, peer = self.pair()
                    server.process_request(peer, number)
                    self.assertEqual(started.get(timeout=1), number)
                client, peer = self.pair()
                server.process_request(peer, 'excess')
                self.assertEqual(client.recv(1), b'')
                self.assertTrue(started.empty())
                self.assertTrue(server.finished.empty())

                release.release()
                server.finished.get(timeout=1)
                _, peer = self.pair()
                server.process_request(peer, 'replacement')
                self.assertEqual(started.get(timeout=1), 'replacement')
                release.release(2)
                server.finished.get(timeout=1)
                server.finished.get(timeout=1)
                self.assertTrue(started.empty(), 'Excess request was queued')
                self.assertTrue(server.failures.empty())
            finally:
                release.release(3)

    def test_handler_exception_releases_its_slot(self):
        def handler(request, address, server):
            if address == 'failure':
                raise RuntimeError('Synthetic handler failure')

        with ObservedServer(handler) as server:
            # Repeated failures must not exhaust the two available slots.
            for _ in range(2):
                _, peer = self.pair()
                server.process_request(peer, 'failure')
                self.assertEqual(server.finished.get(timeout=1), 'failure')
                self.assertEqual(server.failures.get(timeout=1), 'failure')
            _, peer = self.pair()
            server.process_request(peer, 'success')
            self.assertEqual(server.finished.get(timeout=1), 'success')
            self.assertTrue(server.failures.empty())

    def test_thread_start_failure_does_not_leak_admission_slots(self):
        with ObservedServer(lambda *args: None) as server:
            for _ in range(3):
                _, peer = self.pair()
                with patch('threading.Thread.start', side_effect=RuntimeError('Synthetic thread start failure')):
                    with self.assertRaisesRegex(RuntimeError, 'Synthetic thread start failure'):
                        server.process_request(peer, 'not-started')
                # Normal BaseServer dispatch owns socket cleanup on start error.
                server.shutdown_request(peer)
            _, peer = self.pair()
            server.process_request(peer, 'success')
            self.assertEqual(server.finished.get(timeout=1), 'success')
            self.assertTrue(server.failures.empty())

    def test_http_idle_timeouts_release_capacity_for_next_authenticated_route(self):
        class ShortIdleHandler(Handler):
            timeout = 0.3
            request_timeout = 0.6

        def response(client):
            wire = bytearray()
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    return bytes(wire)
                wire.extend(chunk)

        with ObservedServer(ShortIdleHandler) as server, patch('server.overview', side_effect=AssertionError('Collector forbidden')) as reader:
            server.admin_token = 'fixture-token'
            idle_clients = []
            for number in range(2):
                client, peer = self.pair()
                idle_clients.append(client)
                server.process_request(peer, ('idle', number))
            client, peer = self.pair()
            server.process_request(peer, ('excess', 0))
            self.assertEqual(client.recv(1), b'')
            for client in idle_clients:
                wire = response(client)
                self.assertTrue(wire.startswith(b'HTTP/1.0 408 '))
                self.assertEqual(wire.count(b'HTTP/1.0 '), 1)
            finished = {server.finished.get(timeout=1), server.finished.get(timeout=1)}
            self.assertEqual(finished, {('idle', 0), ('idle', 1)})

            client, peer = self.pair()
            client.sendall(b'GET /api/overview HTTP/1.1\r\nHost: offline.invalid\r\n\r\n')
            server.process_request(peer, ('recovery', 0))
            self.assertTrue(response(client).startswith(b'HTTP/1.0 401 '))
            self.assertEqual(server.finished.get(timeout=1), ('recovery', 0))
            self.assertTrue(server.failures.empty())
            reader.assert_not_called()


if __name__ == '__main__':
    unittest.main()
