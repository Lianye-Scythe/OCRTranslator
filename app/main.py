from pathlib import Path
import sys

from .crash_handling import install_crash_hooks

install_crash_hooks()

from PySide6.QtCore import QLockFile, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtWidgets import QApplication

from .app_defaults import DEFAULT_UI_LANGUAGE
from .config_store import load_config
from .i18n import I18N, normalize_ui_language
from .runtime_paths import APP_LOCK_PATH, APP_SERVER_NAME, LOCK_STALE_MS
from .ui.message_boxes import show_information_message
from .ui.theme_tokens import resolve_theme_name
from .ui.main_window import MainWindow


class CrashAwareApplication(QApplication):
    def notify(self, receiver, event):
        try:
            return super().notify(receiver, event)
        except Exception as exc:  # noqa: BLE001
            sys.excepthook(type(exc), exc, exc.__traceback__)
            self.quit()
            return False


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
    window.show()
    if pending_capture:
        QTimer.singleShot(0, window.start_selection)
        return
    QTimer.singleShot(0, window.show_main_window)


def run_app():
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication.instance() or CrashAwareApplication([])
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("OCRTranslator")

    pending_capture = should_forward_capture_request()
    lock = acquire_single_instance_lock()
    if lock is None:
        action = "capture" if pending_capture else "show"
        if request_existing_instance_action(action):
            return

        lock = recover_stale_single_instance_lock()
        if lock is None:
            message_config = load_config()
            lang = normalize_ui_language(message_config.ui_language, default=DEFAULT_UI_LANGUAGE)
            show_information_message(
                None,
                I18N[lang]["already_running_title"],
                I18N[lang]["already_running_message"],
                theme_name=resolve_theme_name(getattr(message_config, "theme_mode", None)),
            )
            return

    window = MainWindow()
    app.instance_lock = lock
    schedule_initial_window_action(window, pending_capture=pending_capture)
    app.exec()


if __name__ == "__main__":
    run_app()
