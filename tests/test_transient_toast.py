import unittest
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication, QWidget

from app.services.transient_toast import TransientToastService


class _FakeToastWindow:
    def __init__(self):
        self.is_quitting = False
        self.workspace_surface = None

    def effective_theme_name(self):
        return "dark"

    def isVisible(self):
        return False

    def isMinimized(self):
        return False


class TransientToastServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_show_message_displays_and_hide_message_closes_widget(self):
        window = _FakeToastWindow()
        service = TransientToastService(window)
        self.addCleanup(service.close)

        self.assertTrue(service.show_message("Request submitted", duration_ms=500))
        self.assertTrue(service.widget.isVisible())
        self.assertEqual(service.widget.label.text(), "Request submitted")

        service.hide_message()
        self.assertFalse(service.widget.isVisible())

    def test_show_message_uses_workspace_anchor_when_window_is_visible(self):
        window = _FakeToastWindow()
        host = QWidget()
        host.resize(500, 300)
        host.show()
        self.addCleanup(lambda: (host.close(), host.deleteLater(), self.app.processEvents()))
        self.app.processEvents()

        window.workspace_surface = host
        window.isVisible = lambda: True
        service = TransientToastService(window)
        self.addCleanup(service.close)

        self.assertTrue(service.show_message("Anchored toast", duration_ms=500))
        self.assertTrue(service.widget.x() >= host.mapToGlobal(host.rect().topLeft()).x())


if __name__ == "__main__":
    unittest.main()
