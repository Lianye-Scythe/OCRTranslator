from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.ui.font_utils import resolve_overlay_font_family


class OverlayFontTests(unittest.TestCase):
    def resolve_with_fonts(self, requested, families, target_language=None):
        app = SimpleNamespace(font=lambda: SimpleNamespace(family=lambda: "System UI"))
        with patch("app.ui.font_utils.QGuiApplication.instance", return_value=app), patch(
            "app.ui.font_utils.QFontDatabase.families", return_value=families
        ):
            return resolve_overlay_font_family(requested, target_language=target_language)

    def test_missing_regional_noto_uses_matching_windows_face(self):
        available = ["Noto Sans TC", "Microsoft JhengHei UI", "Microsoft YaHei UI", "Yu Gothic UI", "Segoe UI"]
        for requested, expected in (("Noto Sans SC", "Microsoft YaHei UI"), ("Noto Sans JP", "Yu Gothic UI"), ("Noto Sans", "Segoe UI")):
            self.assertEqual(self.resolve_with_fonts(requested, available), expected)

    def test_empty_or_missing_custom_font_uses_target_language(self):
        available = ["Noto Sans TC", "Noto Sans SC", "Noto Sans JP", "Noto Sans", "System UI"]
        for target, expected in (("English", "Noto Sans"), ("简体中文", "Noto Sans SC"), ("日本語", "Noto Sans JP")):
            for requested in (None, "Reader Font Missing"):
                self.assertEqual(self.resolve_with_fonts(requested, available, target), expected)

    def test_cjk_regional_alias_does_not_fall_back_to_tc(self):
        available = ["Noto Sans TC", "Noto Sans CJK SC", "Noto Sans CJK JP"]
        self.assertEqual(self.resolve_with_fonts("Noto Sans SC", available), "Noto Sans CJK SC")
        self.assertEqual(self.resolve_with_fonts("Noto Sans JP", available), "Noto Sans CJK JP")

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
