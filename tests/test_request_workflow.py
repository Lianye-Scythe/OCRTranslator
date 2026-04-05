import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.request_workflow import RequestWorkflowController


class _FakeOverlay:
    def __init__(self):
        self.manual_positioned = False
        self.is_pinned = False
        self.last_geometry = None
        self.last_text = ""
        self._visible = False
        self.restore_last_overlay = Mock()

    def isVisible(self):
        return self._visible

    def setVisible(self, value: bool):
        self._visible = bool(value)


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
            overlay_presenter=SimpleNamespace(show_response=Mock(), show_translation=Mock()),
            bridge=SimpleNamespace(invoke_main_thread=SimpleNamespace(emit=lambda callback, payload: callback(payload))),
            handle_error=Mock(),
            tr=lambda key, **kwargs: key,
            restore_window_after_capture=False,
            restore_pinned_overlay_after_capture=False,
            pending_capture_profile=None,
            pending_capture_target_language="English",
            pending_capture_prompt_preset=None,
        )
        window.background_busy = (
            lambda: window.fetch_models_in_progress
            or window.test_profile_in_progress
            or window.translation_in_progress
            or window.selected_text_capture_in_progress
        )
        window.show_main_window = Mock()
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

    def test_submit_text_request_reuses_pinned_overlay_geometry(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        overlay = window.translation_overlay
        overlay.is_pinned = True
        overlay.last_geometry = object()
        overlay.manual_positioned = True
        window.run_worker = Mock()

        controller.submit_text_request(
            "Hello",
            profile=window.build_profile_from_form(),
            target_language="English",
            prompt_preset=window.build_prompt_preset_from_form(),
            anchor_point="anchor",
            source_key="manual_input_processing",
        )

        callback = window.run_worker.call_args.args[1]
        callback("done")

        window.overlay_presenter.show_response.assert_called_once_with(
            "done", anchor_point="anchor", preset_name="Translate", preserve_manual_position=False, preserve_geometry=True
        )

    def test_submit_text_request_keeps_pinned_geometry_flag_even_when_runtime_geometry_is_not_loaded(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        overlay = window.translation_overlay
        overlay.is_pinned = True
        overlay.last_geometry = None
        window.run_worker = Mock()

        controller.submit_text_request(
            "Hello",
            profile=window.build_profile_from_form(),
            target_language="English",
            prompt_preset=window.build_prompt_preset_from_form(),
            anchor_point="anchor",
            source_key="manual_input_processing",
        )

        callback = window.run_worker.call_args.args[1]
        callback("done")

        window.overlay_presenter.show_response.assert_called_once_with(
            "done", anchor_point="anchor", preset_name="Translate", preserve_manual_position=False, preserve_geometry=True
        )

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

    def test_handle_capture_ready_restores_pinned_overlay_while_request_continues(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        overlay = window.translation_overlay
        overlay.is_pinned = True
        overlay.last_text = "previous"
        overlay.setVisible(True)
        window.capture_workflow_active = True
        window.restore_window_after_capture = True
        window.restore_pinned_overlay_after_capture = True
        window.pending_capture_profile = object()
        window.pending_capture_prompt_preset = object()
        window.screen_capture_service = SimpleNamespace(build_preview_pixmap_from_bytes=Mock(return_value="preview-pixmap"))
        window.update_preview = Mock()

        controller._handle_capture_ready(b"png-data")

        window.update_preview.assert_called_once_with(preview_pixmap="preview-pixmap")
        self.assertFalse(window.capture_workflow_active)
        self.assertTrue(window.restore_window_after_capture)
        overlay.restore_last_overlay.assert_called_once_with()
        window.show_main_window.assert_not_called()

    def test_handle_capture_ready_keeps_unpinned_overlay_hidden(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        overlay = window.translation_overlay
        overlay.is_pinned = False
        overlay.last_text = "previous"
        overlay.setVisible(True)
        window.capture_workflow_active = True
        window.restore_pinned_overlay_after_capture = False
        window.screen_capture_service = SimpleNamespace(build_preview_pixmap_from_bytes=Mock(return_value="preview-pixmap"))
        window.update_preview = Mock()

        controller._handle_capture_ready(b"png-data")

        window.update_preview.assert_called_once_with(preview_pixmap="preview-pixmap")
        overlay.restore_last_overlay.assert_not_called()
        self.assertFalse(window.capture_workflow_active)

    @patch("app.services.request_workflow.build_image_request_prompt", return_value="image-prompt")
    def test_handle_selection_captures_in_worker_and_dispatches_preview(self, _mock_prompt):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        events = []

        window.screen_capture_service = SimpleNamespace(
            capture_bbox_png_bytes_threadsafe=Mock(return_value=b"png-data"),
            build_preview_pixmap_from_bytes=Mock(return_value="preview-pixmap"),
        )
        window.pending_capture_profile = None
        window.pending_capture_target_language = "English"
        window.pending_capture_prompt_preset = None
        window.build_prompt_preset_from_form = lambda validate_name=False: SimpleNamespace(name="Translate", image_prompt="Describe")

        def record_update_preview(image=None, *, preview_pixmap=None):
            events.append(("update_preview", image, preview_pixmap))

        def request_image(*args, **kwargs):
            events.append("request_image")
            return "done"

        window.api_client.request_image_png = Mock(side_effect=request_image)
        window.update_preview = Mock(side_effect=record_update_preview)

        controller.handle_selection((10, 20, 110, 120))

        window.run_worker.assert_called_once()
        request_callable = window.run_worker.call_args.args[0]
        window.screen_capture_service.capture_bbox_png_bytes_threadsafe.assert_not_called()
        request_context = SimpleNamespace(is_cancelled=lambda: False)
        self.assertEqual(request_callable(request_context), ("done", unittest.mock.ANY, 8, unittest.mock.ANY))
        window.screen_capture_service.capture_bbox_png_bytes_threadsafe.assert_called_once_with((10, 20, 110, 120))
        window.api_client.request_image_png.assert_called_once_with(b"png-data", unittest.mock.ANY, "image-prompt", 0.2, request_context=request_context)
        window.update_preview.assert_called_once_with(preview_pixmap="preview-pixmap")
        self.assertEqual(events[0], ("update_preview", None, "preview-pixmap"))
        self.assertEqual(events[1], "request_image")
        self.assertEqual(window.set_status.call_args_list[0].args[0], "capturing")
        window.show_tray_toast.assert_called_once_with("tray_capturing")


if __name__ == "__main__":
    unittest.main()
