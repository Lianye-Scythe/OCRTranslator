from ..operation_control import RequestContext


class OperationManager:
    def __init__(self, set_operation_state, *, log_func=None):
        self._set_operation_state = set_operation_state
        self._log = log_func or (lambda message: None)
        self._counter = 0
        self._task_ids: dict[str, int] = {}
        self._request_contexts: dict[str, tuple[int, RequestContext]] = {}

    def begin(self, operation_key: str, *, cancellable: bool = False) -> tuple[int, RequestContext | None]:
        self._counter += 1
        task_id = self._counter
        request_context = RequestContext() if cancellable else None
        self._task_ids[operation_key] = task_id
        if request_context is not None:
            self._request_contexts[operation_key] = (task_id, request_context)
        else:
            self._request_contexts.pop(operation_key, None)
        self._set_operation_state(operation_key, True)
        return task_id, request_context

    def is_task_active(self, operation_key: str, task_id: int | None) -> bool:
        return task_id is not None and self._task_ids.get(operation_key) == task_id

    def finish(self, operation_key: str, task_id: int | None) -> bool:
        if not self.is_task_active(operation_key, task_id):
            return False
        self._task_ids.pop(operation_key, None)
        self._request_contexts.pop(operation_key, None)
        self._set_operation_state(operation_key, False)
        return True

    def cancel(self, operation_key: str) -> bool:
        context_entry = self._request_contexts.pop(operation_key, None)
        task_id = self._task_ids.pop(operation_key, None)
        if task_id is None and context_entry is None:
            return False
        self._set_operation_state(operation_key, False)
        if context_entry:
            _, request_context = context_entry
            request_context.cancel()
        return True

    def cancel_all(self) -> None:
        for operation_key in list(self._task_ids):
            self.cancel(operation_key)
        self._task_ids.clear()
        self._request_contexts.clear()

    def current_active(self, preferred_order: tuple[str, ...]) -> str | None:
        for operation_key in preferred_order:
            if operation_key in self._task_ids:
                return operation_key
        return None

    def is_stale(self, operation_key: str | None, task_id: int | None) -> bool:
        if operation_key is None or task_id is None:
            return False
        return not self.is_task_active(operation_key, task_id)

    def log_stale_result(self, operation_key: str, task_id: int, *, kind: str, detail: str = "") -> None:
        suffix = f": {detail}" if detail else ""
        self._log(f"Ignored stale {operation_key} {kind} from task {task_id}{suffix}")
