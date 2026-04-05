import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QMessageBox

if "pynput" not in sys.modules:
    pynput_stub = types.ModuleType("pynput")
    pynput_stub.keyboard = types.SimpleNamespace(Listener=object)
    sys.modules["pynput"] = pynput_stub

from app.ui.main_window_profiles import MainWindowProfilesMixin


class MainWindowProfilesDialogTests(unittest.TestCase):
    class _EventFilterBase:
        def eventFilter(self, watched, event):
            return (watched, event)

    class _EventFilterHarness(MainWindowProfilesMixin, _EventFilterBase):
        pass

    def test_delete_current_profile_uses_destructive_confirmation(self):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        profile = SimpleNamespace(name="Demo")
        other_profile = SimpleNamespace(name="Other")
        window.config = SimpleNamespace(api_profiles=[profile, other_profile], active_profile_name=profile.name)
        window.resolve_unsaved_changes = lambda: True
        window.tr = lambda key, **kwargs: kwargs.get("name", key)
        window.load_profile_to_form = Mock()
        window.set_unsaved_changes = Mock()
        window.set_status = Mock()
        window.log = Mock()

        with patch("app.ui.main_window_profiles.show_destructive_confirmation", return_value=False) as mock_confirmation:
            MainWindowProfilesMixin.delete_current_profile(window)

        mock_confirmation.assert_called_once()
        _, kwargs = mock_confirmation.call_args
        self.assertEqual(kwargs["confirm_text"], "delete_profile")
        self.assertEqual(kwargs["cancel_text"], "unsaved_changes_cancel")

    def test_prompt_unsaved_changes_maps_escape_to_cancel(self):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        window.tr = lambda key, **kwargs: key

        with patch("app.ui.main_window_profiles.show_custom_message_box", return_value=QMessageBox.Cancel) as mock_dialog:
            result = MainWindowProfilesMixin.prompt_unsaved_changes(window)

        self.assertEqual(result, QMessageBox.Cancel)
        mock_dialog.assert_called_once()
        self.assertTrue(mock_dialog.call_args.kwargs["center_text"])

    def test_stop_hotkey_recording_skips_hotkey_restore_when_requested(self):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        edit = SimpleNamespace(setReadOnly=Mock())
        button = SimpleNamespace(setText=Mock())
        window.hotkey_record_target = "capture"
        window.hotkey_record_listener = object()
        window.hotkey_listener_paused_for_recording = True
        window.hotkey_fields = lambda: {"capture": (edit, button)}
        window.tr = lambda key, **kwargs: key
        window.setup_hotkey_listener = Mock()
        window.validate_form_inputs = Mock(return_value=(True, ""))
        window.set_status = Mock()

        with patch.object(MainWindowProfilesMixin, "_stop_external_listener_best_effort") as mock_stop:
            MainWindowProfilesMixin.stop_hotkey_recording(window, cancelled=False, restore_hotkey_listener=False)

        mock_stop.assert_called_once()
        window.setup_hotkey_listener.assert_not_called()
        self.assertFalse(window.hotkey_listener_paused_for_recording)
        self.assertIsNone(window.hotkey_record_target)
        edit.setReadOnly.assert_called_once_with(False)
        button.setText.assert_called_once_with("record_hotkey")

    def test_stop_hotkey_recording_restores_current_runtime_hotkeys_when_available(self):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        edit = SimpleNamespace(setReadOnly=Mock())
        button = SimpleNamespace(setText=Mock())
        active_hotkeys = {
            "capture": "Ctrl+Shift+X",
            "selection_text": "Ctrl+Shift+C",
            "manual_input": "Ctrl+Shift+Z",
        }
        window.hotkey_record_target = "capture"
        window.hotkey_record_listener = object()
        window.hotkey_listener_paused_for_recording = True
        window.registered_hotkeys = dict(active_hotkeys)
        window.hotkey_fields = lambda: {"capture": (edit, button)}
        window.tr = lambda key, **kwargs: key
        window.setup_hotkey_listener = Mock()
        window.validate_form_inputs = Mock(return_value=(True, ""))
        window.set_status = Mock()

        with patch.object(MainWindowProfilesMixin, "_stop_external_listener_best_effort"):
            MainWindowProfilesMixin.stop_hotkey_recording(window, cancelled=False)

        window.setup_hotkey_listener.assert_called_once_with(initial=True, hotkey_actions=active_hotkeys)

    def test_handle_recorded_hotkey_applies_runtime_hotkeys_without_saving(self):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        capture_edit = SimpleNamespace(setText=Mock(), text=lambda: "Ctrl+Shift+X")
        selection_edit = SimpleNamespace(text=lambda: "Ctrl+Shift+C")
        input_edit = SimpleNamespace(text=lambda: "Ctrl+Shift+Z")
        window.hotkey_record_target = "capture"
        window.hotkey_fields = lambda: {"capture": (capture_edit, object())}
        window.hotkey_edit = capture_edit
        window.selection_hotkey_edit = selection_edit
        window.input_hotkey_edit = input_edit
        window.stop_hotkey_recording = Mock()
        active_hotkeys = {
            "capture": "Ctrl+Shift+X",
            "selection_text": "Ctrl+Shift+C",
            "manual_input": "Ctrl+Shift+Z",
        }
        window.validate_form_inputs = Mock(return_value=(True, ""))
        window.runtime_hotkey_actions_from_form = Mock(return_value=active_hotkeys)
        window.setup_hotkey_listener = Mock(return_value=True)
        window.set_status = Mock()
        window.log = Mock()

        MainWindowProfilesMixin.handle_recorded_hotkey(window, "capture", "Ctrl+Shift+X")

        capture_edit.setText.assert_called_once_with("Ctrl+Shift+X")
        window.stop_hotkey_recording.assert_called_once_with(cancelled=False)
        window.validate_form_inputs.assert_called_once_with(scope="hotkeys")
        window.setup_hotkey_listener.assert_called_once_with(initial=True, hotkey_actions=active_hotkeys, raise_on_error=True)
        window.set_status.assert_called_once_with("hotkeys_registered_pending_save")

    def test_reload_saved_config_reapplies_saved_hotkeys(self):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        saved_config = SimpleNamespace(active_profile_name="Demo", active_prompt_preset_name="Translate")
        window.load_profile_to_form = Mock()
        window.load_prompt_preset_to_form = Mock()
        window.setup_hotkey_listener = Mock(return_value=True)
        window.log = Mock()
        window.handle_error = Mock()

        with patch("app.ui.main_window_profiles.load_config", return_value=saved_config):
            MainWindowProfilesMixin.reload_saved_config(window)

        self.assertIs(window.config, saved_config)
        window.load_profile_to_form.assert_called_once_with("Demo")
        window.load_prompt_preset_to_form.assert_called_once_with("Translate")
        window.setup_hotkey_listener.assert_called_once_with(initial=True, config=saved_config, raise_on_error=True)

    def test_discard_unsaved_changes_reloads_saved_state_and_restores_scroll(self):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        window.has_unsaved_changes = True
        window.current_settings_scroll_value = Mock(return_value=188)
        window.reload_saved_config = Mock()
        window.restore_post_save_view_state = Mock()
        window.set_status = Mock()
        window.log = Mock()

        result = MainWindowProfilesMixin.discard_unsaved_changes(window)

        self.assertTrue(result)
        window.reload_saved_config.assert_called_once_with()
        window.restore_post_save_view_state.assert_called_once_with(188)
        window.set_status.assert_called_once_with("changes_discarded")

    def test_get_profile_by_name_recovers_empty_profile_list(self):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        window.config = SimpleNamespace(api_profiles=[], active_profile_name="")

        profile = MainWindowProfilesMixin.get_profile_by_name(window, "missing")

        self.assertEqual(profile.name, "Default Gemini")
        self.assertEqual(len(window.config.api_profiles), 1)
        self.assertEqual(window.config.active_profile_name, "Default Gemini")

    def test_refresh_api_keys_editor_uses_hidden_empty_guidance_when_no_keys_exist(self):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        window.api_keys_actual_text = ""
        window.api_keys_visible = False
        window._api_keys_hint_override_key = None
        window.set_api_keys_editor_text = Mock()
        window._refresh_widget_style = Mock()
        window._sync_multiline_editor_surface_state = Mock()
        window.tr = lambda key, **kwargs: key
        window.api_keys_edit = SimpleNamespace(setReadOnly=Mock(), setFocusPolicy=Mock(), setPlaceholderText=Mock(), setProperty=Mock())
        window.api_keys_label_row = SimpleNamespace(setText=Mock())
        window.api_keys_toggle_button = SimpleNamespace(setText=Mock())
        window.api_keys_hint = SimpleNamespace(setText=Mock())
        window.api_keys_shell = SimpleNamespace(setProperty=Mock())
        window.api_keys_editor_surface = SimpleNamespace(setProperty=Mock())

        MainWindowProfilesMixin.refresh_api_keys_editor(window)

        window.set_api_keys_editor_text.assert_called_once_with("")
        window.api_keys_edit.setReadOnly.assert_called_once_with(True)
        window.api_keys_edit.setFocusPolicy.assert_called_once_with(Qt.NoFocus)
        window._sync_multiline_editor_surface_state.assert_called_once_with(window.api_keys_edit, focused=False)
        window.api_keys_edit.setProperty.assert_called_once_with("concealed", True)
        window.api_keys_edit.setPlaceholderText.assert_called_once_with("api_keys_hidden_empty_placeholder")
        window.api_keys_label_row.setText.assert_called_once_with("api_keys_hidden")
        window.api_keys_toggle_button.setText.assert_called_once_with("show_api_keys")
        window.api_keys_hint.setText.assert_called_once_with("api_keys_mask_hint_empty")
        window.api_keys_shell.setProperty.assert_any_call("concealed", True)
        window.api_keys_editor_surface.setProperty.assert_called_once_with("concealed", True)
        self.assertGreaterEqual(window._refresh_widget_style.call_count, 3)

    def test_is_hidden_api_keys_interaction_target_matches_editor_surface_and_viewport(self):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        viewport = object()
        window.api_keys_edit = SimpleNamespace(viewport=lambda: viewport)
        window.api_keys_editor_surface = object()

        self.assertTrue(MainWindowProfilesMixin.is_hidden_api_keys_interaction_target(window, viewport))
        self.assertTrue(MainWindowProfilesMixin.is_hidden_api_keys_interaction_target(window, window.api_keys_editor_surface))
        self.assertFalse(MainWindowProfilesMixin.is_hidden_api_keys_interaction_target(window, object()))

    def test_event_filter_handles_api_keys_click_before_api_keys_visible_is_initialized(self):
        window = self._EventFilterHarness()
        viewport = object()
        event = SimpleNamespace(type=lambda: QEvent.Type.MouseButtonPress)
        window.api_keys_edit = SimpleNamespace(viewport=lambda: viewport)
        window.api_keys_editor_surface = object()
        window.api_keys_toggle_button = object()
        window.api_keys_hint = object()
        window.multiline_editor_surface_for = lambda watched: None
        window.hotkey_field_key_for_widget = lambda watched: None
        window.nudge_api_keys_visibility_affordance = Mock()

        result = window.eventFilter(viewport, event)

        self.assertTrue(result)
        window.nudge_api_keys_visibility_affordance.assert_called_once_with()
        self.assertFalse(hasattr(window, "api_keys_visible"))

    @patch("app.ui.main_window_profiles.QTimer.singleShot")
    def test_nudge_api_keys_visibility_affordance_tolerates_late_timer_on_disposed_widgets(self, mock_single_shot):
        window = MainWindowProfilesMixin.__new__(MainWindowProfilesMixin)
        window.api_keys_visible = False
        window._api_keys_hint_override_key = None
        window._api_keys_reveal_pulse_id = 0
        window._apply_api_keys_hint_text = Mock()
        window._set_api_keys_reveal_pulse = Mock(side_effect=[None, RuntimeError("wrapped C/C++ object has been deleted")])

        MainWindowProfilesMixin.nudge_api_keys_visibility_affordance(window)

        self.assertEqual(mock_single_shot.call_count, 2)
        _, idle_callback = mock_single_shot.call_args_list[0].args
        _, finish_callback = mock_single_shot.call_args_list[1].args
        idle_callback()
        finish_callback()
        self.assertEqual(window._api_keys_reveal_pulse_id, 1)
        self.assertEqual(window._set_api_keys_reveal_pulse.call_count, 2)
