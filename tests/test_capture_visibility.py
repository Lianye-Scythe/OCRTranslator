import unittest
from unittest.mock import Mock, patch

from app.platform.windows.capture_visibility import (
    DWMWA_CLOAK,
    begin_temporary_capture_conceal,
    restore_temporary_capture_conceal,
)


class CaptureVisibilityTests(unittest.TestCase):
    def test_begin_temporary_capture_conceal_uses_dwm_cloak_when_available(self):
        widget = Mock()
        widget.winId.return_value = 123
        dwmapi = Mock()
        dwmapi.DwmSetWindowAttribute.return_value = 0

        with patch("app.platform.windows.capture_visibility.DWMAPI", dwmapi):
            state = begin_temporary_capture_conceal(widget)

        self.assertEqual(state["method"], "cloak")
        self.assertEqual(state["hwnd"], 123)
        dwmapi.DwmSetWindowAttribute.assert_called_once()
        args = dwmapi.DwmSetWindowAttribute.call_args.args
        self.assertEqual(args[0], 123)
        self.assertEqual(args[1], DWMWA_CLOAK)

    def test_begin_temporary_capture_conceal_falls_back_to_opacity(self):
        widget = Mock()
        widget.winId.side_effect = RuntimeError("no hwnd")
        widget.windowOpacity.return_value = 0.75
        dwmapi = Mock()

        with patch("app.platform.windows.capture_visibility.DWMAPI", dwmapi):
            state = begin_temporary_capture_conceal(widget)

        self.assertEqual(state, {"widget": widget, "method": "opacity", "opacity": 0.75})
        widget.setWindowOpacity.assert_called_once_with(0.0)

    def test_restore_temporary_capture_conceal_uncloaks_window(self):
        widget = Mock()
        widget.winId.return_value = 321
        dwmapi = Mock()
        dwmapi.DwmSetWindowAttribute.return_value = 0

        with patch("app.platform.windows.capture_visibility.DWMAPI", dwmapi):
            result = restore_temporary_capture_conceal({"widget": widget, "method": "cloak", "hwnd": 321})

        self.assertTrue(result)
        dwmapi.DwmSetWindowAttribute.assert_called_once()
        args = dwmapi.DwmSetWindowAttribute.call_args.args
        self.assertEqual(args[0], 321)
        self.assertEqual(args[1], DWMWA_CLOAK)

    def test_restore_temporary_capture_conceal_restores_opacity(self):
        widget = Mock()

        result = restore_temporary_capture_conceal({"widget": widget, "method": "opacity", "opacity": 0.6})

        self.assertTrue(result)
        widget.setWindowOpacity.assert_called_once_with(0.6)


if __name__ == "__main__":
    unittest.main()
