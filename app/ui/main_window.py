from __future__ import annotations

from html import escape
import os
import sys
import threading
import time
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QWidget

from ..app_defaults import DEFAULT_UI_LANGUAGE, normalize_theme_mode
from ..app_metadata import APP_VERSION
from ..config_store import load_config, save_config
from ..hotkey_utils import find_hotkey_conflicts, hotkey_has_primary_key, hotkey_unsupported_parts, normalize_hotkey_text
from ..i18n import I18N, normalize_ui_language
from ..operation_control import RequestCancelledError
from ..profile_utils import normalize_provider_name
from ..runtime_paths import APP_SERVER_NAME
from .message_boxes import show_critical_message, show_information_message, show_non_blocking_critical_message
from ..crash_reporter import safe_record_exception
from ..services.background_task_runner import BackgroundTaskRunner
from ..services.instance_server import InstanceServerService
from ..services.operation_manager import OperationManager
from ..services.request_workflow import RequestWorkflowController
from ..services.runtime_log import RuntimeLogStore
from ..services.startup_timing import StartupTimingTracker
from ..services.system_tray import SystemTrayService
from ..services.transient_toast import TransientToastService
from ..services.update_checker import UpdateCheckService
from ..workers import AppBridge, WorkerThread
from .theme_tokens import color, resolve_theme_name, set_theme_mode
from .main_window_layout import MainWindowLayoutMixin
from .main_window_settings_layout import MainWindowSettingsLayoutMixin
from .main_window_prompts import MainWindowPromptPresetsMixin
from .main_window_profiles import MainWindowProfilesMixin
from .selection_overlay import SelectionOverlay


