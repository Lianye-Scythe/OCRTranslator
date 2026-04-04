import unittest

from app.ui.style_utils import load_style_sheet


class StyleSheetTests(unittest.TestCase):
    def test_main_window_inputs_define_selection_foreground(self):
        style = load_style_sheet("main_window.qss", theme_name="dark")

        self.assertIn("selection-background-color:#2A2D35;", style)
        self.assertIn("selection-color:#D1D5DB;", style)

    def test_message_box_tone_styles_are_present(self):
        style = load_style_sheet("main_window.qss", theme_name="dark")

        self.assertIn('QMessageBox[messageBox="true"][messageBoxTone="information"] QLabel#qt_msgboxex_icon_label', style)
        self.assertIn('QMessageBox[messageBox="true"][messageBoxTone="destructive"] QLabel#qt_msgboxex_icon_label', style)

    def test_translation_overlay_pin_toggle_matches_action_corner_radius(self):
        style = load_style_sheet("translation_overlay.qss", theme_name="light")

        self.assertIn('#overlayActionButton[pinToggle="true"] {', style)
        self.assertIn('border-radius:10px;', style)
        self.assertIn('background:#f5f5f7;', style)
