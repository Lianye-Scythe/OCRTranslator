import unittest

from app.ui.style_utils import load_style_sheet


class StyleSheetTests(unittest.TestCase):
    def test_main_window_single_line_inputs_use_distinct_dark_selection_colors(self):
        style = load_style_sheet("main_window.qss", theme_name="dark")

        self.assertIn("QLineEdit,", style)
        self.assertIn("selection-background-color:#41516A;", style)
        self.assertIn("selection-color:#F3F6FA;", style)

    def test_main_window_single_line_inputs_use_distinct_light_selection_colors(self):
        style = load_style_sheet("main_window.qss", theme_name="light")

        self.assertIn("QLineEdit,", style)
        self.assertIn("selection-background-color:#dbe7f6;", style)
        self.assertIn("selection-color:#0f172a;", style)

    def test_message_box_tone_styles_are_present(self):
        style = load_style_sheet("main_window.qss", theme_name="dark")

        self.assertIn('QMessageBox[messageBox="true"][messageBoxTone="information"] QLabel#qt_msgboxex_icon_label', style)
        self.assertIn('QMessageBox[messageBox="true"][messageBoxTone="destructive"] QLabel#qt_msgboxex_icon_label', style)

    def test_api_keys_multiline_editor_uses_single_surface_focus_treatment(self):
        style = load_style_sheet("main_window.qss", theme_name="dark")

        self.assertIn('#InlinePanel[panelRole="apiKeys"] {', style)
        self.assertIn('#MultiLineFieldSurface[focused="true"] {', style)
        self.assertIn('QPlainTextEdit#FramelessFieldEditor {', style)
        self.assertIn('QPlainTextEdit#FramelessFieldEditor:focus {', style)
        self.assertIn('border:none;', style)
        self.assertIn('selection-background-color:#41516A;', style)
        self.assertIn('selection-color:#F3F6FA;', style)

    def test_multiline_editor_selection_colors_are_more_distinct_in_light_theme(self):
        style = load_style_sheet("main_window.qss", theme_name="light")

        self.assertIn('QPlainTextEdit#FramelessFieldEditor {', style)
        self.assertIn('selection-background-color:#dbe7f6;', style)
        self.assertIn('selection-color:#0f172a;', style)

    def test_translation_overlay_pin_toggle_matches_action_corner_radius(self):
        style = load_style_sheet("translation_overlay.qss", theme_name="light")

        self.assertIn('#overlayActionButton[pinToggle="true"] {', style)
        self.assertIn('border-radius:10px;', style)
        self.assertIn('background:#f5f5f7;', style)
