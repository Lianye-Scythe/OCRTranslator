from types import SimpleNamespace

from PySide6.QtGui import QCursor

from ..ui.overlay_positioning import (
    clamp_rect_to_visible_screen,
    clamp_overlay_size_to_screen,
    compute_overlay_position,
    compute_overlay_position_for_point,
    fit_overlay_size,
    overlay_vertical_safe_margins,
    get_screen_rect_for_point,
    get_target_screen_rect,
)


class OverlayPresenter:
    def __init__(self, window, overlay):
        self.window = window
        self.overlay = overlay

    def _overlay_config(self):
        return SimpleNamespace(
            mode=self.window.current_mode(),
            margin=self.window.current_margin(),
            overlay_auto_expand_top_margin=self.window.current_overlay_auto_expand_top_margin(),
            overlay_auto_expand_bottom_margin=self.window.current_overlay_auto_expand_bottom_margin(),
            overlay_width=self.window.current_overlay_width(),
            overlay_height=self.window.current_overlay_height(),
        )

    def _preserved_geometry(self, *, preserve_geometry: bool):
        if not preserve_geometry:
            return None
        geometry = self.overlay.resolved_pinned_geometry() if hasattr(self.overlay, "resolved_pinned_geometry") else getattr(self.overlay, "last_geometry", None)
        if geometry is None:
            return None
        geometry = clamp_rect_to_visible_screen(geometry)
        if geometry.width() <= 0 or geometry.height() <= 0:
            return None
        return geometry

    def show_response(
        self,
        text: str,
        *,
        bbox=None,
        anchor_point=None,
        preset_name: str = "",
        preserve_manual_position: bool = False,
        preserve_geometry: bool = False,
        reflow_only: bool = False,
        complete_capture_flow: bool = False,
    ):
        text = text or self.window.tr("empty_result")
        overlay_config = self._overlay_config()
        self.overlay.apply_typography()
        width, height = self.overlay.calculate_size(text)
        preserved_geometry = self._preserved_geometry(preserve_geometry=preserve_geometry)

        if preserved_geometry is not None:
            x = preserved_geometry.x()
            y = preserved_geometry.y()
            width = preserved_geometry.width()
            height = preserved_geometry.height()
        elif bbox is not None:
            width, height = fit_overlay_size(overlay_config, self.overlay, bbox, text, width, height)
            target_screen_rect = get_target_screen_rect(bbox)
            if preserve_manual_position and self.overlay.last_geometry is not None:
                margin = overlay_config.margin
                soft_top_margin, soft_bottom_margin = overlay_vertical_safe_margins(overlay_config)
                x = max(
                    target_screen_rect.left() + margin,
                    min(self.overlay.last_geometry.x(), target_screen_rect.right() - width - margin + 1),
                )
                y = max(
                    target_screen_rect.top() + soft_top_margin,
                    min(self.overlay.last_geometry.y(), target_screen_rect.bottom() - height - soft_bottom_margin + 1),
                )
            else:
                x, y = compute_overlay_position(overlay_config, bbox, width, height)
        else:
            anchor_point = anchor_point or self.overlay.last_anchor_point or QCursor.pos()
            target_screen_rect = get_screen_rect_for_point(anchor_point)
            width, height = clamp_overlay_size_to_screen(overlay_config, self.overlay, target_screen_rect, text, width, height)
            if preserve_manual_position and self.overlay.last_geometry is not None:
                margin = overlay_config.margin
                soft_top_margin, soft_bottom_margin = overlay_vertical_safe_margins(overlay_config)
                x = max(
                    target_screen_rect.left() + margin,
                    min(self.overlay.last_geometry.x(), target_screen_rect.right() - width - margin + 1),
                )
                y = max(
                    target_screen_rect.top() + soft_top_margin,
                    min(self.overlay.last_geometry.y(), target_screen_rect.bottom() - height - soft_bottom_margin + 1),
                )
            else:
                x, y = compute_overlay_position_for_point(overlay_config, anchor_point, width, height)

        self.overlay.remember_context(bbox, text, anchor_point=anchor_point, preset_name=preset_name)
        self.overlay.show_text(text, x, y, width, height, keep_manual_position=preserve_manual_position or bool(preserved_geometry and self.overlay.manual_positioned))
        if complete_capture_flow and not reflow_only:
            self.window.finish_capture_workflow()
            self.window.restore_pinned_overlay_after_capture = False
        if not reflow_only:
            self.window.set_status("translated")
            self.window.log_tr("log_request_finished", preset=preset_name or "default")

    def show_translation(self, bbox, text: str, *, preset_name: str = "", preserve_manual_position: bool = False, preserve_geometry: bool = False, reflow_only: bool = False):
        self.show_response(
            text,
            bbox=bbox,
            preset_name=preset_name,
            preserve_manual_position=preserve_manual_position,
            preserve_geometry=preserve_geometry,
            reflow_only=reflow_only,
            complete_capture_flow=not reflow_only,
        )

    def adjust_font_size(self, direction: int):
        if self.window.translation_in_progress:
            return
        current_size = self.window.current_overlay_font_size()
        new_size = max(10, min(32, current_size + direction))
        if new_size == current_size:
            return
        self.window.config.overlay_font_size = new_size
        self.window._suppress_form_tracking = True
        try:
            self.window.overlay_font_size_spin.setValue(new_size)
        finally:
            self.window._suppress_form_tracking = False
        self.window.note_runtime_preference_changed()
        self.overlay.apply_typography()
        self.window.set_status("font_zoomed", size=new_size)
        preserve_geometry = bool(self.overlay.is_pinned or self.overlay.manual_positioned)
        if self.overlay.isVisible() and self.overlay.last_text:
            if self.overlay.last_bbox is not None:
                self.show_translation(
                    self.overlay.last_bbox,
                    self.overlay.last_text,
                    preset_name=self.overlay.last_preset_name,
                    preserve_manual_position=self.overlay.manual_positioned and not self.overlay.is_pinned,
                    preserve_geometry=preserve_geometry,
                    reflow_only=True,
                )
            else:
                self.show_response(
                    self.overlay.last_text,
                    anchor_point=self.overlay.last_anchor_point,
                    preset_name=self.overlay.last_preset_name,
                    preserve_manual_position=self.overlay.manual_positioned and not self.overlay.is_pinned,
                    preserve_geometry=preserve_geometry,
                    reflow_only=True,
                )
