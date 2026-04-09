import time
from types import SimpleNamespace

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication

from ..prompt_utils import build_image_request_prompt, build_text_request_prompt
from ..profile_utils import normalize_model_value, unique_non_empty
from ..operation_control import RequestCancelledError
from ..ui.overlay_positioning import preferred_overlay_width_for_bbox

SelectedTextCaptureSession = None
PromptInputDialog = None


class RequestWorkflowController:
    PARTIAL_STREAM_FRAME_INTERVAL_MS = 16

    def __init__(self, window):
        self.window = window
        self._active_stream_partial_request_token = None
        self._latest_stream_partial_payload = None
        self._scheduled_stream_partial_request_token = None

    def _begin_streaming_response_update_state(self):
        request_token = object()
        self._active_stream_partial_request_token = request_token
        self._latest_stream_partial_payload = None
        self._scheduled_stream_partial_request_token = None
        return request_token

    def clear_streaming_response_update_state(self):
        self._active_stream_partial_request_token = None
        self._latest_stream_partial_payload = None
        self._scheduled_stream_partial_request_token = None

    def _complete_streaming_response_update_state(self, request_token):
        if request_token is not None and request_token is self._active_stream_partial_request_token:
            self.clear_streaming_response_update_state()

    def _existing_translation_overlay(self):
        getter = getattr(self.window, "existing_translation_overlay", None)
        if callable(getter):
            return getter()
        return getattr(self.window, "translation_overlay", None)

    @staticmethod
    def _normalize_internal_selected_text(text) -> str:
        return str(text or "").replace("\u2029", "\n").replace("\u2028", "\n").strip()

    def _read_selected_text_from_widget(self, widget) -> str:
        if widget is None:
            return ""
        selected_text_getter = getattr(widget, "selectedText", None)
        if callable(selected_text_getter):
            try:
                selected_text = self._normalize_internal_selected_text(selected_text_getter())
            except Exception:  # noqa: BLE001
                selected_text = ""
            if selected_text:
                return selected_text
        text_cursor_getter = getattr(widget, "textCursor", None)
        if callable(text_cursor_getter):
            try:
                cursor = text_cursor_getter()
            except Exception:  # noqa: BLE001
                cursor = None
            if cursor is not None and hasattr(cursor, "hasSelection") and cursor.hasSelection():
                try:
                    selected_text = self._normalize_internal_selected_text(cursor.selectedText())
                except Exception:  # noqa: BLE001
                    selected_text = ""
                if selected_text:
                    return selected_text
        return ""

    def _capture_in_app_selected_text(self) -> str:
        active_window = QApplication.activeWindow()
        focus_widget = QApplication.focusWidget()
        if active_window is None or focus_widget is None:
            return ""
        widget = focus_widget
        while widget is not None:
            selected_text = self._read_selected_text_from_widget(widget)
            if selected_text:
                return selected_text
            parent_getter = getattr(widget, "parentWidget", None)
            widget = parent_getter() if callable(parent_getter) else None
            if widget is active_window:
                selected_text = self._read_selected_text_from_widget(widget)
                return selected_text or ""
        return ""

    def _selection_overlay(self):
        return getattr(self.window, "selection_overlay", None)

    def _set_capture_desktop_snapshot(self, snapshot, background_pixmap) -> None:
        self.window.capture_desktop_snapshot = snapshot
        overlay = self._selection_overlay()
        if overlay is None:
            return
        setter = getattr(overlay, "set_snapshot_background", None)
        if callable(setter):
            setter(background_pixmap, virtual_rect=getattr(snapshot, "virtual_rect", None))

    def _clear_capture_desktop_snapshot(self) -> None:
        self.window.capture_desktop_snapshot = None
        overlay = self._selection_overlay()
        if overlay is None:
            return
        clearer = getattr(overlay, "clear_snapshot_background", None)
        if callable(clearer):
            clearer()

    def _capture_desktop_snapshot(self):
        snapshot = self.window.screen_capture_service.capture_desktop_snapshot()
        background_pixmap = self.window.screen_capture_service.build_snapshot_background_pixmap(snapshot)
        return snapshot, background_pixmap

    def _capture_conceal_targets(self, overlay) -> list[object]:
        targets = []
        candidates = [self.window, overlay, *list(getattr(self.window, "_active_error_dialogs", []) or [])]
        for widget in candidates:
            if widget is None or widget in targets:
                continue
            try:
                if hasattr(widget, "isVisible") and widget.isVisible():
                    targets.append(widget)
            except Exception:  # noqa: BLE001
                continue
        return targets

    def _apply_capture_window_concealment(self, widgets) -> list[dict]:
        from ..platform.windows.capture_visibility import begin_temporary_capture_conceal

        states: list[dict] = []
        method_counts: dict[str, int] = {}
        for widget in widgets or []:
            state = begin_temporary_capture_conceal(widget)
            if not state:
                continue
            states.append(state)
            method = str(state.get("method") or "unknown")
            method_counts[method] = method_counts.get(method, 0) + 1
        if method_counts:
            methods_text = ", ".join(f"{name}:{count}" for name, count in sorted(method_counts.items()))
            self.window.log(f"截圖瞬時隱身已套用｜widgets={len(states)}｜methods={methods_text}")
        return states

    def _restore_capture_window_concealment(self, states) -> None:
        from ..platform.windows.capture_visibility import restore_temporary_capture_conceal

        for state in reversed(list(states or [])):
            restore_temporary_capture_conceal(state)
        app = QApplication.instance()
        if app is not None:
            try:
                app.processEvents()
            except Exception:  # noqa: BLE001
                pass

    def _hide_app_owned_windows_for_capture(self) -> int:
        hidden_windows = []
        toast_service = getattr(self.window, "toast_service", None)
        if toast_service is not None and hasattr(toast_service, "hide_message"):
            try:
                toast_service.hide_message()
            except Exception:  # noqa: BLE001
                pass
        for dialog in list(getattr(self.window, "_active_error_dialogs", []) or []):
            if dialog is None:
                continue
            try:
                if hasattr(dialog, "isVisible") and dialog.isVisible() and hasattr(dialog, "hide"):
                    dialog.hide()
                    hidden_windows.append(dialog)
            except Exception:  # noqa: BLE001
                continue
        self.window.capture_hidden_owned_windows = hidden_windows
        return len(hidden_windows)

    def _restore_hidden_app_owned_windows_after_capture(self) -> None:
        hidden_windows = list(getattr(self.window, "capture_hidden_owned_windows", []) or [])
        self.window.capture_hidden_owned_windows = []
        for widget in hidden_windows:
            if widget is None:
                continue
            try:
                if hasattr(widget, "show"):
                    widget.show()
                if hasattr(widget, "raise_"):
                    widget.raise_()
                if hasattr(widget, "activateWindow"):
                    widget.activateWindow()
            except Exception:  # noqa: BLE001
                continue

    def _run_capture_hide_barrier(self) -> tuple[float, bool]:
        app = QApplication.instance()
        if app is not None:
            try:
                app.processEvents()
            except Exception:  # noqa: BLE001
                pass
        from ..platform.windows.compositor_sync import flush_window_composition

        barrier_started_at = time.perf_counter()
        dwm_flushed = flush_window_composition()
        if app is not None:
            try:
                app.processEvents()
            except Exception:  # noqa: BLE001
                pass
        return time.perf_counter() - barrier_started_at, dwm_flushed

    @staticmethod
    def _selected_text_capture_session_class():
        global SelectedTextCaptureSession
        if SelectedTextCaptureSession is None:
            from ..selected_text_capture import SelectedTextCaptureSession as _SelectedTextCaptureSession
            SelectedTextCaptureSession = _SelectedTextCaptureSession
        return SelectedTextCaptureSession

    @staticmethod
    def _prompt_input_dialog_class():
        global PromptInputDialog
        if PromptInputDialog is None:
            from ..ui.prompt_input_dialog import PromptInputDialog as _PromptInputDialog
            PromptInputDialog = _PromptInputDialog
        return PromptInputDialog

    def preload_support_classes(self):
        return self._selected_text_capture_session_class(), self._prompt_input_dialog_class()

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

    def _stream_locked_width(self) -> int | None:
        width_getter = getattr(self.window, "current_request_overlay_width", None)
        if callable(width_getter):
            try:
                return int(width_getter())
            except Exception:  # noqa: BLE001
                return None
        return None

    def _stream_locked_width_for_bbox(self, bbox) -> int | None:
        locked_width = self._stream_locked_width()
        if bbox is None:
            return locked_width
        current_mode = getattr(self.window, "current_mode", None)
        if callable(current_mode):
            try:
                if str(current_mode() or "").strip() != "book_lr":
                    return locked_width
            except Exception:  # noqa: BLE001
                return locked_width
        if getattr(self.window, "_runtime_unpinned_overlay_width", None) is not None:
            return locked_width
        pending_width_change_getter = getattr(self.window, "_has_pending_overlay_width_form_change", None)
        if callable(pending_width_change_getter):
            try:
                if pending_width_change_getter():
                    return locked_width
            except Exception:  # noqa: BLE001
                return locked_width
        auto_width = getattr(self.window, "_runtime_auto_unpinned_overlay_width", None)
        try:
            auto_width = int(auto_width) if auto_width is not None else None
        except (TypeError, ValueError):
            auto_width = None
        overlay_config = SimpleNamespace(mode="book_lr", margin=self.window.current_margin())
        try:
            return max(int(locked_width or 0), int(auto_width or 0), preferred_overlay_width_for_bbox(overlay_config, bbox))
        except Exception:  # noqa: BLE001
            return locked_width
        return None

    def _queue_streaming_response_update(self, payload: dict) -> None:
        bridge = getattr(self.window, "bridge", None)
        signal = getattr(bridge, "invoke_main_thread", None)
        if signal is None or not hasattr(signal, "emit"):
            self._handle_streaming_response_update(payload)
            return
        signal.emit(self._handle_streaming_response_update, payload)

    def _render_streaming_response_update(self, payload: dict):
        kwargs = {
            "preset_name": str(payload.get("preset_name") or ""),
            "preserve_manual_position": bool(payload.get("preserve_manual_position", False)),
            "preserve_geometry": bool(payload.get("preserve_geometry", False)),
            "locked_width": payload.get("locked_width"),
            "partial": True,
        }
        bbox = payload.get("bbox")
        if bbox is not None:
            self.window.overlay_presenter.show_response(str(payload.get("text") or ""), bbox=bbox, **kwargs)
            return
        self.window.overlay_presenter.show_response(str(payload.get("text") or ""), anchor_point=payload.get("anchor_point"), **kwargs)

    def _flush_streaming_response_update(self, request_token):
        if self._scheduled_stream_partial_request_token is not request_token:
            return
        self._scheduled_stream_partial_request_token = None
        if request_token is not self._active_stream_partial_request_token:
            return
        payload = self._latest_stream_partial_payload
        if not isinstance(payload, dict) or payload.get("_stream_request_token") is not request_token:
            return
        self._latest_stream_partial_payload = None
        self._render_streaming_response_update(payload)

    def _handle_streaming_response_update(self, payload: dict):
        if not isinstance(payload, dict):
            return
        request_token = payload.get("_stream_request_token")
        if request_token is None or request_token is not self._active_stream_partial_request_token:
            return
        text = str(payload.get("text") or "")
        if not text.strip():
            return
        self._latest_stream_partial_payload = dict(payload)
        if self._scheduled_stream_partial_request_token is request_token:
            return
        self._scheduled_stream_partial_request_token = request_token
        QTimer.singleShot(self.PARTIAL_STREAM_FRAME_INTERVAL_MS, lambda request_token=request_token: self._flush_streaming_response_update(request_token))

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
        stream_enabled = bool(getattr(self.window, "current_stream_responses", lambda: True)())
        request_signature = self.profile_request_signature(profile, include_model=True)
        self.window.log_tr("log_test_started", name=profile.name, model=profile.model)
        self.window.run_worker(
            lambda request_context, stream_enabled=stream_enabled: (
                request_id, request_signature, self.window.api_client.test_profile(profile, stream=stream_enabled, request_context=request_context)
            ),
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
        overlay = self._existing_translation_overlay()
        preserve_pinned_geometry = bool(overlay.is_pinned) if overlay is not None else False
        preserve_manual_position = bool(
            overlay is not None
            and overlay.isVisible()
            and overlay.manual_positioned
            and not preserve_pinned_geometry
        )
        temperature = self.window.current_temperature()
        stream_enabled = bool(getattr(self.window, "current_stream_responses", lambda: True)())
        stream_request_token = self._begin_streaming_response_update_state() if stream_enabled else None
        stream_locked_width = self._stream_locked_width() if stream_enabled else None

        stream_callback = None
        if stream_enabled:
            stream_callback = lambda partial_text, anchor_point=anchor_point, preset_name=prompt_preset.name, preserve_manual_position=preserve_manual_position, preserve_pinned_geometry=preserve_pinned_geometry, stream_locked_width=stream_locked_width, stream_request_token=stream_request_token: self._queue_streaming_response_update(
                {
                    "text": partial_text,
                    "anchor_point": anchor_point,
                    "preset_name": preset_name,
                    "preserve_manual_position": preserve_manual_position,
                    "preserve_geometry": preserve_pinned_geometry,
                    "_stream_request_token": stream_request_token,
                    "locked_width": stream_locked_width,
                }
            )
        else:
            self.clear_streaming_response_update_state()

        def handle_text_request_success(result, *, anchor_point=anchor_point, preset_name=prompt_preset.name, preserve_manual_position=preserve_manual_position, preserve_pinned_geometry=preserve_pinned_geometry, stream_request_token=stream_request_token):
            self._complete_streaming_response_update_state(stream_request_token)
            kwargs = {
                "anchor_point": anchor_point,
                "preset_name": preset_name,
                "preserve_manual_position": preserve_manual_position,
                "preserve_geometry": preserve_pinned_geometry,
            }
            if stream_locked_width is not None:
                kwargs["locked_width"] = stream_locked_width
            self.window.overlay_presenter.show_response(result, **kwargs)

        self.window.run_worker(
            lambda request_context, prompt=prompt, profile=profile, temperature=temperature, stream_enabled=stream_enabled, stream_callback=stream_callback: self.window.api_client.request_text(
                prompt,
                profile,
                temperature,
                stream=stream_enabled,
                stream_callback=stream_callback,
                request_context=request_context,
            ),
            handle_text_request_success,
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
        selected_text = self._capture_in_app_selected_text()
        if selected_text:
            self.window.log("Using in-app selected text without clipboard capture")
            self.submit_text_request(
                selected_text,
                profile=request_context["profile"],
                target_language=request_context["target_language"],
                prompt_preset=request_context["prompt_preset"],
                anchor_point=QCursor.pos(),
                source_key="selected_text_processing",
            )
            return
        anchor_point = QCursor.pos()
        SelectedTextCaptureSession = self._selected_text_capture_session_class()
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
        PromptInputDialog = self._prompt_input_dialog_class()
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

    def start_selection(self, *, restore_window_after_capture: bool | None = None):
        request_context = self.prepare_request_context(focus_first_invalid=True, validation_scope="image_request")
        if not request_context:
            return
        restore_window_after_capture = (self.window.isVisible() and not self.window.isMinimized()) if restore_window_after_capture is None else bool(restore_window_after_capture)
        self.window.pending_capture_profile = request_context["profile"]
        self.window.pending_capture_target_language = request_context["target_language"]
        self.window.pending_capture_prompt_preset = request_context["prompt_preset"]
        overlay = self._existing_translation_overlay()
        self.window.restore_pinned_overlay_after_capture = bool(
            overlay is not None
            and overlay.isVisible()
            and overlay.is_pinned
            and overlay.last_text.strip()
        )
        # Recreate the selection overlay for each capture so Windows/DWM does not
        # briefly reuse the previous transparent top-level surface on the first frame.
        recreate_selection_overlay = getattr(self.window, "recreate_selection_overlay", None)
        if callable(recreate_selection_overlay):
            recreate_selection_overlay()
        self.window.log_tr("log_capture_started", preset=self.window.pending_capture_prompt_preset.name, target=self.window.pending_capture_target_language)
        self.window.capture_workflow_active = True
        self.window.restore_window_after_capture = restore_window_after_capture
        self.window.update_action_states()
        conceal_states = self._apply_capture_window_concealment(self._capture_conceal_targets(overlay))
        try:
            self.window.hide()
            if overlay is not None:
                overlay.hide()
            hidden_dialog_count = self._hide_app_owned_windows_for_capture()
            self._clear_capture_desktop_snapshot()
            barrier_elapsed, dwm_flushed = self._run_capture_hide_barrier()
            log_debug = getattr(self.window, "log_debug", None)
            if callable(log_debug):
                log_debug(
                    "截圖隱藏屏障完成｜"
                    f"barrier={barrier_elapsed * 1000:.0f}ms｜"
                    f"dwm_flush={'yes' if dwm_flushed else 'no'}｜"
                    f"hidden_dialogs={hidden_dialog_count}"
                )
            snapshot_started_at = time.perf_counter()
            snapshot, background_pixmap = self._capture_desktop_snapshot()
            snapshot_elapsed = time.perf_counter() - snapshot_started_at
        finally:
            self._restore_capture_window_concealment(conceal_states)
        self._set_capture_desktop_snapshot(snapshot, background_pixmap)
        self.window.log(
            "截圖快照已凍結｜"
            f"snapshot={snapshot_elapsed * 1000:.0f}ms｜"
            f"screens={len(getattr(snapshot, 'segments', ()))}"
        )
        self.window.selection_overlay.show_overlay()

    def finish_capture_workflow(self, restore_window: bool = False, *, clear_restore_window_state: bool = True):
        should_restore = restore_window and self.window.restore_window_after_capture
        self.window.capture_workflow_active = False
        self._clear_capture_desktop_snapshot()
        if clear_restore_window_state:
            self.window.restore_window_after_capture = False
        self.window.pending_capture_profile = None
        self.window.pending_capture_target_language = self.window.current_target_language()
        self.window.pending_capture_prompt_preset = None
        self.window.update_action_states()
        if should_restore:
            self.window.show_main_window()
            self._restore_hidden_app_owned_windows_after_capture()
        else:
            self.window.capture_hidden_owned_windows = []


    def _handle_capture_ready(self, png_bytes: bytes):
        self._update_preview_from_png_bytes(png_bytes)
        if self.window.capture_workflow_active:
            self.finish_capture_workflow(restore_window=False, clear_restore_window_state=False)
        overlay = self._existing_translation_overlay()
        if self.window.restore_pinned_overlay_after_capture and overlay is not None:
            overlay.restore_last_overlay()

    def handle_capture_cancelled(self):
        self.window.log_tr("log_capture_cancelled")
        self.finish_capture_workflow(restore_window=True)
        overlay = self._existing_translation_overlay()
        if self.window.restore_pinned_overlay_after_capture and overlay is not None:
            overlay.restore_last_overlay()
            self.window.restore_pinned_overlay_after_capture = False
        self.window.set_status("capture_cancelled")
        self.window.show_tray_toast(self.window.tr("capture_cancelled"))

    def _handle_image_translation_success(self, text: str, *, bbox, preset_name: str, capture_started_at: float, request_started_at: float, capture_elapsed: float, payload_bytes: int, locked_width: int | None = None):
        overlay = self._existing_translation_overlay()
        kwargs = {
            "preset_name": preset_name,
            "preserve_geometry": bool(overlay.is_pinned) if overlay is not None else False,
        }
        if locked_width is not None:
            kwargs["locked_width"] = locked_width
        self.window.overlay_presenter.show_translation(bbox, text, **kwargs)
        request_elapsed = time.perf_counter() - request_started_at
        total_elapsed = time.perf_counter() - capture_started_at
        log_debug = getattr(self.window, "log_debug", None)
        if callable(log_debug):
            log_debug(
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
        capture_started_at = time.perf_counter()
        capture_plan = self.window.screen_capture_service.build_capture_plan(bbox)
        self.window.screen_capture_service.log_capture_plan(bbox, capture_plan)
        snapshot = getattr(self.window, "capture_desktop_snapshot", None)
        if snapshot is not None:
            png_bytes = self.window.screen_capture_service.capture_bbox_png_bytes_from_snapshot(
                snapshot,
                bbox,
                capture_plan=capture_plan,
            )
            capture_log_label = "snapshot_crop"
        else:
            png_bytes = self.window.screen_capture_service.capture_bbox_png_bytes_threadsafe(
                bbox,
                capture_plan=capture_plan,
            )
            capture_log_label = "main_thread_capture"
        capture_elapsed = time.perf_counter() - capture_started_at
        payload_bytes = len(png_bytes)
        self._clear_capture_desktop_snapshot()
        log_debug = getattr(self.window, "log_debug", None)
        if callable(log_debug):
            log_debug(
                f"截圖同步抓取完成｜{capture_log_label}={capture_elapsed * 1000:.0f}ms｜png={payload_bytes / 1024:.1f}KB"
            )
        self.window.show_tray_toast(self.window.tr("tray_capturing"))

        profile = self.window.pending_capture_profile or self.window.build_profile_from_form(validate_name=False)
        target_language = self.window.pending_capture_target_language or self.window.current_target_language()
        prompt_preset = self.window.pending_capture_prompt_preset or self.window.build_prompt_preset_from_form(validate_name=False)
        prompt = build_image_request_prompt(prompt_preset.image_prompt, target_language=target_language)
        temperature = self.window.current_temperature()
        overlay = self._existing_translation_overlay()
        stream_enabled = bool(getattr(self.window, "current_stream_responses", lambda: True)())
        stream_request_token = self._begin_streaming_response_update_state() if stream_enabled else None
        stream_locked_width = self._stream_locked_width_for_bbox(bbox) if stream_enabled else None
        self._handle_capture_ready(png_bytes)

        stream_callback = None
        if stream_enabled:
            stream_callback = lambda partial_text, bbox=bbox, preset_name=prompt_preset.name, overlay=overlay, stream_locked_width=stream_locked_width, stream_request_token=stream_request_token: self._queue_streaming_response_update(
                {
                    "text": partial_text,
                    "bbox": bbox,
                    "preset_name": preset_name,
                    "preserve_manual_position": False,
                    "preserve_geometry": bool(overlay.is_pinned) if overlay is not None else False,
                    "_stream_request_token": stream_request_token,
                    "locked_width": stream_locked_width,
                }
            )
        else:
            self.clear_streaming_response_update_state()

        def capture_and_request(request_context):
            if request_context is not None and request_context.is_cancelled():
                raise RequestCancelledError()
            request_started_at = time.perf_counter()
            text = self.window.api_client.request_image_png(
                png_bytes,
                profile,
                prompt,
                temperature,
                stream=stream_enabled,
                stream_callback=stream_callback,
                request_context=request_context,
            )
            return text, capture_elapsed, payload_bytes, request_started_at

        def handle_image_request_success(result, *, bbox=bbox, preset_name=prompt_preset.name, capture_started_at=capture_started_at, stream_request_token=stream_request_token):
            self._complete_streaming_response_update_state(stream_request_token)
            self._handle_image_translation_success(
                result[0],
                bbox=bbox,
                preset_name=preset_name,
                capture_started_at=capture_started_at,
                request_started_at=result[3],
                capture_elapsed=result[1],
                payload_bytes=result[2],
                locked_width=stream_locked_width,
            )

        self.window.run_worker(
            capture_and_request,
            handle_image_request_success,
            operation_key="translation",
            cancellable=True,
        )
