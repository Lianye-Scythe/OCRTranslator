from collections.abc import Callable
import threading

import requests


class RequestCancelledError(RuntimeError):
    def __init__(self, message: str = "Request cancelled"):
        super().__init__(message)
        self.user_message = "目前操作已取消。"
        self.retryable = False
        self.retry_same_key = False


class OperationError(RuntimeError):
    def __init__(self, operation: str, original: Exception, *, task_id: int | None = None):
        super().__init__(str(original))
        self.operation = operation
        self.original = original
        self.task_id = task_id


class CancellationToken:
    def __init__(self):
        self._event = threading.Event()
        self._callbacks: list[Callable[[], None]] = []
        self._lock = threading.Lock()

    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> bool:
        with self._lock:
            if self._event.is_set():
                return False
            self._event.set()
            callbacks = list(self._callbacks)
            self._callbacks.clear()
        for callback in callbacks:
            try:
                callback()
            except Exception:  # noqa: BLE001
                pass
        return True

    def add_cancel_callback(self, callback) -> None:
        if not callable(callback):
            return
        should_call_now = False
        with self._lock:
            if self._event.is_set():
                should_call_now = True
            else:
                self._callbacks.append(callback)
        if should_call_now:
            try:
                callback()
            except Exception:  # noqa: BLE001
                pass


class RequestContext:
    def __init__(self):
        self.cancellation_token = CancellationToken()
        self.session = requests.Session()
        self.cancellation_token.add_cancel_callback(self.session.close)

    def cancel(self) -> bool:
        return self.cancellation_token.cancel()

    def is_cancelled(self) -> bool:
        return self.cancellation_token.is_cancelled()

    def close(self) -> None:
        try:
            self.session.close()
        except Exception:  # noqa: BLE001
            pass
