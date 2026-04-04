import unittest

from app.ui.theme_tokens import theme_colors


class ThemeTokenTests(unittest.TestCase):
    def test_light_theme_focus_tokens_follow_primary_focus(self):
        colors = theme_colors("light")

        self.assertEqual(colors["accent_focus"], "#94a3b8")
        self.assertEqual(colors["nav_focus_border"], "#94a3b8")
        self.assertEqual(colors["field_focus_border"], "#94a3b8")
        self.assertEqual(colors["overlay_focus_border"], "#94a3b8")

    def test_dark_theme_focus_tokens_follow_primary_focus(self):
        colors = theme_colors("dark")

        self.assertEqual(colors["accent_focus"], "#8B92A0")
        self.assertEqual(colors["nav_focus_border"], "#8B92A0")
        self.assertEqual(colors["field_focus_border"], "#8B92A0")
        self.assertEqual(colors["overlay_focus_border"], "#8B92A0")
