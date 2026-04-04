import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.ui.main_window_prompts import MainWindowPromptPresetsMixin


class PromptPresetRuntimeTests(unittest.TestCase):
    def test_delete_current_prompt_preset_blocks_builtin_presets(self):
        window = MainWindowPromptPresetsMixin.__new__(MainWindowPromptPresetsMixin)
        preset = SimpleNamespace(name="翻譯 (Translate)", builtin_id="translate")
        window.config = SimpleNamespace(prompt_presets=[preset], active_prompt_preset_name=preset.name)
        window.resolve_unsaved_changes = lambda: True
        window.tr = lambda key, **kwargs: key
        window.get_active_prompt_preset = lambda: preset

        with patch("app.ui.main_window_prompts.QMessageBox.information") as mock_information:
            MainWindowPromptPresetsMixin.delete_current_prompt_preset(window)

        mock_information.assert_called_once()


if __name__ == "__main__":
    unittest.main()
