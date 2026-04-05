import unittest
from pathlib import Path


class ReleaseWorkflowTests(unittest.TestCase):
    def test_release_build_workflow_only_publishes_zip_asset(self):
        workflow = Path('.github/workflows/release-build.yml').read_text(encoding='utf-8')
        self.assertIn('release\\OCRTranslator-v*-windows-x64.zip', workflow)
        self.assertIn('FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"', workflow)
        self.assertIn('group: release-${{ github.workflow }}-${{ github.ref }}', workflow)
        self.assertIn('uses: actions/checkout@v6', workflow)
        self.assertIn('uses: actions/setup-python@v6', workflow)
        self.assertIn('cache: "pip"', workflow)
        self.assertIn('id: signpath_gate', workflow)
        self.assertIn("if: ${{ steps.signpath_gate.outputs.enabled == 'true' }}", workflow)
        self.assertIn('files: ${{ steps.release_archive.outputs.path }}', workflow)
        self.assertIn("'release\\LICENSE'", workflow)
        self.assertIn('id: release_notes', workflow)
        self.assertIn("git tag -l --format='%(contents)' $tagName", workflow)
        self.assertIn('body_path: ${{ steps.release_notes.outputs.path }}', workflow)
        self.assertNotIn('files: |\n            release/OCRTranslator.exe', workflow)
        self.assertNotIn("if: ${{ secrets.SIGNPATH_API_TOKEN != ''", workflow)
        self.assertNotIn('generate_release_notes: true', workflow)

    def test_build_script_copies_license_into_release_archive(self):
        script = Path('build_exe.bat').read_text(encoding='utf-8')
        self.assertIn('copy /y "LICENSE" "%RELEASE_DIR%\\LICENSE" >nul', script)
        self.assertIn("'%RELEASE_DIR%\\LICENSE'", script)

    def test_signpath_artifact_configuration_targets_executable_inside_zip_artifact(self):
        config = Path('packaging/signpath/artifact-configurations/default.xml').read_text(encoding='utf-8')
        self.assertIn('<zip-file>', config)
        self.assertIn('<pe-file path="OCRTranslator.exe">', config)
        self.assertIn('<authenticode-sign />', config)

    def test_ci_workflow_uses_node24_compatible_actions(self):
        workflow = Path('.github/workflows/ci.yml').read_text(encoding='utf-8')
        self.assertIn('FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"', workflow)
        self.assertIn('workflow_dispatch:', workflow)
        self.assertIn('group: ci-${{ github.workflow }}-${{ github.ref }}', workflow)
        self.assertIn('uses: actions/checkout@v6', workflow)
        self.assertIn('uses: actions/setup-python@v6', workflow)
        self.assertIn('cache: "pip"', workflow)


if __name__ == '__main__':
    unittest.main()
