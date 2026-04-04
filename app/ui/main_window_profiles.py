import copy

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMessageBox

from ..config_store import load_config, save_config
from ..app_defaults import DEFAULT_THEME_MODE, PROVIDER_LABELS, normalize_theme_mode
from ..hotkey_utils import hotkey_has_modifier as hotkey_has_modifier_rule
from ..i18n import I18N
from ..models import ApiProfile, AppConfig
from .message_boxes import (
    MessageBoxAction,
    show_critical_message,
    show_custom_message_box,
    show_destructive_confirmation,
    show_warning_message,
)
from ..profile_utils import (
    default_base_url_for_provider,
    default_model_for_provider,
    display_model_value,
    normalize_model_value,
    normalize_provider_name,
    unique_non_empty,
)
from ..settings_models import SettingsFormSnapshot
from ..settings_service import build_candidate_config, build_profile_from_snapshot, validate_profile_name as validate_profile_name_rule, validate_settings_snapshot


class MainWindowProfilesMixin:
    FIELD_WIDGET_MAP = {
        "profile_name": "profile_name_edit",
        "base_url": "base_url_edit",
        "model": "model_combo",
        "api_keys": "api_keys_edit",
        "prompt_preset_name": "prompt_preset_name_edit",
        "image_prompt": "image_prompt_edit",
        "text_prompt": "text_prompt_edit",
        "target_language": "target_language_edit",
        "capture": "hotkey_edit",
        "selection": "selection_hotkey_edit",
        "input": "input_hotkey_edit",
    }

    def provider_display(self, provider: str) -> str:
        return PROVIDER_LABELS.get(provider, {}).get(self.current_ui_language(), provider)

    def is_form_tracking_suppressed(self) -> bool:
        return bool(getattr(self, "_suppress_form_tracking", False))

    def set_unsaved_changes(self, dirty: bool):
        self.has_unsaved_changes = bool(dirty)
        self.setWindowModified(self.has_unsaved_changes)
        if hasattr(self, "refresh_save_button_emphasis"):
            self.refresh_save_button_emphasis()
        if hasattr(self, "update_action_states"):
            self.update_action_states()

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
        self.load_prompt_preset_to_form(self.config.active_prompt_preset_name)

    def prompt_unsaved_changes(self) -> QMessageBox.StandardButton:
        return show_custom_message_box(
            self,
            self.tr("unsaved_changes_title"),
            self.tr("unsaved_changes_message"),
            icon=QMessageBox.Warning,
            actions=[
                MessageBoxAction(self.tr("unsaved_changes_save"), QMessageBox.AcceptRole, QMessageBox.Save, variant="primary", is_default=True),
                MessageBoxAction(self.tr("unsaved_changes_discard"), QMessageBox.DestructiveRole, QMessageBox.Discard, variant="danger"),
                MessageBoxAction(self.tr("unsaved_changes_cancel"), QMessageBox.RejectRole, QMessageBox.Cancel, variant="neutral", is_escape=True),
            ],
            preserve_initial_focus=False,
            escape_result=QMessageBox.Cancel,
        )

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

    def update_theme_mode_options(self, current: str | None = None):
        current_value = normalize_theme_mode(current or self.current_theme_mode() or getattr(self.config, "theme_mode", DEFAULT_THEME_MODE))
        symbols = {
            "system": "◐",
            "light": "☀",
            "dark": "☾",
        }
        tooltips = {
            "system": self.tr("theme_system"),
            "light": self.tr("theme_light"),
            "dark": self.tr("theme_dark"),
        }
        if hasattr(self, "theme_mode_switch"):
            self.theme_mode_switch.setToolTip(self.tr("theme_mode"))
            self.theme_mode_switch.setAccessibleName(self.tr("theme_mode"))
        if hasattr(self, "theme_mode_buttons"):
            for mode, button in self.theme_mode_buttons.items():
                button.blockSignals(True)
                button.setText(symbols[mode])
                button.setToolTip(tooltips[mode])
                button.setAccessibleName(tooltips[mode])
                button.setChecked(mode == current_value)
                button.blockSignals(False)
            return

        if hasattr(self, "theme_mode_combo"):
            self.theme_mode_combo.blockSignals(True)
            self.theme_mode_combo.clear()
            self.theme_mode_combo.addItem(self.tr("theme_system"), "system")
            self.theme_mode_combo.addItem(self.tr("theme_light"), "light")
            self.theme_mode_combo.addItem(self.tr("theme_dark"), "dark")
            index = self.theme_mode_combo.findData(current_value)
            self.theme_mode_combo.setCurrentIndex(max(0, index))
            self.theme_mode_combo.blockSignals(False)

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

    def hotkey_fields(self) -> dict[str, tuple]:
        fields = {}
        if hasattr(self, "hotkey_edit") and hasattr(self, "hotkey_record_button"):
            fields["capture"] = (self.hotkey_edit, self.hotkey_record_button)
        if hasattr(self, "selection_hotkey_edit") and hasattr(self, "selection_hotkey_record_button"):
            fields["selection"] = (self.selection_hotkey_edit, self.selection_hotkey_record_button)
        if hasattr(self, "input_hotkey_edit") and hasattr(self, "input_hotkey_record_button"):
            fields["input"] = (self.input_hotkey_edit, self.input_hotkey_record_button)
        return fields

    def hotkey_field_key_for_widget(self, widget) -> str | None:
        for key, (edit, _) in self.hotkey_fields().items():
            if widget is edit:
                return key
        return None

    def hotkey_inputs(self) -> dict[str, object]:
        fields = self.hotkey_fields()
        return {key: edit for key, (edit, _) in fields.items()}

    def hotkey_value_map(self) -> dict[str, str]:
        values = {}
        for key, edit in self.hotkey_inputs().items():
            values[key] = edit.text().strip()
        return values

    def capture_settings_snapshot(self) -> SettingsFormSnapshot:
        current_profile = self.get_active_profile()
        current_prompt_preset = self.get_active_prompt_preset()
        return SettingsFormSnapshot(
            profile_name=self.profile_name_edit.text().strip(),
            provider=normalize_provider_name(self.provider_combo.currentData() or current_profile.provider),
            base_url=self.base_url_edit.text().strip(),
            model_text=self.model_combo.currentText().strip(),
            model_items=[self.model_combo.itemText(index) for index in range(self.model_combo.count())],
            api_keys_text=self.get_api_keys_text(),
            retry_count=self.retry_count_spin.value(),
            retry_interval=self.retry_interval_spin.value(),
            target_language=self.target_language_edit.text().strip(),
            ui_language=self.ui_language_combo.currentText().strip(),
            theme_mode=self.current_theme_mode(),
            hotkey=self.hotkey_edit.text().strip(),
            selection_hotkey=self.selection_hotkey_edit.text().strip(),
            input_hotkey=self.input_hotkey_edit.text().strip(),
            overlay_font_family=self.overlay_font_combo.currentFont().family(),
            overlay_font_size=self.overlay_font_size_spin.value(),
            temperature=self.temperature_spin.value(),
            overlay_width=self.overlay_width_spin.value(),
            overlay_height=self.overlay_height_spin.value(),
            overlay_margin=self.overlay_margin_spin.value(),
            overlay_auto_expand_top_margin=self.overlay_auto_expand_top_margin_spin.value(),
            overlay_auto_expand_bottom_margin=self.overlay_auto_expand_bottom_margin_spin.value(),
            close_to_tray_on_close=self.close_to_tray_on_close_checkbox.isChecked(),
            mode=self.mode_combo.currentData() or self.config.mode,
            prompt_preset_name=self.prompt_preset_name_edit.text().strip() or current_prompt_preset.name,
            image_prompt=self.image_prompt_edit.toPlainText(),
            text_prompt=self.text_prompt_edit.toPlainText(),
            active_record_target=getattr(self, "hotkey_record_target", None),
        )

    def widget_for_field_key(self, field_key: str):
        widget_name = self.FIELD_WIDGET_MAP.get(field_key)
        return getattr(self, widget_name, None) if widget_name else None

    def hotkey_field_label(self, field_key: str) -> str:
        label_map = {
            "capture": self.tr("capture_hotkey"),
            "selection": self.tr("selection_hotkey"),
            "input": self.tr("input_hotkey"),
        }
        return label_map.get(field_key, self.tr("hotkey"))

    def hotkey_has_modifier(self, hotkey_text: str) -> bool:
        return hotkey_has_modifier_rule(hotkey_text)

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

    def validate_form_inputs(self, *, focus_first_invalid: bool = False, scope: str = "save") -> tuple[bool, str]:
        tracked_widgets = [
            self.profile_name_edit,
            self.base_url_edit,
            self.model_combo,
            self.api_keys_edit,
            self.prompt_preset_name_edit,
            self.image_prompt_edit,
            self.text_prompt_edit,
            self.target_language_edit,
            self.hotkey_edit,
            self.selection_hotkey_edit,
            self.input_hotkey_edit,
        ]
        for widget in tracked_widgets:
            self.set_widget_invalid(widget, False)
        snapshot = self.capture_settings_snapshot()
        validation = validate_settings_snapshot(
            snapshot,
            existing_profile_names={profile.name for profile in self.config.api_profiles},
            current_profile_name=self.get_active_profile().name,
            existing_prompt_preset_names={preset.name for preset in self.config.prompt_presets},
            current_prompt_preset_name=self.get_active_prompt_preset().name,
            normalize_hotkey=self.normalize_hotkey,
            hotkey_has_modifier=self.hotkey_has_modifier,
            tr=self.tr,
            scope=scope,
        )
        invalid_widgets = []
        for field_key in validation.field_keys():
            widget = self.widget_for_field_key(field_key)
            if widget is None:
                continue
            self.set_widget_invalid(widget, True)
            if widget not in invalid_widgets:
                invalid_widgets.append(widget)

        self.set_validation_message(self.api_validation_label, validation.messages_for_category("api"))
        self.set_validation_message(self.prompt_validation_label, validation.messages_for_category("prompt"))
        self.set_validation_message(self.reading_validation_label, validation.messages_for_category("reading"))

        if focus_first_invalid and invalid_widgets:
            invalid_widgets[0].setFocus()
        return validation.is_valid, validation.first_error

    def start_hotkey_recording(self, field_key: str = "capture"):
        if getattr(self, "hotkey_record_target", None) == field_key:
            self.stop_hotkey_recording(cancelled=True)
            return
        self.stop_hotkey_recording(cancelled=False)
        field = self.hotkey_fields().get(field_key)
        if not field:
            return
        self.hotkey_record_target = field_key
        edit, button = field
        edit.setFocus()
        edit.selectAll()
        edit.setReadOnly(True)
        button.setText(self.tr("recording_hotkey"))
        if getattr(self, "hotkey_listener", None):
            self.hotkey_listener.stop()
            self.hotkey_listener = None
            self.hotkey_listener_paused_for_recording = True
        self._start_global_hotkey_recorder(field_key)
        self.set_status("hotkey_recording")
        self.validate_form_inputs()

    def stop_hotkey_recording(self, *, cancelled: bool = False):
        field_key = getattr(self, "hotkey_record_target", None)
        listener = getattr(self, "hotkey_record_listener", None)
        if listener:
            try:
                listener.stop()
            except Exception:  # noqa: BLE001
                pass
            self.hotkey_record_listener = None
        if not field_key:
            if getattr(self, "hotkey_listener_paused_for_recording", False):
                self.hotkey_listener_paused_for_recording = False
                self.setup_hotkey_listener(initial=True)
            return
        self.hotkey_record_target = None
        field = self.hotkey_fields().get(field_key)
        if field:
            _, button = field
            field[0].setReadOnly(False)
            button.setText(self.tr("record_hotkey"))
        if getattr(self, "hotkey_listener_paused_for_recording", False):
            self.hotkey_listener_paused_for_recording = False
            self.setup_hotkey_listener(initial=True)
        self.validate_form_inputs()
        if cancelled:
            self.set_status("hotkey_record_cancelled")

    @staticmethod
    def _normalize_recorded_key_token(key) -> str:
        from pynput import keyboard

        if key in {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}:
            return "Ctrl"
        if key in {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr}:
            return "Alt"
        if key in {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r}:
            return "Shift"
        if key in {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r}:
            return "Win"

        special_keys = {
            keyboard.Key.enter: "Enter",
            keyboard.Key.tab: "Tab",
            keyboard.Key.space: "Space",
            keyboard.Key.backspace: "Backspace",
            keyboard.Key.delete: "Delete",
            keyboard.Key.insert: "Insert",
            keyboard.Key.home: "Home",
            keyboard.Key.end: "End",
            keyboard.Key.page_up: "PageUp",
            keyboard.Key.page_down: "PageDown",
            keyboard.Key.left: "Left",
            keyboard.Key.right: "Right",
            keyboard.Key.up: "Up",
            keyboard.Key.down: "Down",
            keyboard.Key.esc: "Esc",
        }
        if key in special_keys:
            return special_keys[key]

        if isinstance(key, keyboard.KeyCode):
            char = (key.char or "").strip()
            if char:
                return char.upper()
        name = getattr(key, "name", "") or ""
        if name.startswith("f") and name[1:].isdigit():
            return name.upper()
        if len(name) == 1 and name.isalnum():
            return name.upper()
        return ""

    @staticmethod
    def _format_recorded_hotkey(modifiers: set[str], key_token: str) -> str:
        ordered_modifiers = [token for token in ("Ctrl", "Alt", "Shift", "Win") if token in modifiers]
        parts = ordered_modifiers.copy()
        if key_token and key_token not in parts:
            parts.append(key_token)
        return "+".join(parts)

    def _start_global_hotkey_recorder(self, field_key: str):
        from pynput import keyboard

        modifier_tokens = {"Ctrl", "Alt", "Shift", "Win"}
        pressed_modifiers: set[str] = set()
        pressed_modifier_order: list[str] = []
        recorded = False

        def on_press(key):
            nonlocal recorded
            token = self._normalize_recorded_key_token(key)
            if not token:
                return
            if token == "Esc":
                recorded = True
                self.bridge.hotkey_recorded.emit(field_key, "")
                return False
            if token in modifier_tokens:
                pressed_modifiers.add(token)
                if token not in pressed_modifier_order:
                    pressed_modifier_order.append(token)
                return
            ordered_modifiers = [token for token in pressed_modifier_order if token in pressed_modifiers]
            hotkey_text = self._format_recorded_hotkey(set(ordered_modifiers), token)
            if hotkey_text:
                recorded = True
                self.bridge.hotkey_recorded.emit(field_key, hotkey_text)
                return False

        def on_release(key):
            nonlocal recorded
            token = self._normalize_recorded_key_token(key)
            if token in modifier_tokens:
                pressed_modifiers.discard(token)
            if recorded:
                return False

        self.hotkey_record_listener = keyboard.Listener(on_press=on_press, on_release=on_release, suppress=True)
        self.hotkey_record_listener.start()

    def handle_recorded_hotkey(self, field_key: str, hotkey_text: str):
        if getattr(self, "hotkey_record_target", None) != field_key:
            return
        if not hotkey_text:
            self.stop_hotkey_recording(cancelled=True)
            return
        field = self.hotkey_fields().get(field_key)
        if not field:
            self.stop_hotkey_recording(cancelled=True)
            return
        widget, _ = field
        widget.setText(hotkey_text)
        self.stop_hotkey_recording(cancelled=False)
        self.validate_form_inputs()
        self.set_status("hotkey_recorded", hotkey=hotkey_text)

    def eventFilter(self, watched, event):
        field_key = self.hotkey_field_key_for_widget(watched)
        if field_key and getattr(self, "hotkey_record_target", None) == field_key:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self.stop_hotkey_recording(cancelled=True)
                    return True
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
            self.update_theme_mode_options(getattr(self.config, "theme_mode", DEFAULT_THEME_MODE))
            self.hotkey_edit.setText(self.config.hotkey)
            self.selection_hotkey_edit.setText(self.config.selection_hotkey)
            self.input_hotkey_edit.setText(self.config.input_hotkey)
            self.overlay_font_combo.setCurrentFont(QFont(self.config.overlay_font_family))
            self.temperature_spin.setValue(self.config.temperature)
            self.overlay_font_size_spin.setValue(self.config.overlay_font_size)
            self.overlay_width_spin.setValue(self.config.overlay_width)
            self.overlay_height_spin.setValue(self.config.overlay_height)
            self.overlay_margin_spin.setValue(self.config.margin)
            self.overlay_auto_expand_top_margin_spin.setValue(int(getattr(self.config, "overlay_auto_expand_top_margin", 42)))
            self.overlay_auto_expand_bottom_margin_spin.setValue(int(getattr(self.config, "overlay_auto_expand_bottom_margin", 24)))
            self.close_to_tray_on_close_checkbox.setChecked(bool(getattr(self.config, "close_to_tray_on_close", False)))
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
        try:
            return validate_profile_name_rule(
                name,
                {profile.name for profile in self.config.api_profiles},
                current_name,
                fallback_name=self.tr("untitled_profile"),
            )
        except ValueError as exc:
            raise ValueError(self.tr("profile_name_exists", name=str(exc))) from exc

    def build_profile_from_form(self, *, validate_name: bool = True) -> ApiProfile:
        snapshot = self.capture_settings_snapshot()
        current_profile = self.get_active_profile()
        profile = build_profile_from_snapshot(snapshot, current_profile=current_profile)
        if validate_name:
            profile.name = self.validate_profile_name(profile.name, current_profile.name)
        return profile


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
            show_warning_message(self, self.tr("warning_title"), self.tr("at_least_one_profile"))
            return
        name = self.config.active_profile_name
        if not show_destructive_confirmation(
            self,
            self.tr("confirm_title"),
            self.tr("confirm_delete_profile", name=name),
            confirm_text=self.tr("delete_profile"),
            cancel_text=self.tr("unsaved_changes_cancel"),
        ):
            return
        self.config.api_profiles = [profile for profile in self.config.api_profiles if profile.name != name]
        self.config.active_profile_name = self.config.api_profiles[0].name
        self.load_profile_to_form(self.config.active_profile_name)
        self.set_unsaved_changes(True)
        self.set_status("profile_deleted", name=name)
        self.log(f"Deleted profile (pending save): {name}")

    def sync_form_to_config(self) -> tuple[str, AppConfig, ApiProfile]:
        valid, first_error = self.validate_form_inputs(focus_first_invalid=True, scope="save")
        if not valid:
            raise ValueError(first_error)
        snapshot = self.capture_settings_snapshot()
        previous_language, candidate_config, profile, _ = build_candidate_config(
            self.config,
            snapshot,
            current_profile=self.get_active_profile(),
            current_prompt_preset=self.get_active_prompt_preset(),
        )
        profile.name = self.validate_profile_name(profile.name, self.get_active_profile().name)
        return previous_language, candidate_config, profile

    def auto_save_theme_mode(self) -> bool:
        previous_mode = normalize_theme_mode(getattr(self.config, "theme_mode", DEFAULT_THEME_MODE))
        selected_mode = self.current_theme_mode()
        if selected_mode == previous_mode:
            return True
        keep_dirty = bool(getattr(self, "has_unsaved_changes", False))
        try:
            self.config.theme_mode = selected_mode
            save_config(self.config)
            self.set_status("settings_saved")
            self.log(f"Theme mode auto-saved: {selected_mode}")
            self.set_unsaved_changes(keep_dirty)
            return True
        except Exception as exc:  # noqa: BLE001
            self.config.theme_mode = previous_mode
            self._suppress_form_tracking = True
            try:
                self.update_theme_mode_options(previous_mode)
            finally:
                self._suppress_form_tracking = False
            self.handle_error(exc)
            return False

    def save_settings(self):
        try:
            valid, _ = self.validate_form_inputs(focus_first_invalid=True, scope="save")
            if not valid:
                self.set_status("validation_failed")
                return False
            previous_runtime_config = copy.deepcopy(self.config)
            previous_language, candidate_config, profile = self.sync_form_to_config()
            try:
                self.setup_hotkey_listener(initial=True, config=candidate_config, raise_on_error=True)
            except Exception as exc:  # noqa: BLE001
                self.config = previous_runtime_config
                try:
                    self.setup_hotkey_listener(initial=True, config=previous_runtime_config, raise_on_error=True)
                except Exception as restore_exc:  # noqa: BLE001
                    self.log(f"Failed to restore previous hotkeys after save abort: {restore_exc}")
                self.set_status("hotkey_register_failed", error=exc)
                self.log(f"Settings not saved because hotkey registration failed: {exc}")
                show_critical_message(self, self.tr("error_title"), self.tr("save_settings_aborted_hotkeys", error=exc))
                return False

            self.config = candidate_config
            save_config(self.config)
            self.apply_language()
            self.load_profile_to_form(self.config.active_profile_name)
            self.load_prompt_preset_to_form(self.config.active_prompt_preset_name)
            self.set_status("language_saved" if self.config.ui_language != previous_language else "settings_saved")
            self.log(f"Saved profile: {profile.name} | provider={profile.provider} | base_url={profile.base_url}")
            return True
        except Exception as exc:  # noqa: BLE001
            try:
                restored_config = copy.deepcopy(locals().get("previous_runtime_config", self.config))
                self.config = restored_config
                self.setup_hotkey_listener(initial=True, config=restored_config, raise_on_error=True)
            except Exception as restore_exc:  # noqa: BLE001
                self.log(f"Failed to restore runtime state after save error: {restore_exc}")
            self.handle_error(exc)
            return False

    def on_ui_language_changed(self, value: str):
        if value not in I18N:
            return
        if self.is_form_tracking_suppressed():
            return
        self.apply_language()
        self.on_form_input_changed()

    def on_theme_mode_changed(self, _value: str):
        if self.is_form_tracking_suppressed():
            return
        self.apply_language()
        if not self.auto_save_theme_mode():
            self.apply_language()
