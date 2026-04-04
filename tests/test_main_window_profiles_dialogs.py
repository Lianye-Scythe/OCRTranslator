import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QMessageBox

if "pynput" not in sys.modules:
    pynput_stub = types.ModuleType("pynput")
    pynput_stub.keyboard = types.SimpleNamespace(Listener=object)
    sys.modules["pynput"] = pynput_stub

from app.ui.main_window_profiles import MainWindowProfilesMixin


class MainWindowProfilesDialogTests(unittest.TestCase):
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
