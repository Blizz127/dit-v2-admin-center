import unittest

from r10_projection import project_learning, project_learning_attention


class ProjectionTests(unittest.TestCase):
    def test_light_response_does_not_claim_evidence_or_policy(self):
        payload = {'gameId': 'ffxi', 'tasks': [
            {'id': 'one', 'gameId': 'ffxi', 'topic': 'Navigation', 'status': 'verified', 'updatedAtUtc': '2026-01-01T00:00:00Z'},
            {'id': 'two', 'gameId': 'ffxi', 'topic': 'Missions', 'status': 'failed', 'reason': 'Insufficient evidence'},
        ]}
        rows = project_learning(payload)
        self.assertEqual(rows[0]['evidence'], 'Not included')
        self.assertEqual(rows[0]['policy'], 'Unknown')
        self.assertEqual(project_learning_attention(rows)[0]['detail'], 'Insufficient evidence')
        self.assertEqual(project_learning_attention(rows)[0]['learningId'], 'two')
        self.assertEqual(len(project_learning_attention(rows)), 1)

    def test_rejects_missing_or_mismatched_scope(self):
        with self.assertRaises(ValueError):
            project_learning({'gameId': 'ffxi', 'tasks': [{'id': 'one', 'gameId': 'swtor', 'topic': 'X', 'status': 'failed'}]})
        with self.assertRaises(ValueError):
            project_learning({'gameId': 'ffxi'})

class RosterAndHealthTests(unittest.TestCase):
    def test_roster_registration_does_not_prove_presence(self):
        from r10_projection import project_roster
        bot = project_roster('ffxi', [{'key': 'example', 'name': 'Example', 'bodyKind': 'fixture'}])[0]
        self.assertEqual(bot['status'], 'Unknown')
        self.assertIsNone(bot['observedAt'])
        self.assertIn('not presence', bot['source'])

    def test_service_state_is_not_bot_health_and_omits_target(self):
        from r10_projection import project_health
        health = project_health({'utc': '2026-01-01T00:00:00Z', 'services': [
            {'id': 'example', 'label': 'Example feed', 'game': 'ffxi', 'state': 'quiet', 'target': '/private/path'}]})[0]
        self.assertEqual(health['status'], 'quiet')
        self.assertEqual(health['observedAt'], '2026-01-01T00:00:00Z')
        self.assertNotIn('target', health)


if __name__ == '__main__':
    unittest.main()
