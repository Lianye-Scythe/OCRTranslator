import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QPoint, QRect

from app.services.overlay_presenter import OverlayPresenter


class _FakeOverlay:
    def __init__(self):
        self.last_geometry = QRect(120, 140, 500, 360)
        self.last_bbox = None
        self.last_anchor_point = None
        self.last_preset_name = ""
        self.last_text = "previous"
        self.manual_positioned = True
        self.is_pinned = True
        self.show_calls = []
        self.context_calls = []
        self.partial_state_calls = []
        self._has_partial_result = False

    def apply_typography(self):
        return None

    def calculate_size(self, _text, *, base_width=None):
        return ((base_width if base_width is not None else 860), 900)

    def show_text(self, text, x, y, width, height, *, keep_manual_position=False, remember_state=True):
        self.show_calls.append(
            {
                "text": text,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "keep_manual_position": keep_manual_position,
                "remember_state": remember_state,
            }
        )
        self._has_partial_result = not remember_state

    def remember_context(self, bbox, text, *, anchor_point=None, preset_name=""):
        self.context_calls.append(
            {
                "bbox": bbox,
                "text": text,
                "anchor_point": anchor_point,
                "preset_name": preset_name,
            }
        )

    def has_partial_result(self):
        return self._has_partial_result

    def set_partial_result_state(self, state, *, preset_name=None):
        self.partial_state_calls.append((state, preset_name))
        self._has_partial_result = bool(state)

    def measure_content_height(self, text, width):
        return 400

    def isVisible(self):
        return True


class OverlayPresenterTests(unittest.TestCase):
    def _build_window(self):
        return SimpleNamespace(
            current_mode=lambda: "book_lr",
            current_margin=lambda: 18,
            current_overlay_auto_expand_top_margin=lambda: 42,
            current_overlay_auto_expand_bottom_margin=lambda: 24,
            current_overlay_width=lambda: 440,
            current_overlay_height=lambda: 520,
            tr=lambda key, **kwargs: key,
            finish_capture_workflow=Mock(),
            restore_pinned_overlay_after_capture=True,
            set_status=Mock(),
            log_tr=Mock(),
            translation_in_progress=False,
            config=SimpleNamespace(overlay_font_size=12),
            _suppress_form_tracking=False,
            overlay_font_size_spin=SimpleNamespace(setValue=Mock()),
            toast_service=SimpleNamespace(hide_message=Mock()),
            note_runtime_preference_changed=Mock(),
        )

    @patch("app.services.overlay_presenter.clamp_rect_to_visible_screen", side_effect=lambda rect: QRect(rect))
    def test_show_response_preserves_existing_geometry_when_requested(self, _mock_clamp_rect):
        window = self._build_window()
        overlay = _FakeOverlay()
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_response(
            "new text",
            anchor_point=QPoint(30, 40),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=True,
        )

        self.assertEqual(
            overlay.show_calls[-1],
            {
                "text": "new text",
                "x": 120,
                "y": 140,
                "width": 500,
                "height": 360,
                "keep_manual_position": True,
                "remember_state": True,
            },
        )
        self.assertEqual(overlay.context_calls[-1]["anchor_point"], QPoint(30, 40))
        window.set_status.assert_called_once_with("translated")
        window.log_tr.assert_called_once_with("log_request_finished", preset="Translate")
        window.toast_service.hide_message.assert_called_once_with()

    @patch("app.services.overlay_presenter.clamp_rect_to_visible_screen", side_effect=lambda rect: QRect(rect))
    def test_show_translation_keeps_pinned_geometry_for_capture_results(self, _mock_clamp_rect):
        window = self._build_window()
        overlay = _FakeOverlay()
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_translation(
            (10, 20, 110, 120),
            "captured text",
            preset_name="Translate",
            preserve_geometry=True,
        )

        self.assertEqual(overlay.show_calls[-1]["x"], 120)
        self.assertEqual(overlay.show_calls[-1]["y"], 140)
        self.assertEqual(overlay.show_calls[-1]["width"], 500)
        self.assertEqual(overlay.show_calls[-1]["height"], 360)
        window.finish_capture_workflow.assert_called_once_with()
        self.assertFalse(window.restore_pinned_overlay_after_capture)

    @patch("app.services.overlay_presenter.clamp_rect_to_visible_screen", side_effect=lambda rect: QRect(rect))
    def test_show_response_uses_overlay_resolved_geometry_when_runtime_last_geometry_is_missing(self, _mock_clamp_rect):
        window = self._build_window()
        overlay = _FakeOverlay()
        overlay.last_geometry = None
        overlay.manual_positioned = False
        overlay.resolved_pinned_geometry = lambda: QRect(210, 180, 460, 330)
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_response(
            "restored text",
            anchor_point=QPoint(50, 60),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=True,
        )

        self.assertEqual(
            overlay.show_calls[-1],
            {
                "text": "restored text",
                "x": 210,
                "y": 180,
                "width": 460,
                "height": 330,
                "keep_manual_position": False,
                "remember_state": True,
            },
        )

    def test_show_response_prefers_runtime_request_width_override_when_not_pinned(self):
        window = self._build_window()
        window.current_request_overlay_width = lambda: 420
        overlay = _FakeOverlay()
        overlay.is_pinned = False
        overlay.manual_positioned = False
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_response(
            "manual width",
            anchor_point=QPoint(80, 90),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=False,
        )

        self.assertEqual(overlay.show_calls[-1]["width"], 420)

    def test_show_response_can_lock_width_for_streaming_updates(self):
        window = self._build_window()
        overlay = _FakeOverlay()
        overlay.is_pinned = False
        overlay.manual_positioned = False
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_response(
            "stream text",
            anchor_point=QPoint(80, 90),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=False,
            locked_width=420,
        )

        self.assertEqual(overlay.show_calls[-1]["width"], 420)
        self.assertEqual(overlay.context_calls[-1]["preset_name"], "Translate")

    @patch("app.services.overlay_presenter.clamp_rect_to_visible_screen", side_effect=lambda rect: QRect(rect))
    def test_show_response_partial_update_does_not_replace_persisted_context_or_finish_state(self, _mock_clamp_rect):
        window = self._build_window()
        overlay = _FakeOverlay()
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_response(
            "partial",
            anchor_point=QPoint(70, 80),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=False,
            partial=True,
        )

        self.assertEqual(overlay.partial_state_calls, [("streaming", "Translate")])
        self.assertEqual(overlay.show_calls[-1]["text"], "partial")
        self.assertFalse(overlay.show_calls[-1]["remember_state"])
        self.assertEqual(overlay.context_calls, [])
        self.assertTrue(overlay.has_partial_result())
        window.set_status.assert_not_called()
        window.log_tr.assert_not_called()
        window.finish_capture_workflow.assert_not_called()
        window.toast_service.hide_message.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
