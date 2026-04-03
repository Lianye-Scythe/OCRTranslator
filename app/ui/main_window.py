import io
import time
from collections import deque
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageGrab
from pynput import keyboard
from PySide6.QtCore import QBuffer, QByteArray, QRect, Qt, QTimer
from PySide6.QtGui import QAction, QGuiApplication, QPixmap
from PySide6.QtNetwork import QLocalServer
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMenu, QMessageBox, QSystemTrayIcon

from ..api_client import ApiClient
from ..config_store import load_config, save_config
from ..constants import APP_SERVER_NAME, I18N
from ..profile_utils import normalize_model_value, normalize_provider_name, unique_non_empty
from ..workers import AppBridge, WorkerThread
from .main_window_layout import MainWindowLayoutMixin
from .main_window_profiles import MainWindowProfilesMixin
from .overlay_positioning import compute_overlay_position, fit_overlay_size, get_target_screen_rect
from .selection_overlay import SelectionOverlay
from .translation_overlay import TranslationOverlay


class OperationError(RuntimeError):
    def __init__(self, operation: str, original: Exception):
        super().__init__(str(original))
        self.operation = operation
        self.original = original


class MainWindow(MainWindowLayoutMixin, MainWindowProfilesMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.bridge = AppBridge()
        self.bridge.hotkey_triggered.connect(self.start_selection)
        self.bridge.worker_success.connect(self._handle_worker_success)
        self.bridge.worker_error.connect(self.handle_error)

        self.config = load_config()
        self.logs = deque(maxlen=100)
        self.api_client = ApiClient(self.log)
        self.hotkey_listener = None
        self.registered_hotkey = None
        self.preview_pixmap = None
        self.current_status_key = "ready"
        self.current_status_kwargs = {}
        self.is_quitting = False
        self.capture_workflow_active = False
        self.restore_window_after_capture = False
        self.restore_pinned_overlay_after_capture = False
        self._form_provider = normalize_provider_name(self.config.api_profiles[0].provider if self.config.api_profiles else "gemini")
        self.icon = self.create_app_icon()
        self.has_unsaved_changes = False
        self._suppress_form_tracking = False
        self.fetch_models_in_progress = False
        self.test_profile_in_progress = False
        self.translation_in_progress = False
        self._fetch_models_request_id = 0
        self._test_profile_request_id = 0
        self.pending_capture_profile = None
        self.pending_capture_target_language = self.config.target_language
        self.config_save_timer = QTimer(self)
        self.config_save_timer.setSingleShot(True)
        self.config_save_timer.timeout.connect(self.persist_config_now)

        self.selection_overlay = SelectionOverlay()
        self.selection_overlay.selected.connect(self.handle_selection)
        self.selection_overlay.cancelled.connect(self.handle_capture_cancelled)

        self.translation_overlay = TranslationOverlay(self)
        self.translation_overlay.request_font_zoom.connect(self.adjust_overlay_font_size)

        self.build_ui()
        self.setup_tray()
        self.apply_styles()
        self.apply_language()
        self.load_profile_to_form(self.config.active_profile_name)
        self.setup_instance_server()
        self.setup_hotkey_listener(initial=True)
        self.log("Application started")

    def tr(self, key: str, **kwargs) -> str:
        lang = self.current_ui_language()
        text = I18N[lang].get(key, key)
        return text.format(**kwargs) if kwargs else text

    def current_ui_language(self) -> str:
        if hasattr(self, "ui_language_combo"):
            value = self.ui_language_combo.currentText().strip()
            if value in I18N:
                return value
        return self.config.ui_language if self.config.ui_language in I18N else "zh-TW"

    def current_target_language(self) -> str:
        if hasattr(self, "target_language_edit"):
            return self.target_language_edit.text().strip() or self.config.target_language
        return self.config.target_language

    def current_hotkey(self) -> str:
        if hasattr(self, "hotkey_edit"):
            return self.hotkey_edit.text().strip() or self.config.hotkey
        return self.config.hotkey

    def current_mode(self) -> str:
        if hasattr(self, "mode_combo"):
            return self.mode_combo.currentData() or self.config.mode
        return self.config.mode

    def current_overlay_font_family(self) -> str:
        if hasattr(self, "overlay_font_combo"):
            return self.overlay_font_combo.currentFont().family()
        return self.config.overlay_font_family

    def current_overlay_font_size(self) -> int:
        if hasattr(self, "overlay_font_size_spin"):
            return self.overlay_font_size_spin.value()
        return self.config.overlay_font_size

    def set_operation_state(self, operation: str, active: bool):
        setattr(self, f"{operation}_in_progress", active)
        self.update_action_states()

    def update_action_states(self):
        if not hasattr(self, "fetch_models_button"):
            return
        api_request_busy = self.fetch_models_in_progress or self.test_profile_in_progress
        any_background_busy = self.fetch_models_in_progress or self.test_profile_in_progress or self.translation_in_progress
        capture_busy = self.capture_workflow_active or self.translation_in_progress or self.fetch_models_in_progress or self.test_profile_in_progress
        for widget_name in ("profile_name_edit", "provider_combo", "base_url_edit", "model_combo", "api_keys_edit", "retry_count_spin", "retry_interval_spin"):
            if hasattr(self, widget_name):
                getattr(self, widget_name).setEnabled(not api_request_busy)
        self.fetch_models_button.setText(self.tr("fetch_models_busy") if self.fetch_models_in_progress else self.tr("fetch_models"))
        self.test_button.setText(self.tr("test_api_busy") if self.test_profile_in_progress else self.tr("test_api"))
        capture_text = self.tr("start_capture_busy") if self.translation_in_progress else self.tr("start_capture")
        self.hero_capture_button.setText(capture_text)
        self.preview_capture_button.setText(capture_text)
        self.fetch_models_button.setEnabled(not any_background_busy)
        self.test_button.setEnabled(not any_background_busy)
        self.save_button.setEnabled(not any_background_busy)
        self.hero_capture_button.setEnabled(not capture_busy)
        self.preview_capture_button.setEnabled(not capture_busy)
        self.profile_combo.setEnabled(not any_background_busy)
        self.new_profile_button.setEnabled(not any_background_busy)
        self.delete_profile_button.setEnabled(not any_background_busy)
        if getattr(self, "tray", None):
            self.tray_capture_action.setEnabled(not capture_busy)

    def setup_instance_server(self):
        try:
            QLocalServer.removeServer(APP_SERVER_NAME)
        except Exception:  # noqa: BLE001
            pass
        self.instance_server = QLocalServer(self)
        self.instance_server.newConnection.connect(self._handle_instance_activation)
        if not self.instance_server.listen(APP_SERVER_NAME):
            self.log(f"Instance server listen failed: {self.instance_server.errorString()}")

    def _handle_instance_activation(self):
        while self.instance_server.hasPendingConnections():
            socket = self.instance_server.nextPendingConnection()
            socket.readyRead.connect(lambda socket=socket: self._read_instance_message(socket))
            socket.disconnected.connect(socket.deleteLater)

    def _read_instance_message(self, socket):
        message = bytes(socket.readAll()).decode("utf-8", errors="ignore").strip()
        if message == "show":
            self.log("Received activation request from another launch")
            self.show_main_window()
        elif message == "capture":
            self.log("Received capture request from another launch")
            self.show_main_window()
            self.start_selection()
        socket.disconnectFromServer()

    def setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = None
            self.log("System tray is not available on this environment")
            return
        self.tray = QSystemTrayIcon(self.icon, self)
        self.tray.setToolTip(self.tr("tray_title"))
        menu = QMenu(self)
        self.tray_show_action = QAction(self)
        self.tray_capture_action = QAction(self)
        self.tray_quit_action = QAction(self)
        self.tray_show_action.triggered.connect(self.show_main_window)
        self.tray_capture_action.triggered.connect(self.start_selection)
        self.tray_quit_action.triggered.connect(self.quit_app)
        menu.addAction(self.tray_show_action)
        menu.addAction(self.tray_capture_action)
        if menu.actions():
            menu.addSeparator()
        menu.addAction(self.tray_quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()
        self.update_action_states()

    def on_tray_activated(self, reason):
        if not self.tray:
            return
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_main_window()

    def update_tray_texts(self):
        if not self.tray:
            return
        self.tray.setToolTip(self.tr("tray_title"))
        self.tray_show_action.setText(self.tr("tray_show"))
        self.tray_capture_action.setText(self.tr("tray_capture"))
        self.tray_quit_action.setText(self.tr("tray_quit"))

    def refresh_log_view(self):
        if not hasattr(self, "log_text"):
            return
        if self.logs:
            self.log_text.setPlainText("\n".join(reversed(self.logs)))
        else:
            self.log_text.setPlainText("")
            self.log_text.setPlaceholderText(self.tr("logs_empty"))

    def log(self, message: str):
        self.logs.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        if hasattr(self, "log_text"):
            self.log_text.setPlaceholderText("")
            self.refresh_log_view()

    def clear_logs(self):
        self.logs.clear()
        self.refresh_log_view()
        self.set_status("logs_cleared")

    def persist_config_now(self):
        try:
            save_config(self.config)
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def export_logs(self):
        try:
            if not self.logs:
                self.set_status("logs_export_empty")
                return
            default_name = f"ocrtranslator-log-{time.strftime('%Y%m%d-%H%M%S')}.txt"
            target_path, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("export_logs_dialog_title"),
                str(Path.cwd() / default_name),
                self.tr("export_logs_filter"),
            )
            if not target_path:
                return
            Path(target_path).write_text("\n".join(reversed(self.logs)) + "\n", encoding="utf-8")
            self.log(f"Runtime log exported: {target_path}")
            self.set_status("logs_exported", path=Path(target_path).name)
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def schedule_config_persist(self, delay_ms: int = 350):
        self.config_save_timer.start(delay_ms)

    def flush_pending_config_save(self):
        if not self.config_save_timer.isActive():
            return
        self.config_save_timer.stop()
        self.persist_config_now()

    def normalize_hotkey(self, hotkey_text: str) -> str:
        parts = [part.strip().lower() for part in hotkey_text.replace("-", "+").split("+") if part.strip()]
        key_map = {
            "ctrl": "<ctrl>",
            "control": "<ctrl>",
            "alt": "<alt>",
            "shift": "<shift>",
            "cmd": "<cmd>",
            "win": "<cmd>",
            "windows": "<cmd>",
            "enter": "<enter>",
            "return": "<enter>",
            "tab": "<tab>",
            "space": "<space>",
            "backspace": "<backspace>",
            "delete": "<delete>",
            "insert": "<insert>",
            "home": "<home>",
            "end": "<end>",
            "pageup": "<page_up>",
            "page_up": "<page_up>",
            "pagedown": "<page_down>",
            "page_down": "<page_down>",
            "left": "<left>",
            "right": "<right>",
            "up": "<up>",
            "down": "<down>",
        }
        mapped = [key_map.get(part, part) for part in parts]
        if not mapped:
            raise ValueError("Empty hotkey")
        mapped = [f"<{part}>" if part.startswith("f") and part[1:].isdigit() else part for part in mapped]
        return "+".join(mapped)

    def setup_hotkey_listener(self, initial: bool = False):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        self.registered_hotkey = None
        try:
            if not self.hotkey_has_modifier(self.config.hotkey):
                raise ValueError(self.tr("validation_hotkey_requires_modifier"))
            normalized = self.normalize_hotkey(self.config.hotkey)
            self.hotkey_listener = keyboard.GlobalHotKeys({normalized: self.bridge.hotkey_triggered.emit})
            self.hotkey_listener.start()
            self.registered_hotkey = self.config.hotkey
            self.log(f"Hotkey listener registered: {self.config.hotkey}")
            if not initial:
                self.set_status("hotkey_registered", hotkey=self.config.hotkey)
        except Exception as exc:  # noqa: BLE001
            self.log(f"Hotkey registration failed: {exc}")
            if not initial:
                QMessageBox.critical(self, self.tr("error_title"), self.tr("hotkey_register_failed", error=exc))

    def run_worker(self, fn, on_success, *, operation_key: str | None = None):
        worker_target = fn
        worker_callback = on_success

        if operation_key:
            self.set_operation_state(operation_key, True)

            def guarded_target():
                try:
                    return fn()
                except Exception as exc:  # noqa: BLE001
                    raise OperationError(operation_key, exc) from exc

            def guarded_success(result):
                self.set_operation_state(operation_key, False)
                if callable(on_success):
                    on_success(result)

            worker_target = guarded_target
            worker_callback = guarded_success

        WorkerThread(worker_target, self.bridge, worker_callback).start()

    def _handle_worker_success(self, callback, result):
        if callable(callback):
            try:
                callback(result)
            except Exception as exc:  # noqa: BLE001
                self.handle_error(exc)

    @staticmethod
    def profile_request_signature(profile) -> tuple:
        return (
            profile.name,
            profile.provider,
            profile.base_url.strip(),
            tuple(profile.api_keys),
        )

    def form_matches_profile_request(self, signature: tuple) -> bool:
        try:
            current_profile = self.build_profile_from_form()
        except Exception:  # noqa: BLE001
            return False
        return self.profile_request_signature(current_profile) == signature

    def fetch_models(self):
        try:
            if self.fetch_models_in_progress or self.test_profile_in_progress or self.translation_in_progress:
                return
            valid, first_error = self.validate_form_inputs(focus_first_invalid=True)
            if not valid:
                self.set_status("validation_failed")
                self.log(f"Fetch models blocked by validation: {first_error}")
                return
            profile = self.build_profile_from_form()
            request_id = self._fetch_models_request_id = self._fetch_models_request_id + 1
            request_signature = self.profile_request_signature(profile)
            self.log(f"Fetching models for profile: {profile.name}")
            self.run_worker(
                lambda: (request_id, request_signature, profile.provider, self.api_client.list_models(profile)),
                self.on_models_loaded,
                operation_key="fetch_models",
            )
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def on_models_loaded(self, result):
        request_id, request_signature, provider, models = result
        if request_id != self._fetch_models_request_id:
            self.log("Discarded stale model list result from an older request")
            return
        if not self.form_matches_profile_request(request_signature):
            self.log("Discarded model list result because the form changed while the request was running")
            return
        normalized_models = unique_non_empty(normalize_model_value(item, provider) for item in models)
        if not normalized_models:
            return
        current_model = self.normalize_model_name(self.model_combo.currentText(), provider)
        self._suppress_form_tracking = True
        try:
            self.model_combo.blockSignals(True)
            self.model_combo.clear()
            self.model_combo.addItems([self.display_model_name(item, provider) for item in normalized_models])
            selected_model = current_model if current_model in normalized_models else normalized_models[0]
            self.model_combo.setCurrentText(self.display_model_name(selected_model, provider))
        finally:
            self.model_combo.blockSignals(False)
            self._suppress_form_tracking = False
        self.on_form_input_changed()
        self.set_status("models_loaded", count=len(normalized_models))
        self.log(f"Loaded {len(normalized_models)} models")

    def test_profile(self):
        try:
            if self.fetch_models_in_progress or self.test_profile_in_progress or self.translation_in_progress:
                return
            valid, first_error = self.validate_form_inputs(focus_first_invalid=True)
            if not valid:
                self.set_status("validation_failed")
                self.log(f"Test API blocked by validation: {first_error}")
                return
            profile = self.build_profile_from_form()
            request_id = self._test_profile_request_id = self._test_profile_request_id + 1
            request_signature = self.profile_request_signature(profile)
            self.log(f"Testing profile: {profile.name}")
            self.run_worker(
                lambda: (request_id, request_signature, self.api_client.test_profile(profile)),
                self.on_test_success,
                operation_key="test_profile",
            )
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def on_test_success(self, result):
        request_id, request_signature, message = result
        if request_id != self._test_profile_request_id or not self.form_matches_profile_request(request_signature):
            self.log("Discarded stale API test result because the form changed while the request was running")
            return
        self.log(message)
        self.set_status("test_success")

    def set_status(self, key: str, **kwargs):
        self.current_status_key = key
        self.current_status_kwargs = kwargs
        self.status_label.setText(self.tr(key, **kwargs))

    def start_selection(self):
        try:
            if self.capture_workflow_active:
                self.log("Capture request ignored because another capture workflow is still active")
                return
            if self.fetch_models_in_progress or self.test_profile_in_progress or self.translation_in_progress:
                self.log("Capture request ignored because another background operation is still running")
                return
            valid, first_error = self.validate_form_inputs(focus_first_invalid=True)
            if not valid:
                self.set_status("validation_failed")
                self.log(f"Capture blocked by validation: {first_error}")
                return
            restore_window_after_capture = self.isVisible() and not self.isMinimized()
            self.pending_capture_profile = self.build_profile_from_form()
            self.pending_capture_target_language = self.current_target_language()
            self.restore_pinned_overlay_after_capture = bool(
                self.translation_overlay.isVisible() and self.translation_overlay.is_pinned and self.translation_overlay.last_text.strip()
            )
            self.capture_workflow_active = True
            self.restore_window_after_capture = restore_window_after_capture
            self.update_action_states()
            self.hide()
            self.translation_overlay.hide()
            self.selection_overlay.show_overlay()
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def finish_capture_workflow(self, restore_window: bool = False):
        should_restore = restore_window and self.restore_window_after_capture
        self.capture_workflow_active = False
        self.restore_window_after_capture = False
        self.pending_capture_profile = None
        self.pending_capture_target_language = self.current_target_language()
        self.update_action_states()
        if should_restore:
            self.show_main_window()

    def handle_capture_cancelled(self):
        self.log("Capture cancelled")
        self.finish_capture_workflow(restore_window=True)
        if self.restore_pinned_overlay_after_capture:
            self.translation_overlay.restore_last_overlay()
            self.restore_pinned_overlay_after_capture = False
        self.set_status("capture_cancelled")
        self.show_tray_toast(self.tr("capture_cancelled"))

    @staticmethod
    def pixmap_to_image(pixmap: QPixmap) -> Image.Image:
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.WriteOnly)
        pixmap.save(buffer, "PNG")
        buffer.close()
        return Image.open(io.BytesIO(byte_array.data())).convert("RGB")

    def capture_bbox_image(self, bbox) -> Image.Image:
        left, top, right, bottom = bbox
        width = max(1, right - left)
        height = max(1, bottom - top)
        capture_rect = QRect(left, top, width, height)
        screen = QGuiApplication.screenAt(capture_rect.center()) or QGuiApplication.primaryScreen()
        if screen and screen.geometry().contains(capture_rect.topLeft()) and screen.geometry().contains(capture_rect.bottomRight()):
            local_rect = capture_rect.translated(-screen.geometry().topLeft())
            pixmap = screen.grabWindow(0, local_rect.x(), local_rect.y(), local_rect.width(), local_rect.height())
            if not pixmap.isNull():
                return self.pixmap_to_image(pixmap)
        self.log("Qt capture crossed screen bounds or returned empty data, falling back to Pillow all-screen capture")
        return ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True).convert("RGB")

    def handle_selection(self, bbox):
        try:
            image = self.capture_bbox_image(bbox)
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)
            return
        self.update_preview(image)
        self.set_status("capturing")
        self.show_tray_toast(self.tr("tray_capturing"))
        profile = self.pending_capture_profile or self.build_profile_from_form()
        target_language = self.pending_capture_target_language or self.current_target_language()
        self.run_worker(
            lambda: self.api_client.translate_image(image, profile, target_language, self.config.temperature),
            lambda text: self.show_translation(bbox, text),
            operation_key="translation",
        )

    def show_translation(self, bbox, text: str, *, preserve_manual_position: bool = False, reflow_only: bool = False):
        text = text or self.tr("empty_result")
        overlay_config = SimpleNamespace(
            mode=self.current_mode(),
            margin=self.config.margin,
            overlay_width=self.config.overlay_width,
            overlay_height=self.config.overlay_height,
        )
        self.translation_overlay.apply_typography()
        width, height = self.translation_overlay.calculate_size(text)
        width, height = fit_overlay_size(overlay_config, self.translation_overlay, bbox, text, width, height)
        if preserve_manual_position and self.translation_overlay.last_geometry is not None:
            screen_rect = get_target_screen_rect(bbox)
            margin = overlay_config.margin
            soft_margin = max(42, margin * 2)
            x = max(screen_rect.left() + margin, min(self.translation_overlay.last_geometry.x(), screen_rect.right() - width - margin + 1))
            y = max(screen_rect.top() + soft_margin, min(self.translation_overlay.last_geometry.y(), screen_rect.bottom() - height - soft_margin + 1))
        else:
            x, y = compute_overlay_position(overlay_config, bbox, width, height)
        self.translation_overlay.remember_context(bbox, text)
        self.translation_overlay.show_text(text, x, y, width, height, keep_manual_position=preserve_manual_position)
        if not reflow_only:
            self.finish_capture_workflow()
            self.restore_pinned_overlay_after_capture = False
            self.set_status("translated")
            self.log("Translation finished")

    def adjust_overlay_font_size(self, direction: int):
        if self.translation_in_progress:
            return
        current_size = self.current_overlay_font_size()
        new_size = max(10, min(32, current_size + direction))
        if new_size == current_size:
            return
        self.config.overlay_font_size = new_size
        self._suppress_form_tracking = True
        try:
            self.overlay_font_size_spin.setValue(new_size)
        finally:
            self._suppress_form_tracking = False
        self.schedule_config_persist()
        self.translation_overlay.apply_typography()
        self.set_status("font_zoomed", size=new_size)
        if self.translation_overlay.isVisible() and self.translation_overlay.last_bbox and self.translation_overlay.last_text:
            self.show_translation(
                self.translation_overlay.last_bbox,
                self.translation_overlay.last_text,
                preserve_manual_position=self.translation_overlay.manual_positioned,
                reflow_only=True,
            )

    def update_preview(self, image: Image.Image):
        preview = image.copy()
        preview.thumbnail((1280, 720))
        data = io.BytesIO()
        preview.save(data, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(data.getvalue(), "PNG")
        self.preview_pixmap = pixmap
        self.refresh_preview_pixmap()

    def refresh_preview_pixmap(self):
        if not hasattr(self, "preview_label"):
            return
        if not self.preview_pixmap:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText(self.tr("preview_placeholder"))
            return
        viewport_size = self.preview_label.contentsRect().size()
        if viewport_size.width() < 40 or viewport_size.height() < 40:
            self.preview_label.setText("")
            self.preview_label.setPixmap(self.preview_pixmap)
            return
        scaled = self.preview_pixmap.scaled(viewport_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setText("")
        self.preview_label.setPixmap(scaled)

    def show_tray_toast(self, message: str):
        if self.tray:
            self.tray.showMessage(self.tr("tray_title"), message, self.icon, 2500)

    def minimize_to_tray(self):
        if not self.tray:
            self.set_status("tray_unavailable")
            QMessageBox.information(self, self.tr("tray_title"), self.tr("tray_unavailable"))
            return
        self.hide()
        if not self.translation_overlay.is_pinned:
            self.translation_overlay.hide()
        self.set_status("tray_minimized")
        self.show_tray_toast(self.tr("tray_minimized"))

    def show_main_window(self):
        self.show()
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.raise_()
        self.activateWindow()

    def handle_error(self, exc: Exception):
        operation = getattr(exc, "operation", None)
        if operation in {"fetch_models", "test_profile", "translation"}:
            self.set_operation_state(operation, False)
        actual_exc = getattr(exc, "original", exc)
        is_capture_error = self.capture_workflow_active or operation == "translation"
        self.finish_capture_workflow(restore_window=is_capture_error)
        if is_capture_error and self.restore_pinned_overlay_after_capture:
            self.translation_overlay.restore_last_overlay()
            self.restore_pinned_overlay_after_capture = False
        self.set_status("translate_failed" if is_capture_error else "operation_failed")
        self.log(f"Error: {actual_exc}")
        display_message = getattr(actual_exc, "user_message", str(actual_exc))
        QMessageBox.critical(self if self.isVisible() else None, self.tr("error_title"), display_message)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.preview_pixmap:
            self.refresh_preview_pixmap()

    def closeEvent(self, event):
        if self.quit_app():
            event.accept()
        else:
            event.ignore()

    def quit_app(self):
        if self.is_quitting:
            return True
        if not self.resolve_unsaved_changes(for_exit=True):
            return False
        self.is_quitting = True
        self.log("Application exiting")
        try:
            self.selection_overlay.hide()
        except Exception:  # noqa: BLE001
            pass
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        self.registered_hotkey = None
        if hasattr(self, "instance_server") and self.instance_server and self.instance_server.isListening():
            self.instance_server.close()
            QLocalServer.removeServer(APP_SERVER_NAME)
        self.flush_pending_config_save()
        self.translation_overlay.close()
        if self.tray:
            self.tray.hide()
        QApplication.instance().quit()
        return True
