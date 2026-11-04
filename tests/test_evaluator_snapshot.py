"""Offline evaluator snapshot import: off by default, strict shape, no inferred fields."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import evaluator_snapshot as snap

FIXTURE = Path(__file__).resolve().parent / 'fixtures/evaluator-snapshot.json'


class EvaluatorSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.records = json.loads(FIXTURE.read_text())

    def write(self, data, raw=None):
        path = Path(self.temp.name) / 'snapshot.json'
        path.write_bytes(raw if raw is not None else json.dumps(data).encode())
        return path

    def test_unset_switch_reads_nothing(self):
        with patch('evaluator_snapshot.read_bytes', side_effect=AssertionError('read while off')):
            rows, coverage = snap.from_env({})
        self.assertEqual(rows, [])
        self.assertEqual(coverage['status'], 'Not configured')

    def test_fixture_projects_without_inventing_fields(self):
        rows, coverage = snap.from_env({snap.ENV: str(FIXTURE)})
        self.assertEqual((coverage['status'], coverage['records'], coverage['omitted']), ('Loaded', 3, 0))
        self.assertEqual([r['model'] for r in rows],
                         ['deterministic / fixed-template', 'example-a / example-a-v1', 'example-b / example-b-v1'])
        self.assertEqual([r['latencyMs'] for r in rows], [0.0, 250.0, 100.0])
        self.assertEqual([r['cost'] for r in rows], [None, 0.00012, None])
        for row in rows:
            self.assertIsNone(row['purpose'])
            self.assertIsNone(row['quality'], 'Scores without a rubric must not become quality')
            self.assertIsNone(row['observedAt'])
            self.assertIn('not live hub data', row['source'])
            for key in ('fallbackEligible', 'delivery', 'attribution', 'runId', 'scoreRubric'):
                self.assertTrue(row['evaluator'][key].startswith('Unknown'))
        self.assertEqual(rows[1]['evaluator']['scores'], [{'evaluator': 'example-judge', 'score': 0.75}])
        self.assertEqual((rows[1]['evaluator']['inputTokens'], rows[1]['evaluator']['outputTokens']), (24, 8))
        self.assertEqual(rows[2]['evaluator']['completionStatus'], 'TimedOut')

    def test_relayed_or_drifted_field_names_are_omitted(self):
        renamed = copy.deepcopy(self.records[0])
        renamed['ProviderName'] = renamed.pop('Provider')
        extra = dict(copy.deepcopy(self.records[1]), FallbackEligible=True)
        rows, coverage = snap.load(self.write([renamed, extra, self.records[2]]))
        self.assertEqual((len(rows), coverage['omitted']), (1, 2))

    def test_malformed_values_are_omitted_not_repaired(self):
        cases = [('Latency', '-00:00:01'), ('Latency', '00:61:00'), ('Latency', 250), ('CompletionStatus', 'Done'),
                 ('SemanticCompliance', 'Maybe'), ('EstimatedCost', -1), ('EstimatedCost', True),
                 ('TokenUsage', {'InputTokens': -1}), ('EvaluatorScores', [{'Evaluator': 'x'}]),
                 ('Provider', 'has space'), ('StructuralValidation', {'Status': 'Fine'})]
        bad = []
        for field, value in cases:
            record = copy.deepcopy(self.records[1])
            record[field] = value
            bad.append(record)
        rows, coverage = snap.load(self.write(bad + [self.records[0]]))
        self.assertEqual((len(rows), coverage['omitted']), (1, len(cases)))

    def test_duplicates_and_unreadable_files_import_nothing_unsafe(self):
        rows, coverage = snap.load(self.write([self.records[1], self.records[1]]))
        self.assertEqual((len(rows), coverage['omitted']), (1, 1))
        for raw in (b'{"a": 1}', b'[NaN]', b'[{"RequestId": "a", "RequestId": "b"}]', b'\xff', b'[' + b' ' * snap.LIMIT + b']'):
            rows, coverage = snap.load(self.write(None, raw))
            self.assertEqual((rows, coverage['status']), ([], 'Unavailable'))
            self.assertNotIn('RequestId', coverage['reason'])
        fifo = Path(self.temp.name) / 'fifo.json'
        os.mkfifo(fifo)
        self.assertEqual(snap.load(fifo)[1]['status'], 'Unavailable')
        link = Path(self.temp.name) / 'link.json'
        link.symlink_to(FIXTURE)
        self.assertEqual(snap.load(link)[1]['status'], 'Unavailable')
        self.assertEqual(snap.load(Path(self.temp.name) / 'missing.json')[1]['status'], 'Unavailable')

    def test_malformed_json_types_and_large_numbers_do_not_hide_valid_rows(self):
        bad = []
        for field, value in (('CompletionStatus', []), ('SemanticCompliance', {}),
                             ('StructuralValidation', {'Status': []}),
                             ('EstimatedCost', 10**400),
                             ('EvaluatorScores', [{'Evaluator': 'judge', 'Score': 10**400}])):
            record = copy.deepcopy(self.records[1])
            record[field] = value
            bad.append(record)
        rows, coverage = snap.load(self.write(bad + [self.records[0]]))
        self.assertEqual((coverage['status'], coverage['records'], coverage['omitted']), ('Loaded', 1, len(bad)))
        self.assertEqual(rows[0]['model'], 'deterministic / fixed-template')

    def test_overview_appends_rows_only_when_switched_on(self):
        import server
        with patch.dict('os.environ', {}, clear=True), \
             patch.object(Path, 'home', return_value=Path(self.temp.name)), \
             patch('server.LOCAL_DATA', Path(self.temp.name) / 'local'):
            off = server.overview()
        self.assertEqual(off['evaluatorSnapshot']['status'], 'Not configured')
        self.assertFalse(any(r.get('id', '').startswith('snapshot:') for r in off['modelCalls']))
        with patch.dict('os.environ', {snap.ENV: str(FIXTURE)}, clear=True), \
             patch.object(Path, 'home', return_value=Path(self.temp.name)), \
             patch('server.LOCAL_DATA', Path(self.temp.name) / 'local'):
            on = server.overview()
        self.assertEqual(on['evaluatorSnapshot']['records'], 3)
        self.assertEqual(len(on['modelCalls']), len(off['modelCalls']) + 3)
        malformed = copy.deepcopy(self.records[1])
        malformed['CompletionStatus'] = []
        path = self.write([malformed, self.records[0]])
        with patch.dict('os.environ', {snap.ENV: str(path)}, clear=True), \
             patch.object(Path, 'home', return_value=Path(self.temp.name)), \
             patch('server.LOCAL_DATA', Path(self.temp.name) / 'local'):
            partial = server.overview()
        self.assertEqual((partial['evaluatorSnapshot']['records'], partial['evaluatorSnapshot']['omitted']), (1, 1))
        self.assertEqual(len(partial['modelCalls']), len(off['modelCalls']) + 1)


if __name__ == '__main__':
    unittest.main()
