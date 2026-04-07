import unittest
from unittest.mock import Mock, patch

from app.platform.windows.compositor_sync import flush_window_composition


class WindowsCompositorSyncTests(unittest.TestCase):
    def test_flush_window_composition_returns_false_without_dwmapi(self):
        with patch("app.platform.windows.compositor_sync.DWMAPI", None):
            self.assertFalse(flush_window_composition())

    def test_flush_window_composition_returns_true_when_dwmflush_succeeds(self):
        dwmapi = Mock()
        dwmapi.DwmFlush.return_value = 0

        with patch("app.platform.windows.compositor_sync.DWMAPI", dwmapi):
            self.assertTrue(flush_window_composition())

        dwmapi.DwmFlush.assert_called_once_with()

    def test_flush_window_composition_returns_false_when_dwmflush_raises(self):
        dwmapi = Mock()
        dwmapi.DwmFlush.side_effect = RuntimeError("boom")

        with patch("app.platform.windows.compositor_sync.DWMAPI", dwmapi):
            self.assertFalse(flush_window_composition())


if __name__ == "__main__":
    unittest.main()
