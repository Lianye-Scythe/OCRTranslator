from pathlib import Path
import sys

from .crash_handling import install_crash_hooks

install_crash_hooks()

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtNetwork import QLocalSocket

from .runtime_paths import APP_LOCK_PATH, APP_SERVER_NAME, LOCK_STALE_MS
from .services.startup_timing import StartupTimingTracker

_CRASH_AWARE_APPLICATION_CLASS = None


def request_application_shutdown(app) -> bool:
    window = getattr(app, "main_window", None)
    shutdown = getattr(window, "emergency_shutdown", None) if window is not None else None
    if callable(shutdown):
        try:
            return bool(shutdown())
        except Exception as exc:  # noqa: BLE001
            try:
                sys.stderr.write(f"Emergency shutdown fallback after failure: {exc}\n")
                sys.stderr.flush()
            except Exception:  # noqa: BLE001
                pass
    try:
        app.quit()
        return True
    except Exception:  # noqa: BLE001
        return False


def crash_aware_application_class():
    global _CRASH_AWARE_APPLICATION_CLASS
    if _CRASH_AWARE_APPLICATION_CLASS is None:
        from PySide6.QtWidgets import QApplication

        class CrashAwareApplication(QApplication):
            def notify(self, receiver, event):
                try:
                    return super().notify(receiver, event)
                except Exception as exc:  # noqa: BLE001
                    sys.excepthook(type(exc), exc, exc.__traceback__)
                    request_application_shutdown(self)
                    return False

        _CRASH_AWARE_APPLICATION_CLASS = CrashAwareApplication
    return _CRASH_AWARE_APPLICATION_CLASS


def acquire_single_instance_lock() -> QLockFile | None:
    Path(APP_LOCK_PATH).parent.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(APP_LOCK_PATH)
    lock.setStaleLockTime(LOCK_STALE_MS)
    if lock.tryLock(100):
        return lock
    return None


def recover_stale_single_instance_lock() -> QLockFile | None:
    recovery_lock = QLockFile(APP_LOCK_PATH)
    recovery_lock.setStaleLockTime(LOCK_STALE_MS)
    if not recovery_lock.removeStaleLockFile():
        return None
    return acquire_single_instance_lock()


def request_existing_instance_action(action: str) -> bool:
    socket = QLocalSocket()
    socket.connectToServer(APP_SERVER_NAME)
    if not socket.waitForConnected(400):
        return False
    socket.write(f"{action}\n".encode("utf-8"))
    socket.flush()
    if not socket.waitForBytesWritten(400):
        socket.disconnectFromServer()
        return False
    if not socket.waitForReadyRead(800):
        socket.disconnectFromServer()
        return False
    reply = bytes(socket.readAll()).decode("utf-8", errors="ignore").strip().lower()
    socket.disconnectFromServer()
    return reply == "ok"


def should_forward_capture_request() -> bool:
    args = {arg.lower() for arg in sys.argv[1:]}
    return any(arg in {"--capture", "/capture", "capture"} for arg in args)


def schedule_initial_window_action(window, *, pending_capture: bool) -> None:
    if pending_capture:
        QTimer.singleShot(0, window.start_selection_from_launch)
        return
    window.show()
    QTimer.singleShot(0, window.show_main_window)


def create_ui_application():
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    application_class = crash_aware_application_class()
    app = QApplication.instance() or application_class([])
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("OCRTranslator")
    return app


def run_app():
    startup_timing = StartupTimingTracker()
    pending_capture = should_forward_capture_request()
    startup_timing.mark("capture_mode_decided")
    lock = acquire_single_instance_lock()
    if lock is None:
        action = "capture" if pending_capture else "show"
        if request_existing_instance_action(action):
            return

        startup_timing.mark("existing_instance_forward_failed")
        lock = recover_stale_single_instance_lock()
        if lock is None:
            from .app_defaults import DEFAULT_UI_LANGUAGE
            from .config_store import load_config
            from .i18n import I18N, normalize_ui_language
            from .ui.message_boxes import show_information_message
            from .ui.theme_tokens import resolve_theme_name

            app = create_ui_application()
            message_config = load_config()
            lang = normalize_ui_language(message_config.ui_language, default=DEFAULT_UI_LANGUAGE)
            show_information_message(
                None,
                I18N[lang]["already_running_title"],
                I18N[lang]["already_running_message"],
                theme_name=resolve_theme_name(getattr(message_config, "theme_mode", None)),
            )
            return
        startup_timing.mark("stale_lock_recovered")
    else:
        startup_timing.mark("single_instance_lock_acquired")

    app = create_ui_application()
    startup_timing.mark("ui_application_created")
    from .ui.main_window import MainWindow

    startup_timing.mark("main_window_imported")

    window = MainWindow(startup_timing=startup_timing)
    startup_timing.mark("main_window_created")
    app.main_window = window
    app.instance_lock = lock
    schedule_initial_window_action(window, pending_capture=pending_capture)
    startup_timing.mark("initial_window_action_scheduled")
    if hasattr(app, "aboutToQuit"):
        app.aboutToQuit.connect(window.handle_about_to_quit)
    QTimer.singleShot(0, window.complete_startup_services)
    app.exec()


if __name__ == "__main__":
    run_app()
