import unittest

from PySide6.QtWidgets import QApplication, QPushButton

from app.ui.focus_utils import clear_focus_if_alive, schedule_clear_focus


class FocusUtilsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_clear_focus_if_alive_ignores_deleted_widget(self):
        button = QPushButton()
        button.deleteLater()
        self.app.processEvents()

        clear_focus_if_alive(button)

    def test_schedule_clear_focus_ignores_deleted_widget(self):
        button = QPushButton()
        schedule_clear_focus(button)
        button.deleteLater()
        self.app.processEvents()

        self.app.processEvents()
