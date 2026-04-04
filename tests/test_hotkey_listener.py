import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

if "pynput" not in sys.modules:
    pynput_stub = types.ModuleType("pynput")
    pynput_stub.keyboard = types.SimpleNamespace(Listener=object)
    sys.modules["pynput"] = pynput_stub

from app.hotkey_listener import HotkeyListener, VK_CONTROL, VK_SHIFT, VK_LWIN, WM_KEYDOWN, WM_KEYUP, find_hotkey_conflicts


class _FakePynputListener:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.daemon = False
        self.started = False

    def start(self):
        self.started = True


class HotkeyListenerTests(unittest.TestCase):
    def test_find_hotkey_conflicts_detects_subset_conflict(self):
        conflicts = find_hotkey_conflicts(
            {
                "capture": "Ctrl+X",
                "selection": "Ctrl+Shift+X",
                "input": "Ctrl+Z",
            }
        )

        self.assertIn(("subset", "capture", "selection"), conflicts)

    def test_refresh_active_state_prefers_most_specific_action(self):
        listener = HotkeyListener({}, lambda action: None)
        listener._combo_virtual_keys = {
            "capture": {VK_CONTROL, ord("X")},
            "selection_text": {VK_CONTROL, VK_SHIFT, ord("X")},
        }
        listener._pressed_virtual_keys = {VK_CONTROL, VK_SHIFT, ord("X")}

        new_actions = listener._refresh_active_state()

        self.assertEqual(new_actions, {"selection_text"})
        self.assertEqual(listener._active_actions, {"selection_text"})
        self.assertEqual(listener._suppressed_virtual_keys, {VK_CONTROL, VK_SHIFT, ord("X")})

    @patch("app.platform.windows.hotkeys._is_virtual_key_pressed", return_value=True)
    def test_keyup_suppression_tracks_only_suppressed_keydowns(self, _mock_is_pressed):
        triggered = []
        listener = HotkeyListener({"capture": "Shift+Win+X"}, triggered.append)
        listener._combo_virtual_keys = {"capture": {VK_SHIFT, ord("X"), VK_LWIN}}
        suppressions = []
        listener.listener = SimpleNamespace(suppress_event=lambda: suppressions.append("suppress"))

        listener._win32_event_filter(WM_KEYDOWN, SimpleNamespace(vkCode=VK_SHIFT))
        listener._win32_event_filter(WM_KEYDOWN, SimpleNamespace(vkCode=VK_LWIN))
        listener._win32_event_filter(WM_KEYDOWN, SimpleNamespace(vkCode=ord("X")))

        self.assertEqual(triggered, ["capture"])
        self.assertEqual(suppressions, ["suppress"])

        listener._win32_event_filter(WM_KEYUP, SimpleNamespace(vkCode=VK_SHIFT))
        self.assertEqual(suppressions, ["suppress"])

        listener._win32_event_filter(WM_KEYUP, SimpleNamespace(vkCode=ord("X")))
        self.assertEqual(suppressions, ["suppress", "suppress"])

        listener._win32_event_filter(WM_KEYUP, SimpleNamespace(vkCode=VK_LWIN))
        self.assertEqual(suppressions, ["suppress", "suppress"])
        self.assertEqual(listener._pressed_virtual_keys, set())
        self.assertEqual(listener._suppressed_pressed_virtual_keys, set())

    @patch("app.platform.windows.hotkeys._is_virtual_key_pressed")
    def test_resync_pressed_virtual_keys_clears_missed_modifier_release(self, mock_is_pressed):
        listener = HotkeyListener({"capture": "Shift+X"}, lambda action: None, log_func=lambda message: logs.append(message))
        listener._combo_virtual_keys = {"capture": {VK_SHIFT, ord("X")}}
        listener._pressed_virtual_keys = {VK_SHIFT, ord("X")}
        listener._active_actions = {"capture"}
        listener._suppressed_virtual_keys = {VK_SHIFT, ord("X")}
        listener._suppressed_pressed_virtual_keys = {ord("X")}
        logs = []

        mock_is_pressed.side_effect = lambda vk: vk == ord("X")

        listener._resync_pressed_virtual_keys()

        self.assertEqual(listener._pressed_virtual_keys, {ord("X")})
        self.assertEqual(listener._active_actions, set())
        self.assertEqual(listener._suppressed_pressed_virtual_keys, {ord("X")})
        self.assertTrue(any("Resynced hotkey state" in message for message in logs))

    @patch("app.platform.windows.hotkeys.keyboard.Listener")
    def test_start_marks_underlying_listener_as_daemon(self, mock_listener_cls):
        fake_listener = _FakePynputListener()
        mock_listener_cls.return_value = fake_listener
        listener = HotkeyListener({"capture": "Shift+Win+X"}, lambda action: None)

        listener.start()

        self.assertTrue(fake_listener.daemon)
        self.assertTrue(fake_listener.started)

    def test_stop_uses_best_effort_listener_shutdown(self):
        listener = HotkeyListener({}, lambda action: None)
        listener.listener = object()
        with patch.object(HotkeyListener, "_stop_listener_best_effort") as mock_stop:
            listener.stop()
        mock_stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
