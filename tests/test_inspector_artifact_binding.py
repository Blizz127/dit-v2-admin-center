"""Stale preview refusal for the synthetic inspector integration entry point."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InspectorArtifactBindingTests(unittest.TestCase):
    def test_stale_artifact_is_refused_before_fixture_execution(self):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Installed Node is required; no skip/download')
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / 'stale.html'
            artifact.write_text('<html><script>// obsolete fixture app</script></html>')
            environment = dict(os.environ, DIT_TEST_ARTIFACT=str(artifact), PATH=directory)
            # No Python on this PATH: source mismatch must be caught before
            # invoking the template/handler fixture subprocess.
            result = subprocess.run([node, 'tests/inspector_integration.test.js'], cwd=ROOT,
                                    env=environment, capture_output=True, text=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Artifact does not embed the current application source', result.stderr)
            self.assertNotIn('integration passed', result.stdout)
            self.assertNotIn('ENOENT', result.stderr)


if __name__ == '__main__':
    unittest.main()
