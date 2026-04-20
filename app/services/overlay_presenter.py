from types import SimpleNamespace

from PySide6.QtCore import QRect, QTimer
from PySide6.QtGui import QCursor

from ..ui.overlay_positioning import (
    clamp_rect_to_visible_screen,
    clamp_overlay_size_to_screen,
    compute_overlay_position,
    compute_overlay_position_for_point,
    fit_overlay_size,
    overlay_vertical_safe_margins,
    preferred_overlay_width_for_bbox,
    get_screen_rect_for_point,
    get_target_screen_rect,
)


class OverlayPresenter:
    def __init__(self, window):
        self.window = window

    @property
    def overlay(self):
        return self.window.translation_overlay

    def _overlay_config(self):
        return SimpleNamespace(
            mode=self.window.current_mode(),
            margin=self.window.current_margin(),
            overlay_auto_expand_top_margin=self.window.current_overlay_auto_expand_top_margin(),
            overlay_auto_expand_bottom_margin=self.window.current_overlay_auto_expand_bottom_margin(),
            overlay_width=self.window.current_overlay_width(),
            overlay_height=self.window.current_overlay_height(),
        )

    @staticmethod
    def _bbox_rect(bbox) -> QRect | None:
        if bbox is None:
            return None
        try:
            left, top, right, bottom = (int(value) for value in bbox)
        except Exception:  # noqa: BLE001
            return None
        return QRect(left, top, max(0, right - left), max(0, bottom - top))

    @staticmethod
    def _format_rect(rect: QRect | None) -> str:
        if rect is None:
            return "none"
        return f"{rect.x()},{rect.y()},{rect.width()}x{rect.height()}"

    @classmethod
    def _format_rect_overlap(cls, rect: QRect | None, other: QRect | None) -> str:
        if rect is None or other is None:
            return "n/a"
        overlap = rect.intersected(other)
        if overlap.isNull() or overlap.width() <= 0 or overlap.height() <= 0:
            return "none"
        return cls._format_rect(overlap)

    def _log_bbox_overlay_diagnostics(self, *, phase: str, mode: str, bbox, initial_planned_rect: QRect, planned_rect: QRect):
        log_func = getattr(self.window, "log_debug", None) or getattr(self.window, "log", None)
        if not callable(log_func):
            return

        bbox_rect = self._bbox_rect(bbox)
        corrected_rect = planned_rect if planned_rect != initial_planned_rect else None

        def emit(stage: str):
            overlay = self.overlay
            geometry = QRect(overlay.geometry())
            frame_geometry = QRect(overlay.frameGeometry())
            corrected_fragment = f"corrected={self._format_rect(corrected_rect)}｜" if corrected_rect is not None else ""
            log_func(
                "浮窗定位诊断｜"
                f"stage={stage}｜"
                f"phase={phase}｜"
                f"mode={mode}｜"
                f"bbox={self._format_rect(bbox_rect)}｜"
                f"initial_planned={self._format_rect(initial_planned_rect)}｜"
                f"planned={self._format_rect(planned_rect)}｜"
                f"{corrected_fragment}"
                f"geom={self._format_rect(geometry)}｜"
                f"frame={self._format_rect(frame_geometry)}｜"
                f"initial_planned_overlap={self._format_rect_overlap(initial_planned_rect, bbox_rect)}｜"
                f"planned_overlap={self._format_rect_overlap(planned_rect, bbox_rect)}｜"
                f"geom_overlap={self._format_rect_overlap(geometry, bbox_rect)}｜"
                f"frame_overlap={self._format_rect_overlap(frame_geometry, bbox_rect)}｜"
                f"visible={'yes' if overlay.isVisible() else 'no'}"
            )

        emit("immediate")
        QTimer.singleShot(0, lambda: emit("deferred"))

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

    def _current_request_overlay_width(self) -> int | None:
        width_getter = getattr(self.window, "current_request_overlay_width", None)
        if not callable(width_getter):
            return None
        try:
            return int(width_getter())
        except Exception:  # noqa: BLE001
            return None

    def _recompute_auto_position(self, overlay_config, *, bbox, anchor_point, width: int, height: int) -> tuple[int, int]:
        if bbox is not None:
            return compute_overlay_position(overlay_config, bbox, width, height)
        resolved_anchor_point = anchor_point or self.overlay.last_anchor_point or QCursor.pos()
        return compute_overlay_position_for_point(overlay_config, resolved_anchor_point, width, height)

    def _prepare_hidden_first_partial_rect(self, *, text: str, preset_name: str, initial_planned_rect: QRect, overlay_config, bbox, anchor_point) -> QRect:
        body = getattr(self.overlay, "body", None)
        set_geometry = getattr(self.overlay, "setGeometry", None)
        set_body_content = getattr(self.overlay, "_set_body_content", None)
        if body is None or not callable(getattr(body, "setPlainText", None)) or not callable(set_geometry):
            return QRect(initial_planned_rect)

        current_text = body.toPlainText() if callable(getattr(body, "toPlainText", None)) else ""
        if current_text != text:
            if callable(set_body_content):
                set_body_content(text, render_markdown=False)
            else:
                body.setPlainText(text)
        set_geometry(QRect(initial_planned_rect))
        actual_rect = QRect(self.overlay.geometry())
        if actual_rect.size() == initial_planned_rect.size():
            return actual_rect

        corrected_x, corrected_y = self._recompute_auto_position(
            overlay_config,
            bbox=bbox,
            anchor_point=anchor_point,
            width=actual_rect.width(),
            height=actual_rect.height(),
        )
        corrected_rect = QRect(int(corrected_x), int(corrected_y), actual_rect.width(), actual_rect.height())
        set_geometry(QRect(corrected_rect))
        return corrected_rect

    def _remember_auto_learned_unpinned_width(self, *, initial_planned_rect: QRect, final_rect: QRect, preserved_geometry, keep_manual_position: bool) -> None:
        if preserved_geometry is not None or keep_manual_position:
            return
        if final_rect.width() <= max(0, initial_planned_rect.width()):
            return
        overlay = self.overlay
        if getattr(overlay, "is_pinned", False) or getattr(overlay, "manual_positioned", False):
            return
        learner = getattr(self.window, "learn_runtime_auto_unpinned_overlay_width", None)
        if not callable(learner):
            return
        try:
            learner(int(final_rect.width()))
        except Exception:  # noqa: BLE001
            pass

    def _should_seed_initial_unpinned_width(self, *, was_visible: bool, preserve_manual_position: bool, preserve_geometry: bool, locked_width: int | None) -> bool:
        if was_visible or preserve_manual_position or preserve_geometry or locked_width is not None:
            return False
        overlay = self.overlay
        if getattr(overlay, "is_pinned", False) or getattr(overlay, "manual_positioned", False):
            return False
        if getattr(self.window, "_runtime_unpinned_overlay_width", None) is not None:
            return False
        pending_width_change_getter = getattr(self.window, "_has_pending_overlay_width_form_change", None)
        if callable(pending_width_change_getter):
            try:
                if pending_width_change_getter():
                    return False
            except Exception:  # noqa: BLE001
                return False
        return True

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
        locked_width: int | None = None,
        partial: bool = False,
    ):
        text = text or self.window.tr("empty_result")
        was_visible = self.overlay.isVisible()
        had_partial_result = bool(partial and hasattr(self.overlay, "has_partial_result") and self.overlay.has_partial_result())
        if not was_visible:
            primer = getattr(self.overlay, "prime_first_show", None)
            if callable(primer):
                primer()

        overlay_config = self._overlay_config()
        request_overlay_width = self._current_request_overlay_width()
        base_width = locked_width
        if partial and hasattr(self.overlay, "set_partial_result_state"):
            self.overlay.set_partial_result_state("streaming", preset_name=preset_name)
        if base_width is None:
            base_width = request_overlay_width
        elif request_overlay_width is not None:
            base_width = max(int(base_width), request_overlay_width)
        if partial and bbox is not None and self._should_seed_initial_unpinned_width(
            was_visible=was_visible,
            preserve_manual_position=preserve_manual_position,
            preserve_geometry=preserve_geometry,
            locked_width=locked_width,
        ):
            seeded_width = preferred_overlay_width_for_bbox(overlay_config, bbox)
            base_width = max(int(base_width or 0), int(seeded_width))
        self.overlay.apply_typography()

        if partial and had_partial_result and was_visible:
            preserved_geometry = self._preserved_geometry(preserve_geometry=preserve_geometry)
            if preserved_geometry is None and not preserve_manual_position:
                current_rect = QRect(self.overlay.geometry())
                if current_rect.width() > 0 and current_rect.height() > 0:
                    if bbox is not None:
                        target_screen_rect = get_target_screen_rect(bbox)
                    else:
                        anchor_point = anchor_point or self.overlay.last_anchor_point or QCursor.pos()
                        target_screen_rect = get_screen_rect_for_point(anchor_point)

                    width = max(1, current_rect.width())
                    height = max(1, current_rect.height())
                    width, height = clamp_overlay_size_to_screen(
                        overlay_config,
                        self.overlay,
                        target_screen_rect,
                        text,
                        width,
                        height,
                        render_markdown=False,
                    )
                    margin = overlay_config.margin
                    soft_top_margin, soft_bottom_margin = overlay_vertical_safe_margins(overlay_config)
                    x = max(
                        target_screen_rect.left() + margin,
                        min(current_rect.x(), target_screen_rect.right() - width - margin + 1),
                    )
                    y = max(
                        target_screen_rect.top() + soft_top_margin,
                        min(current_rect.y(), target_screen_rect.bottom() - height - soft_bottom_margin + 1),
                    )
                    if x != current_rect.x() or y != current_rect.y():
                        x = current_rect.x()
                        y = current_rect.y()
                        width = current_rect.width()
                        height = current_rect.height()
                    keep_manual_position = False
                    initial_planned_rect = QRect(int(x), int(y), int(width), int(height))
                    planned_rect = QRect(initial_planned_rect)
                    self.overlay.show_text(text, x, y, width, height, keep_manual_position=keep_manual_position, remember_state=False)
                    if hasattr(self.window, "toast_service"):
                        self.window.toast_service.hide_message()
                    return

        width, height = self.overlay.calculate_size(text, base_width=base_width, preset_name=preset_name, partial_state="streaming" if partial else None)
        preserved_geometry = self._preserved_geometry(preserve_geometry=preserve_geometry)
        if locked_width is not None:
            width = max(1, int(locked_width))

        if preserved_geometry is not None:
            x = preserved_geometry.x()
            y = preserved_geometry.y()
            width = preserved_geometry.width()
            height = preserved_geometry.height()
        elif bbox is not None:
            width, height = fit_overlay_size(overlay_config, self.overlay, bbox, text, width, height, render_markdown=not partial)
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
            width, height = clamp_overlay_size_to_screen(
                overlay_config,
                self.overlay,
                target_screen_rect,
                text,
                width,
                height,
                render_markdown=not partial,
            )
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

        if not partial:
            self.overlay.remember_context(bbox, text, anchor_point=anchor_point, preset_name=preset_name)
        keep_manual_position = preserve_manual_position or bool(preserved_geometry and self.overlay.manual_positioned)
        initial_planned_rect = QRect(int(x), int(y), int(width), int(height))
        planned_rect = QRect(initial_planned_rect)
        if partial and not had_partial_result and not was_visible and preserved_geometry is None and not keep_manual_position:
            planned_rect = self._prepare_hidden_first_partial_rect(
                text=text,
                preset_name=preset_name,
                initial_planned_rect=initial_planned_rect,
                overlay_config=overlay_config,
                bbox=bbox,
                anchor_point=anchor_point,
            )
        self.overlay.show_text(text, planned_rect.x(), planned_rect.y(), planned_rect.width(), planned_rect.height(), keep_manual_position=keep_manual_position, remember_state=not partial)
        actual_rect = QRect(self.overlay.geometry())
        if preserved_geometry is None and not keep_manual_position and actual_rect.size() != planned_rect.size():
            corrected_x, corrected_y = self._recompute_auto_position(
                overlay_config,
                bbox=bbox,
                anchor_point=anchor_point,
                width=actual_rect.width(),
                height=actual_rect.height(),
            )
            corrected_rect = QRect(int(corrected_x), int(corrected_y), actual_rect.width(), actual_rect.height())
            planned_rect = QRect(corrected_rect)
            if corrected_rect != actual_rect:
                self.overlay.show_text(
                    text,
                    corrected_x,
                    corrected_y,
                    actual_rect.width(),
                    actual_rect.height(),
                    keep_manual_position=keep_manual_position,
                    remember_state=not partial,
                )
        final_rect = QRect(self.overlay.geometry())
        self._remember_auto_learned_unpinned_width(
            initial_planned_rect=initial_planned_rect,
            final_rect=final_rect,
            preserved_geometry=preserved_geometry,
            keep_manual_position=keep_manual_position,
        )
        if hasattr(self.window, "toast_service"):
            self.window.toast_service.hide_message()
        diagnostic_phase = None
        if bbox is not None:
            if not was_visible:
                diagnostic_phase = "first_visible_partial" if partial else "first_visible_final"
            elif reflow_only:
                diagnostic_phase = "reflow"
        if diagnostic_phase:
            self._log_bbox_overlay_diagnostics(
                phase=diagnostic_phase, mode=str(getattr(overlay_config, "mode", "")), bbox=bbox, initial_planned_rect=initial_planned_rect, planned_rect=planned_rect
            )
        if complete_capture_flow and not reflow_only:
            self.window.finish_capture_workflow()
            self.window.restore_pinned_overlay_after_capture = False
        if not reflow_only and not partial:
            self.window.set_status("translated")
            self.window.log_tr("log_request_finished", preset=preset_name or "default")

    def show_translation(self, bbox, text: str, *, preset_name: str = "", preserve_manual_position: bool = False, preserve_geometry: bool = False, reflow_only: bool = False, locked_width: int | None = None):
        self.show_response(
            text,
            bbox=bbox,
            preset_name=preset_name,
            preserve_manual_position=preserve_manual_position,
            preserve_geometry=preserve_geometry,
            reflow_only=reflow_only,
            locked_width=locked_width,
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
