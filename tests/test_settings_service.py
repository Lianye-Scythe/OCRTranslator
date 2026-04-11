import sys
import types
import unittest

if "pynput" not in sys.modules:
    pynput_stub = types.ModuleType("pynput")
    pynput_stub.keyboard = types.SimpleNamespace(Listener=object)
    sys.modules["pynput"] = pynput_stub

from app.models import ApiProfile, AppConfig, PromptPreset
from app.settings_models import SettingsFormSnapshot
from app.settings_service import build_candidate_config, validate_settings_snapshot


class SettingsServiceTests(unittest.TestCase):
    def _snapshot(self, **overrides):
        data = {
            "profile_name": "Demo",
            "provider": "openai",
            "base_url": "https://api.openai.com",
            "model_text": "gpt-4o-mini",
            "model_items": ["gpt-4o-mini"],
            "api_keys_text": "key-1\nkey-2",
            "retry_count": 1,
            "retry_interval": 2.0,
            "target_language": "English",
            "ui_language": "en",
            "theme_mode": "dark",
            "hotkey": "Ctrl+Shift+X",
            "selection_hotkey": "Ctrl+Shift+C",
            "input_hotkey": "Ctrl+Shift+Z",
            "overlay_font_family": "Segoe UI",
            "overlay_font_size": 13,
            "temperature": 0.4,
            "overlay_width": 500,
            "overlay_height": 600,
            "overlay_margin": 20,
            "overlay_auto_expand_top_margin": 56,
            "overlay_auto_expand_bottom_margin": 18,
            "toast_duration_seconds": 1.5,
            "stream_responses": True,
            "check_updates_on_startup": True,
            "close_to_tray_on_close": True,
            "mode": "web_ud",
            "prompt_preset_name": "Translate",
            "image_prompt": "Translate image to {target_language}",
            "text_prompt": "Translate text to {target_language}",
            "active_record_target": None,
        }
        data.update(overrides)
        return SettingsFormSnapshot(**data)

    def test_validate_settings_snapshot_detects_subset_hotkey_conflict(self):
        snapshot = self._snapshot(selection_hotkey="Ctrl+X", input_hotkey="Ctrl+Shift+X")

        result = validate_settings_snapshot(
            snapshot,
            existing_profile_names={"Demo"},
            current_profile_name="Demo",
            existing_prompt_preset_names={"Translate"},
            current_prompt_preset_name="Translate",
            normalize_hotkey=lambda hotkey: hotkey.lower(),
            hotkey_has_modifier=lambda hotkey: hotkey.lower().startswith("ctrl"),
            tr=lambda key, **kwargs: key if not kwargs else f"{key}:{kwargs}",
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.field_key == "selection" for issue in result.issues))
        self.assertTrue(any(issue.field_key == "input" for issue in result.issues))

    def test_validate_settings_snapshot_rejects_unsupported_hotkey_primary(self):
        snapshot = self._snapshot(hotkey="Ctrl+Foo")

        result = validate_settings_snapshot(
            snapshot,
            existing_profile_names={"Demo"},
            current_profile_name="Demo",
            existing_prompt_preset_names={"Translate"},
            current_prompt_preset_name="Translate",
            normalize_hotkey=lambda hotkey: hotkey.lower(),
            hotkey_has_modifier=lambda hotkey: hotkey.lower().startswith("ctrl"),
            tr=lambda key, **kwargs: key if not kwargs else f"{key}:{kwargs}",
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.field_key == "capture" and issue.message.startswith("validation_hotkey_unsupported_key") for issue in result.issues))

    def test_validate_settings_snapshot_rejects_modifier_only_hotkey(self):
        snapshot = self._snapshot(hotkey="Ctrl+Shift")

        result = validate_settings_snapshot(
            snapshot,
            existing_profile_names={"Demo"},
            current_profile_name="Demo",
            existing_prompt_preset_names={"Translate"},
            current_prompt_preset_name="Translate",
            normalize_hotkey=lambda hotkey: hotkey.lower(),
            hotkey_has_modifier=lambda hotkey: hotkey.lower().startswith("ctrl"),
            tr=lambda key, **kwargs: key if not kwargs else f"{key}:{kwargs}",
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.field_key == "capture" and issue.message == "validation_hotkey_requires_primary" for issue in result.issues))

    def test_validate_settings_snapshot_uses_runtime_virtual_key_semantics_for_conflicts(self):
        snapshot = self._snapshot(hotkey="Ctrl+Foo", selection_hotkey="Ctrl+Bar")

        result = validate_settings_snapshot(
            snapshot,
            existing_profile_names={"Demo"},
            current_profile_name="Demo",
            existing_prompt_preset_names={"Translate"},
            current_prompt_preset_name="Translate",
            normalize_hotkey=lambda hotkey: hotkey.lower(),
            hotkey_has_modifier=lambda hotkey: hotkey.lower().startswith("ctrl"),
            tr=lambda key, **kwargs: key if not kwargs else f"{key}:{kwargs}",
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.field_key == "capture" and issue.message.startswith("validation_hotkey_unsupported_key") for issue in result.issues))
        self.assertTrue(any(issue.field_key == "selection" and issue.message.startswith("validation_hotkey_unsupported_key") for issue in result.issues))

    def test_validate_fetch_models_scope_skips_unrelated_prompt_target_and_hotkey_rules(self):
        snapshot = self._snapshot(
            model_text="",
            target_language="",
            image_prompt="",
            text_prompt="",
            hotkey="",
            selection_hotkey="",
            input_hotkey="",
        )

        result = validate_settings_snapshot(
            snapshot,
            existing_profile_names={"Demo"},
            current_profile_name="Demo",
            existing_prompt_preset_names={"Translate"},
            current_prompt_preset_name="Translate",
            normalize_hotkey=lambda hotkey: hotkey.lower(),
            hotkey_has_modifier=lambda hotkey: hotkey.lower().startswith("ctrl"),
            tr=lambda key, **kwargs: key if not kwargs else f"{key}:{kwargs}",
            scope="fetch_models",
        )

        self.assertTrue(result.is_valid)

    def test_validate_save_scope_allows_blank_target_language_to_preserve_existing_value(self):
        snapshot = self._snapshot(target_language="")

        result = validate_settings_snapshot(
            snapshot,
            existing_profile_names={"Demo"},
            current_profile_name="Demo",
            existing_prompt_preset_names={"Translate"},
            current_prompt_preset_name="Translate",
            normalize_hotkey=lambda hotkey: hotkey.lower(),
            hotkey_has_modifier=lambda hotkey: hotkey.lower().startswith("ctrl"),
            tr=lambda key, **kwargs: key if not kwargs else f"{key}:{kwargs}",
            scope="save",
        )

        self.assertTrue(result.is_valid)

    def test_validate_text_request_scope_requires_only_text_prompt_and_target_language(self):
        snapshot = self._snapshot(image_prompt="", text_prompt="", target_language="")

        result = validate_settings_snapshot(
            snapshot,
            existing_profile_names={"Demo"},
            current_profile_name="Demo",
            existing_prompt_preset_names={"Translate"},
            current_prompt_preset_name="Translate",
            normalize_hotkey=lambda hotkey: hotkey.lower(),
            hotkey_has_modifier=lambda hotkey: hotkey.lower().startswith("ctrl"),
            tr=lambda key, **kwargs: key if not kwargs else f"{key}:{kwargs}",
            scope="text_request",
        )

        self.assertFalse(result.is_valid)
        self.assertEqual({issue.field_key for issue in result.issues}, {"text_prompt", "target_language"})

    def test_validate_manual_input_scope_requires_text_prompt_but_allows_blank_target_language(self):
        snapshot = self._snapshot(image_prompt="", text_prompt="", target_language="")

        result = validate_settings_snapshot(
            snapshot,
            existing_profile_names={"Demo"},
            current_profile_name="Demo",
            existing_prompt_preset_names={"Translate"},
            current_prompt_preset_name="Translate",
            normalize_hotkey=lambda hotkey: hotkey.lower(),
            hotkey_has_modifier=lambda hotkey: hotkey.lower().startswith("ctrl"),
            tr=lambda key, **kwargs: key if not kwargs else f"{key}:{kwargs}",
            scope="manual_input",
        )

        self.assertFalse(result.is_valid)
        self.assertEqual({issue.field_key for issue in result.issues}, {"text_prompt"})


    def test_build_candidate_config_returns_new_config_and_keeps_original(self):
        base_config = AppConfig(
            target_language="繁體中文",
            ui_language="zh-TW",
            active_profile_name="Default Gemini",
            active_prompt_preset_name="翻譯 (Translate)",
            api_profiles=[ApiProfile(name="Default Gemini", provider="gemini", base_url="https://generativelanguage.googleapis.com", api_keys=["legacy"], model="models/gemini-1.5-flash")],
            prompt_presets=[PromptPreset(name="翻譯 (Translate)", builtin_id="translate", image_prompt="old-image", text_prompt="old-text")],
        )
        snapshot = self._snapshot()

        previous_language, candidate_config, profile, prompt_preset = build_candidate_config(
            base_config,
            snapshot,
            current_profile=base_config.api_profiles[0],
            current_prompt_preset=base_config.prompt_presets[0],
        )

        self.assertEqual(previous_language, "zh-TW")
        self.assertEqual(base_config.ui_language, "zh-TW")
        self.assertEqual(base_config.api_profiles[0].provider, "gemini")
        self.assertEqual(candidate_config.ui_language, "en")
        self.assertEqual(candidate_config.theme_mode, "dark")
        self.assertEqual(candidate_config.target_language, "English")
        self.assertEqual(candidate_config.active_profile_name, "Demo")
        self.assertEqual(candidate_config.active_prompt_preset_name, "Translate")
        self.assertEqual(profile.provider, "openai")
        self.assertEqual(prompt_preset.name, "Translate")
        self.assertEqual(candidate_config.api_profiles[0].api_keys, ["key-1", "key-2"])
        self.assertEqual(candidate_config.overlay_auto_expand_top_margin, 56)
        self.assertEqual(candidate_config.overlay_auto_expand_bottom_margin, 18)
        self.assertEqual(candidate_config.toast_duration_seconds, 1.5)
        self.assertTrue(candidate_config.stream_responses)
        self.assertTrue(candidate_config.check_updates_on_startup)

    def test_build_candidate_config_clears_saved_unpinned_width_override_when_overlay_width_changes(self):
        base_config = AppConfig(
            overlay_width=440,
            overlay_unpinned_width=620,
            overlay_unpinned_width_source="manual",
            active_profile_name="Default Gemini",
            active_prompt_preset_name="翻譯 (Translate)",
            api_profiles=[ApiProfile(name="Default Gemini", provider="gemini", base_url="https://generativelanguage.googleapis.com", api_keys=["legacy"], model="models/gemini-1.5-flash")],
            prompt_presets=[PromptPreset(name="翻譯 (Translate)", builtin_id="translate", image_prompt="old-image", text_prompt="old-text")],
        )
        snapshot = self._snapshot(overlay_width=500)

        _previous_language, candidate_config, _profile, _prompt_preset = build_candidate_config(
            base_config,
            snapshot,
            current_profile=base_config.api_profiles[0],
            current_prompt_preset=base_config.prompt_presets[0],
        )

        self.assertIsNone(candidate_config.overlay_unpinned_width)
        self.assertEqual(candidate_config.overlay_unpinned_width_source, "")


if __name__ == "__main__":
    unittest.main()
