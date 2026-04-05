import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication

from ..prompt_utils import build_image_request_prompt, build_text_request_prompt
from ..profile_utils import normalize_model_value, unique_non_empty
from ..operation_control import RequestCancelledError
from ..selected_text_capture import SelectedTextCaptureSession
from ..ui.prompt_input_dialog import PromptInputDialog


class RequestWorkflowController:
    def __init__(self, window):
        self.window = window

    def prepare_request_context(self, *, focus_first_invalid: bool = True, validation_scope: str = "image_request"):
        if self.window.capture_workflow_active:
            self.window.log_tr("log_request_ignored_capture_workflow")
            return None
        if self.window.background_busy():
            self.window.log_tr("log_request_ignored_background_busy")
            return None
        valid, first_error = self.window.validate_form_inputs(focus_first_invalid=focus_first_invalid, scope=validation_scope)
        if not valid:
            self.window.set_status("validation_failed")
            self.window.log_tr("log_request_blocked_validation", error=first_error)
            return None
        return {
            "profile": self.window.build_profile_from_form(validate_name=False),
            "target_language": self.window.current_target_language(),
            "prompt_preset": self.window.build_prompt_preset_from_form(validate_name=False),
        }

    @staticmethod
    def profile_request_signature(profile, *, include_model: bool = False) -> tuple:
        return (
            profile.name,
            profile.provider,
            profile.base_url.strip(),
            tuple(profile.api_keys),
            str(profile.model or "").strip() if include_model else "",
        )

    def form_matches_profile_request(self, signature: tuple, *, include_model: bool = False) -> bool:
        try:
            current_profile = self.window.build_profile_from_form(validate_name=False)
        except Exception:  # noqa: BLE001
            return False
        return self.profile_request_signature(current_profile, include_model=include_model) == signature

    def fetch_models(self):
        if self.window.fetch_models_in_progress or self.window.test_profile_in_progress or self.window.translation_in_progress:
            return
        valid, first_error = self.window.validate_form_inputs(focus_first_invalid=True, scope="fetch_models")
        if not valid:
            self.window.set_status("validation_failed")
            self.window.log_tr("log_request_blocked_validation", error=first_error)
            return
        profile = self.window.build_profile_from_form(validate_name=False)
        request_id = self.window._fetch_models_request_id = self.window._fetch_models_request_id + 1
        request_signature = self.profile_request_signature(profile)
        self.window.log_tr("log_fetch_models_started", name=profile.name)
        self.window.run_worker(
            lambda request_context: (request_id, request_signature, profile.provider, self.window.api_client.list_models(profile, request_context=request_context)),
            self.on_models_loaded,
            operation_key="fetch_models",
            cancellable=True,
        )

    def on_models_loaded(self, result):
        request_id, request_signature, provider, models = result
        if request_id != self.window._fetch_models_request_id:
            self.window.log_tr("log_models_stale_request")
            return
        if not self.form_matches_profile_request(request_signature):
            self.window.log_tr("log_models_stale_form")
            return
        normalized_models = unique_non_empty(normalize_model_value(item, provider) for item in models)
        if not normalized_models:
            return
        current_model = self.window.normalize_model_name(self.window.model_combo.currentText(), provider)
        self.window._suppress_form_tracking = True
        try:
            self.window.model_combo.blockSignals(True)
            self.window.model_combo.clear()
            self.window.model_combo.addItems([self.window.display_model_name(item, provider) for item in normalized_models])
            selected_model = current_model if current_model in normalized_models else normalized_models[0]
            self.window.model_combo.setCurrentText(self.window.display_model_name(selected_model, provider))
        finally:
            self.window.model_combo.blockSignals(False)
            self.window._suppress_form_tracking = False
        self.window.on_form_input_changed()
        self.window.set_status("models_loaded", count=len(normalized_models))
        self.window.log_tr("log_models_loaded", count=len(normalized_models))

    def test_profile(self):
        if self.window.fetch_models_in_progress or self.window.test_profile_in_progress or self.window.translation_in_progress:
            return
        valid, first_error = self.window.validate_form_inputs(focus_first_invalid=True, scope="test_profile")
        if not valid:
            self.window.set_status("validation_failed")
            self.window.log_tr("log_request_blocked_validation", error=first_error)
            return
        profile = self.window.build_profile_from_form(validate_name=False)
        request_id = self.window._test_profile_request_id = self.window._test_profile_request_id + 1
        request_signature = self.profile_request_signature(profile, include_model=True)
        self.window.log_tr("log_test_started", name=profile.name, model=profile.model)
        self.window.run_worker(
            lambda request_context: (request_id, request_signature, self.window.api_client.test_profile(profile, request_context=request_context)),
            self.on_test_success,
            operation_key="test_profile",
            cancellable=True,
        )

    def on_test_success(self, result):
        request_id, request_signature, message = result
        if request_id != self.window._test_profile_request_id or not self.form_matches_profile_request(request_signature, include_model=True):
            self.window.log_tr("log_test_stale_form")
            return
        self.window.log(message)
        self.window.set_status("test_success")

    def submit_text_request(self, text: str, *, profile, target_language: str, prompt_preset, anchor_point, source_key: str):
        prompt = build_text_request_prompt(prompt_preset.text_prompt, text, target_language=target_language)
        self.window.set_status(source_key)
        self.window.log_tr("log_text_request_submitted", preset=prompt_preset.name, chars=len(text))
        self.window.show_tray_toast(self.window.tr(source_key))
        overlay = self.window.translation_overlay
        preserve_pinned_geometry = bool(overlay.is_pinned)
        preserve_manual_position = bool(
            overlay.isVisible()
            and overlay.manual_positioned
            and not preserve_pinned_geometry
        )
        temperature = self.window.current_temperature()
        self.window.run_worker(
            lambda request_context, prompt=prompt, profile=profile, temperature=temperature: self.window.api_client.request_text(
                prompt, profile, temperature, request_context=request_context
            ),
            lambda result, anchor_point=anchor_point, preset_name=prompt_preset.name, preserve_manual_position=preserve_manual_position, preserve_pinned_geometry=preserve_pinned_geometry: self.window.overlay_presenter.show_response(
                result,
                anchor_point=anchor_point,
                preset_name=preset_name,
                preserve_manual_position=preserve_manual_position,
                preserve_geometry=preserve_pinned_geometry,
            ),
            operation_key="translation",
            cancellable=True,
        )

    @staticmethod
    def _restore_override_cursor():
        if QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()

    def _cleanup_selected_text_capture(self, session) -> bool:
        if session is not self.window.selected_text_capture_session:
            return False
        self.window.selected_text_capture_session = None
        self.window.selected_text_capture_in_progress = False
        self._restore_override_cursor()
        self.window.update_action_states()
        try:
            session.deleteLater()
        except Exception:  # noqa: BLE001
            pass
        return True

    def _handle_selected_text_capture_finished(self, session, request_context, anchor_point, selected_text: str):
        if not self._cleanup_selected_text_capture(session):
            return
        if not selected_text:
            self.window.set_status("selected_text_empty")
            self.window.log_tr("log_selected_text_empty")
            self.window.show_tray_toast(self.window.tr("selected_text_empty"))
            return
        self.submit_text_request(
            selected_text,
            profile=request_context["profile"],
            target_language=request_context["target_language"],
            prompt_preset=request_context["prompt_preset"],
            anchor_point=anchor_point,
            source_key="selected_text_processing",
        )

    def _handle_selected_text_capture_failed(self, session, exc: Exception):
        if not self._cleanup_selected_text_capture(session):
            return
        self.window.handle_error(exc)

    def _handle_selected_text_capture_cancelled(self, session):
        if not self._cleanup_selected_text_capture(session):
            return
        self.window.log("Selected text capture cancelled")
        self.window.set_status("request_cancelled")
        self.window.show_tray_toast(self.window.tr("request_cancelled"))

    def cancel_selected_text_capture(self) -> bool:
        session = getattr(self.window, "selected_text_capture_session", None)
        if not session:
            return False
        return bool(session.cancel())

    def translate_selected_text(self):
        request_context = self.prepare_request_context(focus_first_invalid=True, validation_scope="text_request")
        if not request_context:
            return
        anchor_point = QCursor.pos()
        self.window.log_tr("log_selected_text_capture_started")
        self.window.set_status("selected_text_capturing")
        session = SelectedTextCaptureSession(hotkey_text=self.window.current_selection_hotkey(), parent=self.window)
        self.window.selected_text_capture_session = session
        self.window.selected_text_capture_in_progress = True
        self.window.update_action_states()
        session.finished.connect(lambda selected_text, session=session, request_context=request_context, anchor_point=anchor_point: self._handle_selected_text_capture_finished(session, request_context, anchor_point, selected_text))
        session.failed.connect(lambda exc, session=session: self._handle_selected_text_capture_failed(session, exc))
        session.cancelled.connect(lambda session=session: self._handle_selected_text_capture_cancelled(session))
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            session.start()
        except Exception:
            self._cleanup_selected_text_capture(session)
            raise

    def open_prompt_input_dialog(self):
        request_context = self.prepare_request_context(focus_first_invalid=True, validation_scope="text_request")
        if not request_context:
            return
        dialog = PromptInputDialog(self.window, request_context["prompt_preset"].name, request_context["target_language"])
        if not dialog.exec():
            return
        self.submit_text_request(
            dialog.input_text(),
            profile=request_context["profile"],
            target_language=request_context["target_language"],
            prompt_preset=request_context["prompt_preset"],
            anchor_point=dialog.last_anchor_point or QCursor.pos(),
            source_key="manual_input_processing",
        )

    def start_selection(self):
        request_context = self.prepare_request_context(focus_first_invalid=True, validation_scope="image_request")
        if not request_context:
            return
        restore_window_after_capture = self.window.isVisible() and not self.window.isMinimized()
        self.window.pending_capture_profile = request_context["profile"]
        self.window.pending_capture_target_language = request_context["target_language"]
        self.window.pending_capture_prompt_preset = request_context["prompt_preset"]
        self.window.restore_pinned_overlay_after_capture = bool(
            self.window.translation_overlay.isVisible()
            and self.window.translation_overlay.is_pinned
            and self.window.translation_overlay.last_text.strip()
        )
        self.window.log_tr("log_capture_started", preset=self.window.pending_capture_prompt_preset.name, target=self.window.pending_capture_target_language)
        self.window.capture_workflow_active = True
        self.window.restore_window_after_capture = restore_window_after_capture
        self.window.update_action_states()
        self.window.hide()
        self.window.translation_overlay.hide()
        self.window.selection_overlay.show_overlay()

    def finish_capture_workflow(self, restore_window: bool = False):
        should_restore = restore_window and self.window.restore_window_after_capture
        self.window.capture_workflow_active = False
        self.window.restore_window_after_capture = False
        self.window.pending_capture_profile = None
        self.window.pending_capture_target_language = self.window.current_target_language()
        self.window.pending_capture_prompt_preset = None
        self.window.update_action_states()
        if should_restore:
            self.window.show_main_window()

    def handle_capture_cancelled(self):
        self.window.log_tr("log_capture_cancelled")
        self.finish_capture_workflow(restore_window=True)
        if self.window.restore_pinned_overlay_after_capture:
            self.window.translation_overlay.restore_last_overlay()
            self.window.restore_pinned_overlay_after_capture = False
        self.window.set_status("capture_cancelled")
        self.window.show_tray_toast(self.window.tr("capture_cancelled"))

    def _handle_image_translation_success(self, text: str, *, bbox, preset_name: str, capture_started_at: float, request_started_at: float, capture_elapsed: float, payload_bytes: int):
        self.window.overlay_presenter.show_translation(
            bbox,
            text,
            preset_name=preset_name,
            preserve_geometry=bool(self.window.translation_overlay.is_pinned),
        )
        request_elapsed = time.perf_counter() - request_started_at
        total_elapsed = time.perf_counter() - capture_started_at
        self.window.log(
            "圖片請求完成｜"
            f"capture={capture_elapsed * 1000:.0f}ms｜"
            f"request={request_elapsed:.2f}s｜"
            f"total={total_elapsed:.2f}s｜"
            f"png={payload_bytes / 1024:.1f}KB"
        )

    def _update_preview_from_png_bytes(self, png_bytes: bytes):
        self.window.update_preview(preview_pixmap=self.window.screen_capture_service.build_preview_pixmap_from_bytes(png_bytes))

    def handle_selection(self, bbox):
        self.window.set_status("capturing")
        self.window.show_tray_toast(self.window.tr("tray_capturing"))
        profile = self.window.pending_capture_profile or self.window.build_profile_from_form(validate_name=False)
        target_language = self.window.pending_capture_target_language or self.window.current_target_language()
        prompt_preset = self.window.pending_capture_prompt_preset or self.window.build_prompt_preset_from_form(validate_name=False)
        prompt = build_image_request_prompt(prompt_preset.image_prompt, target_language=target_language)
        temperature = self.window.current_temperature()
        capture_started_at = time.perf_counter()

        def capture_and_request(request_context):
            if request_context is not None and request_context.is_cancelled():
                raise RequestCancelledError()
            png_bytes = self.window.screen_capture_service.capture_bbox_png_bytes_threadsafe(bbox)
            capture_elapsed = time.perf_counter() - capture_started_at
            self.window.log(f"截圖已就緒｜capture={capture_elapsed * 1000:.0f}ms｜png={len(png_bytes) / 1024:.1f}KB")
            self.window.bridge.invoke_main_thread.emit(self._update_preview_from_png_bytes, png_bytes)
            request_started_at = time.perf_counter()
            text = self.window.api_client.request_image_png(
                png_bytes,
                profile,
                prompt,
                temperature,
                request_context=request_context,
            )
            return text, capture_elapsed, len(png_bytes), request_started_at

        self.window.run_worker(
            capture_and_request,
            lambda result, bbox=bbox, preset_name=prompt_preset.name, capture_started_at=capture_started_at: self._handle_image_translation_success(
                result[0],
                bbox=bbox,
                preset_name=preset_name,
                capture_started_at=capture_started_at,
                request_started_at=result[3],
                capture_elapsed=result[1],
                payload_bytes=result[2],
            ),
            operation_key="translation",
            cancellable=True,
        )
