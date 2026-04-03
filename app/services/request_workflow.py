from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication

from ..prompt_utils import build_image_request_prompt, build_text_request_prompt
from ..profile_utils import normalize_model_value, unique_non_empty
from ..selected_text_capture import capture_selected_text
from ..ui.prompt_input_dialog import PromptInputDialog


class RequestWorkflowController:
    def __init__(self, window):
        self.window = window

    def prepare_request_context(self, *, focus_first_invalid: bool = True):
        if self.window.capture_workflow_active:
            self.window.log("Request ignored because another capture workflow is still active")
            return None
        if self.window.background_busy():
            self.window.log("Request ignored because another background operation is still running")
            return None
        valid, first_error = self.window.validate_form_inputs(focus_first_invalid=focus_first_invalid)
        if not valid:
            self.window.set_status("validation_failed")
            self.window.log(f"Request blocked by validation: {first_error}")
            return None
        return {
            "profile": self.window.build_profile_from_form(),
            "target_language": self.window.current_target_language(),
            "prompt_preset": self.window.build_prompt_preset_from_form(),
        }

    @staticmethod
    def profile_request_signature(profile) -> tuple:
        return (
            profile.name,
            profile.provider,
            profile.base_url.strip(),
            tuple(profile.api_keys),
        )

    def form_matches_profile_request(self, signature: tuple) -> bool:
        try:
            current_profile = self.window.build_profile_from_form()
        except Exception:  # noqa: BLE001
            return False
        return self.profile_request_signature(current_profile) == signature

    def fetch_models(self):
        if self.window.fetch_models_in_progress or self.window.test_profile_in_progress or self.window.translation_in_progress:
            return
        valid, first_error = self.window.validate_form_inputs(focus_first_invalid=True)
        if not valid:
            self.window.set_status("validation_failed")
            self.window.log(f"Fetch models blocked by validation: {first_error}")
            return
        profile = self.window.build_profile_from_form()
        request_id = self.window._fetch_models_request_id = self.window._fetch_models_request_id + 1
        request_signature = self.profile_request_signature(profile)
        self.window.log(f"Fetching models for profile: {profile.name}")
        self.window.run_worker(
            lambda request_context: (request_id, request_signature, profile.provider, self.window.api_client.list_models(profile, request_context=request_context)),
            self.on_models_loaded,
            operation_key="fetch_models",
            cancellable=True,
        )

    def on_models_loaded(self, result):
        request_id, request_signature, provider, models = result
        if request_id != self.window._fetch_models_request_id:
            self.window.log("Discarded stale model list result from an older request")
            return
        if not self.form_matches_profile_request(request_signature):
            self.window.log("Discarded model list result because the form changed while the request was running")
            return
        normalized_models = unique_non_empty(normalize_model_value(item, provider) for item in models)
        if not normalized_models:
            return
        current_model = self.window.normalize_model_name(self.window.model_combo.currentText(), provider)
        self.window._suppress_form_tracking = True
        try:
            self.window.model_combo.blockSignals(True)
            self.window.model_combo.clear()
            self.window.model_combo.addItems([self.window.display_model_name(item, provider) for item in normalized_models])
            selected_model = current_model if current_model in normalized_models else normalized_models[0]
            self.window.model_combo.setCurrentText(self.window.display_model_name(selected_model, provider))
        finally:
            self.window.model_combo.blockSignals(False)
            self.window._suppress_form_tracking = False
        self.window.on_form_input_changed()
        self.window.set_status("models_loaded", count=len(normalized_models))
        self.window.log(f"Loaded {len(normalized_models)} models")

    def test_profile(self):
        if self.window.fetch_models_in_progress or self.window.test_profile_in_progress or self.window.translation_in_progress:
            return
        valid, first_error = self.window.validate_form_inputs(focus_first_invalid=True)
        if not valid:
            self.window.set_status("validation_failed")
            self.window.log(f"Test API blocked by validation: {first_error}")
            return
        profile = self.window.build_profile_from_form()
        request_id = self.window._test_profile_request_id = self.window._test_profile_request_id + 1
        request_signature = self.profile_request_signature(profile)
        self.window.log(f"Testing profile: {profile.name}")
        self.window.run_worker(
            lambda request_context: (request_id, request_signature, self.window.api_client.test_profile(profile, request_context=request_context)),
            self.on_test_success,
            operation_key="test_profile",
            cancellable=True,
        )

    def on_test_success(self, result):
        request_id, request_signature, message = result
        if request_id != self.window._test_profile_request_id or not self.form_matches_profile_request(request_signature):
            self.window.log("Discarded stale API test result because the form changed while the request was running")
            return
        self.window.log(message)
        self.window.set_status("test_success")

    def submit_text_request(self, text: str, *, profile, target_language: str, prompt_preset, anchor_point, source_key: str):
        prompt = build_text_request_prompt(prompt_preset.text_prompt, text, target_language=target_language)
        self.window.set_status(source_key)
        self.window.log(f"Submitting text request | preset={prompt_preset.name} | chars={len(text)}")
        self.window.show_tray_toast(self.window.tr(source_key))
        preserve_manual_position = bool(self.window.translation_overlay.isVisible() and self.window.translation_overlay.manual_positioned)
        self.window.run_worker(
            lambda request_context: self.window.api_client.request_text(prompt, profile, self.window.current_temperature(), request_context=request_context),
            lambda result, anchor_point=anchor_point, preset_name=prompt_preset.name, preserve_manual_position=preserve_manual_position: self.window.overlay_presenter.show_response(
                result,
                anchor_point=anchor_point,
                preset_name=preset_name,
                preserve_manual_position=preserve_manual_position,
            ),
            operation_key="translation",
            cancellable=True,
        )

    def translate_selected_text(self):
        request_context = self.prepare_request_context(focus_first_invalid=True)
        if not request_context:
            return
        self.window.log("Attempting to capture selected text via clipboard preservation")
        self.window.set_status("selected_text_capturing")
        self.window.show_tray_toast(self.window.tr("selected_text_capturing"))
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            selected_text = capture_selected_text(hotkey_text=self.window.current_selection_hotkey())
        finally:
            QApplication.restoreOverrideCursor()
        if not selected_text:
            self.window.set_status("selected_text_empty")
            self.window.log("Selected text capture returned no usable text")
            self.window.show_tray_toast(self.window.tr("selected_text_empty"))
            return
        self.submit_text_request(
            selected_text,
            profile=request_context["profile"],
            target_language=request_context["target_language"],
            prompt_preset=request_context["prompt_preset"],
            anchor_point=QCursor.pos(),
            source_key="selected_text_processing",
        )

    def open_prompt_input_dialog(self):
        request_context = self.prepare_request_context(focus_first_invalid=True)
        if not request_context:
            return
        dialog = PromptInputDialog(self.window, request_context["prompt_preset"].name, request_context["target_language"])
        if not dialog.exec():
            return
        self.submit_text_request(
            dialog.input_text(),
            profile=request_context["profile"],
            target_language=request_context["target_language"],
            prompt_preset=request_context["prompt_preset"],
            anchor_point=dialog.last_anchor_point or QCursor.pos(),
            source_key="manual_input_processing",
        )

    def start_selection(self):
        request_context = self.prepare_request_context(focus_first_invalid=True)
        if not request_context:
            return
        restore_window_after_capture = self.window.isVisible() and not self.window.isMinimized()
        self.window.pending_capture_profile = request_context["profile"]
        self.window.pending_capture_target_language = request_context["target_language"]
        self.window.pending_capture_prompt_preset = request_context["prompt_preset"]
        self.window.restore_pinned_overlay_after_capture = bool(
            self.window.translation_overlay.isVisible()
            and self.window.translation_overlay.is_pinned
            and self.window.translation_overlay.last_text.strip()
        )
        self.window.log(
            f"Starting capture workflow | preset={self.window.pending_capture_prompt_preset.name} | target={self.window.pending_capture_target_language}"
        )
        self.window.capture_workflow_active = True
        self.window.restore_window_after_capture = restore_window_after_capture
        self.window.update_action_states()
        self.window.hide()
        self.window.translation_overlay.hide()
        self.window.selection_overlay.show_overlay()

    def finish_capture_workflow(self, restore_window: bool = False):
        should_restore = restore_window and self.window.restore_window_after_capture
        self.window.capture_workflow_active = False
        self.window.restore_window_after_capture = False
        self.window.pending_capture_profile = None
        self.window.pending_capture_target_language = self.window.current_target_language()
        self.window.pending_capture_prompt_preset = None
        self.window.update_action_states()
        if should_restore:
            self.window.show_main_window()

    def handle_capture_cancelled(self):
        self.window.log("Capture cancelled")
        self.finish_capture_workflow(restore_window=True)
        if self.window.restore_pinned_overlay_after_capture:
            self.window.translation_overlay.restore_last_overlay()
            self.window.restore_pinned_overlay_after_capture = False
        self.window.set_status("capture_cancelled")
        self.window.show_tray_toast(self.window.tr("capture_cancelled"))

    def handle_selection(self, bbox):
        image = self.window.screen_capture_service.capture_bbox_image(bbox)
        self.window.update_preview(image)
        self.window.set_status("capturing")
        self.window.show_tray_toast(self.window.tr("tray_capturing"))
        profile = self.window.pending_capture_profile or self.window.build_profile_from_form()
        target_language = self.window.pending_capture_target_language or self.window.current_target_language()
        prompt_preset = self.window.pending_capture_prompt_preset or self.window.build_prompt_preset_from_form()
        prompt = build_image_request_prompt(prompt_preset.image_prompt, target_language=target_language)
        self.window.run_worker(
            lambda request_context: self.window.api_client.request_image(image, profile, prompt, self.window.current_temperature(), request_context=request_context),
            lambda text, bbox=bbox, preset_name=prompt_preset.name: self.window.overlay_presenter.show_translation(
                bbox,
                text,
                preset_name=preset_name,
            ),
            operation_key="translation",
            cancellable=True,
        )
