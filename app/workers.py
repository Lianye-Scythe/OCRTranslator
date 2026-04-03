import threading

from PySide6.QtCore import QObject, Signal


class WorkerThread(threading.Thread):
    def __init__(self, target, bridge, on_success):
        super().__init__(daemon=True)
        self._target = target
        self._bridge = bridge
        self._on_success = on_success

    def run(self):
        try:
            result = self._target()
            self._bridge.worker_success.emit(self._on_success, result)
        except Exception as exc:  # noqa: BLE001
            self._bridge.worker_error.emit(exc)


class AppBridge(QObject):
    action_requested = Signal(str)
    worker_success = Signal(object, object)
    worker_error = Signal(object)
    hotkey_recorded = Signal(str, str)
