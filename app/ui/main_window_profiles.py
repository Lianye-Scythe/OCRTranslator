from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMessageBox

from ..config_store import load_config, save_config
from ..constants import I18N, MODEL_PREFIX, PROVIDER_LABELS
from ..models import ApiProfile
from ..profile_utils import (
    default_base_url_for_provider,
    default_model_for_provider,
    display_model_value,
    normalize_model_value,
    normalize_provider_name,
    unique_non_empty,
)


class MainWindowProfilesMixin:
    def provider_display(self, provider: str) -> str:
        return PROVIDER_LABELS.get(provider, {}).get(self.current_ui_language(), provider)

    def is_form_tracking_suppressed(self) -> bool:
        return bool(getattr(self, "_suppress_form_tracking", False))

    def set_unsaved_changes(self, dirty: bool):
        self.has_unsaved_changes = bool(dirty)
        self.setWindowModified(self.has_unsaved_changes)

    def on_form_input_changed(self, *_):
        if self.is_form_tracking_suppressed():
            return
        self.set_unsaved_changes(True)
        if hasattr(self, "refresh_shell_state"):
            self.refresh_shell_state()
        self.validate_form_inputs()

    def reload_saved_config(self):
        self.config = load_config()
        self.load_profile_to_form(self.config.active_profile_name)

    def prompt_unsaved_changes(self) -> QMessageBox.StandardButton:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle(self.tr("unsaved_changes_title"))
        dialog.setText(self.tr("unsaved_changes_message"))
        save_button = dialog.addButton(self.tr("unsaved_changes_save"), QMessageBox.AcceptRole)
        discard_button = dialog.addButton(self.tr("unsaved_changes_discard"), QMessageBox.DestructiveRole)
        cancel_button = dialog.addButton(self.tr("unsaved_changes_cancel"), QMessageBox.RejectRole)
        dialog.setDefaultButton(save_button)
        dialog.exec()
        clicked = dialog.clickedButton()
        if clicked == save_button:
            return QMessageBox.Save
        if clicked == discard_button:
            return QMessageBox.Discard
        if clicked == cancel_button:
            return QMessageBox.Cancel
        return QMessageBox.Cancel

    def resolve_unsaved_changes(self, *, for_exit: bool = False) -> bool:
        if not getattr(self, "has_unsaved_changes", False):
            return True
        choice = self.prompt_unsaved_changes()
        if choice == QMessageBox.Save:
            return self.save_settings()
        if choice == QMessageBox.Discard:
            if not for_exit:
                self.reload_saved_config()
            return True
        return False

    def display_model_name(self, model_name: str, provider: str | None = None) -> str:
        active_provider = normalize_provider_name(provider or self.provider_combo.currentData() or self.get_active_profile().provider)
        return display_model_value(model_name, active_provider)

    def normalize_model_name(self, model_name: str, provider: str | None = None) -> str:
        active_provider = normalize_provider_name(provider or self.provider_combo.currentData() or self.get_active_profile().provider)
        return normalize_model_value(model_name, active_provider)

    def update_mode_options(self, current: str | None = None):
        current_value = current or self.mode_combo.currentData() or self.config.mode
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        self.mode_combo.addItem(self.tr("mode_book_lr"), "book_lr")
        self.mode_combo.addItem(self.tr("mode_web_ud"), "web_ud")
        index = self.mode_combo.findData(current_value)
        self.mode_combo.setCurrentIndex(max(0, index))
        self.mode_combo.blockSignals(False)

    def update_provider_options(self):
        current = self.provider_combo.currentData() or self.get_active_profile().provider
        self.provider_combo.blockSignals(True)
        self.provider_combo.clear()
        for key in ("gemini", "openai"):
            self.provider_combo.addItem(self.provider_display(key), key)
        idx = self.provider_combo.findData(current)
        self.provider_combo.setCurrentIndex(max(0, idx))
        self.provider_combo.blockSignals(False)

    def on_provider_selected(self):
        provider = normalize_provider_name(self.provider_combo.currentData() or "gemini")
        if self.is_form_tracking_suppressed():
            self._form_provider = provider
            return
        profile = self.get_active_profile()
        previous_provider = getattr(self, "_form_provider", profile.provider)
        if provider != previous_provider:
            self.base_url_edit.setText(default_base_url_for_provider(provider))
            default_model = profile.model if provider == profile.provider else default_model_for_provider(provider)
            self.model_combo.clear()
            if default_model:
                self.model_combo.addItem(self.display_model_name(default_model, provider))
            self.model_combo.setCurrentText(self.display_model_name(default_model, provider))
        else:
            if not self.base_url_edit.text().strip():
                self.base_url_edit.setText(default_base_url_for_provider(provider))
            if not self.model_combo.currentText().strip():
                default_model = profile.model if provider == profile.provider else default_model_for_provider(provider)
                self.model_combo.setCurrentText(self.display_model_name(default_model, provider))
        self._form_provider = provider
        self.on_form_input_changed()
        self.log(f"Provider changed to: {provider}")

    def refresh_profile_combo(self):
        names = [profile.name for profile in self.config.api_profiles]
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(names)
        idx = self.profile_combo.findText(self.config.active_profile_name)
        self.profile_combo.setCurrentIndex(max(0, idx))
        self.profile_combo.blockSignals(False)

    def find_profile_by_name(self, name: str) -> ApiProfile | None:
        for profile in self.config.api_profiles:
            if profile.name == name:
                return profile
        return None

    def get_profile_by_name(self, name: str) -> ApiProfile:
        return self.find_profile_by_name(name) or self.config.api_profiles[0]

    def get_active_profile(self) -> ApiProfile:
        return self.get_profile_by_name(self.config.active_profile_name)

    def on_profile_selected(self, name: str):
        if not name:
            return
        if name == self.config.active_profile_name:
            return
        if not self.resolve_unsaved_changes():
            self.refresh_profile_combo()
            return
        self.load_profile_to_form(name)

    def mask_api_key_line(self, value: str) -> str:
        value = value.strip()
        if not value:
            return ""
        if len(value) <= 8:
            return value[:1] + "*" * max(1, len(value) - 2) + value[-1:]
        return f"{value[:4]}{'*' * max(3, len(value) - 8)}{value[-4:]}"

    def set_api_keys_editor_text(self, text: str):
        self._updating_api_keys = True
        self.api_keys_edit.setPlainText(text)
        self._updating_api_keys = False

    def refresh_api_keys_editor(self):
        masked_lines = [self.mask_api_key_line(line) for line in self.api_keys_actual_text.splitlines() if line.strip()]
        display_text = self.api_keys_actual_text if self.api_keys_visible else "\n".join(masked_lines)
        self.set_api_keys_editor_text(display_text)
        self.api_keys_edit.setReadOnly(not self.api_keys_visible)
        self.api_keys_label_row.setText(self.tr("api_keys") if self.api_keys_visible else self.tr("api_keys_hidden"))
        self.api_keys_toggle_button.setText(
            self.tr("hide_api_keys") if self.api_keys_visible else self.tr("show_api_keys")
        )
        self.api_keys_hint.setText(self.tr("api_keys_hint") if self.api_keys_visible else self.tr("api_keys_mask_hint"))

    def on_api_keys_text_changed(self):
        if getattr(self, "_updating_api_keys", False) or self.is_form_tracking_suppressed():
            return
        if self.api_keys_visible:
            self.api_keys_actual_text = self.api_keys_edit.toPlainText()
        self.on_form_input_changed()

    def toggle_api_keys_visibility(self):
        if self.api_keys_visible:
            self.api_keys_actual_text = self.api_keys_edit.toPlainText()
            self.api_keys_visible = False
        else:
            self.api_keys_visible = True
        self.refresh_api_keys_editor()
        self.validate_form_inputs()

    def get_api_keys_text(self) -> str:
        if self.api_keys_visible:
            self.api_keys_actual_text = self.api_keys_edit.toPlainText()
        return getattr(self, "api_keys_actual_text", "")

    def hotkey_has_modifier(self, hotkey_text: str) -> bool:
        parts = {part.strip().lower() for part in hotkey_text.replace("-", "+").split("+") if part.strip()}
        return any(part in {"ctrl", "control", "alt", "shift", "cmd", "win", "windows", "meta"} for part in parts)

    def _refresh_widget_style(self, widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
        line_edit = widget.lineEdit() if hasattr(widget, "lineEdit") else None
        if line_edit:
            line_edit.setProperty("invalid", widget.property("invalid"))
            line_edit.style().unpolish(line_edit)
            line_edit.style().polish(line_edit)
            line_edit.update()

    def set_widget_invalid(self, widget, invalid: bool):
        widget.setProperty("invalid", invalid)
        self._refresh_widget_style(widget)

    def set_validation_message(self, label, messages: list[str]):
        if messages:
            label.setText("\n".join(f"• {message}" for message in messages[:3]))
            label.show()
        else:
            label.clear()
            label.hide()

    def validate_form_inputs(self, *, focus_first_invalid: bool = False) -> tuple[bool, str]:
        api_errors: list[str] = []
        reading_errors: list[str] = []
        invalid_widgets = []

        for widget in [
            self.profile_name_edit,
            self.base_url_edit,
            self.model_combo,
            self.api_keys_edit,
            self.target_language_edit,
            self.hotkey_edit,
        ]:
            self.set_widget_invalid(widget, False)

        def mark_invalid(widget, message: str, bucket: list[str]):
            self.set_widget_invalid(widget, True)
            if message not in bucket:
                bucket.append(message)
            if widget not in invalid_widgets:
                invalid_widgets.append(widget)

        try:
            self.validate_profile_name(self.profile_name_edit.text(), self.get_active_profile().name)
        except Exception as exc:  # noqa: BLE001
            mark_invalid(self.profile_name_edit, str(exc), api_errors)

        base_url = self.base_url_edit.text().strip()
        if not base_url:
            mark_invalid(self.base_url_edit, self.tr("validation_base_url_required"), api_errors)
        elif not base_url.lower().startswith(("http://", "https://")):
            mark_invalid(self.base_url_edit, self.tr("validation_base_url_scheme"), api_errors)

        if not self.model_combo.currentText().strip():
            mark_invalid(self.model_combo, self.tr("validation_model_required"), api_errors)

        api_keys = unique_non_empty(self.get_api_keys_text().splitlines())
        if not api_keys:
            mark_invalid(self.api_keys_edit, self.tr("validation_api_keys_required"), api_errors)

        if not self.target_language_edit.text().strip():
            mark_invalid(self.target_language_edit, self.tr("validation_target_language_required"), reading_errors)

        hotkey_value = self.hotkey_edit.text().strip()
        if getattr(self, "hotkey_recording", False):
            mark_invalid(self.hotkey_edit, self.tr("validation_hotkey_recording"), reading_errors)
        elif not hotkey_value:
            mark_invalid(self.hotkey_edit, self.tr("validation_hotkey_required"), reading_errors)
        else:
            try:
                self.normalize_hotkey(hotkey_value)
                if not self.hotkey_has_modifier(hotkey_value):
                    mark_invalid(self.hotkey_edit, self.tr("validation_hotkey_requires_modifier"), reading_errors)
            except Exception as exc:  # noqa: BLE001
                mark_invalid(self.hotkey_edit, self.tr("validation_hotkey_invalid", error=exc), reading_errors)

        self.set_validation_message(self.api_validation_label, api_errors)
        self.set_validation_message(self.reading_validation_label, reading_errors)

        first_error = api_errors[0] if api_errors else reading_errors[0] if reading_errors else ""
        if focus_first_invalid and invalid_widgets:
            invalid_widgets[0].setFocus()
        return not (api_errors or reading_errors), first_error

    def start_hotkey_recording(self):
        if getattr(self, "hotkey_recording", False):
            self.stop_hotkey_recording(cancelled=True)
            return
        self.hotkey_recording = True
        self.hotkey_edit.setFocus()
        self.hotkey_edit.selectAll()
        self.hotkey_record_button.setText(self.tr("recording_hotkey"))
        self.set_status("hotkey_recording")
        self.validate_form_inputs()

    def stop_hotkey_recording(self, *, cancelled: bool = False):
        if not getattr(self, "hotkey_recording", False):
            return
        self.hotkey_recording = False
        self.hotkey_record_button.setText(self.tr("record_hotkey"))
        self.validate_form_inputs()
        if cancelled:
            self.set_status("hotkey_record_cancelled")

    def _format_hotkey_from_event(self, event) -> str:
        key = event.key()
        if key in {Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta}:
            return ""

        parts: list[str] = []
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.ShiftModifier:
            parts.append("Shift")
        if modifiers & Qt.MetaModifier:
            parts.append("Win")

        special_keys = {
            Qt.Key_Return: "Enter",
            Qt.Key_Enter: "Enter",
            Qt.Key_Tab: "Tab",
            Qt.Key_Space: "Space",
            Qt.Key_Backspace: "Backspace",
            Qt.Key_Delete: "Delete",
            Qt.Key_Insert: "Insert",
            Qt.Key_Home: "Home",
            Qt.Key_End: "End",
            Qt.Key_PageUp: "PageUp",
            Qt.Key_PageDown: "PageDown",
            Qt.Key_Left: "Left",
            Qt.Key_Right: "Right",
            Qt.Key_Up: "Up",
            Qt.Key_Down: "Down",
        }

        if Qt.Key_F1 <= key <= Qt.Key_F24:
            key_text = f"F{key - Qt.Key_F1 + 1}"
        elif key in special_keys:
            key_text = special_keys[key]
        else:
            key_text = (event.text() or "").strip().upper()

        if not key_text:
            return ""
        if key_text not in parts:
            parts.append(key_text)
        return "+".join(parts)

    def eventFilter(self, watched, event):
        if watched is getattr(self, "hotkey_edit", None) and getattr(self, "hotkey_recording", False):
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self.stop_hotkey_recording(cancelled=True)
                    return True
                hotkey_text = self._format_hotkey_from_event(event)
                if hotkey_text:
                    if not self.hotkey_has_modifier(hotkey_text):
                        self.set_status("validation_hotkey_requires_modifier")
                        self.validate_form_inputs()
                        return True
                    self.hotkey_edit.setText(hotkey_text)
                    self.hotkey_recording = False
                    self.hotkey_record_button.setText(self.tr("record_hotkey"))
                    self.validate_form_inputs()
                    self.set_status("hotkey_recorded", hotkey=hotkey_text)
                elif event.key() not in {Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta}:
                    self.set_status("validation_hotkey_requires_modifier")
                return True
            if event.type() in {QEvent.Type.ShortcutOverride, QEvent.Type.KeyRelease}:
                return True
        return super().eventFilter(watched, event)

    def load_profile_to_form(self, profile_name: str):
        self.stop_hotkey_recording(cancelled=False)
        profile = self.get_profile_by_name(profile_name)
        self._suppress_form_tracking = True
        try:
            self.config.active_profile_name = profile.name
            self.refresh_profile_combo()
            self.profile_name_edit.setText(profile.name)
            self._form_provider = normalize_provider_name(profile.provider)
            idx = self.provider_combo.findData(profile.provider)
            self.provider_combo.setCurrentIndex(max(0, idx))
            self.base_url_edit.setText(profile.base_url or default_base_url_for_provider(profile.provider))
            self.model_combo.clear()
            self.model_combo.addItems(unique_non_empty(self.display_model_name(m, profile.provider) for m in (profile.available_models or [profile.model])))
            self.model_combo.setCurrentText(self.display_model_name(profile.model, profile.provider))
            self.api_keys_actual_text = "\n".join(profile.api_keys)
            self.refresh_api_keys_editor()
            self.retry_count_spin.setValue(profile.retry_count)
            self.retry_interval_spin.setValue(profile.retry_interval)
            self.target_language_edit.setText(self.config.target_language)
            self.ui_language_combo.setCurrentText(self.config.ui_language)
            self.hotkey_edit.setText(self.config.hotkey)
            self.overlay_font_combo.setCurrentFont(QFont(self.config.overlay_font_family))
            self.temperature_spin.setValue(self.config.temperature)
            self.overlay_font_size_spin.setValue(self.config.overlay_font_size)
            self.overlay_width_spin.setValue(self.config.overlay_width)
            self.overlay_height_spin.setValue(self.config.overlay_height)
            self.overlay_margin_spin.setValue(self.config.margin)
            self.update_mode_options(self.config.mode)
        finally:
            self._suppress_form_tracking = False
        self.apply_language()
        self.validate_form_inputs()
        self.set_unsaved_changes(False)
        if hasattr(self, "refresh_shell_state"):
            self.refresh_shell_state()

    def next_profile_name(self) -> str:
        existing = {profile.name for profile in self.config.api_profiles}
        index = 1
        while True:
            candidate = self.tr("profile_name_template", index=index)
            if candidate not in existing:
                return candidate
            index += 1

    def validate_profile_name(self, name: str, current_name: str | None = None) -> str:
        normalized = name.strip() or self.tr("untitled_profile")
        if normalized in {profile.name for profile in self.config.api_profiles if profile.name != current_name}:
            raise ValueError(self.tr("profile_name_exists", name=normalized))
        return normalized

    def build_profile_from_form(self) -> ApiProfile:
        current_profile = self.get_active_profile()
        provider = normalize_provider_name(self.provider_combo.currentData() or "gemini")
        profile_name = self.validate_profile_name(self.profile_name_edit.text(), current_profile.name)
        api_keys = unique_non_empty(self.get_api_keys_text().splitlines())
        available_models = unique_non_empty(self.normalize_model_name(self.model_combo.itemText(i), provider) for i in range(self.model_combo.count()))
        fallback_model = current_profile.model if current_profile.provider == provider else default_model_for_provider(provider)
        model = self.normalize_model_name(self.model_combo.currentText() or fallback_model, provider)
        if provider == "openai" and model.startswith(MODEL_PREFIX):
            model = model[len(MODEL_PREFIX):]
        if not model and available_models:
            model = available_models[0]
        if model and model not in available_models:
            available_models.append(model)
        base_url = self.base_url_edit.text().strip()
        if not base_url:
            if current_profile.provider == provider and current_profile.base_url.strip():
                base_url = current_profile.base_url.strip()
            else:
                base_url = default_base_url_for_provider(provider)
        return ApiProfile(
            name=profile_name,
            provider=provider,
            base_url=base_url,
            api_keys=api_keys,
            model=model,
            available_models=available_models,
            retry_count=self.retry_count_spin.value(),
            retry_interval=self.retry_interval_spin.value(),
        )

    def upsert_profile(self, profile: ApiProfile):
        current_name = self.config.active_profile_name
        for index, item in enumerate(self.config.api_profiles):
            if item.name == current_name:
                self.config.api_profiles[index] = profile
                self.config.active_profile_name = profile.name
                return
        for index, item in enumerate(self.config.api_profiles):
            if item.name == profile.name:
                self.config.api_profiles[index] = profile
                self.config.active_profile_name = profile.name
                return
        self.config.api_profiles.append(profile)
        self.config.active_profile_name = profile.name

    def create_new_profile(self):
        if not self.resolve_unsaved_changes():
            return
        profile = ApiProfile(name=self.next_profile_name())
        self.config.api_profiles.append(profile)
        self.load_profile_to_form(profile.name)
        self.set_unsaved_changes(True)
        self.log(f"Created new profile: {profile.name}")

    def delete_current_profile(self):
        if not self.resolve_unsaved_changes():
            return
        if len(self.config.api_profiles) <= 1:
            QMessageBox.warning(self, self.tr("error_title"), self.tr("at_least_one_profile"))
            return
        name = self.config.active_profile_name
        if QMessageBox.question(self, self.tr("error_title"), self.tr("confirm_delete_profile", name=name)) != QMessageBox.Yes:
            return
        self.config.api_profiles = [profile for profile in self.config.api_profiles if profile.name != name]
        self.config.active_profile_name = self.config.api_profiles[0].name
        self.load_profile_to_form(self.config.active_profile_name)
        self.set_unsaved_changes(True)
        self.set_status("profile_deleted", name=name)
        self.log(f"Deleted profile (pending save): {name}")

    def sync_form_to_config(self) -> tuple[str, ApiProfile]:
        valid, first_error = self.validate_form_inputs(focus_first_invalid=True)
        if not valid:
            raise ValueError(first_error)
        previous_language = self.config.ui_language
        profile = self.build_profile_from_form()
        self.upsert_profile(profile)
        self.config.target_language = self.target_language_edit.text().strip() or "繁體中文"
        self.config.ui_language = self.ui_language_combo.currentText().strip() or "zh-TW"
        self.config.hotkey = self.hotkey_edit.text().strip() or "Shift+Win+A"
        self.config.overlay_font_family = self.overlay_font_combo.currentFont().family()
        self.config.temperature = self.temperature_spin.value()
        self.config.overlay_font_size = self.overlay_font_size_spin.value()
        self.config.overlay_width = self.overlay_width_spin.value()
        self.config.overlay_height = self.overlay_height_spin.value()
        self.config.margin = self.overlay_margin_spin.value()
        self.config.mode = self.mode_combo.currentData() or "book_lr"
        self.translation_overlay.apply_typography()
        if hasattr(self, "refresh_shell_state"):
            self.refresh_shell_state()
        return previous_language, profile

    def save_settings(self):
        try:
            valid, _ = self.validate_form_inputs(focus_first_invalid=True)
            if not valid:
                self.set_status("validation_failed")
                return False
            previous_language, profile = self.sync_form_to_config()
            if hasattr(self, "config_save_timer") and self.config_save_timer.isActive():
                self.config_save_timer.stop()
            save_config(self.config)
            self.apply_language()
            self.load_profile_to_form(self.config.active_profile_name)
            if self.config.hotkey != self.registered_hotkey:
                self.setup_hotkey_listener()
            self.set_status("language_saved" if self.config.ui_language != previous_language else "settings_saved")
            self.log(f"Saved profile: {profile.name} | provider={profile.provider} | base_url={profile.base_url}")
            return True
        except Exception as exc:  # noqa: BLE001
            self.handle_error(exc)
            return False

    def on_ui_language_changed(self, value: str):
        if value not in I18N:
            return
        if self.is_form_tracking_suppressed():
            return
        self.apply_language()
        self.on_form_input_changed()
