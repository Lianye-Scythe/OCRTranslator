from ..operation_control import OperationError, RequestCancelledError
from ..workers import WorkerThread


class BackgroundTaskRunner:
    def __init__(self, operation_manager, bridge, *, error_handler, log_func=None, worker_cls=WorkerThread):
        self.operation_manager = operation_manager
        self.bridge = bridge
        self.error_handler = error_handler
        self.log = log_func or (lambda message: None)
        self.worker_cls = worker_cls
        self.bridge.worker_success.connect(self._handle_worker_success)

    def run_worker(self, fn, on_success, *, operation_key: str | None = None, cancellable: bool = False):
        worker_target = fn
        worker_callback = on_success

        if operation_key:
            task_id, request_context = self.operation_manager.begin(operation_key, cancellable=cancellable)

            def guarded_target():
                try:
                    return fn(request_context) if request_context is not None else fn()
                except Exception as exc:  # noqa: BLE001
                    actual_exc = exc
                    if request_context is not None and request_context.is_cancelled() and not isinstance(exc, RequestCancelledError):
                        actual_exc = RequestCancelledError()
                    raise OperationError(operation_key, actual_exc, task_id=task_id) from exc
                finally:
                    if request_context is not None:
                        request_context.close()

            def guarded_success(result):
                if self._handle_stale_result(operation_key, task_id):
                    return
                self.operation_manager.finish(operation_key, task_id)
                if callable(on_success):
                    on_success(result)

            worker_target = guarded_target
            worker_callback = guarded_success

        self.worker_cls(worker_target, self.bridge, worker_callback).start()

    def _handle_stale_result(self, operation_key: str, task_id: int) -> bool:
        if not self.operation_manager.is_stale(operation_key, task_id):
            return False
        self.operation_manager.log_stale_result(operation_key, task_id, kind="result")
        return True

    def handle_stale_error(self, operation: str | None, task_id: int | None, actual_exc: Exception) -> bool:
        if not operation or task_id is None:
            return False
        if not self.operation_manager.is_stale(operation, task_id):
            return False
        self.operation_manager.log_stale_result(operation, task_id, kind="error", detail=str(actual_exc))
        return True

    def _handle_worker_success(self, callback, result):
        if callable(callback):
            try:
                callback(result)
            except Exception as exc:  # noqa: BLE001
                self.error_handler(exc)
