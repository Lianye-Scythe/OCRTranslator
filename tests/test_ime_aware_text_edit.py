import unittest

from PySide6.QtGui import QInputMethodEvent
from PySide6.QtWidgets import QApplication

from app.ui.ime_aware_text_edit import ImeAwarePlainTextEdit


class ImeAwarePlainTextEditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.editor = ImeAwarePlainTextEdit()
        self.editor.resize(320, 160)
        self.editor.setPlaceholderText("Type the text you want to translate...")
        self.editor.show()
        self.editor.setFocus()
        self.app.processEvents()

    def tearDown(self):
        self.editor.close()
        self.editor.deleteLater()
        self.app.processEvents()

    def test_placeholder_is_visible_only_when_editor_is_empty_and_not_in_preedit(self):
        self.assertTrue(self.editor.placeholder_visible())

        self.editor.setPlainText("hello")
        self.app.processEvents()
        self.assertFalse(self.editor.placeholder_visible())

    def test_placeholder_hides_while_input_method_preedit_text_is_active(self):
        self.editor.inputMethodEvent(QInputMethodEvent("你好", []))
        self.app.processEvents()

        self.assertFalse(self.editor.placeholder_visible())

    def test_placeholder_returns_after_preedit_clears_without_committed_text(self):
        self.editor.inputMethodEvent(QInputMethodEvent("你好", []))
        self.editor.inputMethodEvent(QInputMethodEvent("", []))
        self.app.processEvents()

        self.assertTrue(self.editor.placeholder_visible())


if __name__ == "__main__":
    unittest.main()
