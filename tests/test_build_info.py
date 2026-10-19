import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.generate_build_info import build_info, main


class BuildInfoTests(unittest.TestCase):
    def test_inventory_records_versions_but_not_package_urls_or_environment(self):
        packages = [
            SimpleNamespace(metadata={"Name": "requests"}, version="2.34.2", direct_url="https://private.invalid/token"),
            SimpleNamespace(metadata={"Name": "Pillow"}, version="12.3.0"),
        ]
        with patch("tools.generate_build_info.metadata.distributions", return_value=packages), patch(
            "tools.generate_build_info.shutil.which", return_value=None,
        ):
            info = build_info()
        self.assertEqual(info["packages"], {"Pillow": "12.3.0", "requests": "2.34.2"})
        self.assertEqual(set(info), {"app_version", "source_commit", "python", "platform", "packages"})
        self.assertIsNone(info["source_commit"])
        self.assertNotIn("private.invalid", json.dumps(info))

    def test_available_git_revision_is_recorded(self):
        revision = SimpleNamespace(stdout="a" * 40 + "\n", returncode=0)
        with TemporaryDirectory() as temp:
            (Path(temp) / ".git").mkdir()
            with patch("tools.generate_build_info.ROOT_DIR", Path(temp)), patch(
                "tools.generate_build_info.shutil.which", return_value="git",
            ), patch("tools.generate_build_info.subprocess.run", return_value=revision):
                self.assertEqual(build_info()["source_commit"], "a" * 40)

    def test_cli_writes_readable_json_to_new_directory(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "release" / "BUILD-INFO.json"
            with patch("sys.argv", ["generate_build_info.py", "--output", str(output)]), patch(
                "tools.generate_build_info.build_info", return_value={"app_version": "test", "packages": {}},
            ):
                main()
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"app_version": "test", "packages": {}})
