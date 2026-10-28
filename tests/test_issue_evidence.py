import unittest
from issue_evidence import bridge_fault_issue, pending_decision_issues


class IssueEvidenceTests(unittest.TestCase):
    def test_bridge_evidence_is_historical_and_uncertain(self):
        issue = bridge_fault_issue()
        self.assertIn('current status unknown', issue['status'])
        self.assertIn('exact exception was not observed', issue['detail'])
        self.assertIn('do not replay or restart', issue['suggestedFix'])
        self.assertIn('ef097b2', issue['suggestedFix'])
        self.assertTrue(issue['bridgeObservation'])

    def test_only_returned_pending_records_become_issues(self):
        result = pending_decision_issues({'items': [{'title': 'Example', 'project': 'example', 'createdAt': 'created', 'expiresAt': 'expires'}]})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 'Pending record')
        self.assertTrue(result[0]['ownerAttention'])
        self.assertEqual(pending_decision_issues({'items': []}), [])


if __name__ == '__main__': unittest.main()
