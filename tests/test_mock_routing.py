import unittest

from mock_routing import BotKey, MockRouting


class MockRoutingTests(unittest.TestCase):
    def test_one_and_all_with_audit_and_compare_and_set(self):
        a = BotKey('ffxi', 'synthetic-realm', 'a', 'conversation')
        b = BotKey('ffxi', 'synthetic-realm', 'b', 'conversation')
        simulation = MockRouting([a, b], ['example-model-1', 'example-model-2'])
        self.assertEqual(simulation.apply([a], 'example-model-1', 0, 'fixture-owner', 'example'), 1)
        self.assertEqual(simulation.apply([a, b], 'example-model-2', 1, 'fixture-owner', 'example all'), 2)
        result = simulation.snapshot()
        self.assertEqual(result['policies'], {a: 'example-model-2', b: 'example-model-2'})
        self.assertEqual(result['audit'][1]['changes'], ((a, 'example-model-1', 'example-model-2'), (b, None, 'example-model-2')))
        with self.assertRaises(ValueError):
            simulation.apply([a], 'example-model-1', 1, 'fixture-owner', 'stale')
        self.assertEqual(simulation.snapshot(), result)

    def test_invalid_batch_does_not_partially_apply(self):
        a = BotKey('ffxi', 'synthetic-realm', 'a', 'conversation')
        unknown = BotKey('ffxi', 'synthetic-realm', 'unknown', 'conversation')
        simulation = MockRouting([a], ['example-model'])
        for keys, model in [([a, unknown], 'example-model'), ([a, a], 'example-model'), ([a], 'unapproved')]:
            with self.assertRaises(ValueError):
                simulation.apply(keys, model, 0, 'fixture-owner', 'example')
        self.assertEqual(simulation.snapshot(), {'version': 0, 'policies': {}, 'audit': []})


if __name__ == '__main__':
    unittest.main()
