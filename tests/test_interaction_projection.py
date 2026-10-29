import copy
import unittest

from interaction_projection import project_interaction


def fixture():
    return {'switches': {'contract': True, 'naturalOrders': False, 'selfClaims': False},
            'freshForSeconds': 30, 'truncated': False, 'scopes': [
                {'gameId': 'ffxi', 'caller': 'fixture-adapter', 'serverInstanceId': 'fixture-server', 'bots': [
                    {'actorKey': 'fixture-bot', 'fresh': True, 'snapshotFresh': False, 'activity': 'waiting',
                     'source': 'native report', 'observedAtUtc': '2026-01-01T00:00:00Z', 'ageSeconds': 45,
                     'currentOrder': {'requester': 'private text'}, 'hold': {'target': 'private target'}}]}]}


class InteractionProjectionTests(unittest.TestCase):
    def test_current_view_does_not_make_old_snapshot_fresh(self):
        result = project_interaction(fixture(), 'fetch-time')
        bot = result['bots'][0]
        self.assertEqual(bot['activity'], 'waiting')
        self.assertTrue(bot['fresh'])
        self.assertFalse(bot['snapshotFresh'])
        self.assertNotIn('private', str(result))
        self.assertNotIn('currentOrder', bot)

    def test_stale_or_unknown_current_view_cannot_claim_activity(self):
        for fresh in (False, None, 'true', 1):
            data = fixture(); data['scopes'][0]['bots'][0]['fresh'] = fresh
            self.assertIsNone(project_interaction(data, 'time')['bots'][0]['activity'])

    def test_contract_off_or_unknown_is_not_current_bot_inventory(self):
        for enabled in (False, None, 'true', 1):
            data = fixture(); data['switches']['contract'] = enabled
            result = project_interaction(data, 'time')
            self.assertEqual(result['bots'], [])
            self.assertIs(result['switches']['contract'], False if enabled is False else None)

    def test_scope_and_identity_remain_distinct(self):
        data = fixture(); other = copy.deepcopy(data['scopes'][0]); other['serverInstanceId'] = 'another-server'
        data['scopes'].append(other)
        self.assertEqual(len(project_interaction(data, 'time')['bots']), 2)
        data['scopes'][0]['bots'].append(copy.deepcopy(data['scopes'][0]['bots'][0]))
        with self.assertRaises(ValueError): project_interaction(data, 'time')

    def test_response_limit_and_bad_shapes_are_rejected(self):
        for data in ({}, {'scopes': None}, {'scopes': [], 'switches': []}):
            with self.assertRaises(ValueError): project_interaction(data, 'time')
        data = fixture(); data['scopes'][0]['bots'] *= 51
        with self.assertRaises(ValueError): project_interaction(data, 'time')

    def test_missing_flags_and_unknown_activity_are_unknown(self):
        data = fixture(); del data['switches']['naturalOrders']
        data['scopes'][0]['bots'][0]['activity'] = 'private freeform message'
        data['scopes'][0]['bots'][0]['ageSeconds'] = -1
        result = project_interaction(data, 'time')
        self.assertIsNone(result['switches']['naturalOrders'])
        self.assertIsNone(result['bots'][0]['activity'])
        self.assertIsNone(result['bots'][0]['ageSeconds'])


if __name__ == '__main__': unittest.main()
