from contextlib import redirect_stdout
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tools.docs_policy import check_images, check_links, classify_scope, docs_only, is_docs_path, main, needs_preview_checks


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

    def test_preview_scope_is_limited_to_exact_tool_paths_and_documentation(self):
        files = [
            {"filename": "tools/generate_social_preview.py", "status": "modified"},
            {"filename": "tests/test_social_preview.py", "status": "modified"},
            {"filename": "docs/images/social-preview.png", "status": "modified"},
        ]
        self.assertEqual(classify_scope(files, 3), "preview")
        self.assertFalse(docs_only(files, 3))
        for filename in ("app/main.py", "app/assets/icons/app-icon-256.png", "requirements.txt", "constraints.txt", "build_exe.bat", "tools/docs_policy.py", "tests/test_docs_policy.py", "tools/another_tool.py", ".github/workflows/ci.yml"):
            with self.subTest(filename=filename):
                self.assertEqual(classify_scope(files + [{"filename": filename, "status": "modified"}], 4), "full")
        self.assertEqual(classify_scope(files, 4), "full")
        self.assertEqual(classify_scope([], 0), "full")
        self.assertEqual(classify_scope([{"filename": "README.md", "status": "modified"}], 1), "docs")

    def test_preview_renames_and_unknown_status_cannot_hide_application_changes(self):
        for filename, previous in (
            ("tools/generate_social_preview.py", "app/main.py"),
            ("app/main.py", "tools/generate_social_preview.py"),
            ("tools/generate_social_preview.py", ""),
        ):
            with self.subTest(filename=filename, previous=previous):
                self.assertEqual(classify_scope([{"filename": filename, "previous_filename": previous, "status": "renamed"}], 1), "full")
        self.assertEqual(classify_scope([{"filename": "tools/generate_social_preview.py", "status": "unknown"}], 1), "full")

    def test_image_checks_run_for_image_changes_or_preview_tools_only(self):
        self.assertFalse(needs_preview_checks([{"filename": "README.md"}], "docs"))
        self.assertTrue(needs_preview_checks([{"filename": "docs/images/social-preview.png"}], "docs"))
        self.assertTrue(needs_preview_checks([{"filename": "docs/images/new.png", "previous_filename": "docs/images/old.png"}], "docs"))
        self.assertTrue(needs_preview_checks([{"filename": "tests/test_social_preview.py"}], "preview"))
        self.assertFalse(needs_preview_checks([{"filename": "docs/images/social-preview.png"}], "full"))

    def test_image_integrity_and_social_preview_dimensions_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "docs/images"
            images.mkdir(parents=True)
            preview = images / "social-preview.png"
            Image.new("RGB", (1280, 640)).save(preview)
            self.assertEqual(check_images(root), [])

            Image.new("RGB", (640, 1280)).save(preview)
            self.assertIn("expected 1280x640", check_images(root)[0])

            preview.write_bytes(b"not an image")
            self.assertIn("invalid image", check_images(root)[0])

    def test_cli_keeps_docs_automerge_separate_from_preview_ci(self):
        for filename, scope, docs_eligible, preview_checks in (
            ("README.md", "docs", "true", "false"),
            ("docs/images/social-preview.png", "docs", "true", "true"),
            ("tools/generate_social_preview.py", "preview", "false", "true"),
            ("app/main.py", "full", "false", "false"),
        ):
            with self.subTest(scope=scope, filename=filename), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                files = root / "files.json"
                output = root / "output.txt"
                files.write_text(json.dumps([[{"filename": filename, "status": "modified"}]]), encoding="utf-8")
                with patch("sys.argv", ["docs_policy", "--pr-files", str(files), "--expected-count", "1"]), patch.dict(os.environ, {"GITHUB_OUTPUT": str(output)}), redirect_stdout(io.StringIO()):
                    main()
                self.assertEqual(output.read_text(encoding="utf-8"), f"docs_only={docs_eligible}\nscope={scope}\npreview_checks={preview_checks}\n")

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
            'case "$CI_SCOPE" in', 'docs|preview)', 'full)', '*) exit 1',
            'test "$PACKAGE_RESULT" = success',
            'test "$PACKAGE_RESULT" = skipped',
        ):
            self.assertIn(requirement, gate)
        package = workflow.split("  windows-package:", 1)[1].split("  ci-required:", 1)[0]
        self.assertIn("if: needs.changes.outputs.scope == 'full'", package)
        self.assertIn("python -m unittest tests.test_docs_policy tests.test_social_preview -v", workflow)
        self.assertIn("python -m pip install --constraint constraints.txt Pillow", workflow)
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
