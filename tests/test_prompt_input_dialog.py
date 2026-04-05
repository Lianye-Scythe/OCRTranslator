import unittest
from types import SimpleNamespace

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication

from app.ui.ime_aware_text_edit import ImeAwarePlainTextEdit
from app.ui.prompt_input_dialog import PromptInputDialog


class _FakeAppWindow:
    def isVisible(self):
        return False

    def tr(self, key, **kwargs):
        translations = {
            "manual_input_title": "Send Text Directly to AI",
            "manual_input_hint": "Enter the content to be handled by the current prompt preset.",
            "manual_input_placeholder": "Type the text you want to translate...",
            "manual_input_cancel": "Cancel",
            "manual_input_send": "Send",
            "meta_prompt": "Preset {value}",
            "meta_target": "Target {value}",
            "manual_input_empty": "manual_input_empty",
        }
        text = translations.get(key, key)
        return text.format(**kwargs) if kwargs else text

    def create_button(self, callback, accent=True, secondary=False, success=False, warning=False, danger=False, compact=False):
        from PySide6.QtWidgets import QPushButton

        button = QPushButton()
        button.clicked.connect(callback)
        if secondary:
            button.setProperty("variant", "secondary")
        elif not accent:
            button.setProperty("variant", "neutral")
        else:
            button.setProperty("variant", "primary")
        if compact:
            button.setProperty("compact", True)
        return button

    def set_status(self, *_args, **_kwargs):
        return None


class PromptInputDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = _FakeAppWindow()
        self.dialog = PromptInputDialog(self.window, "Translate", "English")

    def tearDown(self):
        self.dialog.close()
        self.dialog.deleteLater()
        self.app.processEvents()

    def test_dialog_uses_same_single_surface_multiline_editor_structure_as_main_window(self):
        self.assertEqual(self.dialog.text_surface.objectName(), "MultiLineFieldSurface")
        self.assertEqual(self.dialog.text_edit.objectName(), "FramelessFieldEditor")
        self.assertIsInstance(self.dialog.text_edit, ImeAwarePlainTextEdit)
        self.assertFalse(self.dialog.text_surface.property("focused"))

    def test_focus_events_toggle_dialog_multiline_surface_focus_state(self):
        self.dialog.eventFilter(self.dialog.text_edit, QEvent(QEvent.Type.FocusIn))
        self.assertTrue(self.dialog.text_surface.property("focused"))

        self.dialog.eventFilter(self.dialog.text_edit, QEvent(QEvent.Type.FocusOut))
        self.assertFalse(self.dialog.text_surface.property("focused"))


if __name__ == "__main__":
    unittest.main()
