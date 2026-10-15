import unittest
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QEvent, Qt

from app.ui.main_window_hotkeys import MainWindowHotkeysMixin


class MainWindowHotkeysTests(unittest.TestCase):
    class _EventFilterBase:
        def eventFilter(self, watched, event):
            return False

    class _EventFilterHarness(MainWindowHotkeysMixin, _EventFilterBase):
        pass

    def test_recording_consumes_keys_and_escape_cancels_only_active_field(self):
        window = self._EventFilterHarness()
        active, other = object(), object()
        window.hotkey_field_key_for_widget = lambda widget: "capture" if widget is active else "input"
        window.hotkey_record_target = "capture"
        window.stop_hotkey_recording = Mock()
        escape = SimpleNamespace(type=lambda: QEvent.Type.KeyPress, key=lambda: Qt.Key_Escape)
        self.assertFalse(window.eventFilter(other, escape))
        window.stop_hotkey_recording.assert_not_called()
        self.assertTrue(window.eventFilter(active, escape))
        window.stop_hotkey_recording.assert_called_once_with(cancelled=True)
        for kind in (QEvent.Type.KeyRelease, QEvent.Type.ShortcutOverride):
            self.assertTrue(window.eventFilter(active, SimpleNamespace(type=lambda: kind)))

    def test_start_recording_pauses_runtime_listener_and_locks_field(self):
        window = MainWindowHotkeysMixin()
        edit, button = Mock(), Mock()
        listener = Mock()
        window.hotkey_listener = listener
        window.hotkey_fields = lambda: {"input": (edit, button)}
        window.stop_hotkey_recording = Mock()
        window._start_global_hotkey_recorder = Mock()
        window.tr = lambda key: key
        window.set_status = Mock()
        window.validate_form_inputs = Mock()
        window.start_hotkey_recording("input")
        window.stop_hotkey_recording.assert_called_once_with(cancelled=False)
        self.assertEqual(window.hotkey_record_target, "input")
        edit.setReadOnly.assert_called_once_with(True)
        listener.stop.assert_called_once_with()
        self.assertIsNone(window.hotkey_listener)
        self.assertTrue(window.hotkey_listener_paused_for_recording)
        window._start_global_hotkey_recorder.assert_called_once_with("input")

    def test_clicking_active_record_button_cancels(self):
        window = MainWindowHotkeysMixin()
        window.hotkey_record_target = "capture"
        window.stop_hotkey_recording = Mock()
        window.start_hotkey_recording("capture")
        window.stop_hotkey_recording.assert_called_once_with(cancelled=True)

    def test_stale_recorded_hotkey_does_not_change_form(self):
        window = MainWindowHotkeysMixin()
        window.hotkey_record_target = "input"
        window.hotkey_fields = Mock()
        window.handle_recorded_hotkey("capture", "Ctrl+X")
        window.hotkey_fields.assert_not_called()

    def test_global_recorder_tracks_released_modifiers_and_emits_via_bridge(self):
        window = MainWindowHotkeysMixin()
        window._normalize_recorded_key_token = lambda key: key
        window.bridge = SimpleNamespace(hotkey_recorded=SimpleNamespace(emit=Mock()))
        listener = Mock()
        keyboard = SimpleNamespace(Listener=Mock(return_value=listener))
        with patch.dict(sys.modules, {"pynput": SimpleNamespace(keyboard=keyboard)}):
            window._start_global_hotkey_recorder("capture")
        callbacks = keyboard.Listener.call_args.kwargs
        self.assertTrue(callbacks["suppress"])
        self.assertTrue(listener.daemon)
        listener.start.assert_called_once_with()
        press, release = callbacks["on_press"], callbacks["on_release"]
        press("Shift")
        press("Ctrl")
        release("Shift")
        self.assertFalse(press("X"))
        window.bridge.hotkey_recorded.emit.assert_called_once_with("capture", "Ctrl+X")

    def test_global_recorder_escape_emits_cancellation(self):
        window = MainWindowHotkeysMixin()
        window._normalize_recorded_key_token = lambda key: key
        window.bridge = SimpleNamespace(hotkey_recorded=SimpleNamespace(emit=Mock()))
        keyboard = SimpleNamespace(Listener=Mock(return_value=Mock()))
        with patch.dict(sys.modules, {"pynput": SimpleNamespace(keyboard=keyboard)}):
            window._start_global_hotkey_recorder("input")
        self.assertFalse(keyboard.Listener.call_args.kwargs["on_press"]("Esc"))
        window.bridge.hotkey_recorded.emit.assert_called_once_with("input", "")

    def test_stop_hotkey_recording_skips_hotkey_restore_when_requested(self):
        window = MainWindowHotkeysMixin.__new__(MainWindowHotkeysMixin)
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

        with patch.object(MainWindowHotkeysMixin, "_stop_external_listener_best_effort") as mock_stop:
            MainWindowHotkeysMixin.stop_hotkey_recording(window, cancelled=False, restore_hotkey_listener=False)

        mock_stop.assert_called_once()
        window.setup_hotkey_listener.assert_not_called()
        self.assertFalse(window.hotkey_listener_paused_for_recording)
        self.assertIsNone(window.hotkey_record_target)
        edit.setReadOnly.assert_called_once_with(False)
        button.setText.assert_called_once_with("record_hotkey")

    def test_stop_hotkey_recording_restores_current_runtime_hotkeys_when_available(self):
        window = MainWindowHotkeysMixin.__new__(MainWindowHotkeysMixin)
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

        with patch.object(MainWindowHotkeysMixin, "_stop_external_listener_best_effort"):
            MainWindowHotkeysMixin.stop_hotkey_recording(window, cancelled=False)

        window.setup_hotkey_listener.assert_called_once_with(initial=True, hotkey_actions=active_hotkeys)

    def test_handle_recorded_hotkey_applies_runtime_hotkeys_without_saving(self):
        window = MainWindowHotkeysMixin.__new__(MainWindowHotkeysMixin)
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

        MainWindowHotkeysMixin.handle_recorded_hotkey(window, "capture", "Ctrl+Shift+X")

        capture_edit.setText.assert_called_once_with("Ctrl+Shift+X")
        window.stop_hotkey_recording.assert_called_once_with(cancelled=False)
        window.validate_form_inputs.assert_called_once_with(scope="hotkeys")
        window.setup_hotkey_listener.assert_called_once_with(initial=True, hotkey_actions=active_hotkeys, raise_on_error=True)
        window.set_status.assert_called_once_with("hotkeys_registered_pending_save")
