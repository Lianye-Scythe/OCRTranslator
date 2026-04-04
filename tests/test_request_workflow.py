import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.request_workflow import RequestWorkflowController


class _FakeOverlay:
    def __init__(self):
        self.manual_positioned = False

    def isVisible(self):
        return False


class _FakeSignal:
    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args, **kwargs):
        for callback in list(self._callbacks):
            callback(*args, **kwargs)


class _FakeSelectedTextCaptureSession:
    def __init__(self, *args, **kwargs):
        self.finished = _FakeSignal()
        self.failed = _FakeSignal()
        self.cancelled = _FakeSignal()
        self.started = False
        self.cancel_called = False
        self.deleted = False

    def start(self):
        self.started = True

    def cancel(self):
        self.cancel_called = True
        self.cancelled.emit()
        return True

    def deleteLater(self):
        self.deleted = True


class RequestWorkflowControllerTests(unittest.TestCase):
    def _build_window(self):
        window = SimpleNamespace(
            capture_workflow_active=False,
            fetch_models_in_progress=False,
            test_profile_in_progress=False,
            translation_in_progress=False,
            selected_text_capture_in_progress=False,
            selected_text_capture_session=None,
            translation_overlay=_FakeOverlay(),
            validate_form_inputs=lambda focus_first_invalid=True, scope="text_request": (True, ""),
            build_profile_from_form=lambda validate_name=False: SimpleNamespace(
                name="Demo",
                provider="openai",
                base_url="https://api.openai.com",
                api_keys=["key-1"],
                model="gpt-4o-mini",
            ),
            current_target_language=lambda: "English",
            build_prompt_preset_from_form=lambda validate_name=False: SimpleNamespace(
                name="Translate",
                text_prompt="Translate to {target_language}",
            ),
            current_selection_hotkey=lambda: "Shift+Win+C",
            current_temperature=lambda: 0.2,
            api_client=SimpleNamespace(request_text=Mock(return_value="done")),
            set_status=Mock(),
            log_tr=Mock(),
            log=Mock(),
            show_tray_toast=Mock(),
            update_action_states=Mock(),
            run_worker=Mock(),
            handle_error=Mock(),
            tr=lambda key, **kwargs: key,
        )
        window.background_busy = (
            lambda: window.fetch_models_in_progress
            or window.test_profile_in_progress
            or window.translation_in_progress
            or window.selected_text_capture_in_progress
        )
        return window

    def test_profile_request_signature_can_include_model(self):
        profile = SimpleNamespace(
            name="Demo",
            provider="openai",
            base_url="https://api.openai.com",
            api_keys=["key-1"],
            model="gpt-4o-mini",
        )

        signature_without_model = RequestWorkflowController.profile_request_signature(profile)
        signature_with_model = RequestWorkflowController.profile_request_signature(profile, include_model=True)

        self.assertNotEqual(signature_without_model, signature_with_model)
        self.assertEqual(signature_with_model[-1], "gpt-4o-mini")

    def test_translate_selected_text_starts_async_session_before_request_submission(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        session = _FakeSelectedTextCaptureSession()
        fake_cursor = Mock()
        fake_cursor.pos.return_value = "anchor"

        with patch("app.services.request_workflow.SelectedTextCaptureSession", return_value=session), patch("app.services.request_workflow.QApplication.setOverrideCursor") as mock_set_cursor, patch.object(
            RequestWorkflowController, "_restore_override_cursor"
        ), patch("app.services.request_workflow.QCursor", fake_cursor):
            controller.translate_selected_text()

            self.assertTrue(window.selected_text_capture_in_progress)
            self.assertIs(window.selected_text_capture_session, session)
            self.assertTrue(session.started)
            window.show_tray_toast.assert_not_called()
            window.run_worker.assert_not_called()
            self.assertEqual(window.update_action_states.call_count, 1)

            session.finished.emit("Hello")

        self.assertFalse(window.selected_text_capture_in_progress)
        self.assertIsNone(window.selected_text_capture_session)
        self.assertTrue(session.deleted)
        window.show_tray_toast.assert_called_once_with("selected_text_processing")
        self.assertEqual(window.set_status.call_args_list[0].args[0], "selected_text_capturing")
        self.assertEqual(window.set_status.call_args_list[-1].args[0], "selected_text_processing")
        window.run_worker.assert_called_once()
        mock_set_cursor.assert_called_once()

    def test_cancel_selected_text_capture_cleans_up_without_submitting_request(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        session = _FakeSelectedTextCaptureSession()
        fake_cursor = Mock()
        fake_cursor.pos.return_value = "anchor"

        with patch("app.services.request_workflow.SelectedTextCaptureSession", return_value=session), patch("app.services.request_workflow.QApplication.setOverrideCursor"), patch.object(
            RequestWorkflowController, "_restore_override_cursor"
        ), patch("app.services.request_workflow.QCursor", fake_cursor):
            controller.translate_selected_text()
            self.assertTrue(controller.cancel_selected_text_capture())

        self.assertTrue(session.cancel_called)
        self.assertFalse(window.selected_text_capture_in_progress)
        self.assertIsNone(window.selected_text_capture_session)
        self.assertTrue(session.deleted)
        window.run_worker.assert_not_called()
        window.show_tray_toast.assert_called_once_with("request_cancelled")
        self.assertEqual(window.set_status.call_args_list[-1].args[0], "request_cancelled")


if __name__ == "__main__":
    unittest.main()
