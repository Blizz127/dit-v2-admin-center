"""Offline interpretation checks, not party-test or game-execution evidence."""
import copy
import json
from pathlib import Path
import unittest
from tools.review_party_greeting import review


class PartyGreetingReviewTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parent / 'fixtures/party-greeting-review.json').read_text())

    def speech(self):
        return dict(scope=copy.deepcopy(self.data['scope']), correlationId='fixture-attempt',
                    reporter='owner', confirmed=True, heardAt='2026-01-01T12:01:06Z',
                    reportedAt='2026-01-01T12:01:30Z')

    def test_queue_and_service_health_do_not_prove_speech_or_model(self):
        self.data.update(unit='active', marker='absent', traceFinal=True, replySource='model',
                         text='OMIT_PRIVATE_CHAT')
        original = copy.deepcopy(self.data)
        result = review(self.data)
        self.assertIn('matching new queue', result['queuedReply'])
        self.assertEqual(result['nativeSpeech'], 'Unknown')
        self.assertEqual(result['modelOrigin'], 'Unknown')
        self.assertNotIn('OMIT_PRIVATE', json.dumps(result))
        self.assertEqual(self.data, original)

    def test_old_unrelated_future_and_unconfirmed_queue_rows_stay_unknown(self):
        for change in ({'observedAt': '2025-12-31T23:59:00Z'},
                       {'observedAt': '2026-01-01T12:03:00Z'}, {'observedAt': 'bad'},
                       {'correlationId': 'another-attempt'}, {'scope': {**self.data['scope'], 'party': 'other'}},
                       {'enqueued': 'true'}):
            with self.subTest(change=change):
                data = copy.deepcopy(self.data)
                data['queuedReplies'][0].update(change)
                self.assertEqual(review(data)['queuedReply'], 'Unknown')

    def test_owner_report_is_separate_from_queue_and_never_proves_ai(self):
        self.data['ownerSpeech'] = self.speech()
        self.data['queuedReplies'] = []
        result = review(self.data)
        self.assertEqual(result['queuedReply'], 'Unknown')
        self.assertIn('Owner-reported', result['nativeSpeech'])
        self.assertEqual(result['modelOrigin'], 'Unknown')
        for change in ({'confirmed': False}, {'reporter': 'model'}, {'correlationId': 'other'},
                       {'heardAt': '2026-01-01T11:59:00Z'}, {'reportedAt': '2026-01-01T12:03:00Z'},
                       {'scope': {**self.data['scope'], 'botId': 'other'}}):
            data = copy.deepcopy(self.data); data['ownerSpeech'].update(change)
            self.assertEqual(review(data)['nativeSpeech'], 'Unknown')

    def test_scope_eligibility_and_owner_greeting_are_required(self):
        for key, value in [('eligibility', None), ('greeting', None), ('scope', {}),
                           ('restartAt', '2026-01-01T12:01:00Z'), ('observedThrough', 'invalid')]:
            data = copy.deepcopy(self.data); data[key] = value
            self.assertEqual(review(data)['queuedReply'], 'Unknown')
        for field in ('identityVerified', 'partyMember'):
            data = copy.deepcopy(self.data); data['eligibility'][field] = 'true'
            self.assertEqual(review(data)['queuedReply'], 'Unknown')
        self.data['greeting']['ownerGenerated'] = False
        self.assertEqual(review(self.data)['queuedReply'], 'Unknown')

    def test_absent_or_malformed_evidence_does_not_become_negative_proof(self):
        for queue in (None, [], 'invalid', [None, {}]):
            self.data['queuedReplies'] = queue
            self.assertEqual(review(self.data)['queuedReply'], 'Unknown')
        for data in (None, {}, [], 'invalid'):
            self.assertEqual(review(data)['nativeSpeech'], 'Unknown')

    def test_multiple_or_mixed_reports_require_review_without_overriding_speech(self):
        original = self.data['queuedReplies'][0]
        positive = copy.deepcopy(original)
        negative = {**original, 'enqueued': False}
        self.data['ownerSpeech'] = self.speech()
        for rows in ([positive, negative], [negative, positive]):
            self.data['queuedReplies'] = rows
            result = review(self.data)
            self.assertIn('Mixed enqueue claims', result['queueReview'])
            self.assertIn('matching new queue', result['queuedReply'])
            self.assertIn('Owner-reported', result['nativeSpeech'])
            self.assertEqual(result['modelOrigin'], 'Unknown')
        self.data['queuedReplies'] = [positive, positive]
        self.assertIn('distinct replies are not established', review(self.data)['queueReview'])
        self.data['queuedReplies'] = [negative]
        result = review(self.data)
        self.assertEqual(result['queuedReply'], 'Unknown')
        self.assertIn('do not prove no reply occurred', result['queueReview'])
        self.data['queuedReplies'] = [positive, {**negative, 'correlationId': 'other'}]
        self.assertIn('One positive report', review(self.data)['queueReview'])
