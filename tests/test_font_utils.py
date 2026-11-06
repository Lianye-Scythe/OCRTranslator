from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.ui.font_utils import resolve_overlay_font_family


class OverlayFontTests(unittest.TestCase):
    def resolve_with_fonts(self, requested, families):
        app = SimpleNamespace(font=lambda: SimpleNamespace(family=lambda: "System UI"))
        with patch("app.ui.font_utils.QGuiApplication.instance", return_value=app), patch(
            "app.ui.font_utils.QFontDatabase.families", return_value=families
        ):
            return resolve_overlay_font_family(requested)

    def test_installed_user_font_wins_over_the_noto_default(self):
        families = ["System UI", "Noto Sans TC", "Microsoft JhengHei UI", "Reader Font"]
        for requested in ("Microsoft JhengHei UI", "Reader Font"):
            with self.subTest(font=requested):
                self.assertEqual(self.resolve_with_fonts(requested, families), requested)

    def test_missing_noto_uses_an_installed_windows_cjk_font(self):
        self.assertEqual(
            self.resolve_with_fonts("Noto Sans TC", ["System UI", "Microsoft JhengHei UI"]),
            "Microsoft JhengHei UI",
        )

    def test_noto_cjk_family_name_is_supported(self):
        self.assertEqual(
            self.resolve_with_fonts("Noto Sans TC", ["System UI", "Noto Sans CJK TC"]),
            "Noto Sans CJK TC",
        )

    def test_unavailable_preference_uses_the_system_font_when_no_cjk_face_exists(self):
        self.assertEqual(self.resolve_with_fonts("Missing Font", ["System UI"]), "System UI")

    def test_resolution_before_application_creation_does_not_query_qt_fonts(self):
        with patch("app.ui.font_utils.QGuiApplication.instance", return_value=None), patch(
            "app.ui.font_utils.QFontDatabase.families"
        ) as families:
            self.assertEqual(resolve_overlay_font_family("Reader Font"), "Reader Font")
        families.assert_not_called()


if __name__ == "__main__":
    unittest.main()
