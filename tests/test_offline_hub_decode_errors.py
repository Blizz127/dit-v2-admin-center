"""Exercise bounded response decoding with synthetic bytes, never a listener."""
from contextlib import ExitStack
import io
from http.client import IncompleteRead
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from live_hub import HubReader, HubReadError, HubResponseTooLarge, MAX_RESPONSE


class OfflineHubDecodeErrorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        token = Path(temp.name) / 'token'
        token.write_text('synthetic-token')
        stack = ExitStack()
        self.addCleanup(stack.close)
        for target in ('socket.socket', 'socket.create_connection'):
            stack.enter_context(patch(target, side_effect=AssertionError('Network forbidden')))
        self.reader = HubReader('http://127.0.0.1:1', token)
        self.reader.opener = Mock()

    def test_malformed_utf8_json_and_excessive_nesting_are_redacted(self):
        for raw in (b'\xffOMIT_PRIVATE_UTF8', b'{OMIT_PRIVATE_JSON', b'[' * 10000 + b'0' + b']' * 10000):
            with self.subTest(size=len(raw)):
                self.reader.opener.open.return_value = io.BytesIO(raw)
                with self.assertRaises(HubReadError) as raised:
                    self.reader.health()
                self.assertEqual(str(raised.exception), 'Hub read unavailable')
                self.assertTrue(raised.exception.__suppress_context__)

    def test_duplicate_fields_and_nonfinite_numbers_are_unavailable_on_every_read(self):
        reads = (self.reader.health, self.reader.interaction,
                 lambda: self.reader.trace('ffxi', 'fixture-correlation'),
                 *(lambda view=view: self.reader.get(view, 'ffxi')
                   for view in ('bots', 'learning', 'server-status')))
        invalid = (
            b'{"gameId":"ffxi","gameId":"swtor","private":"OMIT_PRIVATE"}',
            b'{"row":{"key":"one","key":"two"}}',
            b'{"row":{"key":"same","key":"same"}}',
            b'{"key":"one","\\u006bey":"two"}',
            b'{"metric":NaN}', b'{"metric":Infinity}', b'{"metric":-Infinity}',
            b'{"metric":1e999}', b'{"metric":-1e999}',
        )
        for read in reads:
            for raw in invalid:
                stream = io.BytesIO(raw)
                self.reader.opener.open.return_value = stream
                with self.subTest(raw=raw), self.assertRaises(HubReadError) as raised:
                    read()
                self.assertEqual(str(raised.exception), 'Hub read unavailable')
                self.assertTrue(raised.exception.__suppress_context__)
                self.assertTrue(stream.closed)
            # Valid field names may repeat in separate objects. Zero and finite
            # scientific notation must not be lost to numeric rejection.
            self.reader.opener.open.return_value = io.BytesIO(
                b'{"rows":[{"key":"one"},{"key":"two"}],"zero":0,"fraction":1.25e-2}')
            data, fetched = read()
            self.assertEqual(data, {'rows':[{'key':'one'}, {'key':'two'}], 'zero':0, 'fraction':0.0125})
            self.assertTrue(fetched)

    def test_oversize_stays_distinct_and_next_valid_read_recovers(self):
        self.reader.opener.open.return_value = io.BytesIO(b'x' * (MAX_RESPONSE + 1))
        with self.assertRaises(HubResponseTooLarge):
            self.reader.health()
        self.reader.opener.open.return_value = io.BytesIO(b'{"services":[]}')
        data, fetched = self.reader.health()
        self.assertEqual(data, {'services': []})
        self.assertTrue(fetched)
        args, kwargs = self.reader.opener.open.call_args
        self.assertEqual(args[0].get_method(), 'GET')
        self.assertEqual(kwargs['timeout'], 3)

    def test_empty_and_truncated_bodies_are_read_failures_not_empty_services(self):
        for raw in (b'', b' \n\t', b'{"services":[', b'{"services":[]'):
            with self.subTest(raw=raw):
                stream = io.BytesIO(raw)
                self.reader.opener.open.return_value = stream
                with self.assertRaisesRegex(HubReadError, '^Hub read unavailable$'):
                    self.reader.health()
                self.assertTrue(stream.closed)
        self.reader.opener.open.return_value = io.BytesIO(b'{"services":[]}')
        self.assertEqual(self.reader.health()[0], {'services': []})

    def test_truncated_transport_error_is_redacted_and_response_closed(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.side_effect = IncompleteRead(b'OMIT_PRIVATE_PARTIAL_BODY', 100)
        self.reader.opener.open.return_value = response
        with self.assertRaises(HubReadError) as raised:
            self.reader.health()
        self.assertEqual(str(raised.exception), 'Hub read unavailable')
        self.assertTrue(raised.exception.__suppress_context__)
        response.read.assert_called_once_with(MAX_RESPONSE + 1)
        response.__exit__.assert_called_once()


if __name__ == '__main__':
    unittest.main()
