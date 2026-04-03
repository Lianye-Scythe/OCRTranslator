import sys
import types
import unittest

if "pynput" not in sys.modules:
    pynput_stub = types.ModuleType("pynput")
    pynput_stub.keyboard = types.SimpleNamespace(Listener=object)
    sys.modules["pynput"] = pynput_stub

from app.hotkey_listener import HotkeyListener, VK_CONTROL, VK_SHIFT, find_hotkey_conflicts


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


if __name__ == "__main__":
    unittest.main()
