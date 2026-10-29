"""Offline reader contract checks for HUB-CONTRACT-DRAFT.md at f95fe8a.

The JSON fixture models candidate e8c81be's interaction wire shape; it is not
live evidence. The routing sketch in the draft remains unimplemented.
"""
import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hub_cache import HubViewsCache
from interaction_projection import project_interaction
from live_hub import HubReader


FIXTURE = Path(__file__).parent / 'fixtures/interaction-e8c81be.json'
GENERATED = FIXTURE.parent / 'interaction-generated'


class InteractionContractTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.token = Path(self.directory.name) / 'fixture-token'
        self.token.write_text('synthetic-admin-token')
        self.payload = json.loads(FIXTURE.read_text())
        self.requests = []
        # Any accidental real socket use fails this offline test immediately.
        for guard in (patch('socket.create_connection', side_effect=AssertionError('network forbidden')),
                      patch('socket.socket.connect', side_effect=AssertionError('network forbidden')),
                      patch('urllib.request.OpenerDirector.open', side_effect=self.open_fixture)):
            guard.start()
            self.addCleanup(guard.stop)

    def open_fixture(self, request, timeout):
        self.requests.append(request)
        self.assertEqual(request.get_method(), 'GET')
        self.assertEqual(request.full_url, 'http://127.0.0.1:7390/v1/control/interaction?limit=50')
        self.assertEqual(request.get_header('Authorization'), 'Bearer synthetic-admin-token')
        self.assertIsNone(request.data)
        self.assertLessEqual(timeout, 3)
        return io.BytesIO(json.dumps(self.payload).encode())

    def read(self):
        return project_interaction(*HubReader('http://127.0.0.1:7390', self.token).interaction())

    def test_reader_preserves_scope_and_independent_freshness(self):
        result = self.read()
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(result['switches'], self.payload['switches'])
        self.assertEqual(result['freshForSeconds'], 30)
        self.assertIs(result['truncated'], True)
        self.assertTrue(result['fetchedAt'])
        self.assertIn('deployed revision unverified', result['coverage'])
        self.assertEqual(len(result['bots']), 3)
        identities = {(b['caller'], b['serverInstanceId'], b['actorKey']) for b in result['bots']}
        self.assertEqual(len(identities), 3)
        first, second, third = result['bots']
        self.assertEqual((first['fresh'], first['snapshotFresh'], first['activity']), (True, False, 'waiting'))
        self.assertEqual((second['fresh'], second['snapshotFresh'], second['activity']), (False, True, None))
        self.assertEqual(third['activity'], 'following')
        self.assertIsNone(third['observedAt'])
        self.assertIsNone(third['ageSeconds'])
        self.assertEqual(first['observedAt'], '2026-01-01T00:00:00Z')
        self.assertEqual(first['ageSeconds'], 45)
        self.assertNotIn('OMIT_PRIVATE', json.dumps(result))
        for row in result['bots']:
            self.assertNotIn('botId', row)  # No inferred roster identity.

    def test_disabled_or_unknown_collection_does_not_return_inventory(self):
        for value in (False, None, 'true', 1):
            with self.subTest(contract=value):
                self.payload['switches']['contract'] = value
                result = self.read()
                self.assertEqual(result['bots'], [])
                self.assertIs(result['switches']['contract'], False if value is False else None)

    def test_cache_keeps_fetch_time_and_does_not_share_mutable_state(self):
        clock = [100]
        cache = HubViewsCache(lambda url, token: project_interaction(*HubReader(url, token).interaction()),
                              clock=lambda: clock[0])
        first = cache.get('http://127.0.0.1:7390', self.token)
        expected = copy.deepcopy(first)
        first['bots'].clear()
        clock[0] = 114.9
        self.assertEqual(cache.get('http://127.0.0.1:7390', self.token), expected)
        self.assertEqual(len(self.requests), 1)
        clock[0] = 115
        cache.get('http://127.0.0.1:7390', self.token)
        self.assertEqual(len(self.requests), 2)

    def test_duplicate_scope_identity_rejected_without_partial_inventory(self):
        self.payload['scopes'].append(copy.deepcopy(self.payload['scopes'][0]))
        with self.assertRaises(ValueError): self.read()

    def test_invalid_numeric_metadata_stays_unknown_through_reader(self):
        for label, value in [('oversized integer', 10 ** 400), ('negative', -1),
                             ('boolean', True), ('string', '30')]:
            with self.subTest(case=label):
                self.payload['freshForSeconds'] = value
                self.payload['scopes'][0]['bots'][0]['ageSeconds'] = value
                result = self.read()
                self.assertIsNone(result['freshForSeconds'])
                self.assertIsNone(result['bots'][0]['ageSeconds'])

    def test_proposed_routing_sketch_is_not_a_reader_endpoint(self):
        reader = HubReader('http://127.0.0.1:7390', self.token)
        for route in ('routing', 'model-routing', 'providers', 'goals'):
            with self.subTest(route=route), self.assertRaises(ValueError):
                reader.get(route, 'ffxi')
        self.assertEqual(self.requests, [])

    def test_generated_snapshots_through_reader_projection_and_cache(self):
        # Expected semantics are explicit, independent of projection logic.
        cases = {
            'contract-off-empty': (0, None),
            'contract-off-retained': (0, None),
            'contract-on-empty': (0, None),
            'fresh-snapshot': (1, (True, True, 'idle')),
            'fresh-snapshot-superseded-view': (1, (False, True, None)),
            'fresh-mode-stale-snapshot': (1, (True, False, 'following')),
            'stale-mode-and-snapshot': (1, (False, False, None)),
            'same-actor-distinct-scopes': (3, None),
            'limit-50-truncated': (50, None),
        }
        manifest = json.loads((GENERATED / 'MANIFEST.json').read_text())
        self.assertEqual(set(manifest['files']),
                         {name + '.json' for name in cases} | {'route-check.json'})
        for name, (count, freshness) in cases.items():
            with self.subTest(snapshot=name):
                raw = (GENERATED / (name + '.json')).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), manifest['files'][name + '.json'])
                self.payload = json.loads(raw)
                self.requests.clear()
                clock = [0]
                cache = HubViewsCache(
                    lambda url, token: project_interaction(*HubReader(url, token).interaction()),
                    clock=lambda: clock[0])
                result = cache.get('http://127.0.0.1:7390', self.token)
                self.assertEqual(len(result['bots']), count)
                self.assertEqual(result['switches'], self.payload['switches'])
                self.assertEqual(result['truncated'], name == 'limit-50-truncated')
                if freshness:
                    bot = result['bots'][0]
                    self.assertEqual(tuple(bot[k] for k in ('fresh', 'snapshotFresh', 'activity')), freshness)
                identities = {(b['caller'], b['serverInstanceId'], b['actorKey']) for b in result['bots']}
                self.assertEqual(len(identities), count)
                if name == 'same-actor-distinct-scopes':
                    self.assertEqual(len({b['actorKey'] for b in result['bots']}), 1)
                self.assertNotIn('FixtureRequester', json.dumps(result))
                for row in [result, *result['bots']]:
                    for field in ('currentOrder', 'recentOrders', 'mode', 'hold', 'follow',
                                  'capabilities', 'stateCounts', 'ledgerCounts', 'botId'):
                        self.assertNotIn(field, row)
                expected = copy.deepcopy(result)
                result['bots'].clear()
                clock[0] = 14.9
                self.assertEqual(cache.get('http://127.0.0.1:7390', self.token), expected)
                self.assertEqual(len(self.requests), 1)
                clock[0] = 15
                cache.get('http://127.0.0.1:7390', self.token)
                self.assertEqual(len(self.requests), 2)


if __name__ == '__main__': unittest.main()
