import unittest
from unittest.mock import call, patch

from PySide6.QtWidgets import QApplication

from app.models import AppConfig
from app.ui.translation_overlay import TranslationOverlay


class _FakeAppWindow:
    def __init__(self):
        self.config = AppConfig(overlay_opacity=35)
        self.runtime_pref_change_count = 0
        self.runtime_overlay_save_count = 0
        self.status_calls = []

    def tr(self, key, **kwargs):
        translations = {
            "overlay_title": "结果",
            "copy_response": "复制",
            "overlay_partial_streaming": "流式接收中…",
            "overlay_partial_cancelled": "部分结果（已取消）",
            "overlay_partial_failed": "部分结果（请求失败）",
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

    def persist_runtime_overlay_state(self):
        self.runtime_overlay_save_count += 1

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

    def test_toggle_pin_persists_current_geometry_without_marking_unsaved_preferences(self):
        self.overlay.setGeometry(120, 140, 500, 360)

        self.overlay.toggle_pin(True)

        self.assertTrue(self.window.config.overlay_pinned)
        self.assertEqual(self.window.config.overlay_pinned_x, 120)
        self.assertEqual(self.window.config.overlay_pinned_y, 140)
        self.assertEqual(self.window.config.overlay_pinned_width, 500)
        self.assertEqual(self.window.config.overlay_pinned_height, 360)
        self.assertEqual(self.window.runtime_overlay_save_count, 1)
        self.assertEqual(self.window.runtime_pref_change_count, 0)

    def test_sync_last_geometry_from_saved_pinned_geometry_restores_runtime_rect(self):
        self.window.config.overlay_pinned = True
        self.window.config.overlay_pinned_x = 210
        self.window.config.overlay_pinned_y = 180
        self.window.config.overlay_pinned_width = 460
        self.window.config.overlay_pinned_height = 330

        restored = TranslationOverlay(self.window)
        self.addCleanup(lambda: (restored.close(), restored.deleteLater(), self.app.processEvents()))

        self.assertIsNotNone(restored.last_geometry)
        self.assertEqual(restored.last_geometry.getRect(), (210, 180, 460, 330))

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

    def test_calculate_size_accounts_for_header_width_for_partial_title(self):
        title_text = self.overlay._title_text_for_state(preset_name="翻译 (Translate)", partial_state="streaming")
        header_width = self.overlay._measure_header_width(title_text)

        width, _height = self.overlay.calculate_size(
            "短文本",
            base_width=440,
            preset_name="翻译 (Translate)",
            partial_state="streaming",
        )

        self.assertGreaterEqual(width, header_width)

    def test_partial_result_title_uses_streaming_and_interrupted_labels(self):
        self.overlay.set_partial_result_state("streaming", preset_name="翻译")
        self.assertEqual(self.overlay.title_label.text(), "结果 · 翻译 · 流式接收中…")

        self.overlay.set_partial_result_state("failed")
        self.assertEqual(self.overlay.title_label.text(), "结果 · 翻译 · 部分结果（请求失败）")

        self.overlay.set_partial_result_state("cancelled")
        self.assertEqual(self.overlay.title_label.text(), "结果 · 翻译 · 部分结果（已取消）")

    def test_copy_text_uses_visible_partial_content_when_partial_result_is_active(self):
        self.overlay.last_text = "old persisted result"
        self.overlay.set_partial_result_state("streaming", preset_name="翻译")
        self.overlay.body.setPlainText("partial text")

        self.overlay.copy_text()

        self.assertEqual(QApplication.clipboard().text(), "partial text")
        self.assertEqual(self.window.status_calls[-1], ("overlay_copied", {}))

    def test_prime_first_show_warms_native_window_once_without_leaving_overlay_visible(self):
        self.overlay.hide()

        with patch.object(self.overlay, "show", wraps=self.overlay.show) as mock_show, patch.object(self.overlay, "hide", wraps=self.overlay.hide) as mock_hide:
            self.assertTrue(self.overlay.prime_first_show())

        self.assertFalse(self.overlay.isVisible())
        self.assertTrue(self.overlay._first_show_primed)
        mock_show.assert_called_once_with()
        mock_hide.assert_called_once_with()

        with patch.object(self.overlay, "show") as mock_show_again, patch.object(self.overlay, "hide") as mock_hide_again:
            self.assertFalse(self.overlay.prime_first_show())

        mock_show_again.assert_not_called()
        mock_hide_again.assert_not_called()

    def test_show_text_partial_visible_update_skips_refresh_and_raise_when_overlay_is_already_visible(self):
        self.overlay.set_partial_result_state("streaming", preset_name="翻译")

        with patch.object(self.overlay, "isVisible", return_value=True), patch.object(self.overlay, "refresh_language") as mock_refresh, patch.object(self.overlay, "_show_as_topmost") as mock_show_topmost, patch.object(
            self.overlay, "_sync_topbar_hover_state"
        ) as mock_sync_hover:
            self.overlay.show_text("partial text", 120, 140, 500, 360, remember_state=False)

        mock_refresh.assert_not_called()
        mock_show_topmost.assert_not_called()
        mock_sync_hover.assert_not_called()

    def test_show_text_partial_visible_update_skips_redundant_geometry_and_text_work_when_unchanged(self):
        self.overlay.set_partial_result_state("streaming", preset_name="翻译")
        self.overlay.setGeometry(120, 140, 500, 360)
        self.overlay.body.setPlainText("partial text")

        with patch.object(self.overlay, "isVisible", return_value=True), patch.object(self.overlay, "setGeometry") as mock_set_geometry, patch.object(
            self.overlay.body, "setPlainText"
        ) as mock_set_plain_text, patch.object(self.overlay, "_show_as_topmost") as mock_show_topmost:
            self.overlay.show_text("partial text", 120, 140, 500, 360, remember_state=False)

        mock_set_geometry.assert_not_called()
        mock_set_plain_text.assert_not_called()
        mock_show_topmost.assert_not_called()

    def test_show_text_partial_visible_update_appends_incremental_suffix_without_replacing_full_text(self):
        self.overlay.set_partial_result_state("streaming", preset_name="翻译")
        self.overlay.setGeometry(120, 140, 500, 360)
        self.overlay.body.setPlainText("Hello")

        with patch.object(self.overlay, "isVisible", return_value=True), patch.object(self.overlay.body, "setPlainText") as mock_set_plain_text:
            self.overlay.show_text("Hello world", 120, 140, 500, 360, remember_state=False)

        mock_set_plain_text.assert_not_called()
        self.assertEqual(self.overlay.body.toPlainText(), "Hello world")

    def test_show_text_partial_visible_update_falls_back_to_full_replace_when_stream_text_is_not_prefix_append(self):
        self.overlay.set_partial_result_state("streaming", preset_name="翻译")
        self.overlay.setGeometry(120, 140, 500, 360)
        self.overlay.body.setPlainText("Hello")

        self.overlay.show_text("Hi", 120, 140, 500, 360, remember_state=False)

        self.assertEqual(self.overlay.body.toPlainText(), "Hi")