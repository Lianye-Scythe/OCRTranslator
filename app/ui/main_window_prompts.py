from PySide6.QtWidgets import QMessageBox

from ..models import PromptPreset


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
        names = [preset.name for preset in self.config.prompt_presets]
        self.prompt_preset_combo.blockSignals(True)
        self.prompt_preset_combo.clear()
        self.prompt_preset_combo.addItems(names)
        idx = self.prompt_preset_combo.findText(self.config.active_prompt_preset_name)
        self.prompt_preset_combo.setCurrentIndex(max(0, idx))
        self.prompt_preset_combo.blockSignals(False)

    def find_prompt_preset_by_name(self, name: str) -> PromptPreset | None:
        for preset in self.config.prompt_presets:
            if preset.name == name:
                return preset
        return None

    def get_prompt_preset_by_name(self, name: str) -> PromptPreset:
        return self.find_prompt_preset_by_name(name) or self.config.prompt_presets[0]

    def get_active_prompt_preset(self) -> PromptPreset:
        return self.get_prompt_preset_by_name(self.config.active_prompt_preset_name)

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
        normalized = name.strip() or self.tr("untitled_prompt_preset")
        if normalized in {preset.name for preset in self.config.prompt_presets if preset.name != current_name}:
            raise ValueError(self.tr("prompt_preset_name_exists", name=normalized))
        return normalized

    def load_prompt_preset_to_form(self, preset_name: str):
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
        if hasattr(self, "refresh_shell_state"):
            self.refresh_shell_state()

    def build_prompt_preset_from_form(self) -> PromptPreset:
        current_preset = self.get_active_prompt_preset()
        name = self.validate_prompt_preset_name(self.prompt_preset_name_edit.text(), current_preset.name)
        image_prompt = self.image_prompt_edit.toPlainText().strip() or current_preset.image_prompt.strip()
        text_prompt = self.text_prompt_edit.toPlainText().strip() or current_preset.text_prompt.strip()
        return PromptPreset(
            name=name,
            builtin_id=getattr(current_preset, "builtin_id", ""),
            image_prompt=image_prompt,
            text_prompt=text_prompt,
        )

    def upsert_prompt_preset(self, preset: PromptPreset):
        current_name = self.config.active_prompt_preset_name
        for index, item in enumerate(self.config.prompt_presets):
            if item.name == current_name:
                self.config.prompt_presets[index] = preset
                self.config.active_prompt_preset_name = preset.name
                return
        for index, item in enumerate(self.config.prompt_presets):
            if item.name == preset.name:
                self.config.prompt_presets[index] = preset
                self.config.active_prompt_preset_name = preset.name
                return
        self.config.prompt_presets.append(preset)
        self.config.active_prompt_preset_name = preset.name

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
        if len(self.config.prompt_presets) <= 1:
            QMessageBox.warning(self, self.tr("error_title"), self.tr("at_least_one_prompt_preset"))
            return
        name = self.config.active_prompt_preset_name
        if QMessageBox.question(self, self.tr("error_title"), self.tr("confirm_delete_prompt_preset", name=name)) != QMessageBox.Yes:
            return
        self.config.prompt_presets = [preset for preset in self.config.prompt_presets if preset.name != name]
        self.config.active_prompt_preset_name = self.config.prompt_presets[0].name
        self.load_prompt_preset_to_form(self.config.active_prompt_preset_name)
        self.set_unsaved_changes(True)
        self.set_status("prompt_preset_deleted", name=name)
        self.log(f"Deleted prompt preset (pending save): {name}")
