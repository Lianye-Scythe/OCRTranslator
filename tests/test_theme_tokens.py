import unittest

from app.ui.theme_tokens import theme_colors


class ThemeTokenTests(unittest.TestCase):
    def test_light_theme_focus_tokens_follow_primary_focus(self):
        colors = theme_colors("light")

        self.assertEqual(colors["accent_focus"], "#94a3b8")
        self.assertEqual(colors["nav_focus_border"], "#94a3b8")
        self.assertEqual(colors["field_focus_border"], "#94a3b8")
        self.assertEqual(colors["field_selection_bg"], "#dbe7f6")
        self.assertEqual(colors["field_selection_fg"], "#0f172a")
        self.assertEqual(colors["overlay_focus_border"], "#94a3b8")
        self.assertEqual(colors["hero_tonal_bg"], "#eef3f9")
        self.assertEqual(colors["hero_tonal_border"], "#a4b6ca")
        self.assertEqual(colors["hero_tonal_hover_bg"], "#e6edf6")
        self.assertEqual(colors["hero_tonal_hover_border"], "#8ea4bd")

    def test_dark_theme_focus_tokens_follow_primary_focus(self):
        colors = theme_colors("dark")

        self.assertEqual(colors["accent_focus"], "#8B92A0")
        self.assertEqual(colors["nav_focus_border"], "#8B92A0")
        self.assertEqual(colors["field_focus_border"], "#7D8CA3")
        self.assertEqual(colors["field_selection_bg"], "#41516A")
        self.assertEqual(colors["field_selection_fg"], "#F3F6FA")
        self.assertEqual(colors["overlay_focus_border"], "#8B92A0")
        self.assertEqual(colors["hero_tonal_bg"], "#1D1F25")
        self.assertEqual(colors["hero_tonal_border"], "#363A45")
        self.assertEqual(colors["hero_tonal_hover_bg"], "#262931")
