import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QPoint, QRect

from app.services.overlay_presenter import OverlayPresenter


class _FakeBody:
    def __init__(self):
        self._text = ""

    def toPlainText(self):
        return self._text

    def setPlainText(self, text):
        self._text = str(text)

    def setMarkdown(self, text):
        self._text = str(text)


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
        self._visible = True
        self._geometry = QRect(self.last_geometry)
        self.minimum_runtime_width = None
        self.body = _FakeBody()
        self._has_partial_result = False
        self.prime_first_show_calls = 0

    def apply_typography(self):
        return None

    def calculate_size(self, _text, *, base_width=None, preset_name=None, partial_state=None):
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
        actual_width = int(width)
        if self.minimum_runtime_width is not None:
            actual_width = max(actual_width, int(self.minimum_runtime_width))
        self._visible = True
        self._geometry = QRect(int(x), int(y), actual_width, int(height))
        self.last_geometry = QRect(self._geometry)

    def setGeometry(self, rect):
        actual_width = int(rect.width())
        if self.minimum_runtime_width is not None:
            actual_width = max(actual_width, int(self.minimum_runtime_width))
        self._geometry = QRect(int(rect.x()), int(rect.y()), actual_width, int(rect.height()))

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

    def measure_content_height(self, text, width, *, render_markdown=True):
        return 400

    def geometry(self):
        return QRect(self._geometry)

    def frameGeometry(self):
        return QRect(self._geometry)

    def isVisible(self):
        return self._visible

    def prime_first_show(self):
        self.prime_first_show_calls += 1
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
            current_overlay_font_size=lambda: 12,
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

    def test_show_response_primes_partial_state_before_first_partial_size_measurement(self):
        window = self._build_window()
        overlay = _FakeOverlay()
        overlay.is_pinned = False
        overlay.manual_positioned = False
        overlay._visible = False

        def _calculate_size(_text, *, base_width=None, preset_name=None, partial_state=None):
            self.assertEqual(overlay.partial_state_calls, [("streaming", "Translate")])
            self.assertEqual(partial_state, "streaming")
            return ((base_width if base_width is not None else 440), 520)

        overlay.calculate_size = Mock(side_effect=_calculate_size)
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_response(
            "partial",
            bbox=(604, 16, 1321, 1024),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=False,
            partial=True,
        )
        overlay.calculate_size.assert_called_once()

    def test_show_response_primes_overlay_native_window_before_first_visible_render(self):
        window = self._build_window()
        overlay = _FakeOverlay()
        overlay.is_pinned = False
        overlay.manual_positioned = False
        overlay._visible = False
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_response(
            "partial",
            bbox=(604, 16, 1321, 1024),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=False,
            partial=True,
        )
        self.assertEqual(overlay.prime_first_show_calls, 1)

    @patch("app.services.overlay_presenter.preferred_overlay_width_for_bbox", return_value=565)
    @patch("app.services.overlay_presenter.compute_overlay_position", return_value=(18, 42))
    @patch("app.services.overlay_presenter.fit_overlay_size", return_value=(565, 520))
    def test_show_response_first_visible_partial_seeds_base_width_from_available_bbox_space(self, _mock_fit_size, _mock_position, _mock_preferred_width):
        window = self._build_window()
        overlay = _FakeOverlay()
        overlay.is_pinned = False
        overlay.manual_positioned = False
        overlay._visible = False

        def _calculate_size(_text, *, base_width=None, preset_name=None, partial_state=None):
            self.assertEqual(base_width, 565)
            self.assertEqual(partial_state, "streaming")
            return (565, 520)

        overlay.calculate_size = Mock(side_effect=_calculate_size)
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_response(
            "partial",
            bbox=(601, 12, 1318, 1024),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=False,
            partial=True,
        )
        overlay.calculate_size.assert_called_once()

    @patch("app.services.overlay_presenter.QTimer.singleShot", side_effect=lambda _ms, callback: callback())
    @patch("app.services.overlay_presenter.compute_overlay_position", return_value=(1162, 212))
    @patch("app.services.overlay_presenter.fit_overlay_size", return_value=(320, 300))
    def test_show_translation_logs_bbox_diagnostics_for_first_visible_capture_overlay(self, _mock_fit_size, _mock_position, _mock_timer):
        window = self._build_window()
        window.log = Mock()
        overlay = _FakeOverlay()
        overlay.is_pinned = False
        overlay.manual_positioned = False
        overlay._visible = False
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_translation(
            (1500, 200, 1800, 500),
            "captured text",
            preset_name="Translate",
            preserve_geometry=False,
        )

        diagnostic_messages = [
            call.args[0]
            for call in window.log.call_args_list
            if call.args and isinstance(call.args[0], str) and call.args[0].startswith("浮窗定位诊断｜")
        ]
        self.assertEqual(len(diagnostic_messages), 2)
        self.assertIn("stage=immediate", diagnostic_messages[0])
        self.assertIn("phase=first_visible_final", diagnostic_messages[0])
        self.assertIn("initial_planned=1162,212,320x300", diagnostic_messages[0])
        self.assertIn("planned=1162,212,320x300", diagnostic_messages[0])
        self.assertIn("geom=1162,212,320x300", diagnostic_messages[0])
        self.assertIn("planned_overlap=none", diagnostic_messages[0])
        self.assertIn("stage=deferred", diagnostic_messages[1])

    @patch("app.services.overlay_presenter.QTimer.singleShot", side_effect=lambda _ms, callback: callback())
    @patch("app.services.overlay_presenter.compute_overlay_position", return_value=(1120, 212))
    @patch("app.services.overlay_presenter.fit_overlay_size", return_value=(360, 320))
    def test_adjust_font_size_logs_bbox_diagnostics_for_reflow(self, _mock_fit_size, _mock_position, _mock_timer):
        window = self._build_window()
        window.log = Mock()
        overlay = _FakeOverlay()
        overlay.is_pinned = False
        overlay.manual_positioned = False
        overlay.last_bbox = (1500, 200, 1800, 500)
        overlay.last_text = "captured text"
        overlay.last_preset_name = "Translate"
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.adjust_font_size(1)

        diagnostic_messages = [
            call.args[0]
            for call in window.log.call_args_list
            if call.args and isinstance(call.args[0], str) and call.args[0].startswith("浮窗定位诊断｜")
        ]
        self.assertEqual(len(diagnostic_messages), 2)
        self.assertIn("stage=immediate", diagnostic_messages[0])
        self.assertIn("phase=reflow", diagnostic_messages[0])
        self.assertIn("initial_planned=1120,212,360x320", diagnostic_messages[0])
        self.assertIn("planned=1120,212,360x320", diagnostic_messages[0])
        self.assertIn("stage=deferred", diagnostic_messages[1])

    @patch("app.services.overlay_presenter.QTimer.singleShot", side_effect=lambda _ms, callback: callback())
    @patch("app.services.overlay_presenter.compute_overlay_position")
    @patch("app.services.overlay_presenter.fit_overlay_size", return_value=(440, 520))
    def test_show_response_repositions_capture_overlay_when_runtime_geometry_expands_beyond_planned_width(self, _mock_fit_size, mock_compute_position, _mock_timer):
        mock_compute_position.side_effect = lambda _config, _bbox, width, _height: (146, 42) if int(width) == 440 else (18, 42)
        window = self._build_window()
        window.log = Mock()
        overlay = _FakeOverlay()
        overlay.is_pinned = False
        overlay.manual_positioned = False
        overlay._visible = False
        overlay.minimum_runtime_width = 570
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)
        window.learn_runtime_auto_unpinned_overlay_width = Mock(return_value=True)

        presenter.show_response(
            "partial",
            bbox=(604, 16, 1321, 1024),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=False,
            partial=True,
        )

        self.assertEqual(len(overlay.show_calls), 1)
        self.assertEqual(overlay.show_calls[0]["x"], 18)
        self.assertEqual(overlay.show_calls[0]["width"], 570)
        diagnostic_messages = [
            call.args[0]
            for call in window.log.call_args_list
            if call.args and isinstance(call.args[0], str) and call.args[0].startswith("浮窗定位诊断｜")
        ]
        self.assertEqual(len(diagnostic_messages), 2)
        self.assertIn("initial_planned=146,42,440x520", diagnostic_messages[0])
        self.assertIn("corrected=18,42,570x520", diagnostic_messages[0])
        window.learn_runtime_auto_unpinned_overlay_width.assert_called_once_with(570)

    @patch("app.services.overlay_presenter.get_target_screen_rect", return_value=QRect(0, 0, 1920, 1080))
    @patch("app.services.overlay_presenter.clamp_overlay_size_to_screen", return_value=(500, 420))
    def test_show_response_partial_stream_update_keeps_current_x_and_width_while_growing_height(self, _mock_clamp_size, _mock_screen_rect):
        window = self._build_window()
        overlay = _FakeOverlay()
        overlay.is_pinned = False
        overlay.manual_positioned = False
        overlay._visible = True
        overlay._has_partial_result = True
        overlay.calculate_size = Mock(side_effect=AssertionError("calculate_size should not run for continuing partial stream updates"))
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_response(
            "partial growing text",
            bbox=(604, 16, 1321, 1024),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=False,
            partial=True,
        )

        self.assertEqual(len(overlay.show_calls), 1)
        self.assertEqual(overlay.show_calls[0]["x"], 120)
        self.assertEqual(overlay.show_calls[0]["width"], 500)
        self.assertEqual(overlay.show_calls[0]["height"], 420)

    @patch("app.services.overlay_presenter.get_target_screen_rect", return_value=QRect(0, 0, 1920, 1080))
    @patch("app.services.overlay_presenter.clamp_overlay_size_to_screen", return_value=(500, 420))
    def test_show_response_partial_stream_update_freezes_geometry_when_more_growth_would_require_vertical_reposition(self, _mock_clamp_size, _mock_screen_rect):
        window = self._build_window()
        overlay = _FakeOverlay()
        overlay.is_pinned = False
        overlay.manual_positioned = False
        overlay._visible = True
        overlay._has_partial_result = True
        overlay._geometry = QRect(120, 650, 500, 360)
        overlay.last_geometry = QRect(overlay._geometry)
        overlay.calculate_size = Mock(side_effect=AssertionError("calculate_size should not run for continuing partial stream updates"))
        window.translation_overlay = overlay
        presenter = OverlayPresenter(window)

        presenter.show_response(
            "partial near bottom",
            bbox=(604, 16, 1321, 1024),
            preset_name="Translate",
            preserve_manual_position=False,
            preserve_geometry=False,
            partial=True,
        )

        self.assertEqual(len(overlay.show_calls), 1)
        self.assertEqual(overlay.show_calls[0]["x"], 120)
        self.assertEqual(overlay.show_calls[0]["y"], 650)
        self.assertEqual(overlay.show_calls[0]["width"], 500)
        self.assertEqual(overlay.show_calls[0]["height"], 360)


if __name__ == "__main__":
    unittest.main()
