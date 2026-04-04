import unittest
from types import SimpleNamespace

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


if __name__ == "__main__":
    unittest.main()
