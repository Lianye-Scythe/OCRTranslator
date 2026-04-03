import time
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtNetwork import QLocalServer
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMenu, QMessageBox, QSystemTrayIcon

from ..api_client import ApiClient
from ..config_store import load_config, save_config
from ..hotkey_listener import HotkeyListener, find_hotkey_conflicts
from ..i18n import I18N
from ..profile_utils import normalize_provider_name
from ..runtime_paths import APP_SERVER_NAME
from ..services.image_capture import ScreenCaptureService
from ..services.overlay_presenter import OverlayPresenter
from ..services.request_workflow import RequestWorkflowController
from ..services.runtime_log import RuntimeLogStore
from ..workers import AppBridge, WorkerThread
from .main_window_layout import MainWindowLayoutMixin
from .main_window_settings_layout import MainWindowSettingsLayoutMixin
from .main_window_prompts import MainWindowPromptPresetsMixin
from .main_window_profiles import MainWindowProfilesMixin
from .selection_overlay import SelectionOverlay
from .translation_overlay import TranslationOverlay


class OperationError(RuntimeError):
    def __init__(self, operation: str, original: Exception):
        super().__init__(str(original))
        self.operation = operation
        self.original = original


class MainWindow(MainWindowSettingsLayoutMixin, MainWindowLayoutMixin, MainWindowPromptPresetsMixin, MainWindowProfilesMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.bridge = AppBridge()
        self.bridge.action_requested.connect(self.handle_action_request)
        self.bridge.worker_success.connect(self._handle_worker_success)
        self.bridge.worker_error.connect(self.handle_error)
        self.bridge.hotkey_recorded.connect(self.handle_recorded_hotkey)

        self.config = load_config()
        self.log_store = RuntimeLogStore(max_entries=100)
        self.api_client = ApiClient(self.log)
        self.screen_capture_service = ScreenCaptureService(self.log)
        self.hotkey_listener = None
        self.hotkey_record_listener = None
        self.hotkey_listener_paused_for_recording = False
        self.registered_hotkeys: dict[str, str] = {}
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
        self.pending_capture_prompt_preset = None
        self.config_save_timer = QTimer(self)
        self.config_save_timer.setSingleShot(True)
        self.config_save_timer.timeout.connect(self.persist_config_now)

        self.selection_overlay = SelectionOverlay()
        self.selection_overlay.selected.connect(self.handle_selection)
        self.selection_overlay.cancelled.connect(self.handle_capture_cancelled)

        self.translation_overlay = TranslationOverlay(self)
        self.translation_overlay.request_font_zoom.connect(self.adjust_overlay_font_size)
        self.translation_overlay.overlay_resized.connect(self.handle_overlay_resized)
        self.overlay_presenter = OverlayPresenter(self, self.translation_overlay)
        self.request_workflow = RequestWorkflowController(self)

        self.build_ui()
        self.setup_tray()
        self.apply_styles()
        self.apply_language()
        self.load_profile_to_form(self.config.active_profile_name)
        self.load_prompt_preset_to_form(self.config.active_prompt_preset_name)
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

    def current_selection_hotkey(self) -> str:
        if hasattr(self, "selection_hotkey_edit"):
            return self.selection_hotkey_edit.text().strip() or self.config.selection_hotkey
        return self.config.selection_hotkey

    def current_input_hotkey(self) -> str:
        if hasattr(self, "input_hotkey_edit"):
            return self.input_hotkey_edit.text().strip() or self.config.input_hotkey
        return self.config.input_hotkey

    def current_mode(self) -> str:
        if hasattr(self, "mode_combo"):
            return self.mode_combo.currentData() or self.config.mode
        return self.config.mode

    def current_temperature(self) -> float:
        if hasattr(self, "temperature_spin"):
            return float(self.temperature_spin.value())
        return float(self.config.temperature)

    def current_overlay_width(self) -> int:
        if hasattr(self, "overlay_width_spin"):
            return int(self.overlay_width_spin.value())
        return int(self.config.overlay_width)

    def current_overlay_height(self) -> int:
        if hasattr(self, "overlay_height_spin"):
            return int(self.overlay_height_spin.value())
        return int(self.config.overlay_height)

    def current_margin(self) -> int:
        if hasattr(self, "overlay_margin_spin"):
            return int(self.overlay_margin_spin.value())
        return int(self.config.margin)

    def current_overlay_font_family(self) -> str:
        if hasattr(self, "overlay_font_combo"):
            return self.overlay_font_combo.currentFont().family()
        return self.config.overlay_font_family

    def current_overlay_font_size(self) -> int:
        if hasattr(self, "overlay_font_size_spin"):
            return self.overlay_font_size_spin.value()
        return self.config.overlay_font_size

    def handle_action_request(self, action: str):
        action_map = {
            "capture": self.request_workflow.start_selection,
            "selection_text": self.request_workflow.translate_selected_text,
            "manual_input": self.request_workflow.open_prompt_input_dialog,
        }
        handler = action_map.get(action)
        if handler:
            handler()

    def handle_overlay_resized(self, width: int, height: int):
        self.config.overlay_width = int(width)
        self.config.overlay_height = int(height)
        self._suppress_form_tracking = True
        try:
            if hasattr(self, "overlay_width_spin"):
                self.overlay_width_spin.setValue(int(width))
            if hasattr(self, "overlay_height_spin"):
                self.overlay_height_spin.setValue(int(height))
        finally:
            self._suppress_form_tracking = False
        self.schedule_config_persist()
        self.set_status("overlay_resized", width=int(width), height=int(height))

    def background_busy(self) -> bool:
        return self.fetch_models_in_progress or self.test_profile_in_progress or self.translation_in_progress

    def prepare_request_context(self, *, focus_first_invalid: bool = True):
        return self.request_workflow.prepare_request_context(focus_first_invalid=focus_first_invalid)

    def set_operation_state(self, operation: str, active: bool):
        setattr(self, f"{operation}_in_progress", active)
        self.update_action_states()

    def update_action_states(self):
        if not hasattr(self, "fetch_models_button"):
            return
        any_background_busy = self.fetch_models_in_progress or self.test_profile_in_progress or self.translation_in_progress
        capture_busy = self.capture_workflow_active or self.translation_in_progress or self.fetch_models_in_progress or self.test_profile_in_progress
        for widget_name in (
            "profile_name_edit",
            "provider_combo",
            "base_url_edit",
            "model_combo",
            "api_keys_edit",
            "api_keys_toggle_button",
            "retry_count_spin",
            "retry_interval_spin",
            "target_language_edit",
            "ui_language_combo",
            "hotkey_edit",
            "hotkey_record_button",
            "selection_hotkey_edit",
            "selection_hotkey_record_button",
            "input_hotkey_edit",
            "input_hotkey_record_button",
            "overlay_font_combo",
            "overlay_font_size_spin",
            "mode_combo",
            "prompt_preset_combo",
            "new_prompt_preset_button",
            "delete_prompt_preset_button",
            "prompt_preset_name_edit",
            "image_prompt_edit",
            "text_prompt_edit",
            "temperature_spin",
            "overlay_width_spin",
            "overlay_height_spin",
            "overlay_margin_spin",
            "close_to_tray_on_close_checkbox",
        ):
            if hasattr(self, widget_name):
                getattr(self, widget_name).setEnabled(not any_background_busy)
        self.fetch_models_button.setText(self.tr("fetch_models_busy") if self.fetch_models_in_progress else self.tr("fetch_models"))
        self.test_button.setText(self.tr("test_api_busy") if self.test_profile_in_progress else self.tr("test_api"))
        capture_text = self.tr("start_capture_busy") if self.translation_in_progress else self.tr("start_capture")
        self.hero_capture_button.setText(capture_text)
        self.preview_capture_button.setText(capture_text)
        self.fetch_models_button.setEnabled(not any_background_busy)
        self.test_button.setEnabled(not any_background_busy)
        self.save_button.setEnabled(not any_background_busy)
        self.hero_tray_button.setEnabled(not any_background_busy)
        self.hero_capture_button.setEnabled(not capture_busy)
        self.preview_capture_button.setEnabled(not capture_busy)
        self.profile_combo.setEnabled(not any_background_busy)
        self.new_profile_button.setEnabled(not any_background_busy)
        self.delete_profile_button.setEnabled(not any_background_busy)
        if hasattr(self, "close_to_tray_on_close_checkbox"):
            self.close_to_tray_on_close_checkbox.setEnabled(bool(self.tray) and not any_background_busy)
            self.close_to_tray_on_close_checkbox.setToolTip("" if self.tray else self.tr("tray_unavailable"))
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
        if self.log_store.has_entries():
            self.log_text.setPlainText(self.log_store.as_text())
        else:
            self.log_text.setPlainText("")
            self.log_text.setPlaceholderText(self.tr("logs_empty"))

    def log(self, message: str):
        self.log_store.add(message)
        if hasattr(self, "log_text"):
            self.log_text.setPlaceholderText("")
            self.refresh_log_view()

    def clear_logs(self):
        self.log_store.clear()
        self.refresh_log_view()
        self.set_status("logs_cleared")

    def persist_config_now(self):
        try:
            save_config(self.config)
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def export_logs(self):
        try:
            if not self.log_store.has_entries():
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
            self.log_store.export(target_path)
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

    def build_hotkey_actions(self, config=None) -> dict[str, str]:
        target_config = config or self.config
        return {
            "capture": target_config.hotkey,
            "selection_text": target_config.selection_hotkey,
            "manual_input": target_config.input_hotkey,
        }

    def validate_hotkey_actions(self, hotkey_actions: dict[str, str]) -> dict[str, str]:
        normalized_actions = {}
        for action, hotkey in hotkey_actions.items():
            if not self.hotkey_has_modifier(hotkey):
                raise ValueError(self.tr("validation_hotkey_requires_modifier"))
            normalized = self.normalize_hotkey(hotkey)
            if normalized in normalized_actions:
                raise ValueError(self.tr("validation_hotkey_duplicate", hotkey=hotkey))
            normalized_actions[normalized] = action
        conflicts = find_hotkey_conflicts(hotkey_actions)
        if conflicts:
            kind, left_action, right_action = conflicts[0]
            left_hotkey = hotkey_actions.get(left_action, "")
            right_hotkey = hotkey_actions.get(right_action, "")
            if kind == "duplicate":
                raise ValueError(self.tr("validation_hotkey_duplicate", hotkey=left_hotkey or right_hotkey))
            raise ValueError(self.tr("validation_hotkey_conflict", hotkey_a=left_hotkey, hotkey_b=right_hotkey))
        return hotkey_actions

    def setup_hotkey_listener(self, initial: bool = False, *, config=None, raise_on_error: bool = False):
        previous_hotkeys = dict(getattr(self, "registered_hotkeys", {}))
        previous_listener = self.hotkey_listener
        if previous_listener:
            previous_listener.stop()
        self.hotkey_listener = None
        self.registered_hotkeys = {}
        try:
            hotkey_actions = self.validate_hotkey_actions(self.build_hotkey_actions(config))
            listener = HotkeyListener(
                hotkey_actions,
                lambda action: self.bridge.action_requested.emit(action),
                log_func=self.log,
            )
            listener.start()
            self.hotkey_listener = listener
            self.registered_hotkeys = hotkey_actions
            self.log(
                "Hotkeys registered: "
                f"capture={hotkey_actions['capture']} | "
                f"selection_text={hotkey_actions['selection_text']} | "
                f"manual_input={hotkey_actions['manual_input']}"
            )
            if not initial:
                self.set_status("hotkeys_registered")
            return True
        except Exception as exc:  # noqa: BLE001
            self.log(f"Hotkey registration failed: {exc}")
            if previous_hotkeys:
                try:
                    restored_listener = HotkeyListener(
                        previous_hotkeys,
                        lambda action: self.bridge.action_requested.emit(action),
                        log_func=self.log,
                    )
                    restored_listener.start()
                    self.hotkey_listener = restored_listener
                    self.registered_hotkeys = previous_hotkeys
                    self.log("Previous hotkeys restored after registration failure")
                except Exception as restore_exc:  # noqa: BLE001
                    self.log(f"Failed to restore previous hotkeys: {restore_exc}")
            if hasattr(self, "status_label"):
                self.set_status("hotkey_register_failed", error=exc)
            if not initial:
                QMessageBox.critical(self, self.tr("error_title"), self.tr("hotkey_register_failed", error=exc))
            if raise_on_error:
                raise
            return False

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
        return RequestWorkflowController.profile_request_signature(profile)

    def form_matches_profile_request(self, signature: tuple) -> bool:
        return self.request_workflow.form_matches_profile_request(signature)

    def fetch_models(self):
        try:
            self.request_workflow.fetch_models()
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def on_models_loaded(self, result):
        self.request_workflow.on_models_loaded(result)

    def test_profile(self):
        try:
            self.request_workflow.test_profile()
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def on_test_success(self, result):
        self.request_workflow.on_test_success(result)

    def set_status(self, key: str, **kwargs):
        self.current_status_key = key
        self.current_status_kwargs = kwargs
        self.status_label.setText(self.tr(key, **kwargs))

    def show_response_overlay(
        self,
        text: str,
        *,
        bbox=None,
        anchor_point: QPoint | None = None,
        preset_name: str = "",
        preserve_manual_position: bool = False,
        reflow_only: bool = False,
        complete_capture_flow: bool = False,
    ):
        self.overlay_presenter.show_response(
            text,
            bbox=bbox,
            anchor_point=anchor_point,
            preset_name=preset_name,
            preserve_manual_position=preserve_manual_position,
            reflow_only=reflow_only,
            complete_capture_flow=complete_capture_flow,
        )

    def submit_text_request(self, text: str, *, profile, target_language: str, prompt_preset, anchor_point: QPoint, source_key: str):
        self.request_workflow.submit_text_request(
            text,
            profile=profile,
            target_language=target_language,
            prompt_preset=prompt_preset,
            anchor_point=anchor_point,
            source_key=source_key,
        )

    def translate_selected_text(self):
        try:
            self.request_workflow.translate_selected_text()
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def open_prompt_input_dialog(self):
        try:
            self.request_workflow.open_prompt_input_dialog()
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def start_selection(self):
        try:
            self.request_workflow.start_selection()
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def finish_capture_workflow(self, restore_window: bool = False):
        self.request_workflow.finish_capture_workflow(restore_window=restore_window)

    def handle_capture_cancelled(self):
        self.request_workflow.handle_capture_cancelled()

    def handle_selection(self, bbox):
        try:
            self.request_workflow.handle_selection(bbox)
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def show_translation(
        self,
        bbox,
        text: str,
        *,
        preset_name: str = "",
        preserve_manual_position: bool = False,
        reflow_only: bool = False,
    ):
        self.overlay_presenter.show_translation(
            bbox,
            text,
            preset_name=preset_name,
            preserve_manual_position=preserve_manual_position,
            reflow_only=reflow_only,
        )

    def adjust_overlay_font_size(self, direction: int):
        self.overlay_presenter.adjust_font_size(direction)

    def update_preview(self, image: Image.Image):
        self.preview_pixmap = self.screen_capture_service.build_preview_pixmap(image)
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
        scaled = self.screen_capture_service.scale_preview_pixmap(self.preview_pixmap, viewport_size)
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
        if not self.is_quitting and getattr(self.config, "close_to_tray_on_close", False) and self.tray:
            self.log("Close button redirected to minimize-to-tray behavior")
            self.minimize_to_tray()
            event.ignore()
            return
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
        try:
            self.stop_hotkey_recording(cancelled=False)
        except Exception:  # noqa: BLE001
            pass
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        self.registered_hotkeys = {}
        if hasattr(self, "instance_server") and self.instance_server and self.instance_server.isListening():
            self.instance_server.close()
            QLocalServer.removeServer(APP_SERVER_NAME)
        self.flush_pending_config_save()
        self.translation_overlay.close()
        if self.tray:
            self.tray.hide()
        QApplication.instance().quit()
        return True
