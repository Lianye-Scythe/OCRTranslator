from types import SimpleNamespace
import unittest
import sys
import types

if "pynput" not in sys.modules:
    pynput_stub = types.ModuleType("pynput")
    pynput_stub.keyboard = types.SimpleNamespace(Listener=object)
    sys.modules["pynput"] = pynput_stub

from app.ui.main_window import MainWindow


class _ValueWidget:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class _FakeWidget:
    def __init__(self):
        self.enabled = True
        self.text = None
        self.tooltip = None

    def setEnabled(self, value):
        self.enabled = bool(value)

    def setText(self, value):
        self.text = value

    def setToolTip(self, value):
        self.tooltip = value


class MainWindowRuntimeTests(unittest.TestCase):
    def test_current_runtime_values_prefer_live_form_widgets(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(temperature=0.2, overlay_width=440, overlay_height=520, margin=18)
        window.temperature_spin = _ValueWidget(0.7)
        window.overlay_width_spin = _ValueWidget(900)
        window.overlay_height_spin = _ValueWidget(640)
        window.overlay_margin_spin = _ValueWidget(24)

        self.assertEqual(window.current_temperature(), 0.7)
        self.assertEqual(window.current_overlay_width(), 900)
        self.assertEqual(window.current_overlay_height(), 640)
        self.assertEqual(window.current_margin(), 24)

    def test_update_action_states_freezes_settings_during_translation(self):
        window = MainWindow.__new__(MainWindow)
        window.tr = lambda key, **kwargs: key
        window.fetch_models_in_progress = False
        window.test_profile_in_progress = False
        window.translation_in_progress = True
        window.capture_workflow_active = False
        window.tray = object()
        window.tray_capture_action = _FakeWidget()

        for name in (
            "profile_name_edit",
            "provider_combo",
            "base_url_edit",
            "model_combo",
            "api_keys_edit",
            "api_keys_toggle_button",
            "retry_count_spin",
            "retry_interval_spin",
            "target_language_edit",
            "ui_language_combo",
            "hotkey_edit",
            "hotkey_record_button",
            "selection_hotkey_edit",
            "selection_hotkey_record_button",
            "input_hotkey_edit",
            "input_hotkey_record_button",
            "overlay_font_combo",
            "overlay_font_size_spin",
            "mode_combo",
            "prompt_preset_combo",
            "new_prompt_preset_button",
            "delete_prompt_preset_button",
            "prompt_preset_name_edit",
            "image_prompt_edit",
            "text_prompt_edit",
            "temperature_spin",
            "overlay_width_spin",
            "overlay_height_spin",
            "overlay_margin_spin",
            "close_to_tray_on_close_checkbox",
            "fetch_models_button",
            "test_button",
            "save_button",
            "hero_capture_button",
            "hero_tray_button",
            "preview_capture_button",
            "profile_combo",
            "new_profile_button",
            "delete_profile_button",
        ):
            setattr(window, name, _FakeWidget())

        window.update_action_states()

        self.assertFalse(window.target_language_edit.enabled)
        self.assertFalse(window.prompt_preset_combo.enabled)
        self.assertFalse(window.close_to_tray_on_close_checkbox.enabled)
        self.assertFalse(window.hero_tray_button.enabled)
        self.assertFalse(window.profile_combo.enabled)
        self.assertFalse(window.tray_capture_action.enabled)
        self.assertEqual(window.hero_capture_button.text, "start_capture_busy")
        self.assertEqual(window.preview_capture_button.text, "start_capture_busy")


if __name__ == "__main__":
    unittest.main()
