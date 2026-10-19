import tempfile
import unittest
from pathlib import Path

from tools.docs_policy import check_links, docs_only, is_docs_path


class DocsPolicyTests(unittest.TestCase):
    def test_only_documentation_and_raster_preview_paths_are_allowlisted(self):
        for filename in (
            "README.md", "CHANGELOG.md", "docs/README.en.md", "docs/development.md",
            ".github/CONTRIBUTING.md", "docs/images/screenshots/preview.gif",
            "docs/images/screenshots/window.png",
        ):
            with self.subTest(filename=filename):
                self.assertTrue(is_docs_path(filename))
        for filename in (
            "", "app/main.py", "requirements.txt", "docs/example.py", "build_exe.bat",
            "packaging/windows/README.md", ".github/workflows/ci.yml", ".github/CODEOWNERS",
            "tools/docs_policy.py", "docs/images/script.svg", "docs/../app/main.md",
            "/docs/README.md", "docs\\README.md", "not-docs/README.md",
        ):
            with self.subTest(filename=filename):
                self.assertFalse(is_docs_path(filename))

    def test_empty_incomplete_and_mixed_diffs_require_full_checks(self):
        files = [{"filename": "README.md", "status": "modified"}]
        self.assertTrue(docs_only(files, 1))
        self.assertFalse(docs_only([], 0))
        self.assertFalse(docs_only(files, 2))
        self.assertFalse(docs_only(files, None))
        self.assertFalse(docs_only(files + [{"filename": "app/main.py", "status": "modified"}], 2))
        self.assertFalse(docs_only([{"filename": "README.md", "status": "unknown"}], 1))

    def test_renames_must_not_hide_non_documentation_changes(self):
        file = {"filename": "docs/old.md", "status": "renamed", "previous_filename": "docs/new.md"}
        self.assertTrue(docs_only([file], 1))
        for previous in ("app/main.py", "packaging/windows/README.md", ""):
            self.assertFalse(docs_only([{**file, "previous_filename": previous}], 1))
        self.assertTrue(docs_only([{"filename": "docs/old.md", "status": "removed"}], 1))

    def test_local_markdown_reference_and_html_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "image name.png").touch()
            (root / "README.md").write_text(
                '[image](image%20name.png)\n![image](image%20name.png)\n'
                '<img src="image%20name.png" />\n<a href="README.md#section">page</a>\n'
                '[reference]: image%20name.png\n[web](https://example.com/missing)\n'
                '[anchor](#section)\n```md\n[example](missing.md)\n```\n',
                encoding="utf-8",
            )
            self.assertEqual(check_links(root, ["README.md"]), [])
            (root / "image name.png").unlink()
            self.assertEqual(len(check_links(root, ["README.md"])), 4)

    def test_missing_links_and_repository_escape_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                '[missing](missing.md)\n<img src="missing.png" />\n[outside](../outside.md)\n',
                encoding="utf-8",
            )
            self.assertEqual(len(check_links(root, ["README.md"])), 3)
            self.assertEqual(check_links(root, ["removed.md"]), [])

    def test_ci_requires_successful_classification_and_selected_checks(self):
        workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("--base \"$BASE_SHA\" --check", workflow)
        gate = workflow.split("  ci-required:", 1)[1]
        self.assertIn("if: always()", gate)
        self.assertIn("needs: [changes, test, windows-package]", gate)
        for requirement in (
            'test "$CHANGES_RESULT" = success', 'test "$TEST_RESULT" = success',
            'test "$DOCS_ONLY" = false', 'test "$PACKAGE_RESULT" = success',
            'test "$PACKAGE_RESULT" = skipped',
        ):
            self.assertIn(requirement, gate)
        self.assertNotIn("paths-ignore:", workflow)

    def test_privileged_automerge_only_runs_base_policy_for_owner_prs(self):
        workflow = Path(".github/workflows/docs-automerge.yml").read_text(encoding="utf-8")
        for requirement in (
            "pull_request_target:", "github.event.pull_request.user.login == github.repository_owner",
            "github.event.pull_request.head.repo.full_name == github.repository",
            "ref: ${{ github.event.pull_request.base.sha }}", "persist-credentials: false",
            "--expected-count", "--auto --squash --match-head-commit", "--disable-auto",
            "!github.event.pull_request.draft",
        ):
            self.assertIn(requirement, workflow)
        self.assertLess(workflow.index("--disable-auto"), workflow.index("Checkout trusted base"))
        for forbidden in ("--admin", "pip install", "gh pr review", "ref: ${{ github.event.pull_request.head"):
            self.assertNotIn(forbidden, workflow)


if __name__ == "__main__":
    unittest.main()
