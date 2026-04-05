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

    def apply_typography(self):
        return None

    def calculate_size(self, _text):
        return (860, 900)

    def show_text(self, text, x, y, width, height, *, keep_manual_position=False):
        self.show_calls.append(
            {
                "text": text,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "keep_manual_position": keep_manual_position,
            }
        )

    def remember_context(self, bbox, text, *, anchor_point=None, preset_name=""):
        self.context_calls.append(
            {
                "bbox": bbox,
                "text": text,
                "anchor_point": anchor_point,
                "preset_name": preset_name,
            }
        )

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
            note_runtime_preference_changed=Mock(),
        )

    @patch("app.services.overlay_presenter.clamp_rect_to_visible_screen", side_effect=lambda rect: QRect(rect))
    def test_show_response_preserves_existing_geometry_when_requested(self, _mock_clamp_rect):
        window = self._build_window()
        overlay = _FakeOverlay()
        presenter = OverlayPresenter(window, overlay)

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
            },
        )
        self.assertEqual(overlay.context_calls[-1]["anchor_point"], QPoint(30, 40))
        window.set_status.assert_called_once_with("translated")
        window.log_tr.assert_called_once_with("log_request_finished", preset="Translate")

    @patch("app.services.overlay_presenter.clamp_rect_to_visible_screen", side_effect=lambda rect: QRect(rect))
    def test_show_translation_keeps_pinned_geometry_for_capture_results(self, _mock_clamp_rect):
        window = self._build_window()
        overlay = _FakeOverlay()
        presenter = OverlayPresenter(window, overlay)

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
        presenter = OverlayPresenter(window, overlay)

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
            },
        )


if __name__ == "__main__":
    unittest.main()
