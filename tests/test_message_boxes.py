import unittest
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox

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


    def test_custom_message_box_expands_long_button_labels_to_avoid_clipping(self):
        captured_widths = {}
        captured_dialog_min_width = 0

        def fake_exec(dialog):
            nonlocal captured_dialog_min_width
            for button in dialog.buttons():
                captured_widths[button.text()] = button.minimumWidth()
            captured_dialog_min_width = dialog.minimumWidth()
            return 0

        with patch.object(QMessageBox, "exec", fake_exec), patch.object(QMessageBox, "clickedButton", return_value=None):
            show_custom_message_box(
                None,
                "Unsaved Changes",
                "You have unsaved changes. Save them before continuing?",
                icon=QMessageBox.Warning,
                actions=[
                    MessageBoxAction("Save and Continue", QMessageBox.AcceptRole, "save", variant="primary", is_default=True),
                    MessageBoxAction("Discard Changes", QMessageBox.DestructiveRole, "discard", variant="danger"),
                    MessageBoxAction("Cancel", QMessageBox.RejectRole, "cancel", variant="neutral", is_escape=True),
                ],
                escape_result="cancel",
            )

        self.assertGreaterEqual(captured_widths["Save and Continue"], 120)
        self.assertGreaterEqual(captured_widths["Discard Changes"], 120)
        self.assertGreaterEqual(captured_widths["Cancel"], 96)
        self.assertGreaterEqual(captured_dialog_min_width, 460)

    def test_custom_message_box_can_center_main_text(self):
        captured_alignment = None
        captured_item_alignment = None
        captured_margins = None

        def fake_exec(dialog):
            nonlocal captured_alignment, captured_item_alignment, captured_margins
            label = dialog.findChild(QLabel, "qt_msgbox_label")
            captured_alignment = int(label.alignment()) if label is not None else None
            captured_item_alignment = int(dialog.layout().itemAt(dialog.layout().indexOf(label)).alignment()) if label is not None else None
            captured_margins = (
                (label.contentsMargins().left(), label.contentsMargins().top(), label.contentsMargins().right(), label.contentsMargins().bottom())
                if label is not None else None
            )
            return 0

        with patch.object(QMessageBox, "exec", fake_exec), patch.object(QMessageBox, "clickedButton", return_value=None):
            show_custom_message_box(
                None,
                "Unsaved Changes",
                "You have unsaved changes.\nSave them before continuing?",
                icon=QMessageBox.Warning,
                actions=[MessageBoxAction("OK", QMessageBox.AcceptRole, "ok", variant="primary", is_escape=True)],
                center_text=True,
            )

        self.assertEqual(captured_alignment, int(Qt.AlignLeft | Qt.AlignVCenter))
        self.assertEqual(captured_item_alignment, int(Qt.AlignHCenter | Qt.AlignVCenter))
        self.assertEqual(captured_margins, (10, 8, 10, 8))
