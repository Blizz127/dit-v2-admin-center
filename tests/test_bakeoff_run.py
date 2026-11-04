"""Offline bake-off run import: reviewed defaults enforced, nothing inferred, off by default."""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import bakeoff_run as run

FIXTURE = Path(__file__).resolve().parent / 'fixtures/bakeoff-run'


class BakeoffRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'run'
        shutil.copytree(FIXTURE, self.root)
        self.manifest = json.loads((FIXTURE / 'manifest.json').read_text())
        self.attempts = [json.loads(l) for l in (FIXTURE / 'attempts.jsonl').read_text().splitlines()]

    def write(self, manifest=None, attempts=None):
        if manifest is not None:
            (self.root / 'manifest.json').write_text(json.dumps(manifest))
        if attempts is not None:
            (self.root / 'attempts.jsonl').write_text(''.join(json.dumps(a) + '\n' for a in attempts))
        return run.load(self.root)

    def test_off_by_default_reads_nothing(self):
        with patch('bakeoff_run.read_bytes', side_effect=AssertionError('read while off')):
            self.assertEqual(run.from_env({})[1]['status'], 'Not configured')

    def test_fixture_projects_total_latency_cost_and_single_rubric_quality(self):
        rows, coverage = run.load(FIXTURE)
        self.assertEqual((coverage['status'], coverage['records'], coverage['omitted']), ('Loaded', 4, 0))
        self.assertIn('4 retained of 4 candidate slots across 2 identifiable cases; total case set size unknown', coverage['reason'])
        self.assertIn('example-canonical-v1', coverage['reason'])
        self.assertEqual([r['latencyMs'] for r in rows], [250.0, 500.0, 300.0, 100.0])
        self.assertEqual([r['cost'] for r in rows], [0.00012, 0.00006, None, None])
        self.assertEqual([r['quality'] for r in rows], [4, 3, 5, None])
        self.assertTrue(all(r['purpose'] == 'subscription_chat' for r in rows))
        self.assertTrue(all('first-token time not available' in r['bakeoff']['latency'] for r in rows))
        self.assertIn('example-naturalness@1 by example-judge@1 on 0–5', rows[0]['source'])
        # One comparison group per candidate: scored and unscored attempts share a source.
        groups = {(r['model'], r['purpose'], r['source']) for r in rows}
        self.assertEqual(len(groups), 2)

    def test_mixed_evaluators_suppress_quality_for_the_whole_run(self):
        attempts = copy.deepcopy(self.attempts)
        attempts[1]['scores'][0]['evaluatorVersion'] = '2'
        rows, coverage = self.write(attempts=attempts)
        self.assertTrue(all(r['quality'] is None for r in rows))
        self.assertEqual(len({(r['model'], r['purpose'], r['source']) for r in rows}), 2)
        self.assertIn('mix rubrics, evaluators or scales', coverage['reason'])

    def test_shadow_live_and_bad_manifests_import_nothing(self):
        cases = [dict(environment='shadow_live'), dict(environment='live'), dict(schema='other'),
                 dict(completedAtUtc='2025-01-01T00:00:00Z'), dict(caseSet={'name': 'x', 'version': '1', 'sha256': 'abc'}),
                 dict(candidates=[]), dict(extra=1), dict(inputCanonicalization=None)]
        for change in cases:
            with self.subTest(change=change):
                rows, coverage = self.write(manifest={**self.manifest, **change})
                self.assertEqual((rows, coverage['status']), ([], 'Unavailable'))
        rows, coverage = self.write(manifest={**self.manifest, 'environment': 'shadow_live'})
        self.assertIn('owner decision', coverage['reason'])

    def test_invalid_attempts_are_omitted_never_repaired(self):
        base = self.attempts[0]
        changes = [dict(runId='other'), dict(model='undeclared'), dict(inputSha256='abc'),
                   dict(completedAtUtc='2026-01-01T11:00:00Z'), dict(completionStatus='Succeeded'),
                   dict(delivery={'status': 'delivered', 'evidence': 'x'}), dict(costNusd=-1), dict(costNusd=1.5),
                   dict(fallbackUsed='yes'), dict(unknownField=1), dict(firstTokenAtUtc='soon'),
                   dict(scores=[{**base['scores'][0], 'score': 9}]), dict(scores=[{**base['scores'][0], 'rubric': 'other'}])]
        bad = [{**copy.deepcopy(base), **change} for change in changes]
        missing = copy.deepcopy(base); del missing['purpose']
        rows, coverage = self.write(attempts=bad + [missing] + self.attempts[1:])
        self.assertEqual((len(rows), coverage['omitted']), (3, len(changes) + 1))

    def test_malformed_types_and_oversized_numbers_are_isolated(self):
        bad_manifest = {**self.manifest, 'environment': []}
        self.assertEqual(self.write(manifest=bad_manifest)[1]['status'], 'Unavailable')
        base = self.attempts[0]
        changes = [dict(completionStatus=[]), dict(structuralValidation={}),
                   dict(semanticCompliance=[]), dict(costNusd=10**400),
                   dict(scores=[{**base['scores'][0], 'evaluatorKind': []}]),
                   dict(scores=[{**base['scores'][0], 'score': 10**400}])]
        bad = [{**copy.deepcopy(base), **change} for change in changes]
        rows, coverage = self.write(manifest=self.manifest, attempts=bad + self.attempts[1:])
        self.assertEqual((coverage['status'], len(rows), coverage['omitted']), ('Loaded', 3, len(bad)))
        self.assertIn('3 retained of 4 candidate slots', coverage['reason'])

    def test_first_token_time_is_validated_but_never_shown(self):
        attempts = copy.deepcopy(self.attempts)
        attempts[0]['firstTokenAtUtc'] = '2026-01-01T12:00:00.1Z'
        rows, _ = self.write(attempts=attempts)
        self.assertEqual(rows[0]['latencyMs'], 250.0)
        self.assertNotIn('12:00:00.1', json.dumps(rows))

    def test_mismatched_input_hash_or_duplicate_drops_the_case(self):
        attempts = copy.deepcopy(self.attempts)
        attempts[1]['inputSha256'] = 'f' * 64  # case-1 candidates no longer saw the same input
        attempts.append(copy.deepcopy(attempts[2]))  # duplicate case-2/example-a
        rows, coverage = self.write(attempts=attempts)
        self.assertEqual([r['id'].split(':')[2:] for r in rows], [['case-2', 'example-b/example-b-v1/subscription_chat']])
        self.assertEqual(coverage['omitted'], 4)
        self.assertIn('1 retained of 4 candidate slots across 2 identifiable cases', coverage['reason'])

    def test_unidentifiable_or_missing_cases_do_not_imply_complete_coverage(self):
        rows, coverage = self.write(attempts=[])
        self.assertEqual(rows, [])
        self.assertIn('0 retained of 0 candidate slots across 0 identifiable cases; total case set size unknown', coverage['reason'])
        malformed = copy.deepcopy(self.attempts[0])
        malformed['completionStatus'] = []
        rows, coverage = self.write(attempts=[malformed, self.attempts[2], self.attempts[3]])
        self.assertEqual((len(rows), coverage['omitted']), (2, 1))
        self.assertIn('2 retained of 2 candidate slots across 1 identifiable case; total case set size unknown', coverage['reason'])

    def test_separator_characters_do_not_conflate_distinct_attempt_identities(self):
        manifest = copy.deepcopy(self.manifest)
        manifest['candidates'] = [
            {'provider': 'b', 'model': 'm/x', 'purpose': 'p'},
            {'provider': 'a:b', 'model': 'm', 'purpose': 'x/p'},
        ]
        first = {**copy.deepcopy(self.attempts[0]), 'caseId': 'case:a',
                 'provider': 'b', 'model': 'm/x', 'purpose': 'p'}
        second = {**copy.deepcopy(self.attempts[0]), 'caseId': 'case',
                  'provider': 'a:b', 'model': 'm', 'purpose': 'x/p'}
        rows, coverage = self.write(manifest=manifest, attempts=[first, second])
        self.assertEqual((len(rows), coverage['omitted']), (2, 0))
        self.assertEqual(len({row['id'] for row in rows}), 2)
        rows, coverage = self.write(attempts=[first, first, second])
        self.assertEqual((len(rows), coverage['omitted']), (1, 2))
        self.assertEqual(rows[0]['bakeoff']['caseId'], 'case')

    def test_multiple_rubrics_never_become_quality(self):
        manifest = {**self.manifest, 'rubrics': self.manifest['rubrics'] + [{'name': 'other', 'version': '1'}]}
        rows, _ = self.write(manifest=manifest)
        self.assertTrue(all(r['quality'] is None for r in rows))

    def test_unsafe_files_and_paths(self):
        (self.root / 'attempts.jsonl').unlink()
        os.mkfifo(self.root / 'attempts.jsonl')
        self.assertEqual(run.load(self.root)[1]['status'], 'Unavailable')
        (self.root / 'attempts.jsonl').unlink()
        (self.root / 'attempts.jsonl').symlink_to(FIXTURE / 'attempts.jsonl')
        self.assertEqual(run.load(self.root)[1]['status'], 'Unavailable')
        self.assertEqual(run.load('relative/run')[1]['status'], 'Unavailable')
        (self.root / 'manifest.json').write_bytes(b'{"schema": "a", "schema": "b"}')
        self.assertEqual(run.load(self.root)[1]['status'], 'Unavailable')

    def test_overview_switch(self):
        import server
        def overview(environ):
            with patch.dict('os.environ', environ, clear=True), \
                 patch.object(Path, 'home', return_value=Path(self.temp.name)), \
                 patch('server.LOCAL_DATA', Path(self.temp.name) / 'local'):
                return server.overview()
        off, on = overview({}), overview({run.ENV: str(FIXTURE)})
        self.assertEqual(off['bakeoffRun']['status'], 'Not configured')
        self.assertEqual(on['bakeoffRun']['records'], 4)
        self.assertEqual(len(on['modelCalls']), len(off['modelCalls']) + 4)


if __name__ == '__main__':
    unittest.main()
