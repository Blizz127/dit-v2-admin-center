"""Exercise bounded response decoding with synthetic bytes, never a listener."""
from contextlib import ExitStack
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

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


if __name__ == '__main__':
    unittest.main()
