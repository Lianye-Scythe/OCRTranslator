import tempfile
import unittest
from pathlib import Path

from app.app_metadata import APP_VERSION, WINDOWS_PRODUCT_NAME
from tools.generate_windows_version_info import build_version_resource_text, version_tuple, write_version_resource


class WindowsVersionInfoTests(unittest.TestCase):
    def test_version_tuple_pads_to_four_parts(self):
        self.assertEqual(version_tuple("0.9.1"), (0, 9, 1, 0))
        self.assertEqual(version_tuple("1"), (1, 0, 0, 0))
        self.assertEqual(version_tuple("1.2.3.4.5"), (1, 2, 3, 4))

    def test_build_version_resource_text_contains_metadata(self):
        content = build_version_resource_text()
        self.assertIn("VSVersionInfo(", content)
        self.assertIn(repr(APP_VERSION), content)
        self.assertIn(repr(WINDOWS_PRODUCT_NAME), content)
        self.assertIn("StringStruct('OriginalFilename'", content)

    def test_write_version_resource_creates_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "version-info.txt"
            written_path = write_version_resource(output_path)

            self.assertEqual(written_path, output_path)
            self.assertTrue(output_path.exists())
            self.assertIn("StringStruct('ProductVersion'", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
