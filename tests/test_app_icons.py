import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication
from app.ui.app_icons import APP_ICON_PNG_SIZES, app_icon_ico_path, app_icon_png_path, app_icon_source_path, load_app_icon


class AppIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_icon_assets_exist(self):
        self.assertTrue(app_icon_source_path().exists())
        self.assertTrue(app_icon_ico_path().exists())
        for size in APP_ICON_PNG_SIZES:
            self.assertTrue(app_icon_png_path(size).exists(), msg=f"Missing app icon PNG for size {size}")

    def test_load_app_icon_returns_non_null_icon(self):
        icon = load_app_icon()
        self.assertFalse(icon.isNull())

    def test_spec_references_icon_assets(self):
        spec_text = Path("packaging/windows/OCRTranslator.spec").read_text(encoding="utf-8")
        self.assertIn("app/assets/icons", spec_text)
        self.assertIn("app-icon.ico", spec_text)


if __name__ == "__main__":
    unittest.main()