class MainWindow(MainWindowSettingsLayoutMixin, MainWindowLayoutMixin, MainWindowPromptPresetsMixin, MainWindowProfilesMixin, QMainWindow):
    STARTUP_INTERACTION_EVENTS = {
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonDblClick,
        QEvent.Type.KeyPress,
        QEvent.Type.Wheel,
        QEvent.Type.TouchBegin,
        QEvent.Type.TouchUpdate,
        QEvent.Type.InputMethod,
        QEvent.Type.FocusIn,
    }

    def __init__(self, *, startup_timing: StartupTimingTracker | None = None):
        super().__init__()
        self.startup_timing = startup_timing or StartupTimingTracker(origin_name="mainwindow_init_start")
        self.startup_timing.mark("mainwindow_init_start")
        self.bridge = AppBridge()
        self.bridge.action_requested.connect(self.handle_action_request)
        self.bridge.worker_error.connect(self.handle_error)
        self.bridge.log_message.connect(self._append_log_message)
        self.bridge.invoke_main_thread.connect(self._invoke_main_thread)
        self.bridge.hotkey_recorded.connect(self.handle_recorded_hotkey)

        self.config = load_config()
        self.log_store = RuntimeLogStore(max_entries=100)
        self._startup_summary_logged = False
        self._startup_prewarm_summary_logged = False
        self._startup_first_show_seen = False
        self._startup_interaction_tracking_installed = False
        self._last_user_interaction_at = time.perf_counter()
        self._api_client = None
        self._api_client_class = None
        self._screen_capture_service = None
        self._screen_capture_service_class = None
        self._translation_overlay_class = None
        self._overlay_presenter_class = None
        self._startup_prewarm_queue = []
        self.hotkey_listener = None
        self._hotkey_listener_class = None
        self.operation_manager = OperationManager(self.set_operation_state, log_func=self.log)
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
        self._style_hints = QGuiApplication.instance().styleHints() if QGuiApplication.instance() else None
        self._form_provider = normalize_provider_name(self.config.api_profiles[0].provider if self.config.api_profiles else "gemini")
        set_theme_mode(getattr(self.config, "theme_mode", "system"))
        self.icon = self.create_app_icon()
        self.has_unsaved_changes = False
        self._suppress_form_tracking = False
        self.api_keys_visible = False
        self.api_keys_actual_text = ""
        self._api_keys_hint_override_key = None
        self._api_keys_reveal_pulse_id = 0
        if self._style_hints and hasattr(self._style_hints, "colorSchemeChanged"):
            self._style_hints.colorSchemeChanged.connect(self.handle_system_color_scheme_changed)
        self._active_error_dialogs = []
        self._handling_error = False
        self._exit_watchdog_started = False
        self.fetch_models_in_progress = False
        self.test_profile_in_progress = False
        self.translation_in_progress = False
        self.selected_text_capture_in_progress = False
        self.selected_text_capture_session = None
        self._fetch_models_request_id = 0
        self._test_profile_request_id = 0
        self.pending_capture_profile = None
        self.pending_capture_target_language = self.config.target_language
        self.pending_capture_prompt_preset = None
        self.selection_overlay = SelectionOverlay()
        self.selection_overlay.selected.connect(self.handle_selection)
        self.selection_overlay.cancelled.connect(self.handle_capture_cancelled)

        self._translation_overlay = None
        self._overlay_presenter = None
        self.background_task_runner = BackgroundTaskRunner(
            self.operation_manager,
            self.bridge,
            error_handler=self.handle_error,
            log_func=self.log,
            worker_cls=WorkerThread,
        )
        self.request_workflow = RequestWorkflowController(self)
        self.instance_server_service = InstanceServerService(self, APP_SERVER_NAME, log_func=self.log)
        self.tray = None
        self.tray_show_action = None
        self.tray_capture_action = None
        self.tray_manual_input_action = None
        self.tray_cancel_action = None
        self.tray_quit_action = None
        self.tray_service = SystemTrayService(self, self.icon, log_func=self.log)
        self.toast_service = TransientToastService(self, log_func=self.log)
        self.update_check_service = UpdateCheckService(log_func=self.log)
        self.update_check_in_progress = False
        self._startup_update_check_scheduled = False
        self._last_update_check_result = None

        self._install_startup_interaction_tracker()
        self.build_ui()
        self.startup_timing.mark("mainwindow_ui_built")
        self.load_profile_to_form(self.config.active_profile_name, refresh_ui=False, validate_form=False, mark_clean=False, refresh_shell=False)
        self.startup_timing.mark("mainwindow_profile_loaded")
        self.load_prompt_preset_to_form(self.config.active_prompt_preset_name, refresh_ui=False, validate_form=False, mark_clean=False, refresh_shell=False)
        self.startup_timing.mark("mainwindow_prompt_loaded")
        self.apply_language()
        self.startup_timing.mark("mainwindow_language_applied")
        self.instance_server_service.setup()
        self.startup_timing.mark("instance_server_ready")
        self._startup_prewarm_started = False
        self._startup_prewarm_completed = False
        self._startup_prewarm_pending = False
        self._startup_services_initialized = False
        self.set_unsaved_changes(False)
        self.startup_timing.mark("mainwindow_init_complete")

    def get_api_client_class(self):
        if self._api_client_class is None:
            from ..api_client import ApiClient

            self._api_client_class = ApiClient
        return self._api_client_class

    def get_api_client(self):
        if self._api_client is None:
            self._api_client = self.get_api_client_class()(self.log)
        return self._api_client

    @property
    def api_client(self):
        return self.get_api_client()

    @api_client.setter
    def api_client(self, value):
        self._api_client = value

    def get_screen_capture_service_class(self):
        if self._screen_capture_service_class is None:
            from ..services.image_capture import ScreenCaptureService

            self._screen_capture_service_class = ScreenCaptureService
        return self._screen_capture_service_class

    def get_screen_capture_service(self):
        if self._screen_capture_service is None:
            self._screen_capture_service = self.get_screen_capture_service_class()(self.log)
        return self._screen_capture_service

    @property
    def screen_capture_service(self):
        return self.get_screen_capture_service()

    @screen_capture_service.setter
    def screen_capture_service(self, value):
        self._screen_capture_service = value

    def get_translation_overlay_class(self):
        if self._translation_overlay_class is None:
            from .translation_overlay import TranslationOverlay

            self._translation_overlay_class = TranslationOverlay
        return self._translation_overlay_class

    def get_translation_overlay(self, *, create: bool = True):
        overlay = self._translation_overlay
        if overlay is None and create:
            overlay = self.get_translation_overlay_class()(self)
            overlay.request_font_zoom.connect(self.adjust_overlay_font_size)
            overlay.overlay_resized.connect(self.handle_overlay_resized)
            self._translation_overlay = overlay
        return overlay

    def preload_translation_overlay_class(self):
        return self.get_translation_overlay_class()

    @property
    def translation_overlay(self):
        return self.get_translation_overlay(create=True)

    @translation_overlay.setter
    def translation_overlay(self, value):
        self._translation_overlay = value
        if value is not None:
            self._overlay_presenter = None

    def get_overlay_presenter_class(self):
        if self._overlay_presenter_class is None:
            from ..services.overlay_presenter import OverlayPresenter

            self._overlay_presenter_class = OverlayPresenter
        return self._overlay_presenter_class

    def get_overlay_presenter(self, *, create: bool = True):
        presenter = self._overlay_presenter
        if presenter is None and create:
            presenter = self.get_overlay_presenter_class()(self)
            self._overlay_presenter = presenter
        return presenter

    def preload_overlay_presenter_class(self):
        return self.get_overlay_presenter_class()

    @property
    def overlay_presenter(self):
        return self.get_overlay_presenter(create=True)

    @overlay_presenter.setter
    def overlay_presenter(self, value):
        self._overlay_presenter = value

    def get_hotkey_listener_class(self):
        if self._hotkey_listener_class is None:
            from ..hotkey_listener import HotkeyListener

            self._hotkey_listener_class = HotkeyListener
        return self._hotkey_listener_class

    def existing_translation_overlay(self):
        return self._translation_overlay

    def existing_overlay_presenter(self):
        return self._overlay_presenter

    def _install_startup_interaction_tracker(self):
        if self._startup_interaction_tracking_installed:
            return
        app = QApplication.instance()
        if app is None:
            return
        app.installEventFilter(self)
        self._startup_interaction_tracking_installed = True

    def _remove_startup_interaction_tracker(self):
        if not getattr(self, "_startup_interaction_tracking_installed", False):
            return
        app = QApplication.instance()
        if app is not None:
            try:
                app.removeEventFilter(self)
            except Exception:  # noqa: BLE001
                pass
        self._startup_interaction_tracking_installed = False

    def _should_track_startup_interaction(self, watched, event) -> bool:
        if getattr(self, "_startup_prewarm_completed", False):
            return False
        if event is None or event.type() not in self.STARTUP_INTERACTION_EVENTS:
            return False
        if watched is self:
            return True
        if not isinstance(watched, QWidget):
            return False
        try:
            return watched.window() is self
        except Exception:  # noqa: BLE001
            return False

    def eventFilter(self, watched, event):
        if self._should_track_startup_interaction(watched, event):
            self._last_user_interaction_at = time.perf_counter()
        return super().eventFilter(watched, event)

    def _startup_prewarm_steps(self):
        return [
            {"name": "api_client", "callback": self.get_api_client, "min_idle_ms": 320, "next_delay_ms": 120},
            {"name": "screen_capture_service", "callback": self.get_screen_capture_service, "min_idle_ms": 520, "next_delay_ms": 140},
            {"name": "request_support_classes", "callback": self.request_workflow.preload_support_classes, "min_idle_ms": 760, "next_delay_ms": 140},
            {"name": "translation_overlay_class", "callback": self.preload_translation_overlay_class, "min_idle_ms": 1080, "next_delay_ms": 150},
            {"name": "overlay_presenter_class", "callback": self.preload_overlay_presenter_class, "min_idle_ms": 1220, "next_delay_ms": 0},
        ]

    def schedule_idle_prewarm(self, delay_ms: int = 180):
        if getattr(self, "_startup_prewarm_completed", False) or getattr(self, "_startup_prewarm_pending", False):
            return
        if not getattr(self, "_startup_services_initialized", False):
            return
        self._startup_prewarm_pending = True

        def run():
            self._startup_prewarm_pending = False
            self._run_idle_prewarm_step()

        QTimer.singleShot(max(0, int(delay_ms)), run)

    def _idle_prewarm_wait_delay(self, required_idle_ms: int, current_idle_ms: float) -> int:
        remaining = max(0.0, float(required_idle_ms) - float(current_idle_ms))
        return max(80, min(420, int(remaining + 40)))

    def _log_startup_summary_if_ready(self):
        if self._startup_summary_logged or not self._startup_first_show_seen or not getattr(self, "_startup_services_initialized", False):
            return
        summary = self.startup_timing.describe_segments(
            "Startup timing",
            (
                ("ui_app", "run_app_enter", "ui_application_created"),
                ("window_import", "ui_application_created", "main_window_imported"),
                ("window_init", "mainwindow_init_start", "mainwindow_init_complete"),
                ("first_show", "run_app_enter", "mainwindow_first_show"),
                ("services_ready", "run_app_enter", "startup_services_ready"),
            ),
        )
        if summary:
            self.log(summary)
        if self.startup_timing.verbose:
            mark_line = self.startup_timing.describe_segments(
                "Startup detail",
                (
                    ("ui_built", "mainwindow_init_start", "mainwindow_ui_built"),
                    ("profiles", "mainwindow_ui_built", "mainwindow_profile_loaded"),
                    ("prompts", "mainwindow_profile_loaded", "mainwindow_prompt_loaded"),
                    ("language", "mainwindow_prompt_loaded", "mainwindow_language_applied"),
                    ("instance_server", "mainwindow_language_applied", "instance_server_ready"),
                ),
            )
            if mark_line:
                self.log(mark_line)
        self._startup_summary_logged = True

    def _log_startup_prewarm_summary_if_ready(self):
        if self._startup_prewarm_summary_logged or not getattr(self, "_startup_prewarm_completed", False):
            return
        summary = self.startup_timing.describe_durations("Startup prewarm", prefix="prewarm.")
        if summary:
            self.log(summary)
        self._startup_prewarm_summary_logged = True

    def _run_idle_prewarm_step(self):
        if getattr(self, "is_quitting", False) or getattr(self, "_startup_prewarm_completed", False):
            return
        if not self.isVisible():
            return
        if self.capture_workflow_active or self.background_busy():
            self.schedule_idle_prewarm(delay_ms=360)
            return

        if not getattr(self, "_startup_prewarm_started", False):
            self._startup_prewarm_started = True
            self.startup_timing.mark("startup_prewarm_started")
            self._startup_prewarm_queue = list(self._startup_prewarm_steps())

        queue = getattr(self, "_startup_prewarm_queue", [])
        if not queue:
            self._startup_prewarm_completed = True
            self.startup_timing.mark("startup_prewarm_completed")
            self._remove_startup_interaction_tracker()
            self._log_startup_prewarm_summary_if_ready()
            return

        step = queue[0]
        idle_ms = (time.perf_counter() - getattr(self, "_last_user_interaction_at", time.perf_counter())) * 1000.0
        required_idle_ms = int(step.get("min_idle_ms", 0))
        if idle_ms < required_idle_ms:
            self.schedule_idle_prewarm(delay_ms=self._idle_prewarm_wait_delay(required_idle_ms, idle_ms))
            return

        queue.pop(0)
        name = step["name"]
        callback = step["callback"]
        try:
            self.startup_timing.measure(f"prewarm.{name}", callback)
        except Exception as exc:  # noqa: BLE001
            self.log(f"Startup prewarm skipped for {name}: {exc}")

        if queue:
            self.schedule_idle_prewarm(delay_ms=int(step.get("next_delay_ms", 90) or 90))
            return
        self._startup_prewarm_completed = True
        self.startup_timing.mark("startup_prewarm_completed")
        self._remove_startup_interaction_tracker()
        self._log_startup_prewarm_summary_if_ready()

    def complete_startup_services(self):
        if getattr(self, "_startup_services_initialized", False):
            return
        self._startup_services_initialized = True
        self.tray_service.setup()
        self.setup_hotkey_listener(initial=True)
        self.update_action_states()
        self.startup_timing.mark("startup_services_ready")
        self.log_tr("log_application_started")
        self._log_startup_summary_if_ready()
        self.schedule_startup_update_check()
        self.schedule_idle_prewarm()

    def tr(self, key: str, **kwargs) -> str:
        lang = self.current_ui_language()
        text = I18N[lang].get(key, key)
        return text.format(**kwargs) if kwargs else text

    def log_tr(self, key: str, **kwargs):
        self.log(self.tr(key, **kwargs))

    def current_ui_language(self) -> str:
        if hasattr(self, "ui_language_combo"):
            value = self.ui_language_combo.currentText().strip()
            if value in I18N:
                return value
        return normalize_ui_language(self.config.ui_language, default=DEFAULT_UI_LANGUAGE)

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

    def current_theme_mode(self) -> str:
        if hasattr(self, "theme_mode_buttons"):
            for mode, button in self.theme_mode_buttons.items():
                if button.isChecked():
                    return normalize_theme_mode(mode)
        if hasattr(self, "theme_mode_combo"):
            return normalize_theme_mode(self.theme_mode_combo.currentData() or getattr(self.config, "theme_mode", "system"))
        return normalize_theme_mode(getattr(self.config, "theme_mode", "system"))

    def effective_theme_name(self) -> str:
        return resolve_theme_name(self.current_theme_mode())

    def handle_system_color_scheme_changed(self, _scheme):
        if self.current_theme_mode() == "system":
            self.apply_language()

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

    def current_overlay_auto_expand_top_margin(self) -> int:
        if hasattr(self, "overlay_auto_expand_top_margin_spin"):
            return int(self.overlay_auto_expand_top_margin_spin.value())
        return int(getattr(self.config, "overlay_auto_expand_top_margin", 42))

    def current_overlay_auto_expand_bottom_margin(self) -> int:
        if hasattr(self, "overlay_auto_expand_bottom_margin_spin"):
            return int(self.overlay_auto_expand_bottom_margin_spin.value())
        return int(getattr(self.config, "overlay_auto_expand_bottom_margin", 24))

    def handle_toast_duration_changed(self, _value=None):
        if self.current_toast_duration_ms() <= 0 and hasattr(self, "toast_service"):
            self.toast_service.hide_message()

    def current_toast_duration_seconds(self) -> float:
        if hasattr(self, "toast_duration_spin"):
            return float(self.toast_duration_spin.value())
        config = getattr(self, "config", None)
        return float(getattr(config, "toast_duration_seconds", 1.5))

    def current_toast_duration_ms(self) -> int:
        duration_seconds = max(0.0, self.current_toast_duration_seconds())
        return int(round(duration_seconds * 1000))

    def current_app_version(self) -> str:
        return APP_VERSION

    def persisted_update_check_preference(self) -> bool:
        config = getattr(self, "config", None)
        return bool(getattr(config, "check_updates_on_startup", False))

    def should_check_updates_on_startup(self) -> bool:
        if hasattr(self, "check_updates_on_startup_checkbox"):
            return bool(self.check_updates_on_startup_checkbox.isChecked())
        config = getattr(self, "config", None)
        return bool(getattr(config, "check_updates_on_startup", False))

    def on_update_check_preference_changed(self, _state=None):
        self.refresh_update_check_ui()

    def refresh_update_check_controls(self):
        if hasattr(self, "check_updates_now_button"):
            self.check_updates_now_button.setEnabled(not self.update_check_in_progress)
            self.check_updates_now_button.setText(self.tr("check_updates_now_busy") if self.update_check_in_progress else self.tr("check_updates_now"))
        if hasattr(self, "check_updates_on_startup_checkbox"):
            self.check_updates_on_startup_checkbox.setEnabled(not self.update_check_in_progress)

    def _format_update_check_release_link(self, url: str) -> str:
        safe_url = escape(str(url or ""), quote=True)
        if not safe_url:
            return ""
        link_color = color("link", theme_name=self.effective_theme_name())
        display_url = safe_url.replace("/", "/&#8203;")
        return (
            f"<a href='{safe_url}' style='color:{link_color}; text-decoration:none;'>{display_url}</a>"
        )

    def refresh_update_check_hint(self):
        if not hasattr(self, "update_check_hint_label"):
            return
        text = self.tr(
            "update_check_hint_enabled" if self.should_check_updates_on_startup() else "update_check_hint_disabled",
            version=self.current_app_version(),
        )
        result = getattr(self, "_last_update_check_result", None)
        if self.update_check_in_progress:
            text = self.tr("update_check_hint_checking")
        elif result is not None:
            if getattr(result, "kind", "") == "available":
                release_link = self._format_update_check_release_link(getattr(result, "release_url", "")) or escape(
                    str(getattr(result, "release_url", ""))
                )
            elif getattr(result, "kind", "") == "up_to_date":
                text = self.tr("update_check_hint_latest", version=result.current_version)
            elif getattr(result, "kind", "") == "error":
                text = self.tr("update_check_hint_failed", error=result.error)
            if getattr(result, "kind", "") == "available":
                text = self.tr(
                    "update_check_hint_available",
                    current=self.current_app_version(),
                    version=result.latest_version,
                    url=release_link,
                )
        self.update_check_hint_label.setText(text)

    def refresh_update_check_ui(self):
        self.refresh_update_check_controls()
        self.refresh_update_check_hint()

    def check_for_updates_now(self):
        self.start_update_check(manual=True)

    def schedule_startup_update_check(self, delay_ms: int = 4200):
        if getattr(self, "_startup_update_check_scheduled", False):
            return
        self._startup_update_check_scheduled = True

        def run():
            self._startup_update_check_scheduled = False
            if getattr(self, "is_quitting", False) or self.update_check_in_progress:
                return
            if not self.persisted_update_check_preference():
                return
            self.start_update_check(manual=False)

        QTimer.singleShot(max(0, int(delay_ms)), run)

    def start_update_check(self, *, manual: bool) -> bool:
        if self.update_check_in_progress:
            return False
        self.update_check_in_progress = True
        self.refresh_update_check_ui()
        if manual:
            self.set_status("update_checking_status")
        self.log(f"Checking GitHub releases for updates | manual={manual}")
        self.run_worker(
            lambda: self.update_check_service.check_latest_release(current_version=self.current_app_version()),
            lambda result, manual=manual: self._handle_update_check_result(result, manual=manual),
        )
        return True

    def _handle_update_check_result(self, result, *, manual: bool):
        self.update_check_in_progress = False
        should_keep_result = manual or getattr(result, "has_update", False)
        self._last_update_check_result = result if should_keep_result else None
        if getattr(self, "is_quitting", False):
            return
        self.refresh_update_check_ui()
        if should_keep_result and getattr(result, "has_update", False):
            self.set_status("update_available_status", version=result.latest_version)
            self.log(f"Update available | current={result.current_version} | latest={result.latest_version} | url={result.release_url}")
            return
        if getattr(result, "is_up_to_date", False):
            if manual:
                self.set_status("update_up_to_date_status", version=result.current_version)
            self.log(f"Already up to date | current={result.current_version} | latest={result.latest_version or result.current_version}")
            return
        if manual:
            self.set_status("update_check_failed_status")
        self.log(f"Update check failed: {getattr(result, 'error', 'unknown error')}")

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
        try:
            overlay = getattr(self, "translation_overlay", None)
            if overlay is not None and getattr(overlay, "is_pinned", False):
                overlay.persist_current_geometry_as_pinned()
                self.persist_runtime_overlay_state()
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)
        self.set_status("overlay_resized", width=int(width), height=int(height))

    def persist_runtime_overlay_state(self) -> bool:
        keep_dirty = bool(getattr(self, "has_unsaved_changes", False))
        try:
            save_config(self.config)
            return True
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)
            return False
        finally:
            if hasattr(self, "set_unsaved_changes"):
                try:
                    self.set_unsaved_changes(keep_dirty)
                except Exception:  # noqa: BLE001
                    self.has_unsaved_changes = keep_dirty

    def background_busy(self) -> bool:
        return self.fetch_models_in_progress or self.test_profile_in_progress or self.translation_in_progress or self.selected_text_capture_in_progress

    def set_operation_state(self, operation: str, active: bool):
        setattr(self, f"{operation}_in_progress", active)
        self.update_action_states()

    def update_action_states(self):
        if not hasattr(self, "fetch_models_button"):
            return
        any_background_busy = self.background_busy()
        capture_busy = self.capture_workflow_active or any_background_busy
        cancel_available = bool(self.operation_manager.current_active(("translation", "test_profile", "fetch_models")) or self.selected_text_capture_in_progress or (self.capture_workflow_active and self.selection_overlay.isVisible()))
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
            "theme_mode_switch",
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
            "overlay_auto_expand_top_margin_spin",
            "overlay_auto_expand_bottom_margin_spin",
            "toast_duration_spin",
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
        self.save_button.setEnabled(not any_background_busy and bool(getattr(self, "has_unsaved_changes", False)))
        if hasattr(self, "discard_changes_button"):
            self.discard_changes_button.setEnabled(not any_background_busy and bool(getattr(self, "has_unsaved_changes", False)))
        self.cancel_button.setEnabled(cancel_available)
        self.hero_tray_button.setEnabled(bool(self.tray))
        self.hero_capture_button.setEnabled(not capture_busy)
        if hasattr(self, "hero_manual_input_button"):
            self.hero_manual_input_button.setEnabled(not capture_busy)
        self.preview_capture_button.setEnabled(not capture_busy)
        self.profile_combo.setEnabled(not any_background_busy)
        self.new_profile_button.setEnabled(not any_background_busy)
        self.delete_profile_button.setEnabled(not any_background_busy)
        if hasattr(self, "close_to_tray_on_close_checkbox"):
            self.close_to_tray_on_close_checkbox.setEnabled(bool(self.tray) and not any_background_busy)
            self.close_to_tray_on_close_checkbox.setToolTip("" if self.tray else self.tr("tray_unavailable"))
        if getattr(self, "tray", None):
            self.tray_capture_action.setEnabled(not capture_busy)
            if hasattr(self, "tray_manual_input_action"):
                self.tray_manual_input_action.setEnabled(not capture_busy)
            self.tray_cancel_action.setEnabled(cancel_available)
        if hasattr(self, "refresh_prompt_preset_actions"):
            self.refresh_prompt_preset_actions()
        if hasattr(self, "refresh_update_check_controls"):
            self.refresh_update_check_controls()
        if not any_background_busy and not self.capture_workflow_active:
            self.schedule_idle_prewarm(delay_ms=220)

    def update_tray_texts(self):
        self.tray_service.update_texts()

    def refresh_log_view(self):
        if not hasattr(self, "log_text"):
            return
        if self.log_store.has_entries():
            self.log_text.setPlainText(self.log_store.as_text())
        else:
            self.log_text.setPlainText("")
            self.log_text.setPlaceholderText(self.tr("logs_empty"))

    def _append_log_message(self, message: str):
        self.log_store.add(message)
        if hasattr(self, "log_text"):
            self.log_text.setPlaceholderText("")
            self.refresh_log_view()

    def log(self, message: str):
        self.bridge.log_message.emit(str(message))

    def _invoke_main_thread(self, callback, payload):
        if not callable(callback):
            return
        try:
            callback(payload)
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def _track_error_dialog(self, dialog):
        if dialog is None:
            return
        self._active_error_dialogs.append(dialog)
        dialog.destroyed.connect(lambda *_args, dialog=dialog: self._discard_error_dialog(dialog))

    def _discard_error_dialog(self, dialog):
        self._active_error_dialogs = [item for item in self._active_error_dialogs if item is not dialog]

    @staticmethod
    def _safe_write_stderr(message: str):
        try:
            sys.stderr.write(f"{message}\n")
            sys.stderr.flush()
        except Exception:  # noqa: BLE001
            pass

    @staticmethod
    def _force_process_exit(exit_code: int = 0):
        os._exit(int(exit_code))

    def _run_exit_watchdog(self, timeout_seconds: float = 5.0):
        time.sleep(max(0.0, float(timeout_seconds or 0.0)))
        if not getattr(self, "is_quitting", False):
            return
        self._safe_write_stderr("Quit watchdog forced process exit after shutdown timeout")
        self._force_process_exit(0)

    def _start_exit_watchdog(self, timeout_seconds: float = 5.0):
        if getattr(self, "_exit_watchdog_started", False):
            return
        self._exit_watchdog_started = True
        threading.Thread(
            target=self._run_exit_watchdog,
            args=(timeout_seconds,),
            name="OCRTranslatorQuitWatchdog",
            daemon=True,
        ).start()

    def _show_error_dialog_safe(self, display_message: str):
        dialog = show_non_blocking_critical_message(self if self.isVisible() else None, self.tr("error_title"), display_message, theme_name=self.effective_theme_name())
        self._track_error_dialog(dialog)

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
            self.log_tr("log_runtime_log_exported", path=Path(target_path).name)
            self.set_status("logs_exported", path=Path(target_path).name)
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)

    def cancel_background_operation(self):
        active_operation = self.operation_manager.current_active(("translation", "test_profile", "fetch_models"))
        if active_operation is None:
            if self.selected_text_capture_in_progress and getattr(self, "selected_text_capture_session", None):
                if hasattr(self, "request_workflow"):
                    return self.request_workflow.cancel_selected_text_capture()
                return False
            if self.capture_workflow_active and self.selection_overlay.isVisible():
                self.selection_overlay.hide()
                self.handle_capture_cancelled()
                return True
            self.set_status("cancel_request_unavailable")
            return False
        self.log(f"Cancelling background operation: {active_operation}")
        self.operation_manager.cancel(active_operation)
        if active_operation == "translation":
            should_restore = self.capture_workflow_active or self.restore_window_after_capture or self.restore_pinned_overlay_after_capture
            self.finish_capture_workflow(restore_window=should_restore)
            overlay = self.existing_translation_overlay()
            if should_restore and self.restore_pinned_overlay_after_capture and overlay is not None:
                overlay.restore_last_overlay()
                self.restore_pinned_overlay_after_capture = False
            self.show_tray_toast(self.tr("request_cancelled"))
        self.set_status("request_cancelled")
        return True


    def note_runtime_preference_changed(self):
        self.set_unsaved_changes(True)
        if hasattr(self, "refresh_shell_state"):
            self.refresh_shell_state()

    def normalize_hotkey(self, hotkey_text: str) -> str:
        return normalize_hotkey_text(hotkey_text)

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
            unsupported_parts = hotkey_unsupported_parts(hotkey)
            if unsupported_parts:
                raise ValueError(self.tr("validation_hotkey_unsupported_key", token=unsupported_parts[0]))
            if not hotkey_has_primary_key(hotkey):
                raise ValueError(self.tr("validation_hotkey_requires_primary"))
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

    def setup_hotkey_listener(self, initial: bool = False, *, config=None, hotkey_actions: dict[str, str] | None = None, raise_on_error: bool = False):
        previous_hotkeys = dict(getattr(self, "registered_hotkeys", {}))
        previous_listener = self.hotkey_listener
        hotkey_listener_cls = self.get_hotkey_listener_class()
        if previous_listener:
            previous_listener.stop()
        self.hotkey_listener = None
        self.registered_hotkeys = {}
        try:
            resolved_hotkey_actions = dict(hotkey_actions) if hotkey_actions is not None else self.build_hotkey_actions(config)
            hotkey_actions = self.validate_hotkey_actions(resolved_hotkey_actions)
            listener = hotkey_listener_cls(
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
                    restored_listener = hotkey_listener_cls(
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
                show_critical_message(self, self.tr("error_title"), self.tr("hotkey_register_failed", error=exc))
            if raise_on_error:
                raise
            return False

    def run_worker(self, fn, on_success, *, operation_key: str | None = None, cancellable: bool = False):
        self.background_task_runner.run_worker(
            fn,
            on_success,
            operation_key=operation_key,
            cancellable=cancellable,
        )

    def _handle_stale_operation_error(self, operation: str | None, task_id: int | None, actual_exc: Exception) -> bool:
        return self.background_task_runner.handle_stale_error(operation, task_id, actual_exc)

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

    def finish_capture_workflow(self, restore_window: bool = False, *, clear_restore_window_state: bool = True):
        self.request_workflow.finish_capture_workflow(restore_window=restore_window, clear_restore_window_state=clear_restore_window_state)

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
        preserve_geometry: bool = False,
        reflow_only: bool = False,
    ):
        self.overlay_presenter.show_translation(
            bbox,
            text,
            preset_name=preset_name,
            preserve_manual_position=preserve_manual_position,
            preserve_geometry=preserve_geometry,
            reflow_only=reflow_only,
        )

    def adjust_overlay_font_size(self, direction: int):
        self.overlay_presenter.adjust_font_size(direction)

    def update_preview(self, image: Image.Image | None = None, *, preview_pixmap: QPixmap | None = None):
        if preview_pixmap is not None:
            self.preview_pixmap = preview_pixmap
        elif image is not None:
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

    def show_tray_toast(self, message: str, *, prefer_system: bool = False):
        duration_ms = self.current_toast_duration_ms()
        if duration_ms <= 0:
            if getattr(self, "toast_service", None):
                self.toast_service.hide_message()
            return False
        use_system_toast = bool(
            prefer_system
            or not getattr(self, "isVisible", lambda: False)()
            or getattr(self, "isMinimized", lambda: False)()
        )
        if use_system_toast:
            if getattr(self, "toast_service", None):
                self.toast_service.hide_message()
            return self.tray_service.show_message(message, duration_ms=duration_ms)
        if getattr(self, "toast_service", None) and self.toast_service.show_message(message, duration_ms=duration_ms):
            return True
        return self.tray_service.show_message(message, duration_ms=duration_ms)

    def minimize_to_tray(self):
        if not self.tray:
            self.set_status("tray_unavailable")
            show_information_message(self, self.tr("tray_title"), self.tr("tray_unavailable"))
            return
        self.hide()
        overlay = self.existing_translation_overlay()
        if overlay is not None and not overlay.is_pinned:
            overlay.hide()
        self.set_status("tray_minimized")
        self.show_tray_toast(self.tr("tray_minimized"), prefer_system=True)

    def show_main_window(self):
        self.show()
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.raise_()
        self.activateWindow()

    def handle_error(self, exc: Exception):
        if getattr(self, "_handling_error", False):
            self._safe_write_stderr(f"Suppressed recursive handle_error call: {exc}")
            return
        self._handling_error = True
        try:
            operation = getattr(exc, "operation", None)
            task_id = getattr(exc, "task_id", None)
            actual_exc = getattr(exc, "original", exc)
            if self._handle_stale_operation_error(operation, task_id, actual_exc):
                return
            if operation in {"fetch_models", "test_profile", "translation"}:
                if task_id is not None:
                    self.operation_manager.finish(operation, task_id)
                else:
                    self.set_operation_state(operation, False)
            if isinstance(actual_exc, RequestCancelledError):
                if hasattr(self, "toast_service"):
                    self.toast_service.hide_message()
                if hasattr(self, "status_label"):
                    self.set_status("request_cancelled")
                self.log(f"Operation cancelled: {operation or 'unknown'}")
                return
            is_capture_error = self.capture_workflow_active or operation == "translation"
            try:
                self.finish_capture_workflow(restore_window=is_capture_error)
            except Exception:  # noqa: BLE001
                pass
            if is_capture_error and self.restore_pinned_overlay_after_capture:
                overlay = self.existing_translation_overlay()
                try:
                    if overlay is not None:
                        overlay.restore_last_overlay()
                except Exception:  # noqa: BLE001
                    pass
                self.restore_pinned_overlay_after_capture = False
            if hasattr(self, "toast_service"):
                self.toast_service.hide_message()
            if hasattr(self, "status_label"):
                self.set_status("translate_failed" if is_capture_error else "operation_failed")
            self.log(f"Error: {actual_exc}")
            if not self.isVisible() and not self.is_quitting:
                try:
                    self.show_main_window()
                except Exception:  # noqa: BLE001
                    pass
            display_message = getattr(actual_exc, "user_message", str(actual_exc))
            try:
                self._show_error_dialog_safe(display_message)
            except Exception as dialog_exc:  # noqa: BLE001
                self._safe_write_stderr(f"Failed to show non-blocking error dialog: {dialog_exc}")
                try:
                    show_critical_message(self if self.isVisible() else None, self.tr("error_title"), display_message, theme_name=self.effective_theme_name())
                except Exception as fallback_exc:  # noqa: BLE001
                    self._safe_write_stderr(f"Fallback error dialog also failed: {fallback_exc}")
                    safe_record_exception(type(fallback_exc), fallback_exc, fallback_exc.__traceback__, context="MainWindow.handle_error fallback failure")
        except Exception as handler_exc:  # noqa: BLE001
            self._safe_write_stderr(f"MainWindow.handle_error crashed: {handler_exc}")
            safe_record_exception(type(handler_exc), handler_exc, handler_exc.__traceback__, context="MainWindow.handle_error failure")
        finally:
            self._handling_error = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "refresh_sidebar_layout"):
            self.refresh_sidebar_layout()
        if self.preview_pixmap:
            self.refresh_preview_pixmap()
        if hasattr(self, "toast_service"):
            self.toast_service.reposition()

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "refresh_sidebar_layout"):
            self.refresh_sidebar_layout()
        if not self._startup_first_show_seen:
            self._startup_first_show_seen = True
            self.startup_timing.mark("mainwindow_first_show")
            self._log_startup_summary_if_ready()
        if getattr(self, "_startup_services_initialized", False):
            self.schedule_idle_prewarm()
        if hasattr(self, "toast_service"):
            self.toast_service.reposition()

    def closeEvent(self, event):
        if not self.is_quitting and getattr(self.config, "close_to_tray_on_close", False):
            if not self.tray and not getattr(self, "_startup_services_initialized", False):
                try:
                    self.complete_startup_services()
                except Exception:  # noqa: BLE001
                    pass
            if self.tray:
                self.log_tr("log_close_redirected_to_tray")
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
        self._remove_startup_interaction_tracker()
        self.log_tr("log_application_exiting")
        self._start_exit_watchdog()
        if self.selected_text_capture_in_progress and getattr(self, "selected_text_capture_session", None):
            try:
                self.selected_text_capture_session.cancel()
            except Exception:  # noqa: BLE001
                pass
        self.operation_manager.cancel_all()
        try:
            self.selection_overlay.hide()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.stop_hotkey_recording(cancelled=False, restore_hotkey_listener=False)
        except Exception:  # noqa: BLE001
            pass
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        self.registered_hotkeys = {}
        for dialog in list(getattr(self, "_active_error_dialogs", [])):
            try:
                dialog.close()
            except Exception:  # noqa: BLE001
                pass
        self.instance_server_service.close()
        self.tray_service.close()
        if hasattr(self, "toast_service"):
            self.toast_service.close()
        overlay = self.existing_translation_overlay()
        if overlay is not None:
            overlay.close()
        app = QApplication.instance()
        if app is None:
            return True
        app.quit()
        return True
