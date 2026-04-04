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
            api_client=SimpleNamespace(request_text=Mock(return_value="done"), request_image_png=Mock(return_value="done")),
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

    @patch("app.services.request_workflow.QTimer.singleShot", side_effect=lambda _delay, callback: callback())
    @patch("app.services.request_workflow.build_image_request_prompt", return_value="image-prompt")
    def test_handle_selection_starts_request_before_preview_refresh(self, _mock_prompt, _mock_single_shot):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        capture_result = SimpleNamespace(png_bytes=b"png-data", preview_pixmap="preview-pixmap")
        events = []

        window.screen_capture_service = SimpleNamespace(capture_bbox_image=Mock(return_value=capture_result))
        window.pending_capture_profile = None
        window.pending_capture_target_language = "English"
        window.pending_capture_prompt_preset = None
        window.build_prompt_preset_from_form = lambda validate_name=False: SimpleNamespace(name="Translate", image_prompt="Describe")

        def record_run_worker(*args, **kwargs):
            events.append("run_worker")

        def record_update_preview(image=None, *, preview_pixmap=None):
            events.append(("update_preview", image, preview_pixmap))

        window.run_worker = Mock(side_effect=record_run_worker)
        window.update_preview = Mock(side_effect=record_update_preview)

        controller.handle_selection((10, 20, 110, 120))

        window.screen_capture_service.capture_bbox_image.assert_called_once_with((10, 20, 110, 120))
        window.log.assert_called()
        window.run_worker.assert_called_once()
        request_callable = window.run_worker.call_args.args[0]
        self.assertEqual(request_callable("ctx"), "done")
        window.api_client.request_image_png.assert_called_once_with(b"png-data", unittest.mock.ANY, "image-prompt", 0.2, request_context="ctx")
        window.update_preview.assert_called_once_with(preview_pixmap="preview-pixmap")
        self.assertEqual(events[0], "run_worker")
        self.assertEqual(events[1], ("update_preview", None, "preview-pixmap"))
        self.assertEqual(window.set_status.call_args_list[0].args[0], "capturing")
        window.show_tray_toast.assert_called_once_with("tray_capturing")


if __name__ == "__main__":
    unittest.main()
