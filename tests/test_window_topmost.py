import unittest
from unittest.mock import Mock, patch

from app.platform.windows.window_topmost import (
    HWND_TOPMOST,
    SWP_NOACTIVATE,
    SWP_NOMOVE,
    SWP_NOSIZE,
    SWP_SHOWWINDOW,
    ensure_window_topmost,
)


class WindowTopmostTests(unittest.TestCase):
    def test_ensure_window_topmost_returns_false_without_user32(self):
        widget = Mock()
        widget.winId.return_value = 123

        with patch("app.platform.windows.window_topmost.USER32", None):
            self.assertFalse(ensure_window_topmost(widget))

    def test_ensure_window_topmost_calls_set_window_pos_with_topmost_flags(self):
        widget = Mock()
        widget.winId.return_value = 456
        user32 = Mock()
        user32.SetWindowPos.return_value = 1

        with patch("app.platform.windows.window_topmost.USER32", user32):
            self.assertTrue(ensure_window_topmost(widget))

        user32.SetWindowPos.assert_called_once()
        hwnd, topmost, x, y, width, height, flags = user32.SetWindowPos.call_args.args
        self.assertEqual((hwnd, topmost, x, y, width, height), (456, HWND_TOPMOST, 0, 0, 0, 0))
        self.assertEqual(flags, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW | SWP_NOACTIVATE)


if __name__ == "__main__":
    unittest.main()
