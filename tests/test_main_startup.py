import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.main import request_application_shutdown, request_existing_instance_action, schedule_initial_window_action
from app.models import AppConfig
from app.services.startup_timing import StartupTimingTracker
from app.ui.main_window import MainWindow


class _FakeSelectionOverlay(QObject):
    selected = Signal(object)
    cancelled = Signal()

    def apply_theme(self):
        return None

    def set_hint_text(self, _text):
        return None


class _FakeInstanceServerService:
    def __init__(self, *_args, **_kwargs):
        self.setup_called = False

    def setup(self):
        self.setup_called = True

    def close(self):
        return None


class _FakeTrayService:
    def __init__(self, *_args, **_kwargs):
        self.icon = None

    def apply_styles(self):
        return None

    def setup(self):
        return None

    def update_texts(self):
        return None


class _FakeToastWidget:
    def apply_styles(self):
        return None


class _FakeToastService:
    def __init__(self, *_args, **_kwargs):
        self.widget = _FakeToastWidget()

    def reposition(self):
        return None

    def show_message(self, *_args, **_kwargs):
        return True

    def hide_message(self):
        return None


class _FakeUpdateCheckService:
    def __init__(self, *_args, **_kwargs):
        return None


class _FakeSocket:
    def __init__(self, *, connected=True, bytes_written=True, ready_read=True, reply=b"ok\n"):
        self.connected = connected
        self.bytes_written = bytes_written
        self.ready_read = ready_read
        self.reply = reply
        self.written = []
        self.disconnected = False
        self.server_name = None

    def connectToServer(self, server_name):
        self.server_name = server_name

    def waitForConnected(self, _timeout):
        return self.connected

    def write(self, payload):
        self.written.append(payload)

    def flush(self):
        return True

    def waitForBytesWritten(self, _timeout):
        return self.bytes_written

    def waitForReadyRead(self, _timeout):
        return self.ready_read

    def readAll(self):
        return self.reply

    def disconnectFromServer(self):
        self.disconnected = True


class MainStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_request_existing_instance_action_requires_ok_reply(self):
        fake_socket = _FakeSocket(reply=b"ok\n")

        with patch("app.main.QLocalSocket", return_value=fake_socket):
            self.assertTrue(request_existing_instance_action("show"))

        self.assertEqual(fake_socket.written, [b"show\n"])
        self.assertTrue(fake_socket.disconnected)

    def test_request_existing_instance_action_returns_false_when_ack_missing(self):
        fake_socket = _FakeSocket(reply=b"unknown\n")

        with patch("app.main.QLocalSocket", return_value=fake_socket):
            self.assertFalse(request_existing_instance_action("capture"))

        self.assertEqual(fake_socket.written, [b"capture\n"])
        self.assertTrue(fake_socket.disconnected)

    @patch("app.main.QTimer.singleShot")
    def test_schedule_initial_window_action_reactivates_main_window_on_normal_start(self, mock_single_shot):
        window = Mock()

        schedule_initial_window_action(window, pending_capture=False)

        window.show.assert_called_once_with()
        mock_single_shot.assert_called_once_with(0, window.show_main_window)

    @patch("app.main.QTimer.singleShot")
    def test_schedule_initial_window_action_starts_capture_on_capture_launch(self, mock_single_shot):
        window = Mock()

        schedule_initial_window_action(window, pending_capture=True)

        window.show.assert_not_called()
        mock_single_shot.assert_called_once_with(0, window.start_selection_from_launch)

    @patch("app.main.create_ui_application")
    @patch("app.main.request_existing_instance_action", return_value=True)
    @patch("app.main.acquire_single_instance_lock", return_value=None)
    @patch("app.main.should_forward_capture_request", return_value=False)
    def test_run_app_skips_qapplication_creation_when_existing_instance_acknowledges_request(
        self,
        _mock_pending_capture,
        _mock_lock,
        _mock_forward,
        mock_create_ui_application,
    ):
        from app.main import run_app

        run_app()

        mock_create_ui_application.assert_not_called()

    def test_request_application_shutdown_prefers_main_window_emergency_shutdown(self):
        emergency_shutdown = Mock(return_value=True)
        app = Mock(main_window=Mock(emergency_shutdown=emergency_shutdown))

        self.assertTrue(request_application_shutdown(app))

        emergency_shutdown.assert_called_once_with()
        app.quit.assert_not_called()

    def test_request_application_shutdown_falls_back_to_app_quit_when_window_shutdown_is_missing(self):
        app = Mock(main_window=object())

        self.assertTrue(request_application_shutdown(app))

        app.quit.assert_called_once_with()

    def test_request_application_shutdown_falls_back_to_app_quit_when_window_shutdown_raises(self):
        app = Mock(main_window=Mock(emergency_shutdown=Mock(side_effect=RuntimeError("boom"))))

        self.assertTrue(request_application_shutdown(app))

        app.quit.assert_called_once_with()

    @patch.object(MainWindow, "setup_hotkey_listener", autospec=True, return_value=True)
    @patch("app.ui.main_window.UpdateCheckService", _FakeUpdateCheckService)
    @patch("app.ui.main_window.TransientToastService", _FakeToastService)
    @patch("app.ui.main_window.SystemTrayService", _FakeTrayService)
    @patch("app.ui.main_window.InstanceServerService", _FakeInstanceServerService)
    @patch("app.ui.main_window.SelectionOverlay", _FakeSelectionOverlay)
    @patch("app.ui.main_window.load_config", return_value=AppConfig())
    def test_main_window_startup_smoke_processes_early_events_without_crashing(
        self,
        _mock_load_config,
        _mock_setup_hotkeys,
    ):
        window = MainWindow(startup_timing=StartupTimingTracker(origin_name="startup-smoke"))
        try:
            window.show()
            self.app.processEvents()
            self.app.processEvents()

            self.assertTrue(hasattr(window, "api_keys_visible"))
            self.assertIsNotNone(window.api_keys_edit)
            self.assertFalse(window.is_quitting)
            self.assertTrue(window.instance_server_service.setup_called)
        finally:
            window.hide()
            window.deleteLater()
            self.app.processEvents()

    @patch.object(MainWindow, "setup_hotkey_listener", autospec=True, return_value=True)
    @patch("app.ui.main_window.UpdateCheckService", _FakeUpdateCheckService)
    @patch("app.ui.main_window.TransientToastService", _FakeToastService)
    @patch("app.ui.main_window.SystemTrayService", _FakeTrayService)
    @patch("app.ui.main_window.InstanceServerService", _FakeInstanceServerService)
    @patch("app.ui.main_window.SelectionOverlay", _FakeSelectionOverlay)
    @patch("app.ui.main_window.load_config", side_effect=AppConfig)
    def test_generation_controls_round_trip_and_switch_api_format(self, _load_config, _hotkeys):
        from app.settings_service import build_candidate_config

        window = MainWindow()
        try:
            self.assertFalse(window.render_markdown_checkbox.isChecked())
            self.assertFalse(window.temperature_spin.isEnabled())
            self.assertTrue(window.advanced_content.isAncestorOf(window.use_default_temperature_checkbox))
            self.assertIs(window.use_default_temperature_checkbox.parentWidget(), window.advanced_content)
            from PySide6.QtCore import Qt
            from PySide6.QtTest import QTest

            window.set_advanced_section_expanded(True)
            window.show()
            self.app.processEvents()
            with patch("app.ui.generation_controls.QToolTip.showText") as hint:
                QTest.mouseClick(window.temperature_spin, Qt.LeftButton)
                hint.assert_called_once()
                self.assertEqual(hint.call_args.args[1], window.tr("temperature_disabled_hint"))
            self.assertTrue(window.use_default_temperature_checkbox.isChecked())
            self.assertEqual(window.reasoning_effort_combo.findData("max"), -1)
            window.reasoning_effort_combo.setCurrentIndex(window.reasoning_effort_combo.findData("high"))
            window.use_default_temperature_checkbox.setChecked(False)
            window.render_markdown_checkbox.setChecked(True)
            self.assertTrue(window.temperature_spin.isEnabled())
            window.temperature_spin.setValue(0.7)
            window.use_default_temperature_checkbox.setChecked(True)
            self.assertFalse(window.temperature_spin.isEnabled())
            self.assertEqual(window.temperature_spin.value(), 0.7)
            window.use_default_temperature_checkbox.setChecked(False)
            self.assertTrue(window.temperature_spin.isEnabled())
            snapshot = window.capture_settings_snapshot()
            _, config, profile, _ = build_candidate_config(
                window.config, snapshot, current_profile=window.get_active_profile(), current_prompt_preset=window.get_active_prompt_preset()
            )
            self.assertTrue(config.render_markdown)
            self.assertEqual(profile.reasoning_effort, "high")
            self.assertFalse(profile.use_default_temperature)
            window.config = config
            window.load_profile_to_form(profile.name)
            self.assertTrue(window.render_markdown_checkbox.isChecked())
            self.assertEqual(window.reasoning_effort_combo.currentData(), "high")
            window.translation_in_progress = True
            window.update_action_states()
            window.load_profile_to_form(profile.name)
            self.assertFalse(window.temperature_spin.isEnabled())
            self.assertFalse(window.reasoning_effort_combo.isEnabled())
            self.assertFalse(window.use_default_temperature_checkbox.isEnabled())
            window.translation_in_progress = False
            window.update_action_states()
            self.assertTrue(window.temperature_spin.isEnabled())
            window.provider_combo.setCurrentIndex(window.provider_combo.findData("openai"))
            self.assertGreaterEqual(window.reasoning_effort_combo.findData("max"), 0)
            window.reasoning_effort_combo.setCurrentIndex(window.reasoning_effort_combo.findData("max"))
            self.assertEqual(window.build_profile_from_form(validate_name=False).reasoning_effort, "max")
            window.provider_combo.setCurrentIndex(window.provider_combo.findData("gemini"))
            self.assertEqual(window.reasoning_effort_combo.currentData(), "default")
        finally:
            window.hide()
            window.deleteLater()
            self.app.processEvents()

if __name__ == "__main__":
    unittest.main()
