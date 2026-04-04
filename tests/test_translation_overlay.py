import unittest
from unittest.mock import call, patch

from PySide6.QtWidgets import QApplication

from app.models import AppConfig
from app.ui.translation_overlay import TranslationOverlay


class _FakeAppWindow:
    def __init__(self):
        self.config = AppConfig(overlay_opacity=35)
        self.runtime_pref_change_count = 0
        self.status_calls = []

    def tr(self, key, **kwargs):
        translations = {
            "overlay_title": "结果",
            "copy_response": "复制",
            "toggle_overlay_pin": "切换是否保留浮窗",
            "decrease_overlay_opacity": "降低浮窗透明度",
            "increase_overlay_opacity": "提高浮窗透明度",
            "overlay_pinned_short": "已固定",
            "overlay_pin_short": "Pin",
            "overlay_opacity_set": "浮窗透明度已调整为 {value}%",
        }
        text = translations.get(key, key)
        return text.format(**kwargs) if kwargs else text

    def effective_theme_name(self):
        return "light"

    def current_overlay_font_family(self):
        return self.config.overlay_font_family

    def current_overlay_font_size(self):
        return self.config.overlay_font_size

    def current_overlay_width(self):
        return self.config.overlay_width

    def current_overlay_height(self):
        return self.config.overlay_height

    def note_runtime_preference_changed(self):
        self.runtime_pref_change_count += 1

    def set_status(self, key, **kwargs):
        self.status_calls.append((key, kwargs))


class TranslationOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = _FakeAppWindow()
        self.overlay = TranslationOverlay(self.window)

    def tearDown(self):
        self.overlay.close()
        self.overlay.deleteLater()
        self.app.processEvents()

    def test_surface_opacity_keeps_window_fully_opaque(self):
        self.window.config.overlay_opacity = 35

        self.overlay.apply_surface_state()

        for button in (
            self.overlay.pin_button,
            self.overlay.opacity_down_button,
            self.overlay.opacity_up_button,
            self.overlay.copy_button,
            self.overlay.close_button,
        ):
            self.assertTrue(hasattr(button, "_mouse_click_focus_clear_filter"))

        self.assertEqual(self.overlay.windowOpacity(), 1.0)
        self.assertEqual(self.overlay.opacity_value_label.text(), "35%")
        self.assertEqual(self.overlay.pin_button.text(), "")
        self.assertTrue(self.overlay.pin_button.property("pinToggle"))
        self.assertFalse(self.overlay.pin_button.icon().isNull())
        self.assertEqual(self.overlay.pin_button.toolTip(), "切换是否保留浮窗")
        self.assertEqual(self.overlay.pin_button.accessibleName(), "Pin")
        self.assertTrue(self.overlay.opacity_down_button.isEnabled())
        self.assertTrue(self.overlay.opacity_up_button.isEnabled())

    def test_adjust_opacity_clamps_to_one_without_wrapping(self):
        self.window.config.overlay_opacity = 3

        self.overlay.adjust_opacity(-5)
        self.overlay.adjust_opacity(-5)

        self.assertEqual(self.window.config.overlay_opacity, 1)
        self.assertEqual(self.window.runtime_pref_change_count, 1)
        self.assertEqual(self.overlay.opacity_value_label.text(), "1%")
        self.assertFalse(self.overlay.opacity_down_button.isEnabled())
        self.assertTrue(self.overlay.opacity_up_button.isEnabled())

    def test_click_to_edit_opacity_chip_submits_manual_value(self):
        self.overlay.opacity_value_label.start_editing()
        self.overlay.opacity_value_label.setText("0")

        self.overlay.opacity_value_label._commit_value()

        self.assertEqual(self.window.config.overlay_opacity, 1)
        self.assertEqual(self.overlay.opacity_value_label.text(), "1%")
        self.assertEqual(self.window.status_calls[-1], ("overlay_opacity_set", {"value": 1}))

    def test_dynamic_styles_use_high_contrast_selection_and_full_topbar_hover(self):
        self.window.config.overlay_opacity = 35
        self.overlay.apply_surface_state()

        base_style = self.overlay.styleSheet()
        self.assertIn("selection-background-color:rgba(51, 65, 85, 255);", base_style)
        self.assertIn("selection-color:rgba(255, 255, 255, 255);", base_style)
        self.assertIn("background:rgba(248, 250, 252, 89);", base_style)

        self.overlay._set_topbar_hovered(True)
        hover_style = self.overlay.styleSheet()

        self.assertIn("background:rgba(248, 250, 252, 255);", hover_style)

    def test_clear_initial_focus_removes_focus_from_topbar_actions(self):
        with patch("app.ui.translation_overlay.clear_focus_if_alive") as mock_clear_focus:
            self.overlay._clear_initial_focus()

        mock_clear_focus.assert_has_calls(
            [
                call(self.overlay.pin_button),
                call(self.overlay.opacity_down_button),
                call(self.overlay.opacity_value_label),
                call(self.overlay.opacity_up_button),
                call(self.overlay.copy_button),
                call(self.overlay.close_button),
            ]
        )
        self.assertEqual(mock_clear_focus.call_count, 6)
