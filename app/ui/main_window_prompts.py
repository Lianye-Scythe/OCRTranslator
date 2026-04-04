from .message_boxes import show_destructive_confirmation, show_information_message, show_warning_message
from ..models import PromptPreset, default_prompt_presets
from ..settings_service import build_prompt_preset_from_snapshot, validate_prompt_preset_name as validate_prompt_preset_name_rule


class MainWindowPromptPresetsMixin:
    def current_prompt_preset_name(self) -> str:
        if hasattr(self, "prompt_preset_name_edit"):
            value = self.prompt_preset_name_edit.text().strip()
            if value:
                return value
        if hasattr(self, "prompt_preset_combo"):
            value = self.prompt_preset_combo.currentText().strip()
            if value:
                return value
        return getattr(self.config, "active_prompt_preset_name", "")

    def refresh_prompt_preset_combo(self):
        self.ensure_prompt_preset_list()
        names = [preset.name for preset in self.config.prompt_presets]
        self.prompt_preset_combo.blockSignals(True)
        self.prompt_preset_combo.clear()
        self.prompt_preset_combo.addItems(names)
        idx = self.prompt_preset_combo.findText(self.config.active_prompt_preset_name)
        self.prompt_preset_combo.setCurrentIndex(max(0, idx))
        self.prompt_preset_combo.blockSignals(False)

    def find_prompt_preset_by_name(self, name: str) -> PromptPreset | None:
        for preset in getattr(self.config, "prompt_presets", []) or []:
            if preset.name == name:
                return preset
        return None

    def ensure_prompt_preset_list(self) -> list[PromptPreset]:
        presets = list(getattr(self.config, "prompt_presets", []) or [])
        if not presets:
            presets = default_prompt_presets()
            self.config.prompt_presets = presets
        if not getattr(self.config, "active_prompt_preset_name", ""):
            self.config.active_prompt_preset_name = presets[0].name
        return presets

    def get_prompt_preset_by_name(self, name: str) -> PromptPreset:
        presets = self.ensure_prompt_preset_list()
        return self.find_prompt_preset_by_name(name) or presets[0]

    def get_active_prompt_preset(self) -> PromptPreset:
        return self.get_prompt_preset_by_name(self.config.active_prompt_preset_name)

    def active_prompt_preset_is_builtin(self) -> bool:
        return bool(getattr(self.get_active_prompt_preset(), "builtin_id", ""))

    def refresh_prompt_preset_actions(self):
        if not hasattr(self, "delete_prompt_preset_button"):
            return
        if not getattr(self, "config", None) or not getattr(self.config, "prompt_presets", None):
            return
        deletable = not self.active_prompt_preset_is_builtin()
        busy = bool(getattr(self, "background_busy", lambda: False)())
        self.delete_prompt_preset_button.setEnabled(deletable and not busy)
        self.delete_prompt_preset_button.setToolTip(
            self.tr("builtin_prompt_preset_locked") if not deletable else self.tr("delete_prompt_preset")
        )

    def on_prompt_preset_selected(self, name: str):
        if not name:
            return
        if name == self.config.active_prompt_preset_name:
            return
        if not self.resolve_unsaved_changes():
            self.refresh_prompt_preset_combo()
            return
        self.load_prompt_preset_to_form(name)

    def next_prompt_preset_name(self) -> str:
        existing = {preset.name for preset in self.config.prompt_presets}
        index = 1
        while True:
            candidate = self.tr("prompt_preset_name_template", index=index)
            if candidate not in existing:
                return candidate
            index += 1

    def validate_prompt_preset_name(self, name: str, current_name: str | None = None) -> str:
        try:
            return validate_prompt_preset_name_rule(
                name,
                {preset.name for preset in self.config.prompt_presets},
                current_name,
                fallback_name=self.tr("untitled_prompt_preset"),
            )
        except ValueError as exc:
            raise ValueError(self.tr("prompt_preset_name_exists", name=str(exc))) from exc

    def load_prompt_preset_to_form(self, preset_name: str):
        self.ensure_prompt_preset_list()
        preset = self.get_prompt_preset_by_name(preset_name)
        self._suppress_form_tracking = True
        try:
            self.config.active_prompt_preset_name = preset.name
            self.refresh_prompt_preset_combo()
            self.prompt_preset_name_edit.setText(preset.name)
            self.image_prompt_edit.setPlainText(preset.image_prompt)
            self.text_prompt_edit.setPlainText(preset.text_prompt)
        finally:
            self._suppress_form_tracking = False
        self.apply_language()
        self.validate_form_inputs()
        self.set_unsaved_changes(False)
        self.refresh_prompt_preset_actions()
        if hasattr(self, "refresh_shell_state"):
            self.refresh_shell_state()

    def build_prompt_preset_from_form(self, *, validate_name: bool = True) -> PromptPreset:
        snapshot = self.capture_settings_snapshot()
        current_preset = self.get_active_prompt_preset()
        prompt_preset = build_prompt_preset_from_snapshot(snapshot, current_prompt_preset=current_preset)
        if validate_name:
            prompt_preset.name = self.validate_prompt_preset_name(prompt_preset.name, current_preset.name)
        return prompt_preset


    def create_new_prompt_preset(self):
        if not self.resolve_unsaved_changes():
            return
        source = self.get_active_prompt_preset()
        preset = PromptPreset(
            name=self.next_prompt_preset_name(),
            builtin_id="",
            image_prompt=source.image_prompt,
            text_prompt=source.text_prompt,
        )
        self.config.prompt_presets.append(preset)
        self.load_prompt_preset_to_form(preset.name)
        self.set_unsaved_changes(True)
        self.log(f"Created new prompt preset: {preset.name}")

    def delete_current_prompt_preset(self):
        if not self.resolve_unsaved_changes():
            return
        if self.active_prompt_preset_is_builtin():
            show_information_message(self, self.tr("warning_title"), self.tr("builtin_prompt_preset_locked"))
            return
        if len(self.config.prompt_presets) <= 1:
            show_warning_message(self, self.tr("warning_title"), self.tr("at_least_one_prompt_preset"))
            return
        name = self.config.active_prompt_preset_name
        if not show_destructive_confirmation(
            self,
            self.tr("confirm_title"),
            self.tr("confirm_delete_prompt_preset", name=name),
            confirm_text=self.tr("delete_prompt_preset"),
            cancel_text=self.tr("unsaved_changes_cancel"),
        ):
            return
        self.config.prompt_presets = [preset for preset in self.config.prompt_presets if preset.name != name]
        presets = self.ensure_prompt_preset_list()
        self.config.active_prompt_preset_name = presets[0].name
        self.load_prompt_preset_to_form(self.config.active_prompt_preset_name)
        self.set_unsaved_changes(True)
        self.set_status("prompt_preset_deleted", name=name)
        self.log(f"Deleted prompt preset (pending save): {name}")
