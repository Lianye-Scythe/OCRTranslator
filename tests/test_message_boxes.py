import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMessageBox

from app.ui.message_boxes import MessageBoxAction, show_custom_message_box, show_destructive_confirmation, show_information_message, show_standard_message_box


class MessageBoxHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_standard_message_box_escape_hatch_skips_polish(self):
        with patch("app.ui.message_boxes._polish_dialog") as mock_polish, patch.object(QMessageBox, "exec", return_value=0), patch.object(
            QMessageBox, "clickedButton", return_value=None
        ):
            result = show_standard_message_box(
                None,
                "Title",
                "Body",
                icon=QMessageBox.Warning,
                buttons=[QMessageBox.Yes, QMessageBox.No],
                default_button=QMessageBox.No,
                escape_button=QMessageBox.No,
                prefer_native=True,
            )

        self.assertEqual(result, QMessageBox.No)
        mock_polish.assert_not_called()

    def test_custom_message_box_maps_clicked_button_to_result(self):
        def fake_exec(dialog):
            dialog._test_clicked_button = dialog.buttons()[1]
            return 0

        def fake_clicked_button(dialog):
            return getattr(dialog, "_test_clicked_button", None)

        with patch.object(QMessageBox, "exec", fake_exec), patch.object(QMessageBox, "clickedButton", fake_clicked_button):
            result = show_custom_message_box(
                None,
                "Title",
                "Body",
                icon=QMessageBox.Question,
                actions=[
                    MessageBoxAction("Keep", QMessageBox.AcceptRole, "keep", variant="primary"),
                    MessageBoxAction("Discard", QMessageBox.DestructiveRole, "discard", variant="danger", is_escape=True),
                ],
            )

        self.assertEqual(result, "discard")

    def test_custom_message_box_returns_escape_result_when_closed(self):
        with patch.object(QMessageBox, "exec", return_value=0), patch.object(QMessageBox, "clickedButton", return_value=None):
            result = show_custom_message_box(
                None,
                "Title",
                "Body",
                icon=QMessageBox.Warning,
                actions=[
                    MessageBoxAction("Save", QMessageBox.AcceptRole, "save", variant="primary"),
                    MessageBoxAction("Cancel", QMessageBox.RejectRole, "cancel", variant="neutral", is_escape=True),
                ],
                escape_result="cancel",
            )

        self.assertEqual(result, "cancel")

    def test_destructive_confirmation_returns_true_when_confirmed(self):
        def fake_exec(dialog):
            dialog._test_clicked_button = dialog.buttons()[1]
            return 0

        def fake_clicked_button(dialog):
            return getattr(dialog, "_test_clicked_button", None)

        with patch.object(QMessageBox, "exec", fake_exec), patch.object(QMessageBox, "clickedButton", fake_clicked_button):
            result = show_destructive_confirmation(
                None,
                "Delete",
                "Delete item?",
                confirm_text="Delete",
                cancel_text="Cancel",
            )

        self.assertTrue(result)

    def test_destructive_confirmation_returns_false_when_closed(self):
        with patch.object(QMessageBox, "exec", return_value=0), patch.object(QMessageBox, "clickedButton", return_value=None):
            result = show_destructive_confirmation(
                None,
                "Delete",
                "Delete item?",
                confirm_text="Delete",
                cancel_text="Cancel",
            )

        self.assertFalse(result)

    def test_information_message_uses_information_tone(self):
        with patch("app.ui.message_boxes._polish_dialog") as mock_polish, patch.object(QMessageBox, "exec", return_value=0), patch.object(
            QMessageBox, "clickedButton", return_value=None
        ):
            show_information_message(None, "Title", "Body")

        self.assertEqual(mock_polish.call_args.kwargs["tone"], "information")

    def test_destructive_confirmation_uses_destructive_tone(self):
        with patch("app.ui.message_boxes._polish_dialog") as mock_polish, patch.object(QMessageBox, "exec", return_value=0), patch.object(
            QMessageBox, "clickedButton", return_value=None
        ):
            show_destructive_confirmation(None, "Delete", "Delete item?", confirm_text="Delete", cancel_text="Cancel")

        self.assertEqual(mock_polish.call_args.kwargs["tone"], "destructive")
