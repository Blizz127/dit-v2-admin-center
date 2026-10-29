"""Pure generation and loading of committed synthetic examples; no provider or hub."""
import json
import unittest
from unittest.mock import patch
from routing_audit import examples, FIXTURE
from tools.build_routing_audit_fixture import examples as generated


class RoutingAuditFixtureTests(unittest.TestCase):
    def test_committed_fixture_matches_in_memory_exercise(self):
        with patch('socket.socket.connect', side_effect=AssertionError('network forbidden')):
            expected = generated()
            self.assertEqual(examples(), expected)
            self.assertEqual(json.loads(FIXTURE.read_text()), expected)
        self.assertEqual([len(row['changes']) for row in expected], [1, 2])
        self.assertTrue(all(change['effective'] is None for row in expected for change in row['changes']))
        self.assertEqual(expected[1]['changes'][0]['beforeRequested'], 'fixture-model-one')
        self.assertIsNone(expected[1]['changes'][1]['beforeRequested'])

    def test_missing_or_invalid_fixture_is_unknown(self):
        for error in (OSError('private'), ValueError('private')):
            with patch('routing_audit.FIXTURE') as path:
                path.read_text.side_effect = error
                self.assertIsNone(examples())
