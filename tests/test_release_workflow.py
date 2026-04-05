import unittest
from pathlib import Path


class ReleaseWorkflowTests(unittest.TestCase):
    def test_release_build_workflow_only_publishes_zip_asset(self):
        workflow = Path('.github/workflows/release-build.yml').read_text(encoding='utf-8')
        self.assertIn('release\\OCRTranslator-v*-windows-x64.zip', workflow)
        self.assertIn('files: ${{ steps.release_archive.outputs.path }}', workflow)
        self.assertNotIn('files: |\n            release/OCRTranslator.exe', workflow)

    def test_signpath_artifact_configuration_targets_executable_inside_zip_artifact(self):
        config = Path('.signpath/artifact-configurations/default.xml').read_text(encoding='utf-8')
        self.assertIn('<zip-file>', config)
        self.assertIn('<pe-file path="OCRTranslator.exe">', config)
        self.assertIn('<authenticode-sign />', config)


if __name__ == '__main__':
    unittest.main()
