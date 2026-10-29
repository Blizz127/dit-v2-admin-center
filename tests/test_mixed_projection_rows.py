"""Pure fixture checks: Unknown fields may coexist with valid scoped records."""
import copy
import json
import unittest

from live_hub import project_hub_health, project_trace
from interaction_projection import project_interaction


class MixedProjectionRowsTests(unittest.TestCase):
    def test_trace_empty_truncated_and_valid_inner_bodies_keep_row_order(self):
        bodies = ['', '{"classification":', 'null', '[]',
                  json.dumps({'classification': 'pending', 'isFinal': False}),
                  json.dumps({'classification': 'verified', 'isFinal': True}),
                  json.dumps({'classification': 4, 'isFinal': 'true', 'private': 'OMIT_PRIVATE'})]
        data = [{'kind': 'outcome', 'type': 'fixture.' + str(i), 'body': body} for i, body in enumerate(bodies)]
        original = copy.deepcopy(data)
        rows = project_trace(data)
        self.assertEqual([row['type'] for row in rows], ['fixture.' + str(i) for i in range(7)])
        self.assertEqual([row['isFinal'] for row in rows], [None, None, None, None, False, True, None])
        self.assertEqual([row['classification'] for row in rows], [None, None, None, None, 'pending', 'verified', None])
        self.assertNotIn('OMIT_PRIVATE', str(rows))
        self.assertEqual(data, original)
        with self.assertRaises(ValueError):
            project_trace(data + [None])  # Invalid record structure must not yield partial success.

    def test_health_mixed_valid_unknown_and_out_of_scope_services(self):
        data = {'services': [{'game': 'ffxi', 'label': 'Synthetic bridge', 'state': 'running'},
                             {'game': 'ffxi', 'label': None, 'state': True},
                             {'game': 'swtor', 'label': 'Synthetic adapter', 'state': 'unrecognized'},
                             {'game': 'other', 'label': 'OMIT_PRIVATE', 'state': 'running'}]}
        rows = project_hub_health(data, 'fixture-time')['services']
        self.assertEqual([row['state'] for row in rows], ['running', 'Unknown', 'Unknown'])
        self.assertEqual(rows[1]['label'], 'Unknown service')
        self.assertTrue(all(row['observedAt'] is None for row in rows))
        self.assertNotIn('OMIT_PRIVATE', str(rows))
        with self.assertRaises(ValueError):
            project_hub_health({'services': data['services'] + [None]}, 'fixture-time')

    def test_interaction_unknown_row_does_not_replace_valid_neighbor(self):
        data = {'switches': {'contract': True}, 'scopes': [
            {'gameId': 'ffxi', 'caller': 'fixture', 'serverInstanceId': 'fixture-server', 'bots': [
                {'actorKey': 'valid', 'fresh': True, 'activity': 'waiting', 'ageSeconds': 0},
                {'actorKey': 'unknown', 'fresh': 'true', 'activity': 'fighting', 'ageSeconds': None}]}]}
        rows = project_interaction(data, 'fixture-time')['bots']
        self.assertEqual([row['actorKey'] for row in rows], ['valid', 'unknown'])
        self.assertEqual(rows[0]['activity'], 'waiting')
        self.assertEqual(rows[0]['ageSeconds'], 0)
        self.assertIsNone(rows[1]['fresh'])
        self.assertIsNone(rows[1]['activity'])
        self.assertIsNone(rows[1]['ageSeconds'])
        data['scopes'][0]['bots'].append({'actorKey': ''})
        with self.assertRaises(ValueError):
            project_interaction(data, 'fixture-time')


if __name__ == '__main__':
    unittest.main()
