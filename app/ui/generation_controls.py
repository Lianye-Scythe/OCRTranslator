from PySide6.QtCore import QEvent, QObject, QSignalBlocker
from PySide6.QtWidgets import QToolTip

from ..models import ApiProfile
from ..profile_utils import reasoning_effort_values


class GenerationControls(QObject):
    """Own generation-control state without depending on the main window."""

    def __init__(self, *, reasoning_combo, default_temperature_checkbox, temperature_spin, temperature_field, translate):
        super().__init__(temperature_field)
        self.reasoning_combo = reasoning_combo
        self.default_temperature_checkbox = default_temperature_checkbox
        self.temperature_spin = temperature_spin
        self.temperature_field = temperature_field
        self.translate = translate
        self._busy = False
        default_temperature_checkbox.toggled.connect(self.refresh_enabled_state)
        for widget in (temperature_field, temperature_spin, temperature_spin.lineEdit()):
            widget.installEventFilter(self)
        self.refresh_enabled_state()

    def set_busy(self, busy: bool):
        self._busy = busy
        self.refresh_enabled_state()

    def refresh_enabled_state(self):
        self.reasoning_combo.setEnabled(not self._busy)
        self.default_temperature_checkbox.setEnabled(not self._busy)
        self.temperature_spin.setEnabled(not self._busy and not self.default_temperature_checkbox.isChecked())

    def update_reasoning_options(self, provider: str, value: str | None = None):
        selected = value if value is not None else (self.reasoning_combo.currentData() or "default")
        with QSignalBlocker(self.reasoning_combo):
            self.reasoning_combo.clear()
            for effort in reasoning_effort_values(provider):
                self.reasoning_combo.addItem(self.translate("reasoning_default") if effort == "default" else effort, effort)
            self.reasoning_combo.setCurrentIndex(max(0, self.reasoning_combo.findData(selected)))

    def load(self, profile: ApiProfile, temperature: float):
        self.update_reasoning_options(profile.provider, profile.reasoning_effort)
        self.default_temperature_checkbox.setChecked(profile.use_default_temperature)
        self.temperature_spin.setValue(temperature)
        self.refresh_enabled_state()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonPress and self.default_temperature_checkbox.isChecked():
            position = event.globalPosition().toPoint()
            if self.temperature_spin.rect().contains(self.temperature_spin.mapFromGlobal(position)):
                QToolTip.showText(position, self.translate("temperature_disabled_hint"), self.temperature_field)
                return True
        return super().eventFilter(watched, event)
