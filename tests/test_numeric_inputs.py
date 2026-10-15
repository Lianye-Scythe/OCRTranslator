import unittest

from PySide6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget

from app.ui.main_window_layout import ScrollSafeDoubleSpinBox, ScrollSafeSpinBox
from app.ui.style_utils import load_style_sheet


class NumericInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_styled_numeric_text_keeps_left_inset_in_both_themes_and_states(self):
        for theme in ("light", "dark"):
            for enabled in (True, False):
                with self.subTest(theme=theme, enabled=enabled):
                    container = QWidget()
                    layout = QVBoxLayout(container)
                    reference = QLineEdit("20")
                    layout.addWidget(reference)
                    controls = [ScrollSafeSpinBox(), ScrollSafeDoubleSpinBox()]
                    try:
                        container.setStyleSheet(load_style_sheet("main_window.qss", theme_name=theme))
                        for control in controls:
                            control.setValue(20)
                            control.setEnabled(enabled)
                            layout.addWidget(control)
                        container.show()
                        self.app.processEvents()
                        reference.setCursorPosition(0)
                        reference_x = reference.cursorRect().center().x()
                        for control in controls:
                            editor = control.lineEdit()
                            editor.setCursorPosition(0)
                            cursor_x = editor.geometry().left() + editor.cursorRect().center().x()
                            self.assertLessEqual(abs(cursor_x - reference_x), 1)
                            self.assertLess(cursor_x, control.width() / 4)
                            self.assertEqual(control.value(), 20)
                    finally:
                        container.hide()
                        container.deleteLater()
                        self.app.processEvents()
