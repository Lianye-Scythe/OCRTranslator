import unittest

from app.services.operation_manager import OperationManager


class OperationManagerTests(unittest.TestCase):
    def setUp(self):
        self.state_changes: list[tuple[str, bool]] = []
        self.manager = OperationManager(lambda operation, active: self.state_changes.append((operation, active)))

    def test_begin_and_finish_cancellable_operation(self):
        task_id, request_context = self.manager.begin("translation", cancellable=True)

        self.assertIsNotNone(request_context)
        self.assertEqual(self.state_changes, [("translation", True)])
        self.assertTrue(self.manager.is_task_active("translation", task_id))

        finished = self.manager.finish("translation", task_id)

        self.assertTrue(finished)
        self.assertEqual(self.state_changes[-1], ("translation", False))
        self.assertFalse(self.manager.is_task_active("translation", task_id))

    def test_cancel_marks_request_context_cancelled(self):
        _task_id, request_context = self.manager.begin("translation", cancellable=True)

        cancelled = self.manager.cancel("translation")

        self.assertTrue(cancelled)
        self.assertTrue(request_context.is_cancelled())
        self.assertEqual(self.state_changes[-1], ("translation", False))

    def test_current_active_prefers_first_requested_operation(self):
        self.manager.begin("test_profile")
        self.manager.begin("translation")

        active_operation = self.manager.current_active(("translation", "test_profile", "fetch_models"))

        self.assertEqual(active_operation, "translation")

    def test_is_stale_returns_true_for_replaced_task(self):
        first_task, _ = self.manager.begin("fetch_models")
        second_task, _ = self.manager.begin("fetch_models")

        self.assertNotEqual(first_task, second_task)
        self.assertTrue(self.manager.is_stale("fetch_models", first_task))
        self.assertFalse(self.manager.is_stale("fetch_models", second_task))


if __name__ == "__main__":
    unittest.main()
