import unittest
from unittest.mock import patch

from PySide6.QtCore import QPoint, QRect

from app.ui.overlay_positioning import (
    clamp_rect_to_visible_screen,
    clamp_overlay_size_to_screen,
    compute_overlay_position,
    compute_overlay_position_for_point,
    fit_overlay_size,
)


class _FakeOverlay:
    def measure_content_height(self, text: str, width: int, *, render_markdown: bool = True) -> int:
        return 480 if text else 220


class _FakeConfig:
    def __init__(self, *, mode: str = "book_lr", margin: int = 18, overlay_width: int = 440, overlay_height: int = 520):
        self.mode = mode
        self.margin = margin
        self.overlay_width = overlay_width
        self.overlay_height = overlay_height


class OverlayPositioningTests(unittest.TestCase):
    def test_clamp_overlay_size_respects_screen_bounds_and_content_height(self):
        config = _FakeConfig(margin=18)
        overlay = _FakeOverlay()
        screen_rect = QRect(0, 0, 1280, 720)

        width, height = clamp_overlay_size_to_screen(config, overlay, screen_rect, "translated text", 2000, 1200)

        self.assertEqual(width, 1244)
        self.assertEqual(height, 654)

    def test_clamp_overlay_size_uses_configurable_bottom_safe_margin(self):
        config = _FakeConfig(margin=18)
        config.overlay_auto_expand_top_margin = 42
        config.overlay_auto_expand_bottom_margin = 60
        overlay = _FakeOverlay()
        screen_rect = QRect(0, 0, 1280, 720)

        width, height = clamp_overlay_size_to_screen(config, overlay, screen_rect, "translated text", 900, 1200)

        self.assertEqual(width, 900)
        self.assertEqual(height, 618)

    @patch("app.ui.overlay_positioning.get_target_screen_rect", return_value=QRect(0, 0, 1920, 1080))
    def test_fit_overlay_size_prefers_available_side_space_for_book_mode(self, _mock_screen_rect):
        config = _FakeConfig(mode="book_lr", margin=18)
        overlay = _FakeOverlay()

        width, height = fit_overlay_size(config, overlay, (1500, 200, 1800, 800), "translated text", 1600, 500)

        self.assertEqual(width, 1464)
        self.assertEqual(height, 500)

    @patch("app.ui.overlay_positioning.get_target_screen_rect", return_value=QRect(0, 0, 1920, 1080))
    def test_compute_overlay_position_prefers_left_side_for_right_page_content(self, _mock_screen_rect):
        config = _FakeConfig(mode="book_lr", margin=18)

        x, y = compute_overlay_position(config, (1500, 200, 1800, 500), 320, 300)

        self.assertEqual(x, 1162)
        self.assertEqual(y, 212)

    @patch("app.ui.overlay_positioning.get_screen_rect_for_point", return_value=QRect(0, 0, 1920, 1080))
    def test_compute_overlay_position_for_point_falls_back_above_anchor_when_needed(self, _mock_screen_rect):
        config = _FakeConfig(margin=18)
        anchor_point = QPoint(960, 1050)

        x, y = compute_overlay_position_for_point(config, anchor_point, 300, 200)

        self.assertEqual(x, 810)
        self.assertEqual(y, 832)

    @patch("app.ui.overlay_positioning.get_screen_rect_for_point", return_value=QRect(0, 0, 1920, 1080))
    def test_clamp_rect_to_visible_screen_moves_offscreen_overlay_back_into_view(self, _mock_screen_rect):
        rect = QRect(2500, 1200, 600, 400)

        clamped = clamp_rect_to_visible_screen(rect)

        self.assertEqual(clamped, QRect(1320, 680, 600, 400))


if __name__ == "__main__":
    unittest.main()
