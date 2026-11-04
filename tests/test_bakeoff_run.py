"""Offline bake-off run import: reviewed defaults enforced, nothing inferred, off by default."""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from types import SimpleNamespace
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
        self.assertIn('example-naturalness@1 by example-judge@1 (rule) on 0–5', rows[0]['source'])
        # One comparison group per candidate: scored and unscored attempts share a source.
        groups = {(r['model'], r['purpose'], r['source']) for r in rows}
        self.assertEqual(len(groups), 2)

    def test_mixed_evaluators_suppress_quality_for_the_whole_run(self):
        attempts = copy.deepcopy(self.attempts)
        attempts[1]['scores'][0]['evaluatorVersion'] = '2'
        rows, coverage = self.write(attempts=attempts)
        self.assertTrue(all(r['quality'] is None for r in rows))
        self.assertEqual(len({(r['model'], r['purpose'], r['source']) for r in rows}), 2)
        self.assertIn('scores withheld: evaluator mismatch', coverage['reason'])

    def test_different_evaluator_kinds_or_separator_collisions_never_mix_quality(self):
        for changes in (
            ({'evaluatorKind': 'rule'}, {'evaluatorKind': 'model'}),
            ({'evaluator': 'judge@v', 'evaluatorVersion': '1'},
             {'evaluator': 'judge', 'evaluatorVersion': 'v@1'}),
        ):
            with self.subTest(changes=changes):
                attempts = copy.deepcopy(self.attempts)
                for attempt, change in zip(attempts[:2], changes):
                    attempt['scores'][0].update(change)
                attempts[2]['scores'][0].update(changes[0])
                rows, coverage = self.write(attempts=attempts)
                self.assertTrue(all(row['quality'] is None for row in rows))
                self.assertIn('scores withheld: evaluator mismatch', coverage['reason'])

    def test_withholding_reasons_distinguish_other_cases(self):
        attempts = copy.deepcopy(self.attempts)
        attempts[1]['scores'][0]['scaleMax'] = 10
        _, coverage = self.write(attempts=attempts)
        self.assertIn('scores withheld: score scale mismatch', coverage['reason'])
        attempts[1]['scores'][0]['evaluatorKind'] = 'model'
        _, coverage = self.write(attempts=attempts)
        self.assertIn('scores withheld: evaluator mismatch; score scale mismatch', coverage['reason'])
        for attempt in attempts:
            attempt['scores'] = []
        _, coverage = self.write(attempts=attempts)
        self.assertIn('no quality shown: no attempt was scored', coverage['reason'])

    def test_multiple_scores_are_withheld_and_explained(self):
        attempts = copy.deepcopy(self.attempts)
        attempts[0]['scores'].append(copy.deepcopy(attempts[0]['scores'][0]))
        rows, coverage = self.write(attempts=attempts)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row['quality'] is None for row in rows))
        self.assertIn('scores withheld: multiple scores per attempt', coverage['reason'])

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
        self.assertEqual((coverage['omittedDuplicate'], coverage['omittedHashMismatch']), (2, 2))
        self.assertIn('1 retained of 4 candidate slots across 2 identifiable cases', coverage['reason'])

    def test_overlapping_omission_causes_are_counted_once_and_recover(self):
        attempts = copy.deepcopy(self.attempts)
        attempts[1]['inputSha256'] = 'f' * 64
        duplicate = copy.deepcopy(attempts[0])
        invalid = {**copy.deepcopy(attempts[2]), 'completionStatus': 'invalid'}
        rows, coverage = self.write(attempts=attempts + [duplicate, invalid])
        self.assertEqual([r['bakeoff']['caseId'] for r in rows], ['case-2', 'case-2'])
        self.assertEqual((coverage['records'], coverage['omitted'], coverage['omittedDuplicate'],
                          coverage['omittedHashMismatch']), (2, 4, 2, 1))
        self.assertIn('2 retained of 4 candidate slots across 2 identifiable cases', coverage['reason'])
        rows, coverage = self.write(attempts=self.attempts)
        self.assertEqual((len(rows), coverage['omitted'], coverage['omittedDuplicate'],
                          coverage['omittedHashMismatch']), (4, 0, 0, 0))
        self.assertEqual([row['quality'] for row in rows], [4, 3, 5, None])

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
        rows, coverage = self.write(manifest=manifest)
        self.assertTrue(all(r['quality'] is None for r in rows))
        self.assertIn('scores withheld: run does not declare exactly one rubric', coverage['reason'])

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

    def test_atomic_attempts_replacement_during_open_read(self):
        path = self.root / 'attempts.jsonl'
        replacement = self.root / 'attempts.next'
        updated = copy.deepcopy(self.attempts)
        updated[0]['costNusd'] = 340000
        replacement.write_text(''.join(json.dumps(a) + '\n' for a in updated))
        old_stat = path.stat()
        opened, replaced = threading.Event(), threading.Event()
        errors = []
        original_fstat = os.fstat

        def after_open(fd):
            result = original_fstat(fd)
            if (result.st_dev, result.st_ino) == (old_stat.st_dev, old_stat.st_ino):
                opened.set()
                if not replaced.wait(3):
                    raise OSError('fixture writer did not finish')
            return result

        def writer():
            try:
                if not opened.wait(3):
                    raise RuntimeError('fixture reader did not open attempts')
                os.replace(replacement, path)
            except Exception as error:
                errors.append(error)
            finally:
                replaced.set()

        thread = threading.Thread(target=writer)
        thread.start()
        try:
            with patch('local_evidence.os.fstat', side_effect=after_open):
                old_rows, old_coverage = run.load(self.root)
        finally:
            thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual((old_coverage['status'], old_coverage['omitted'], len(old_rows)), ('Loaded', 0, 4))
        self.assertEqual(old_rows[0]['cost'], 0.00012)
        new_rows, new_coverage = run.load(self.root)
        self.assertEqual((new_coverage['status'], new_coverage['omitted'], len(new_rows)), ('Loaded', 0, 4))
        self.assertEqual(new_rows[0]['cost'], 0.00034)

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

    def test_duplicate_counts_reach_authenticated_overview_api(self):
        import server
        from test_offline_inspector_handler import MemoryConnection
        self.write(attempts=self.attempts + [self.attempts[0]])
        wire = (b'GET /api/overview HTTP/1.1\r\nHost: fixture.invalid\r\n'
                b'Authorization: Bearer fixture-token\r\nConnection: close\r\n\r\n')
        connection = MemoryConnection(wire)
        with patch.dict('os.environ', {run.ENV: str(self.root)}, clear=True), \
             patch.object(Path, 'home', return_value=Path(self.temp.name)), \
             patch('server.LOCAL_DATA', Path(self.temp.name) / 'local'):
            server.Handler(connection, ('127.0.0.1', 0), SimpleNamespace(admin_token='fixture-token'))
        head, body = bytes(connection.outgoing).split(b'\r\n\r\n', 1)
        self.assertEqual(int(head.split()[1]), 200)
        data = json.loads(body)
        self.assertEqual((data['bakeoffRun']['records'], data['bakeoffRun']['omitted'],
                          data['bakeoffRun']['omittedDuplicate'], data['bakeoffRun']['omittedHashMismatch']),
                         (3, 2, 2, 0))
        self.assertEqual(sum(row.get('id', '').startswith('bakeoff:') for row in data['modelCalls']), 3)

    def test_evaluator_mismatch_reason_reaches_authenticated_overview_api(self):
        import server
        from test_offline_inspector_handler import MemoryConnection
        attempts = copy.deepcopy(self.attempts)
        attempts[1]['scores'][0]['evaluatorKind'] = 'model'
        self.write(attempts=attempts)
        connection = MemoryConnection(b'GET /api/overview HTTP/1.1\r\nHost: fixture.invalid\r\n'
                                      b'Authorization: Bearer fixture-token\r\nConnection: close\r\n\r\n')
        with patch.dict('os.environ', {run.ENV: str(self.root)}, clear=True), \
             patch.object(Path, 'home', return_value=Path(self.temp.name)), \
             patch('server.LOCAL_DATA', Path(self.temp.name) / 'local'):
            server.Handler(connection, ('127.0.0.1', 0), SimpleNamespace(admin_token='fixture-token'))
        head, body = bytes(connection.outgoing).split(b'\r\n\r\n', 1)
        self.assertEqual(int(head.split()[1]), 200)
        data = json.loads(body)
        self.assertIn('scores withheld: evaluator mismatch', data['bakeoffRun']['reason'])
        rows = [row for row in data['modelCalls'] if row.get('id', '').startswith('bakeoff:')]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row['quality'] is None for row in rows))

    def test_overview_api_import_unavailable_and_recovery_do_not_leak_old_rows(self):
        import server
        from test_offline_inspector_handler import MemoryConnection
        wire = (b'GET /api/overview HTTP/1.1\r\nHost: fixture.invalid\r\n'
                b'Authorization: Bearer fixture-token\r\nConnection: close\r\n\r\n')

        def request():
            connection = MemoryConnection(wire)
            server.Handler(connection, ('127.0.0.1', 0), SimpleNamespace(admin_token='fixture-token'))
            head, body = bytes(connection.outgoing).split(b'\r\n\r\n', 1)
            self.assertEqual(int(head.split()[1]), 200)
            self.assertNotIn(b'PRIVATE_FIXTURE_MARKER', body)
            return json.loads(body)

        def bakeoff_rows(data):
            return [row for row in data['modelCalls'] if row.get('id', '').startswith('bakeoff:')]

        with patch.dict('os.environ', {run.ENV: str(self.root)}, clear=True), \
             patch.object(Path, 'home', return_value=Path(self.temp.name)), \
             patch('server.LOCAL_DATA', Path(self.temp.name) / 'local'), \
             patch('server.HubReader', side_effect=AssertionError('live hub access forbidden')):
            loaded = request()
            self.assertEqual((loaded['bakeoffRun']['status'], len(bakeoff_rows(loaded))), ('Loaded', 4))
            (self.root / 'manifest.json').write_text('{"PRIVATE_FIXTURE_MARKER":')
            unavailable = request()
            self.assertEqual((unavailable['bakeoffRun']['status'], unavailable['bakeoffRun']['omitted']),
                             ('Unavailable', None))
            self.assertEqual(bakeoff_rows(unavailable), [])
            (self.root / 'manifest.json').write_text(json.dumps(self.manifest))
            recovered = request()
            self.assertEqual((recovered['bakeoffRun']['status'], recovered['bakeoffRun']['omitted'],
                              len(bakeoff_rows(recovered))), ('Loaded', 0, 4))

    def test_overview_api_partial_attempt_line_is_omitted_then_recovers(self):
        import server
        from test_offline_inspector_handler import MemoryConnection
        wire = (b'GET /api/overview HTTP/1.1\r\nHost: fixture.invalid\r\n'
                b'Authorization: Bearer fixture-token\r\nConnection: close\r\n\r\n')
        original = (self.root / 'attempts.jsonl').read_bytes()
        lines = original.splitlines()
        (self.root / 'attempts.jsonl').write_bytes(b'\n'.join(lines[:3]) + b'\n{"PRIVATE_PARTIAL_MARKER":')

        def request():
            connection = MemoryConnection(wire)
            server.Handler(connection, ('127.0.0.1', 0), SimpleNamespace(admin_token='fixture-token'))
            head, body = bytes(connection.outgoing).split(b'\r\n\r\n', 1)
            self.assertEqual(int(head.split()[1]), 200)
            self.assertNotIn(b'PRIVATE_PARTIAL_MARKER', body)
            return json.loads(body)

        with patch.dict('os.environ', {run.ENV: str(self.root)}, clear=True), \
             patch.object(Path, 'home', return_value=Path(self.temp.name)), \
             patch('server.LOCAL_DATA', Path(self.temp.name) / 'local'), \
             patch('server.HubReader', side_effect=AssertionError('live hub access forbidden')):
            partial = request()
            self.assertEqual((partial['bakeoffRun']['status'], partial['bakeoffRun']['records'],
                              partial['bakeoffRun']['omitted']), ('Loaded', 3, 1))
            self.assertIn('total case set size unknown', partial['bakeoffRun']['reason'])
            self.assertEqual(sum(row.get('id', '').startswith('bakeoff:') for row in partial['modelCalls']), 3)
            (self.root / 'attempts.jsonl').write_bytes(original)
            recovered = request()
            self.assertEqual((recovered['bakeoffRun']['records'], recovered['bakeoffRun']['omitted']), (4, 0))
            self.assertEqual(sum(row.get('id', '').startswith('bakeoff:') for row in recovered['modelCalls']), 4)


if __name__ == '__main__':
    unittest.main()
