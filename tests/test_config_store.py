from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app.config_store import _migrate_legacy_config, load_config


class ConfigStoreMigrationTests(unittest.TestCase):
    def test_migrate_profiles_with_invalid_shapes_is_normalized(self):
        with patch("app.config_store.detect_system_ui_language", return_value="zh-CN"):
            config = _migrate_legacy_config(
            {
                "target_language": "",
                "mode": "sideways",
                "temperature": "9.9",
                "overlay_width": "bad",
                "overlay_height": 10000,
                "margin": -5,
                "ui_language": "jp",
                "hotkey": "",
                "overlay_font_family": "",
                "overlay_font_size": 1,
                "overlay_opacity": 5,
                "overlay_pinned": "yes",
                "active_profile_name": "missing",
                "api_profiles": {
                    "name": " Demo ",
                    "provider": "OPENAI",
                    "base_url": "   ",
                    "api_keys": "key-1\nkey-2\nkey-1",
                    "model": "models/gpt-4o-mini",
                    "available_models": "gpt-4o-mini\nmodels/gpt-4.1",
                    "retry_count": 99,
                    "retry_interval": -3,
                },
            }
            )

        self.assertEqual(config.target_language, "English")
        self.assertEqual(config.mode, "book_lr")
        self.assertEqual(config.temperature, 2.0)
        self.assertEqual(config.overlay_width, 440)
        self.assertEqual(config.overlay_height, 1600)
        self.assertEqual(config.margin, 8)
        self.assertEqual(config.ui_language, "en")
        self.assertEqual(config.hotkey, "Shift+Win+X")
        self.assertEqual(config.selection_hotkey, "Shift+Win+C")
        self.assertEqual(config.input_hotkey, "Shift+Win+Z")
        self.assertEqual(config.overlay_font_family, "Microsoft JhengHei UI")
        self.assertEqual(config.overlay_font_size, 10)
        self.assertEqual(config.overlay_opacity, 55)
        self.assertTrue(config.overlay_pinned)
        self.assertEqual(config.active_prompt_preset_name, "翻譯 (Translate)")
        self.assertEqual(len(config.prompt_presets), 3)
        self.assertEqual(config.prompt_presets[0].name, "翻譯 (Translate)")
        self.assertEqual(config.prompt_presets[0].builtin_id, "translate")
        self.assertEqual(len(config.api_profiles), 1)

        profile = config.api_profiles[0]
        self.assertEqual(profile.name, "Demo")
        self.assertEqual(profile.provider, "openai")
        self.assertEqual(profile.base_url, "https://api.openai.com")
        self.assertEqual(profile.api_keys, ["key-1", "key-2"])
        self.assertEqual(profile.available_models, ["gpt-4o-mini", "gpt-4.1"])
        self.assertEqual(profile.model, "gpt-4o-mini")
        self.assertEqual(profile.retry_count, 10)
        self.assertEqual(profile.retry_interval, 0.0)
        self.assertEqual(config.active_profile_name, "Demo")

    def test_migrate_legacy_single_profile_shape(self):
        with patch("app.config_store.detect_system_ui_language", return_value="zh-CN"):
            config = _migrate_legacy_config(
                {
                "target_language": "English",
                "mode": "web_ud",
                "api_key": "legacy-key",
                "base_url": "https://generativelanguage.googleapis.com",
                "model": "gemini-1.5-flash",
                }
            )

        self.assertEqual(config.target_language, "English")
        self.assertEqual(config.mode, "web_ud")
        self.assertEqual(config.ui_language, "zh-CN")
        self.assertEqual(config.active_profile_name, "Default Gemini")
        self.assertEqual(config.overlay_opacity, 96)
        self.assertFalse(config.overlay_pinned)
        self.assertEqual(config.selection_hotkey, "Shift+Win+C")
        self.assertEqual(config.input_hotkey, "Shift+Win+Z")
        self.assertEqual(len(config.api_profiles), 1)
        self.assertEqual(len(config.prompt_presets), 3)

        profile = config.api_profiles[0]
        self.assertEqual(profile.provider, "gemini")
        self.assertEqual(profile.api_keys, ["legacy-key"])
        self.assertEqual(profile.model, "models/gemini-1.5-flash")
        self.assertEqual(profile.available_models, ["models/gemini-1.5-flash"])
        self.assertEqual(config.active_prompt_preset_name, "翻譯 (Translate)")

    def test_migrate_string_false_overlay_flag_as_false(self):
        config = _migrate_legacy_config(
            {
                "overlay_pinned": "false",
                "api_profiles": [
                    {
                        "name": "Default Gemini",
                        "provider": "gemini",
                        "api_keys": ["demo-key"],
                    }
                ],
            }
        )

        self.assertFalse(config.overlay_pinned)

    def test_migrate_close_to_tray_on_close_flag(self):
        config = _migrate_legacy_config(
            {
                "close_to_tray_on_close": "true",
                "api_profiles": [
                    {
                        "name": "Default Gemini",
                        "provider": "gemini",
                        "api_keys": ["demo-key"],
                    }
                ],
            }
        )

        self.assertTrue(config.close_to_tray_on_close)

    def test_load_config_reads_existing_portable_config_from_root(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                '{"target_language":"English","mode":"web_ud","api_key":"legacy-key"}',
                encoding="utf-8",
            )

            with patch("app.config_store.CONFIG_PATH", config_path), patch("app.config_store.detect_system_ui_language", return_value="zh-CN"):
                config = load_config()

            self.assertEqual(config.target_language, "English")
            self.assertEqual(config.ui_language, "zh-CN")
            self.assertTrue(config_path.exists())
            self.assertIn("legacy-key", config_path.read_text(encoding="utf-8"))

    def test_load_config_recreates_portable_config_when_root_config_is_broken(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text("{broken json", encoding="utf-8")

            with patch("app.config_store.CONFIG_PATH", config_path), patch("app.config_store.show_startup_warning") as mock_warning, patch("app.config_store.detect_system_ui_language", return_value="en"):
                config = load_config()

            self.assertEqual(config.target_language, "English")
            self.assertEqual(config.ui_language, "en")
            self.assertTrue(config_path.exists())
            self.assertTrue(any(config_path.parent.glob("config.broken-*.json")))
            mock_warning.assert_called_once()

    def test_load_config_uses_target_language_matching_system_language_on_first_start(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            with patch("app.config_store.CONFIG_PATH", config_path), patch("app.config_store.detect_system_ui_language", return_value="zh-CN"):
                config = load_config()

            self.assertEqual(config.ui_language, "zh-CN")
            self.assertEqual(config.target_language, "简体中文")
            saved = config_path.read_text(encoding="utf-8")
            self.assertIn('"ui_language": "zh-CN"', saved)
            self.assertIn('"target_language": "简体中文"', saved)

    def test_migrate_missing_target_language_follows_resolved_ui_language(self):
        with patch("app.config_store.detect_system_ui_language", return_value="zh-CN"):
            config = _migrate_legacy_config(
                {
                    "ui_language": "zh-TW",
                    "api_profiles": [{"name": "Default Gemini", "provider": "gemini", "api_keys": ["demo-key"]}],
                }
            )

        self.assertEqual(config.ui_language, "zh-TW")
        self.assertEqual(config.target_language, "繁體中文")

    def test_migrate_legacy_prompt_preset_names_to_bilingual_defaults(self):
        config = _migrate_legacy_config(
            {
                "active_prompt_preset_name": "解答",
                "prompt_presets": [
                    {"name": "翻譯", "builtin_id": "translate", "image_prompt": "img-1", "text_prompt": "txt-1"},
                    {"name": "解答", "builtin_id": "answer", "image_prompt": "img-2", "text_prompt": "txt-2"},
                    {"name": "潤色", "builtin_id": "polish", "image_prompt": "img-3", "text_prompt": "txt-3"},
                ],
                "api_profiles": [{"name": "Default Gemini", "provider": "gemini", "api_keys": ["demo-key"]}],
            }
        )

        self.assertEqual(config.active_prompt_preset_name, "解答 (Answer)")
        self.assertEqual([preset.name for preset in config.prompt_presets], ["翻譯 (Translate)", "解答 (Answer)", "潤色 (Polish)"])
        self.assertEqual([preset.builtin_id for preset in config.prompt_presets], ["translate", "answer", "polish"])


if __name__ == "__main__":
    unittest.main()
