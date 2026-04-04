import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

if "pynput" not in sys.modules:
    pynput_stub = types.ModuleType("pynput")
    pynput_stub.keyboard = types.SimpleNamespace(Listener=object)
    sys.modules["pynput"] = pynput_stub

from app.ui.main_window_prompts import MainWindowPromptPresetsMixin


class PromptPresetRuntimeTests(unittest.TestCase):
    def test_delete_current_prompt_preset_blocks_builtin_presets(self):
        window = MainWindowPromptPresetsMixin.__new__(MainWindowPromptPresetsMixin)
        preset = SimpleNamespace(name="翻譯 (Translate)", builtin_id="translate")
        window.config = SimpleNamespace(prompt_presets=[preset], active_prompt_preset_name=preset.name)
        window.resolve_unsaved_changes = lambda: True
        window.tr = lambda key, **kwargs: key
        window.get_active_prompt_preset = lambda: preset

        with patch("app.ui.main_window_prompts.show_information_message") as mock_information:
            MainWindowPromptPresetsMixin.delete_current_prompt_preset(window)

        mock_information.assert_called_once()

    def test_delete_current_prompt_preset_uses_destructive_confirmation(self):
        window = MainWindowPromptPresetsMixin.__new__(MainWindowPromptPresetsMixin)
        preset = SimpleNamespace(name="自定义方案", builtin_id="")
        window.config = SimpleNamespace(prompt_presets=[preset, SimpleNamespace(name="其他方案", builtin_id="")], active_prompt_preset_name=preset.name)
        window.resolve_unsaved_changes = lambda: True
        window.tr = lambda key, **kwargs: kwargs.get("name", key)
        window.active_prompt_preset_is_builtin = lambda: False

        with patch("app.ui.main_window_prompts.show_destructive_confirmation", return_value=False) as mock_confirmation:
            MainWindowPromptPresetsMixin.delete_current_prompt_preset(window)

        mock_confirmation.assert_called_once()
        _, kwargs = mock_confirmation.call_args
        self.assertEqual(kwargs["confirm_text"], "delete_prompt_preset")
        self.assertEqual(kwargs["cancel_text"], "unsaved_changes_cancel")


if __name__ == "__main__":
    unittest.main()
