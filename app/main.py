from pathlib import Path
import sys

from PySide6.QtCore import QLockFile, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

from .config_store import load_config
from .constants import APP_LOCK_PATH, APP_SERVER_NAME, I18N, LOCK_STALE_MS
from .ui.main_window import MainWindow


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
    socket.write(action.encode("utf-8"))
    socket.flush()
    socket.waitForBytesWritten(400)
    socket.disconnectFromServer()
    return True


def should_forward_capture_request() -> bool:
    args = {arg.lower() for arg in sys.argv[1:]}
    return any(arg in {"--capture", "/capture", "capture"} for arg in args)


def run_app():
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication.instance() or QApplication([])
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
            lang = message_config.ui_language if message_config.ui_language in I18N else "zh-TW"
            QMessageBox.information(None, I18N[lang]["already_running_title"], I18N[lang]["already_running_message"])
            return

    window = MainWindow()
    app.instance_lock = lock
    window.show()
    if pending_capture:
        window.start_selection()
    app.exec()


if __name__ == "__main__":
    run_app()
