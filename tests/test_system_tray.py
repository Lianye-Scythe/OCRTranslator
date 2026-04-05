import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.system_tray import SystemTrayService


class SystemTrayServiceTests(unittest.TestCase):
    def test_menu_style_sheet_uses_light_theme_tokens(self):
        window = SimpleNamespace(effective_theme_name=lambda: "light", config=SimpleNamespace(theme_mode="light"))
        service = SystemTrayService(window, icon=None)

        style = service._menu_style_sheet()

        self.assertIn("background:#fbfbfc;", style)
        self.assertIn("color:#1f2937;", style)
        self.assertIn("border:1px solid #d8dde4;", style)
        self.assertIn("QMenu::item:selected", style)

    def test_menu_style_sheet_uses_dark_theme_tokens(self):
        window = SimpleNamespace(effective_theme_name=lambda: "dark", config=SimpleNamespace(theme_mode="dark"))
        service = SystemTrayService(window, icon=None)

        style = service._menu_style_sheet()

        self.assertIn("background:#1b1e24;", style)
        self.assertIn("color:#d6dbe3;", style)
        self.assertIn("border:1px solid #2f343d;", style)
        self.assertIn("QMenu::item:disabled", style)

    def test_show_message_suppresses_duplicate_messages_within_short_window(self):
        tray = SimpleNamespace(showMessage=Mock())
        window = SimpleNamespace(
            tr=lambda key, **kwargs: "OCR Translator" if key == "tray_title" else key,
            effective_theme_name=lambda: "dark",
            config=SimpleNamespace(theme_mode="dark"),
        )
        service = SystemTrayService(window, icon=None)
        service.tray = tray

        self.assertTrue(service.show_message("Request submitted"))
        self.assertFalse(service.show_message("Request submitted"))

        service._last_message_at = time.monotonic() - 2.0

        self.assertTrue(service.show_message("Request submitted"))
        self.assertEqual(tray.showMessage.call_count, 2)

    def test_show_message_returns_false_without_tray_or_empty_text(self):
        service = SystemTrayService(SimpleNamespace(tr=lambda key, **kwargs: key), icon=None)
        self.assertFalse(service.show_message(""))


if __name__ == "__main__":
    unittest.main()
