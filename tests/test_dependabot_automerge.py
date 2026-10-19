import copy
import unittest
from pathlib import Path

from tools.dependabot_automerge import eligible_patch


class DependabotAutomergeTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {
            "names": "requests",
            "ecosystem": "pip",
            "update_type": "version-update:semver-patch",
            "maintainer_changes": "false",
        }
        self.files = [{
            "filename": "requirements.txt",
            "status": "modified",
            "additions": 1,
            "deletions": 1,
            "patch": "@@ -1 +1 @@\n-requests>=2.34.2\n+requests>=2.34.3",
        }]

    def test_allowlisted_patch_and_grouped_patches_are_eligible(self):
        self.assertTrue(eligible_patch(self.metadata, self.files))
        self.metadata["names"] = "requests, Pillow"
        self.files[0]["patch"] += "\n-Pillow>=12.3.0\n+Pillow>=12.3.1"
        self.files[0]["additions"] = self.files[0]["deletions"] = 2
        self.assertTrue(eligible_patch(self.metadata, self.files))

    def test_metadata_requires_known_packages_patch_ecosystem_and_no_manual_changes(self):
        for key, value in (
            ("names", ""), ("names", "requests,PySide6"), ("names", "requests-malicious"),
            ("ecosystem", "github-actions"), ("update_type", "version-update:semver-minor"),
            ("update_type", "version-update:semver-major"), ("maintainer_changes", "true"),
            ("maintainer_changes", ""),
        ):
            with self.subTest(key=key, value=value):
                metadata = {**self.metadata, key: value}
                self.assertFalse(eligible_patch(metadata, self.files))

    def test_constraint_only_and_synchronized_patch_updates_are_eligible(self):
        constraint = {
            "filename": "constraints.txt", "status": "modified", "additions": 1, "deletions": 1,
            "patch": "@@ -1 +1 @@\n-requests==2.34.2\n+requests==2.34.3",
        }
        self.assertTrue(eligible_patch(self.metadata, [constraint]))
        self.assertTrue(eligible_patch(self.metadata, self.files + [constraint]))
        self.metadata["names"] = "requests, Pillow"
        constraint["patch"] = "@@ -1 +1 @@\n-Pillow==13.0.0\n+Pillow==13.0.1"
        self.assertTrue(eligible_patch(self.metadata, self.files + [constraint]))

    def test_constraints_reject_other_packages_options_markers_and_non_patch_updates(self):
        for old, new in (
            ("requests==2.34.2", "requests==2.35.0"),
            ("requests==2.34.2", "requests==2.34.1"),
            ("requests==2.34.2", "requests>=2.34.3"),
            ("requests==2.34.2", "requests==2.34.3; sys_platform == 'win32'"),
            ("requests==2.34.2", "requests==2.34.3 --extra-index-url https://example.com"),
            ("certifi==2026.7.22", "certifi==2026.7.23"),
        ):
            file = {"filename": "constraints.txt", "status": "modified", "additions": 1,
                    "deletions": 1, "patch": "@@ -1 +1 @@\n-" + old + "\n+" + new}
            with self.subTest(new=new):
                self.assertFalse(eligible_patch(self.metadata, [file]))

    def test_constraint_versions_must_agree_and_metadata_must_cover_the_whole_diff(self):
        file = {"filename": "constraints.txt", "status": "modified", "additions": 1,
                "deletions": 1, "patch": "@@ -1 +1 @@\n-requests==2.34.2\n+requests==2.34.4"}
        self.assertFalse(eligible_patch(self.metadata, self.files + [file]))
        self.assertFalse(eligible_patch(self.metadata, [file, file]))
        self.assertFalse(eligible_patch({**self.metadata, "names": "requests,Pillow"}, [file]))
        self.assertFalse(eligible_patch(self.metadata, [{**file, "additions": 2}]))

    def test_actual_diff_rejects_non_patch_versions_and_requirement_changes(self):
        for line in (
            "requests>=2.35.0", "requests>=3.0.0", "requests>=2.34.1", "requests>=2.34.2",
            "requests>=2.34.3rc1", "requests==2.34.3", "requests>=2.34.3 --extra-index-url https://example.com",
            "requests @ https://example.com/package.whl", "PySide6>=6.12.1",
        ):
            with self.subTest(line=line):
                files = copy.deepcopy(self.files)
                files[0]["patch"] = "@@ -1 +1 @@\n-requests>=2.34.2\n+" + line
                self.assertFalse(eligible_patch(self.metadata, files))

    def test_missing_truncated_duplicated_or_extra_file_changes_require_manual_review(self):
        cases = [[], self.files + [{"filename": "app/main.py"}]]
        for changes in (
            {"filename": "requirements-dev.txt"}, {"status": "added"}, {"patch": ""},
            {"additions": 2}, {"deletions": 0},
            {"patch": self.files[0]["patch"] + "\n+--index-url https://example.com"},
            {"patch": self.files[0]["patch"] + "\n+requests>=2.34.4"},
        ):
            cases.append([{**self.files[0], **changes}])
        for files in cases:
            with self.subTest(files=files):
                self.assertFalse(eligible_patch(self.metadata, files))

    def test_privileged_workflow_uses_trusted_base_and_verified_metadata_only(self):
        workflow = Path(".github/workflows/dependabot-automerge.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", workflow)
        self.assertIn("github.event.pull_request.user.login == 'dependabot[bot]'", workflow)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", workflow)
        self.assertIn("ref: ${{ github.event.pull_request.base.sha }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("dependabot/fetch-metadata@25dd0e34f4fe68f24cc83900b1fe3fe149efef98", workflow)
        self.assertIn("--auto --squash --match-head-commit", workflow)
        self.assertLess(workflow.index("--disable-auto"), workflow.index("uses: dependabot/fetch-metadata@"))
        self.assertNotIn("skip-verification:", workflow)
        self.assertNotIn("--admin", workflow)
        self.assertNotIn("pip install", workflow)
        self.assertNotIn("gh pr review", workflow)
