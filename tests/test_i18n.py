import unittest
from unittest.mock import patch

from app.i18n import I18N, SUPPORTED_UI_LANGUAGES, detect_system_ui_language, normalize_ui_language


class I18nTests(unittest.TestCase):
    def test_all_locales_share_the_same_keys(self):
        base_keys = set(I18N[SUPPORTED_UI_LANGUAGES[0]].keys())
        for language in SUPPORTED_UI_LANGUAGES[1:]:
            self.assertEqual(set(I18N[language].keys()), base_keys)

    def test_normalize_ui_language_maps_traditional_and_simplified_markers(self):
        self.assertEqual(normalize_ui_language("zh-Hant-TW"), "zh-TW")
        self.assertEqual(normalize_ui_language("zh_TW"), "zh-TW")
        self.assertEqual(normalize_ui_language("zh-Hans-CN"), "zh-CN")
        self.assertEqual(normalize_ui_language("zh_CN"), "zh-CN")
        self.assertEqual(normalize_ui_language("fr-FR"), "en")

    def test_detect_system_ui_language_prefers_traditional_chinese(self):
        with patch("app.i18n._locale_candidates", return_value=["zh-Hant-TW", "en-US"]):
            self.assertEqual(detect_system_ui_language(), "zh-TW")

    def test_detect_system_ui_language_prefers_simplified_chinese(self):
        with patch("app.i18n._locale_candidates", return_value=["zh-Hans-CN", "en-US"]):
            self.assertEqual(detect_system_ui_language(), "zh-CN")

    def test_detect_system_ui_language_falls_back_to_english(self):
        with patch("app.i18n._locale_candidates", return_value=["ja-JP"]):
            self.assertEqual(detect_system_ui_language(), "en")


if __name__ == "__main__":
    unittest.main()
