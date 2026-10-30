"""Synthetic proposal checks only: no hub or live assessment integration."""
import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from learning_assessment_draft import KINDS, VERSION, review

ROOT = Path(__file__).parent / 'fixtures/learning-assessment-draft'
NOW = datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc)


class AssessmentDraftTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads((ROOT / 'mixed.json').read_text())
        self.scope = copy.deepcopy(self.payload['scope'])
        for target in ('socket.create_connection', 'subprocess.Popen', 'sqlite3.connect'):
            guard = patch(target, side_effect=AssertionError('External access forbidden'))
            guard.start()
            self.addCleanup(guard.stop)

    def check(self, payload=None, **kwargs):
        return review(self.payload if payload is None else payload, self.scope,
                      now=kwargs.get('now', NOW), max_age_seconds=kwargs.get('max_age_seconds', 300))

    def assert_withheld(self, result):
        self.assertEqual(result['status'], 'unavailable')
        self.assertTrue(all(row['state'] == 'Unknown' and not row['evidenceIds'] for row in result['assessments']))
        self.assertEqual(result['policyAdoption'], 'Unknown')
        self.assertEqual(result['sourceAuthenticity'], 'unverified')
        self.assertNotIn('OMIT_PRIVATE', json.dumps(result))

    def test_mixed_and_partial_fixtures_never_promote_policy_or_identity(self):
        original = copy.deepcopy(self.payload)
        result = self.check()
        self.assertEqual(result['status'], 'reviewed-synthetic')
        self.assertEqual([row['state'] for row in result['assessments']], [
            'Reported support (synthetic)', 'Reported contradiction (synthetic)',
            'Unknown', 'Reported support (synthetic)', 'Unknown'])
        self.assertEqual(result['policyAdoption'], 'Unknown')
        self.assertEqual(result['sourceAuthenticity'], 'unverified')
        self.assertEqual(self.payload, original)
        partial = self.check(json.loads((ROOT / 'partial.json').read_text()))
        self.assertEqual(partial['status'], 'reviewed-synthetic')
        self.assertEqual([row['kind'] for row in partial['assessments']], list(KINDS))
        self.assertTrue(all(row['state'] == 'Unknown' for row in partial['assessments']))

    def test_exact_scope_is_required_at_envelope_and_evidence(self):
        self.assert_withheld(self.check(json.loads((ROOT / 'cross-instance-refusal.json').read_text())))
        for field in self.scope:
            for location in ('scope', 'evidence'):
                payload = copy.deepcopy(self.payload)
                scope = payload['scope'] if location == 'scope' else payload['evidence'][0]['scope']
                scope[field] = 'swtor' if field == 'gameId' else 'different-fixture'
                with self.subTest(field=field, location=location):
                    self.assert_withheld(self.check(payload))
        self.scope['nativeBotId'] = ''
        self.assert_withheld(self.check())

    def test_duplicate_dangling_and_unsupported_claims_are_withheld(self):
        variants = []
        p = copy.deepcopy(self.payload); p['assessments'].append(p['assessments'][0]); variants.append(p)
        p = copy.deepcopy(self.payload); p['assessments'][1] = copy.deepcopy(p['assessments'][0]); variants.append(p)
        p = copy.deepcopy(self.payload); p['evidence'].append(p['evidence'][0]); variants.append(p)
        p = copy.deepcopy(self.payload); p['assessments'][0]['evidenceIds'] = ['absent']; variants.append(p)
        p = copy.deepcopy(self.payload); p['assessments'][0]['evidenceIds'] *= 2; variants.append(p)
        p = copy.deepcopy(self.payload); p['assessments'][0]['evidenceIds'] = []; variants.append(p)
        p = copy.deepcopy(self.payload); p['assessments'][0]['claim'] = 'verified'; variants.append(p)
        p = copy.deepcopy(self.payload); p['assessments'][0]['claim'] = 'unknown'; variants.append(p)
        for index, payload in enumerate(variants):
            with self.subTest(index=index):
                self.assert_withheld(self.check(payload))

    def test_freshness_is_explicit_and_observation_cannot_postdate_report(self):
        for field in ('generatedAt', 'observedAt'):
            for timestamp in ('2025-12-31T23:00:00Z', '2026-01-01T00:03:00Z',
                              '2026-02-30T00:00:00Z', '2026-01-01T00:01:00', None):
                p = copy.deepcopy(self.payload)
                (p if field == 'generatedAt' else p['evidence'][0])[field] = timestamp
                self.assert_withheld(self.check(p))
        p = copy.deepcopy(self.payload); p['evidence'][0]['observedAt'] = '2026-01-01T00:01:30Z'
        self.assert_withheld(self.check(p))
        for age in (0, -1, True, float('inf'), float('nan'), 86401):
            self.assert_withheld(self.check(max_age_seconds=age))
        self.assert_withheld(self.check(now=NOW.replace(tzinfo=None)))

    def test_private_unknown_fields_and_wrong_types_are_redacted(self):
        variants = [[], {'error': 'OMIT_PRIVATE'}, 'OMIT_PRIVATE']
        for key, value in (('environment', 'production'), ('contractStatus', 'approved'),
                           ('schema', 'unknown'), ('evidence', {}), ('assessments', None),
                           ('rawBody', 'OMIT_PRIVATE')):
            p = copy.deepcopy(self.payload); p[key] = value; variants.append(p)
        for key, value in (('sourceId', 'file:///OMIT_PRIVATE'), ('receiptId', 'https://OMIT_PRIVATE'),
                           ('rawBody', 'OMIT_PRIVATE'), ('id', 'x' * 97)):
            p = copy.deepcopy(self.payload); p['evidence'][0][key] = value; variants.append(p)
        for payload in variants:
            self.assert_withheld(self.check(payload))

    def test_proposal_schema_and_fixtures_have_matching_top_level_fields(self):
        schema = json.loads((ROOT.parents[2] / 'schemas/learning-assessment-draft-v1.schema.json').read_text())
        self.assertEqual(schema['properties']['schema']['const'], VERSION)
        self.assertFalse(schema['additionalProperties'])
        self.assertEqual(set(schema['required']), set(self.payload))
        self.assertEqual(schema['$defs']['assessment']['properties']['kind']['enum'], list(KINDS))
        # This is a consistency check, not execution by a JSON Schema engine.


if __name__ == '__main__':
    unittest.main()
