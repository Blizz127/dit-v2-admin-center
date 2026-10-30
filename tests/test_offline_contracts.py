"""Discovery hook for real schema validation; missing engine fails explicitly."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class OfflineContractChecks(unittest.TestCase):
    def run_check(self, root):
        # Honor an explicit interpreter without fallback. Otherwise prefer this
        # Python's engine, then the pre-existing system Python on this devbox.
        runtime = os.environ.get('DIT_SCHEMA_PYTHON')
        if runtime is None:
            runtime = sys.executable if importlib.util.find_spec('jsonschema') else '/usr/bin/python3'
        command = [runtime, '-c',
                   'import sys; from pathlib import Path; from tools.check_offline_contracts import main; '
                   'raise SystemExit(main(Path(sys.argv[1])))', str(root)]
        try:
            return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            self.fail('Schema runtime unavailable/timed out; set DIT_SCHEMA_PYTHON to an installed validator Python')

    def copy_inputs(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / 'schemas', root / 'schemas')
        shutil.copytree(ROOT / 'tests/fixtures/learning-assessment-draft', root / 'tests/fixtures/learning-assessment-draft')
        return root

    def test_all_registered_contracts_and_fixtures_with_real_engine(self):
        result = self.run_check(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['engine'], 'jsonschema')
        self.assertGreater(report['fixtures'], 0)

    def test_new_or_missing_fixture_cannot_escape_inventory(self):
        root = self.copy_inputs()
        fixtures = root / 'tests/fixtures/learning-assessment-draft'
        extra = fixtures / 'not-registered.json'
        extra.write_text('{}')
        self.assertEqual(self.run_check(root).returncode, 1)
        extra.unlink()
        (fixtures / 'partial.json').unlink()
        self.assertEqual(self.run_check(root).returncode, 1)

    def test_new_schema_requires_registered_checker(self):
        root = self.copy_inputs()
        (root / 'schemas/unregistered.schema.json').write_text('{}')
        result = self.run_check(root)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['reason'], 'Offline schema/checker inventory mismatch')

    def test_invalid_fixture_and_wrong_semantic_expectation_fail(self):
        root = self.copy_inputs()
        path = root / 'tests/fixtures/learning-assessment-draft/partial.json'
        original = path.read_text()
        payload = json.loads(original); payload['privateText'] = 'OMIT_PRIVATE'
        path.write_text(json.dumps(payload))
        result = self.run_check(root)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('OMIT_PRIVATE', result.stdout + result.stderr)
        path.write_text(original)
        manifest = root / 'schemas/learning-assessment-draft-v1.cases.json'
        cases = json.loads(manifest.read_text())
        cases['cross-instance-refusal.json']['reviewStatus'] = 'reviewed-synthetic'
        manifest.write_text(json.dumps(cases))
        self.assertEqual(self.run_check(root).returncode, 1)

    def test_missing_engine_and_invalid_override_are_explicit_failures(self):
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        # -S excludes installed site packages. This actually exercises the
        # tool's missing-engine branch rather than fabricating its stdout.
        result = subprocess.run([sys.executable, '-S', str(ROOT / 'tools/check_offline_contracts.py')],
                                cwd=ROOT, env=environment, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout),
                         {'status': 'blocked', 'reason': 'JSON Schema engine unavailable'})
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'DIT_SCHEMA_PYTHON': str(Path(directory) / 'missing-python')}):
                with self.assertRaisesRegex(AssertionError, 'Schema runtime unavailable'):
                    self.run_check(ROOT)


if __name__ == '__main__':
    unittest.main()
