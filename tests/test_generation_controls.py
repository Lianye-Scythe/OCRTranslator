import unittest
from unittest.mock import patch

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QVBoxLayout, QWidget

from app.models import ApiProfile
from app.ui.generation_controls import GenerationControls


class GenerationControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.field = QWidget()
        self.reasoning = QComboBox(self.field)
        self.default_temperature = QCheckBox(self.field)
        self.default_temperature.setChecked(True)
        self.temperature = QDoubleSpinBox(self.field)
        layout = QVBoxLayout(self.field)
        for widget in (self.reasoning, self.default_temperature, self.temperature):
            layout.addWidget(widget)
        self.controls = GenerationControls(
            reasoning_combo=self.reasoning,
            default_temperature_checkbox=self.default_temperature,
            temperature_spin=self.temperature,
            temperature_field=self.field,
            translate=lambda key: key,
        )

    def tearDown(self):
        self.field.hide()
        self.field.deleteLater()
        self.app.processEvents()

    def test_temperature_editability_respects_busy_and_default_flags(self):
        self.assertFalse(self.temperature.isEnabled())
        self.default_temperature.setChecked(False)
        self.assertTrue(self.temperature.isEnabled())
        self.controls.set_busy(True)
        self.default_temperature.setChecked(True)
        self.default_temperature.setChecked(False)
        for widget in (self.temperature, self.reasoning, self.default_temperature):
            self.assertFalse(widget.isEnabled())
        self.controls.set_busy(False)
        self.assertTrue(self.temperature.isEnabled())
        self.default_temperature.setChecked(True)
        self.controls.set_busy(True)
        self.controls.set_busy(False)
        self.assertFalse(self.temperature.isEnabled())

    def test_profile_load_during_busy_keeps_controls_disabled_and_value(self):
        self.controls.set_busy(True)
        self.controls.load(ApiProfile(reasoning_effort="high", use_default_temperature=False), 0.7)
        self.assertEqual(self.reasoning.currentData(), "high")
        self.assertEqual(self.temperature.value(), 0.7)
        self.assertFalse(self.temperature.isEnabled())
        self.assertFalse(self.reasoning.isEnabled())
        self.assertFalse(self.default_temperature.isEnabled())
        self.controls.set_busy(False)
        self.assertTrue(self.temperature.isEnabled())

    def test_provider_switch_preserves_supported_effort_and_resets_unsupported(self):
        self.controls.update_reasoning_options("openai", "high")
        self.controls.update_reasoning_options("gemini")
        self.assertEqual(self.reasoning.currentData(), "high")
        self.controls.update_reasoning_options("openai", "max")
        self.controls.update_reasoning_options("gemini")
        self.assertEqual(self.reasoning.currentData(), "default")

    def test_refresh_preserves_existing_signal_block(self):
        with QSignalBlocker(self.reasoning):
            self.controls.update_reasoning_options("gemini", "low")
            self.assertTrue(self.reasoning.signalsBlocked())
        self.assertFalse(self.reasoning.signalsBlocked())

    def test_click_hint_only_for_model_default_and_never_changes_value(self):
        self.temperature.setValue(0.7)
        self.field.show()
        self.app.processEvents()
        with patch("app.ui.generation_controls.QToolTip.showText") as hint:
            QTest.mouseClick(self.temperature, Qt.LeftButton)
            hint.assert_called_once()
            self.assertEqual(hint.call_args.args[1], "temperature_disabled_hint")
            self.assertEqual(self.temperature.value(), 0.7)
            self.assertTrue(self.default_temperature.isChecked())
            self.default_temperature.setChecked(False)
            hint.reset_mock()
            QTest.mouseClick(self.temperature, Qt.LeftButton)
            hint.assert_not_called()
