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

    def hide(self):
        self._visible = False


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
            _fetch_models_request_id=0,
            _test_profile_request_id=0,
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
            current_manual_input_target_language=lambda: "English",
            build_prompt_preset_from_form=lambda validate_name=False: SimpleNamespace(
                name="Translate",
                text_prompt="Translate to {target_language}",
            ),
            current_selection_hotkey=lambda: "Shift+Win+C",
            current_temperature=lambda: 0.2,
            current_mode=lambda: "book_lr",
            current_margin=lambda: 18,
            current_overlay_width=lambda: 440,
            current_request_overlay_width=lambda: 440,
            api_client=SimpleNamespace(
                request_text=Mock(return_value="done"),
                request_image_png=Mock(return_value="done"),
                test_profile=Mock(return_value="OK | provider=openai | model=gpt-4o-mini | response=OK"),
            ),
            config=SimpleNamespace(overlay_unpinned_width=None, overlay_unpinned_width_source="", manual_input_target_language=""),
            set_status=Mock(),
            log_tr=Mock(),
            log=Mock(),
            log_debug=Mock(),
            show_tray_toast=Mock(),
            update_action_states=Mock(),
            run_worker=Mock(),
            overlay_presenter=SimpleNamespace(show_response=Mock(), show_translation=Mock()),
            bridge=SimpleNamespace(invoke_main_thread=SimpleNamespace(emit=lambda callback, payload: callback(payload))),
            handle_error=Mock(),
            tr=lambda key, **kwargs: key,
            restore_window_after_capture=False,
            restore_pinned_overlay_after_capture=False,
            capture_desktop_snapshot=None,
            capture_hidden_owned_windows=[],
            pending_capture_profile=None,
            pending_capture_target_language="English",
            pending_capture_prompt_preset=None,
            current_stream_responses=lambda: True,
            _active_error_dialogs=[],
            screen_capture_service=SimpleNamespace(
                capture_desktop_snapshot=Mock(return_value="desktop-snapshot"),
                build_snapshot_background_pixmap=Mock(return_value="snapshot-background"),
            ),
            toast_service=SimpleNamespace(hide_message=Mock()),
            persist_runtime_overlay_state=Mock(return_value=True),
        )
        window.background_busy = (
            lambda: window.fetch_models_in_progress
            or window.test_profile_in_progress
            or window.translation_in_progress
            or window.selected_text_capture_in_progress
        )
        window.show_main_window = Mock()
        window.hide = Mock()
        window.isVisible = lambda: True
        window.isMinimized = lambda: False
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

    def test_test_profile_uses_current_stream_response_setting(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)

        controller.test_profile()

        worker_target = window.run_worker.call_args.args[0]
        result = worker_target(None)

        self.assertEqual(result[2], "OK | provider=openai | model=gpt-4o-mini | response=OK")
        window.api_client.test_profile.assert_called_once_with(unittest.mock.ANY, stream=True, request_context=None)

        window.api_client.test_profile.reset_mock()
        window.run_worker.reset_mock()
        window.current_stream_responses = lambda: False

        controller.test_profile()
        worker_target = window.run_worker.call_args.args[0]
        worker_target(None)
        window.api_client.test_profile.assert_called_once_with(unittest.mock.ANY, stream=False, request_context=None)

    def test_translate_selected_text_uses_in_app_selection_before_clipboard_capture(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        window.current_stream_responses = lambda: False
        active_window = object()
        selected_widget = SimpleNamespace(selectedText=lambda: "Hello from UI", parentWidget=lambda: active_window)
        fake_cursor = Mock()
        fake_cursor.pos.return_value = "anchor"

        with patch("app.services.request_workflow.QApplication.activeWindow", return_value=active_window), patch(
            "app.services.request_workflow.QApplication.focusWidget", return_value=selected_widget
        ), patch("app.services.request_workflow.QApplication.setOverrideCursor") as mock_set_cursor, patch(
            "app.services.request_workflow.SelectedTextCaptureSession"
        ) as mock_capture_session, patch("app.services.request_workflow.QCursor", fake_cursor):
            controller.translate_selected_text()

        mock_capture_session.assert_not_called()
        mock_set_cursor.assert_not_called()
        self.assertFalse(window.selected_text_capture_in_progress)
        self.assertIsNone(window.selected_text_capture_session)
        window.run_worker.assert_called_once()
        worker_target = window.run_worker.call_args.args[0]
        result = worker_target(None)
        self.assertEqual(result, "done")
        window.api_client.request_text.assert_called_once_with(
            "Translate to English\n\n<text-input>\nHello from UI\n</text-input>",
            unittest.mock.ANY,
            0.2,
            stream=False,
            stream_callback=None,
            request_context=None,
        )

    def test_capture_in_app_selected_text_reads_text_cursor_selection_and_normalizes_newlines(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        active_window = object()
        cursor = SimpleNamespace(hasSelection=lambda: True, selectedText=lambda: "Line 1\u2029Line 2")
        selected_widget = SimpleNamespace(textCursor=lambda: cursor, parentWidget=lambda: active_window)

        with patch("app.services.request_workflow.QApplication.activeWindow", return_value=active_window), patch(
            "app.services.request_workflow.QApplication.focusWidget", return_value=selected_widget
        ):
            self.assertEqual(controller._capture_in_app_selected_text(), "Line 1\nLine 2")

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

    def test_open_prompt_input_dialog_uses_manual_input_scope_and_dialog_target_language(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        window.current_stream_responses = lambda: False
        window.validate_form_inputs = Mock(return_value=(True, ""))
        window.current_manual_input_target_language = lambda: "French"
        created_dialog = {}

        class _FakePromptDialog:
            def __init__(self, app_window, preset_name, target_language):
                created_dialog["window"] = app_window
                created_dialog["preset_name"] = preset_name
                created_dialog["target_language"] = target_language
                self.last_anchor_point = "dialog-anchor"

            def exec(self):
                return True

            def input_text(self):
                return "Hello manual"

            def target_language_text(self):
                return "Japanese"

        with patch.object(controller, "_prompt_input_dialog_class", return_value=_FakePromptDialog):
            controller.open_prompt_input_dialog()

        window.validate_form_inputs.assert_called_once_with(focus_first_invalid=True, scope="manual_input")
        self.assertEqual(created_dialog["preset_name"], "Translate")
        self.assertEqual(created_dialog["target_language"], "French")
        self.assertEqual(window.config.manual_input_target_language, "Japanese")
        window.persist_runtime_overlay_state.assert_called_once_with()
        worker_target = window.run_worker.call_args.args[0]
        result = worker_target(None)

        self.assertEqual(result, "done")
        window.api_client.request_text.assert_called_once_with(
            "Translate to Japanese\n\n<text-input>\nHello manual\n</text-input>",
            unittest.mock.ANY,
            0.2,
            stream=False,
            stream_callback=None,
            request_context=None,
        )


    def test_submit_text_request_reuses_pinned_overlay_geometry(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        overlay = window.translation_overlay
        overlay.is_pinned = True
        overlay.last_geometry = object()
        overlay.manual_positioned = True
        window.current_stream_responses = lambda: False
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
        window.current_stream_responses = lambda: False
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

    def test_submit_text_request_streams_partial_response_updates_when_enabled(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        overlay = window.translation_overlay
        overlay.is_pinned = False
        scheduled_callbacks = []

        def fake_request_text(prompt, profile, temperature, **kwargs):
            self.assertTrue(kwargs["stream"])
            kwargs["stream_callback"]("Hel")
            kwargs["stream_callback"]("Hello")
            return "Hello"

        window.api_client.request_text = Mock(side_effect=fake_request_text)

        with patch("app.services.request_workflow.QTimer.singleShot", side_effect=lambda _ms, callback: scheduled_callbacks.append(callback) or None):
            controller.submit_text_request(
                "Hello",
                profile=window.build_profile_from_form(),
                target_language="English",
                prompt_preset=window.build_prompt_preset_from_form(),
                anchor_point="anchor",
                source_key="manual_input_processing",
            )

            worker_target = window.run_worker.call_args.args[0]
            result = worker_target(None)
            success_callback = window.run_worker.call_args.args[1]

            self.assertEqual(result, "Hello")
            self.assertEqual(len(scheduled_callbacks), 1)
            scheduled_callbacks[0]()

        self.assertEqual(window.overlay_presenter.show_response.call_count, 1)
        first_call = window.overlay_presenter.show_response.call_args_list[0]
        self.assertEqual(first_call.args[0], "Hello")
        self.assertEqual(first_call.kwargs["anchor_point"], "anchor")
        self.assertEqual(first_call.kwargs["locked_width"], 440)
        self.assertTrue(first_call.kwargs["partial"])
        success_callback(result)
        final_call = window.overlay_presenter.show_response.call_args_list[-1]
        self.assertEqual(final_call.args[0], "Hello")
        self.assertEqual(final_call.kwargs["locked_width"], 440)
        self.assertNotIn("partial", final_call.kwargs)

    @patch("app.services.request_workflow.preferred_overlay_width_for_bbox", return_value=565)
    def test_stream_locked_width_for_bbox_seeds_first_capture_request_from_available_space(self, _mock_preferred_width):
        window = self._build_window()
        controller = RequestWorkflowController(window)

        self.assertEqual(controller._stream_locked_width_for_bbox((600, 12, 1322, 1024)), 565)

        window._runtime_auto_unpinned_overlay_width = 620
        self.assertEqual(controller._stream_locked_width_for_bbox((600, 12, 1322, 1024)), 620)

        window._runtime_auto_unpinned_overlay_width = None
        window._runtime_unpinned_overlay_width = 620
        self.assertEqual(controller._stream_locked_width_for_bbox((600, 12, 1322, 1024)), 440)

        window._runtime_unpinned_overlay_width = None
        window.config.overlay_unpinned_width = 620
        window.config.overlay_unpinned_width_source = "manual"
        self.assertEqual(controller._stream_locked_width_for_bbox((600, 12, 1322, 1024)), 565)

        window.config.overlay_unpinned_width = None
        window.current_mode = lambda: "web_ud"
        self.assertEqual(controller._stream_locked_width_for_bbox((600, 12, 1322, 1024)), 440)

    def test_submit_text_request_coalesces_partial_updates_until_next_frame(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        delays = []
        scheduled_callbacks = []

        def fake_request_text(prompt, profile, temperature, **kwargs):
            kwargs["stream_callback"]("Hel")
            kwargs["stream_callback"]("Hello")
            return "Hello"

        window.api_client.request_text = Mock(side_effect=fake_request_text)

        with patch("app.services.request_workflow.QTimer.singleShot", side_effect=lambda delay, callback: delays.append(delay) or scheduled_callbacks.append(callback) or None):
            controller.submit_text_request(
                "Hello",
                profile=window.build_profile_from_form(),
                target_language="English",
                prompt_preset=window.build_prompt_preset_from_form(),
                anchor_point="anchor",
                source_key="manual_input_processing",
            )
            worker_target = window.run_worker.call_args.args[0]
            worker_target(None)

        self.assertEqual(delays, [16])
        self.assertEqual(window.overlay_presenter.show_response.call_count, 0)
        self.assertEqual(len(scheduled_callbacks), 1)
        scheduled_callbacks[0]()
        self.assertEqual(window.overlay_presenter.show_response.call_count, 1)
        partial_call = window.overlay_presenter.show_response.call_args_list[0]
        self.assertEqual(partial_call.args[0], "Hello")
        self.assertTrue(partial_call.kwargs["partial"])

    def test_submit_text_request_final_result_invalidates_pending_partial_flush(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        scheduled_callbacks = []

        def fake_request_text(prompt, profile, temperature, **kwargs):
            kwargs["stream_callback"]("Hello")
            return "Hello"

        window.api_client.request_text = Mock(side_effect=fake_request_text)

        with patch("app.services.request_workflow.QTimer.singleShot", side_effect=lambda _delay, callback: scheduled_callbacks.append(callback) or None):
            controller.submit_text_request(
                "Hello",
                profile=window.build_profile_from_form(),
                target_language="English",
                prompt_preset=window.build_prompt_preset_from_form(),
                anchor_point="anchor",
                source_key="manual_input_processing",
            )
            worker_target = window.run_worker.call_args.args[0]
            result = worker_target(None)
            success_callback = window.run_worker.call_args.args[1]
            success_callback(result)

        self.assertEqual(window.overlay_presenter.show_response.call_count, 1)
        scheduled_callbacks[0]()
        self.assertEqual(window.overlay_presenter.show_response.call_count, 1)
        self.assertEqual(window.overlay_presenter.show_response.call_args_list[0].args[0], "Hello")

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
    def test_handle_selection_captures_before_worker_and_dispatches_preview(self, _mock_prompt):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        events = []
        capture_order = []
        window.capture_desktop_snapshot = "desktop-snapshot"

        window.screen_capture_service = SimpleNamespace(
            build_capture_plan=Mock(side_effect=lambda bbox: capture_order.append("build") or "capture-plan"),
            log_capture_plan=Mock(side_effect=lambda bbox, plan: capture_order.append("log")),
            capture_bbox_png_bytes_from_snapshot=Mock(
                side_effect=lambda snapshot, bbox, *, capture_plan=None: capture_order.append("crop") or b"png-data"
            ),
            build_preview_pixmap_from_bytes=Mock(return_value="preview-pixmap"),
        )
        window.pending_capture_profile = None
        window.pending_capture_target_language = "English"
        window.pending_capture_prompt_preset = None
        window.build_prompt_preset_from_form = lambda validate_name=False: SimpleNamespace(name="Translate", image_prompt="Describe")

        def record_update_preview(*, preview_pixmap=None):
            events.append(("update_preview", preview_pixmap))

        def request_image(*args, **kwargs):
            events.append("request_image")
            return "done"

        window.api_client.request_image_png = Mock(side_effect=request_image)
        window.update_preview = Mock(side_effect=record_update_preview)

        controller.handle_selection((10, 20, 110, 120))

        window.run_worker.assert_called_once()
        window.screen_capture_service.build_capture_plan.assert_called_once_with((10, 20, 110, 120))
        window.screen_capture_service.log_capture_plan.assert_called_once_with((10, 20, 110, 120), "capture-plan")
        window.screen_capture_service.capture_bbox_png_bytes_from_snapshot.assert_called_once_with("desktop-snapshot", (10, 20, 110, 120), capture_plan="capture-plan")
        self.assertEqual(capture_order[:3], ["build", "log", "crop"])
        request_callable = window.run_worker.call_args.args[0]
        request_context = SimpleNamespace(is_cancelled=lambda: False)
        self.assertEqual(request_callable(request_context), ("done", unittest.mock.ANY, 8, unittest.mock.ANY))
        self.assertIsNone(window.capture_desktop_snapshot)
        self.assertTrue(window.log_debug.call_args_list[0].args[0].startswith("截圖同步抓取完成｜snapshot_crop="))
        window.api_client.request_image_png.assert_called_once_with(
            b"png-data",
            unittest.mock.ANY,
            "image-prompt",
            0.2,
            stream=True,
            stream_callback=unittest.mock.ANY,
            request_context=request_context,
        )
        window.update_preview.assert_called_once_with(preview_pixmap="preview-pixmap")
        self.assertEqual(events[0], ("update_preview", "preview-pixmap"))
        self.assertEqual(events[1], "request_image")
        self.assertEqual(window.set_status.call_args_list[0].args[0], "capturing")
        window.show_tray_toast.assert_called_once_with("tray_capturing")

    def test_start_selection_allows_explicit_restore_override_for_capture_launch(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        overlay = window.translation_overlay
        overlay.is_pinned = False
        overlay.last_text = ""
        window.isVisible = lambda: False
        window.isMinimized = lambda: False
        old_selection_overlay = SimpleNamespace(show_overlay=Mock(), set_snapshot_background=Mock(), clear_snapshot_background=Mock(), hide=Mock(), close=Mock(), deleteLater=Mock())
        new_selection_overlay = SimpleNamespace(show_overlay=Mock(), set_snapshot_background=Mock(), clear_snapshot_background=Mock())
        window.selection_overlay = old_selection_overlay
        window.recreate_selection_overlay = Mock(side_effect=lambda: setattr(window, "selection_overlay", new_selection_overlay) or new_selection_overlay)
        dialog = SimpleNamespace(isVisible=lambda: True, hide=Mock(), show=Mock(), raise_=Mock(), activateWindow=Mock())
        window._active_error_dialogs = [dialog]
        window.screen_capture_service = SimpleNamespace(
            capture_desktop_snapshot=Mock(return_value=SimpleNamespace(virtual_rect=(0, 0, 1920, 1080), segments=(object(), object()))),
            build_snapshot_background_pixmap=Mock(return_value="snapshot-background"),
        )

        with patch.object(RequestWorkflowController, "_run_capture_hide_barrier", return_value=(0.012, True)) as mock_barrier:
            controller.start_selection(restore_window_after_capture=True)

        self.assertTrue(window.capture_workflow_active)
        self.assertTrue(window.restore_window_after_capture)
        mock_barrier.assert_called_once_with()
        window.toast_service.hide_message.assert_called_once_with()
        window.recreate_selection_overlay.assert_called_once_with()
        dialog.hide.assert_called_once_with()
        old_selection_overlay.show_overlay.assert_not_called()
        old_selection_overlay.set_snapshot_background.assert_not_called()
        new_selection_overlay.clear_snapshot_background.assert_called_once_with()
        new_selection_overlay.show_overlay.assert_called_once_with()
        new_selection_overlay.set_snapshot_background.assert_called_once_with("snapshot-background", virtual_rect=(0, 0, 1920, 1080))
        window.screen_capture_service.capture_desktop_snapshot.assert_called_once_with()
        window.screen_capture_service.build_snapshot_background_pixmap.assert_called_once()
        self.assertIsNotNone(window.capture_desktop_snapshot)
        self.assertIsNotNone(window.pending_capture_profile)
        self.assertIsNotNone(window.pending_capture_prompt_preset)
        self.assertEqual(window.pending_capture_target_language, "English")
        window.hide.assert_called_once_with()

    def test_finish_capture_workflow_restores_hidden_app_owned_windows_when_window_should_return(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        dialog = SimpleNamespace(show=Mock(), raise_=Mock(), activateWindow=Mock())
        window.capture_hidden_owned_windows = [dialog]
        window.restore_window_after_capture = True
        window.capture_workflow_active = True

        controller.finish_capture_workflow(restore_window=True)

        window.show_main_window.assert_called_once_with()
        dialog.show.assert_called_once_with()
        dialog.raise_.assert_called_once_with()
        dialog.activateWindow.assert_called_once_with()
        self.assertEqual(window.capture_hidden_owned_windows, [])

    def test_finish_capture_workflow_clears_hidden_app_owned_windows_when_window_stays_hidden(self):
        window = self._build_window()
        controller = RequestWorkflowController(window)
        dialog = SimpleNamespace(show=Mock(), raise_=Mock(), activateWindow=Mock())
        window.capture_hidden_owned_windows = [dialog]
        window.restore_window_after_capture = False
        window.capture_workflow_active = True

        controller.finish_capture_workflow(restore_window=False)

        window.show_main_window.assert_not_called()
        dialog.show.assert_not_called()
        self.assertEqual(window.capture_hidden_owned_windows, [])


if __name__ == "__main__":
    unittest.main()
