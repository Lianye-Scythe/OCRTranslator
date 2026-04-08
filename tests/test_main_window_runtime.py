from types import SimpleNamespace
import time
import unittest
import sys
import types
from unittest.mock import Mock, call, patch


if "pynput" not in sys.modules:
    pynput_stub = types.ModuleType("pynput")
    pynput_stub.keyboard = types.SimpleNamespace(Listener=object)
    sys.modules["pynput"] = pynput_stub

from app.ui.main_window import MainWindow
from app.operation_control import RequestCancelledError


class _ValueWidget:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class _FakeWidget:
    def __init__(self):
        self.enabled = True
        self.text = None
        self.tooltip = None

    def setEnabled(self, value):
        self.enabled = bool(value)

    def setText(self, value):
        self.text = value

    def setToolTip(self, value):
        self.tooltip = value


class MainWindowRuntimeTests(unittest.TestCase):
    @patch("app.ui.main_window.SelectionOverlay")
    def test_recreate_selection_overlay_replaces_old_widget_and_syncs_new_one(self, mock_selection_overlay_cls):
        old_overlay = SimpleNamespace(hide=Mock(), close=Mock(), deleteLater=Mock())
        new_overlay = SimpleNamespace(
            selected=SimpleNamespace(connect=Mock()),
            cancelled=SimpleNamespace(connect=Mock()),
            apply_theme=Mock(),
            set_hint_text=Mock(),
        )
        mock_selection_overlay_cls.return_value = new_overlay
        window = MainWindow.__new__(MainWindow)
        window.selection_overlay = old_overlay
        window.handle_selection = Mock()
        window.handle_capture_cancelled = Mock()
        window.tr = lambda key, **kwargs: "Select an area"

        recreated_overlay = window.recreate_selection_overlay()

        self.assertIs(recreated_overlay, new_overlay)
        self.assertIs(window.selection_overlay, new_overlay)
        old_overlay.hide.assert_called_once_with()
        old_overlay.close.assert_called_once_with()
        old_overlay.deleteLater.assert_called_once_with()
        new_overlay.selected.connect.assert_called_once_with(window.handle_selection)
        new_overlay.cancelled.connect.assert_called_once_with(window.handle_capture_cancelled)
        new_overlay.apply_theme.assert_called_once_with()
        new_overlay.set_hint_text.assert_called_once_with("Select an area")

    @patch("app.ui.main_window_settings_layout.install_mouse_click_focus_clear_many")
    def test_install_settings_button_focus_clear_covers_scroll_area_action_buttons(self, mock_install_focus_clear):
        buttons = {name: SimpleNamespace(setFocusPolicy=Mock()) for name in (
            "new_profile_button",
            "delete_profile_button",
            "fetch_models_button",
            "test_button",
            "cancel_button",
            "discard_changes_button",
            "save_button",
            "api_keys_toggle_button",
            "new_prompt_preset_button",
            "delete_prompt_preset_button",
            "hotkey_record_button",
            "selection_hotkey_record_button",
            "input_hotkey_record_button",
            "advanced_toggle_button",
            "check_updates_now_button",
        )}
        window = MainWindow.__new__(MainWindow)
        for name, button in buttons.items():
            setattr(window, name, button)

        window._install_settings_button_focus_clear()

        mock_install_focus_clear.assert_called_once_with(*buttons.values())
        for button in buttons.values():
            button.setFocusPolicy.assert_called_once()
        self.assertEqual(window._settings_mouse_focus_clear_filters, mock_install_focus_clear.return_value)

    @patch("app.ui.main_window.clear_focus_if_alive")
    @patch("app.ui.main_window.QApplication.focusWidget")
    def test_clear_settings_focus_before_disabling_controls_moves_focus_off_settings_area(self, mock_focus_widget, mock_clear_focus):
        focus_widget = object()
        mock_focus_widget.return_value = focus_widget
        settings_tab = SimpleNamespace(isAncestorOf=lambda widget: widget is focus_widget)
        window = MainWindow.__new__(MainWindow)
        window.settings_tab = settings_tab
        window.setFocus = Mock()

        window._clear_settings_focus_before_disabling_controls()

        mock_clear_focus.assert_called_once_with(focus_widget)
        window.setFocus.assert_called_once_with(unittest.mock.ANY)

    @patch("app.ui.main_window.clear_focus_if_alive")
    @patch("app.ui.main_window.QApplication.focusWidget")
    def test_clear_settings_focus_before_disabling_controls_ignores_non_settings_focus(self, mock_focus_widget, mock_clear_focus):
        focus_widget = object()
        mock_focus_widget.return_value = focus_widget
        settings_tab = SimpleNamespace(isAncestorOf=lambda widget: False)
        window = MainWindow.__new__(MainWindow)
        window.settings_tab = settings_tab
        window.setFocus = Mock()

        window._clear_settings_focus_before_disabling_controls()

        mock_clear_focus.assert_not_called()
        window.setFocus.assert_not_called()

    def test_current_theme_mode_prefers_live_theme_buttons(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(theme_mode="system")
        window.theme_mode_buttons = {
            "system": SimpleNamespace(isChecked=lambda: False),
            "light": SimpleNamespace(isChecked=lambda: False),
            "dark": SimpleNamespace(isChecked=lambda: True),
        }
        self.assertEqual(window.current_theme_mode(), "dark")

    def test_auto_save_theme_mode_persists_selection_without_creating_dirty_state(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(theme_mode="system")
        window.has_unsaved_changes = False
        window.current_theme_mode = lambda: "dark"
        window.set_status = Mock()
        window.log = Mock()
        window.handle_error = Mock()
        window.set_unsaved_changes = Mock(side_effect=lambda dirty: setattr(window, "has_unsaved_changes", bool(dirty)))

        with patch("app.ui.main_window_profiles.save_config") as mock_save_config:
            result = window.auto_save_theme_mode()

        self.assertTrue(result)
        self.assertEqual(window.config.theme_mode, "dark")
        self.assertFalse(window.has_unsaved_changes)
        mock_save_config.assert_called_once_with(window.config)
        window.set_unsaved_changes.assert_called_once_with(False)

    def test_auto_save_theme_mode_preserves_existing_unsaved_changes(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(theme_mode="system")
        window.has_unsaved_changes = True
        window.current_theme_mode = lambda: "light"
        window.set_status = Mock()
        window.log = Mock()
        window.handle_error = Mock()
        window.set_unsaved_changes = Mock(side_effect=lambda dirty: setattr(window, "has_unsaved_changes", bool(dirty)))

        with patch("app.ui.main_window_profiles.save_config"):
            self.assertTrue(window.auto_save_theme_mode())
        self.assertTrue(window.has_unsaved_changes)

    def test_update_sidebar_width_for_language_expands_english_sidebar(self):
        window = MainWindow.__new__(MainWindow)
        window.current_ui_language = lambda: "en"
        window.sidebar_scroll = SimpleNamespace(setMinimumWidth=Mock(), setMaximumWidth=Mock())

        window.update_sidebar_width_for_language()

        window.sidebar_scroll.setMinimumWidth.assert_called_once_with(300)
        window.sidebar_scroll.setMaximumWidth.assert_called_once_with(376)

    def test_build_about_meta_markup_compacts_english_metadata(self):
        window = MainWindow.__new__(MainWindow)
        translations = {
            "about_author_label": "Author",
            "about_repo_label": "Repo",
        }
        window.tr = lambda key, **kwargs: translations.get(key, key)
        window.current_ui_language = lambda: "en"

        markup = window.build_about_meta_markup()

        self.assertIn("License: GPLv3", markup)
        self.assertIn("Author", markup)
        self.assertIn("Repo", markup)
        self.assertIn("scythenight", markup)
        self.assertIn("OCRTranslator", markup)
        self.assertIn("<br/>", markup)
        self.assertIn("&nbsp;&nbsp;&nbsp;", markup)
        self.assertIn("Author:", markup)
        self.assertIn("Repo:", markup)

    def test_refresh_shell_state_moves_profile_into_header_context(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(mode="book_lr", hotkey="Shift+Win+X", selection_hotkey="Shift+Win+C", input_hotkey="Shift+Win+V", target_language="繁體中文", active_prompt_preset_name="翻译", api_profiles=[SimpleNamespace(name="Default Gemini")])
        window.page_context_label = _FakeWidget()
        window.profile_name_edit = SimpleNamespace(text=lambda: "Default Gemini")
        window.get_active_profile = lambda: SimpleNamespace(name="Default Gemini")
        window.current_mode = lambda: "book_lr"
        window.current_hotkey = lambda: "Shift+Win+X"
        window.current_selection_hotkey = lambda: "Shift+Win+C"
        window.current_input_hotkey = lambda: "Shift+Win+V"
        window.current_target_language = lambda: "繁體中文"
        window.current_prompt_preset_name = lambda: "翻译"
        translations = {
            "header_summary": "当前配置：{profile} · {prompt} · {target} · {mode}\n{hotkeys}",
            "header_summary_primary": "当前配置：{profile} · {prompt} · {target} · {mode}",
            "meta_hotkeys": "快捷键：{capture} · {selection} · {input}",
            "meta_hotkey_capture": "截图 {value}",
            "meta_hotkey_selection": "选字 {value}",
            "meta_hotkey_input": "输入框 {value}",
            "mode_book_lr": "双页左右",
            "mode_web_ud": "网页上下",
            "untitled_profile": "未命名配置",
        }
        window.tr = lambda key, **kwargs: translations.get(key, key).format(**kwargs) if kwargs else translations.get(key, key)

        window.refresh_shell_state()

        expected_plain = "当前配置：Default Gemini · 翻译 · 繁體中文 · 双页左右\n快捷键：截图 Shift+Win+X · 选字 Shift+Win+C · 输入框 Shift+Win+V"
        self.assertEqual(window.page_context_label.tooltip, expected_plain)
        self.assertIn("Default Gemini", window.page_context_label.text)
        self.assertIn("Shift+Win+X", window.page_context_label.text)
        self.assertIn("Shift+Win+C", window.page_context_label.text)
        self.assertIn("Shift+Win+V", window.page_context_label.text)
        self.assertIn("快捷键：", window.page_context_label.text)
        self.assertIn("<br/>", window.page_context_label.text)
        self.assertIn("<span style=", window.page_context_label.text)

    def test_current_runtime_values_prefer_live_form_widgets(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(
            temperature=0.2,
            overlay_width=440,
            overlay_height=520,
            margin=18,
            overlay_auto_expand_top_margin=42,
            overlay_auto_expand_bottom_margin=24,
        )
        window.temperature_spin = _ValueWidget(0.7)
        window.overlay_width_spin = _ValueWidget(900)
        window.overlay_height_spin = _ValueWidget(640)
        window.overlay_margin_spin = _ValueWidget(24)
        window.overlay_auto_expand_top_margin_spin = _ValueWidget(64)
        window.overlay_auto_expand_bottom_margin_spin = _ValueWidget(18)

        self.assertEqual(window.current_temperature(), 0.7)
        self.assertEqual(window.current_overlay_width(), 900)
        self.assertEqual(window.current_overlay_height(), 640)
        self.assertEqual(window.current_margin(), 24)
        self.assertEqual(window.current_overlay_auto_expand_top_margin(), 64)
        self.assertEqual(window.current_overlay_auto_expand_bottom_margin(), 18)

    def test_get_api_client_injects_stream_fallback_status_notifier(self):
        window = MainWindow.__new__(MainWindow)
        window._api_client = None
        window._api_client_class = Mock(return_value="client")
        window.log = Mock()
        window.config = SimpleNamespace(debug_logging_enabled=False)

        result = window.get_api_client()

        self.assertEqual(result, "client")
        window._api_client_class.assert_called_once_with(window.log_debug, status_notifier=window.notify_stream_fallback_status, event_notifier=window.notify_api_event)

    def test_log_debug_respects_runtime_setting(self):
        window = MainWindow.__new__(MainWindow)
        window.log = Mock()
        window.config = SimpleNamespace(debug_logging_enabled=False)

        window.log_debug("hidden")
        window.config.debug_logging_enabled = True
        window.log_debug("visible")

        self.assertEqual(window.log.call_args_list, [call("visible")])

    def test_current_debug_logging_enabled_prefers_checkbox_state(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(debug_logging_enabled=False)
        window.debug_logging_checkbox = SimpleNamespace(isChecked=lambda: True)

        self.assertTrue(window.current_debug_logging_enabled())

    def test_notify_stream_fallback_status_updates_status_on_main_thread(self):
        window = MainWindow.__new__(MainWindow)
        window.is_quitting = False
        window.status_label = object()
        window.set_status = Mock()
        window.log_tr = Mock()
        window.bridge = SimpleNamespace(invoke_main_thread=SimpleNamespace(emit=lambda callback, payload: callback(payload)))
        window.tr = lambda key, **kwargs: key

        window.notify_stream_fallback_status("retrying", {"provider": "openai", "request_kind": "image"})
        window.notify_stream_fallback_status("succeeded", {"provider": "openai", "request_kind": "image"})

        self.assertEqual(
            [call.args[0] for call in window.set_status.call_args_list],
            ["stream_fallback_retrying", "stream_fallback_succeeded"],
        )
        self.assertEqual(
            [call.args[0] for call in window.log_tr.call_args_list],
            ["log_api_stream_fallback_retrying", "log_api_stream_fallback_succeeded"],
        )

    def test_notify_api_event_logs_retrying_message_on_main_thread(self):
        window = MainWindow.__new__(MainWindow)
        window.is_quitting = False
        window.log_tr = Mock()
        window.bridge = SimpleNamespace(invoke_main_thread=SimpleNamespace(emit=lambda callback, payload: callback(payload)))
        window.tr = lambda key, **kwargs: key

        window.notify_api_event("retrying", {"request_kind": "text", "attempt": 2, "total": 3})

        window.log_tr.assert_called_once_with(
            "log_api_retrying",
            kind="api_request_kind_text",
            attempt=2,
            total=3,
        )


    def test_current_request_overlay_width_prefers_runtime_unpinned_override(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(overlay_width=440, overlay_unpinned_width=560)
        window.overlay_width_spin = _ValueWidget(440)
        window._runtime_unpinned_overlay_width = 620

        self.assertEqual(window.current_request_overlay_width(), 620)

    def test_sync_runtime_unpinned_overlay_width_from_config_restores_saved_override(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(overlay_unpinned_width=620)
        window._runtime_unpinned_overlay_width = None

        window.sync_runtime_unpinned_overlay_width_from_config()

        self.assertEqual(window._runtime_unpinned_overlay_width, 620)

    def test_handle_overlay_width_setting_changed_clears_runtime_unpinned_width_override(self):
        window = MainWindow.__new__(MainWindow)
        window._suppress_form_tracking = False
        window.config = SimpleNamespace(overlay_width=440, overlay_unpinned_width=620)
        window.overlay_width_spin = _ValueWidget(500)
        window._runtime_unpinned_overlay_width = 620

        window.handle_overlay_width_setting_changed()

        self.assertIsNone(window._runtime_unpinned_overlay_width)
        self.assertEqual(window.config.overlay_unpinned_width, 620)

    def test_current_request_overlay_width_ignores_saved_unpinned_override_while_overlay_width_change_is_unsaved(self):
        window = MainWindow.__new__(MainWindow)
        window._suppress_form_tracking = False
        window.config = SimpleNamespace(overlay_width=440, overlay_unpinned_width=620)
        window.overlay_width_spin = _ValueWidget(500)
        window._runtime_unpinned_overlay_width = 620

        window.handle_overlay_width_setting_changed()

        self.assertEqual(window.current_request_overlay_width(), 500)

    def test_handle_overlay_width_setting_changed_ignores_suppressed_form_updates(self):
        window = MainWindow.__new__(MainWindow)
        window._suppress_form_tracking = True
        window.config = SimpleNamespace(overlay_width=440, overlay_unpinned_width=620)
        window.overlay_width_spin = _ValueWidget(500)
        window._runtime_unpinned_overlay_width = 620

        window.handle_overlay_width_setting_changed()

        self.assertEqual(window._runtime_unpinned_overlay_width, 620)
        self.assertEqual(window.config.overlay_unpinned_width, 620)

    def test_handle_overlay_resized_tracks_and_persists_runtime_unpinned_width(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(overlay_width=440, overlay_height=520, overlay_unpinned_width=None)
        window.translation_overlay = SimpleNamespace(is_pinned=False)
        window.persist_runtime_overlay_state = Mock()
        window.handle_error = Mock()
        window.set_status = Mock()

        window.handle_overlay_resized(900, 640)

        self.assertEqual(window._runtime_unpinned_overlay_width, 900)
        self.assertEqual(window.config.overlay_unpinned_width, 900)
        window.persist_runtime_overlay_state.assert_called_once_with()
        window.set_status.assert_called_once_with("overlay_resized", width=900, height=640)

    def test_persist_runtime_overlay_state_keeps_existing_dirty_flag(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace()
        window.has_unsaved_changes = True
        window.handle_error = Mock()
        window.set_unsaved_changes = Mock(side_effect=lambda dirty: setattr(window, "has_unsaved_changes", bool(dirty)))

        with patch("app.ui.main_window.save_config") as mock_save_config:
            self.assertTrue(window.persist_runtime_overlay_state())

        mock_save_config.assert_called_once_with(window.config)
        self.assertTrue(window.has_unsaved_changes)
        window.set_unsaved_changes.assert_called_once_with(True)

    def test_handle_overlay_resized_does_not_overwrite_default_overlay_size_when_unpinned(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(overlay_width=440, overlay_height=520, overlay_unpinned_width=None)
        window.translation_overlay = SimpleNamespace(is_pinned=False, persist_current_geometry_as_pinned=Mock())
        window.persist_runtime_overlay_state = Mock()
        window.handle_error = Mock()
        window.set_status = Mock()
        window.overlay_width_spin = SimpleNamespace(setValue=Mock())
        window.overlay_height_spin = SimpleNamespace(setValue=Mock())

        window.handle_overlay_resized(900, 640)

        self.assertEqual(window.config.overlay_width, 440)
        self.assertEqual(window.config.overlay_height, 520)
        self.assertEqual(window.config.overlay_unpinned_width, 900)
        window.translation_overlay.persist_current_geometry_as_pinned.assert_not_called()
        window.persist_runtime_overlay_state.assert_called_once_with()
        window.overlay_width_spin.setValue.assert_not_called()
        window.overlay_height_spin.setValue.assert_not_called()
        window.set_status.assert_called_once_with("overlay_resized", width=900, height=640)

    def test_handle_overlay_resized_persists_pinned_geometry_without_touching_default_size(self):
        window = MainWindow.__new__(MainWindow)
        window.config = SimpleNamespace(overlay_width=440, overlay_height=520, overlay_unpinned_width=700)
        window.translation_overlay = SimpleNamespace(is_pinned=True, persist_current_geometry_as_pinned=Mock())
        window.persist_runtime_overlay_state = Mock()
        window.handle_error = Mock()
        window.set_status = Mock()

        window.handle_overlay_resized(900, 640)

        self.assertEqual(window.config.overlay_width, 440)
        self.assertEqual(window.config.overlay_height, 520)
        self.assertEqual(window.config.overlay_unpinned_width, 700)
        window.translation_overlay.persist_current_geometry_as_pinned.assert_called_once_with()
        window.persist_runtime_overlay_state.assert_called_once_with()
        window.set_status.assert_called_once_with("overlay_resized", width=900, height=640)

    def test_complete_startup_services_runs_once_and_schedules_idle_prewarm(self):
        window = MainWindow.__new__(MainWindow)
        window.startup_timing = SimpleNamespace(mark=Mock(), measure=lambda _name, callback: callback())
        window._startup_services_initialized = False
        window.tray_service = SimpleNamespace(setup=Mock())
        window.setup_hotkey_listener = Mock()
        window.update_action_states = Mock()
        window.log_tr = Mock()
        window.schedule_idle_prewarm = Mock()
        window._log_startup_summary_if_ready = Mock()

        window.complete_startup_services()
        window.complete_startup_services()

        window.tray_service.setup.assert_called_once_with()
        window.setup_hotkey_listener.assert_called_once_with(initial=True)
        window.update_action_states.assert_called_once_with()
        window.log_tr.assert_called_once_with("log_application_started")
        window.schedule_idle_prewarm.assert_called_once_with()

    def test_minimize_to_tray_can_finish_startup_services_before_reporting_unavailable(self):
        window = MainWindow.__new__(MainWindow)
        window.tray = None
        window._startup_services_initialized = False
        window.config = SimpleNamespace(ui_language="en")
        window.tr = lambda key, **kwargs: key
        window.complete_startup_services = Mock(side_effect=lambda: setattr(window, "tray", object()))
        window.set_status = Mock()
        window.show_tray_toast = Mock()
        window.hide = Mock()
        window.existing_translation_overlay = lambda: None

        window.minimize_to_tray()

        window.complete_startup_services.assert_called_once_with()
        window.hide.assert_called_once_with()
        window.set_status.assert_called_once_with("tray_minimized")


    def test_show_tray_toast_prefers_transient_toast_for_visible_window(self):
        window = MainWindow.__new__(MainWindow)
        window.toast_service = SimpleNamespace(show_message=Mock(return_value=True), hide_message=Mock())
        window.tray_service = SimpleNamespace(show_message=Mock(return_value=True))
        window.isVisible = lambda: True
        window.isMinimized = lambda: False

        result = window.show_tray_toast("request submitted")

        self.assertTrue(result)
        window.toast_service.show_message.assert_called_once_with("request submitted", duration_ms=1500)
        window.tray_service.show_message.assert_not_called()

    def test_show_tray_toast_uses_system_tray_when_window_is_hidden(self):
        window = MainWindow.__new__(MainWindow)
        window.toast_service = SimpleNamespace(show_message=Mock(return_value=True), hide_message=Mock())
        window.tray_service = SimpleNamespace(show_message=Mock(return_value=True))
        window.isVisible = lambda: False
        window.isMinimized = lambda: False

        result = window.show_tray_toast("background request")

        self.assertTrue(result)
        window.toast_service.show_message.assert_not_called()
        window.toast_service.hide_message.assert_called_once_with()
        window.tray_service.show_message.assert_called_once_with("background request", duration_ms=1500)

    def test_show_tray_toast_uses_system_tray_when_requested(self):
        window = MainWindow.__new__(MainWindow)
        window.toast_service = SimpleNamespace(show_message=Mock(return_value=True), hide_message=Mock())
        window.tray_service = SimpleNamespace(show_message=Mock(return_value=True))
        window.isVisible = lambda: True
        window.isMinimized = lambda: False

        result = window.show_tray_toast("tray only", prefer_system=True)

        self.assertTrue(result)
        window.toast_service.hide_message.assert_called_once_with()
        window.tray_service.show_message.assert_called_once_with("tray only", duration_ms=1500)

    def test_show_tray_toast_uses_configured_duration_and_can_be_disabled(self):
        window = MainWindow.__new__(MainWindow)
        window.toast_service = SimpleNamespace(show_message=Mock(return_value=True), hide_message=Mock())
        window.tray_service = SimpleNamespace(show_message=Mock(return_value=True))
        window.toast_duration_spin = _ValueWidget(1.5)
        window.isVisible = lambda: True
        window.isMinimized = lambda: False

        result = window.show_tray_toast("timed toast")

        self.assertTrue(result)
        window.toast_service.show_message.assert_called_once_with("timed toast", duration_ms=1500)

        window.toast_service.show_message.reset_mock()
        window.toast_duration_spin = _ValueWidget(0)

        result = window.show_tray_toast("disabled toast")

        self.assertFalse(result)
        window.toast_service.hide_message.assert_called_once_with()
        window.toast_service.show_message.assert_not_called()
        window.tray_service.show_message.assert_not_called()

    def test_handle_toast_duration_changed_hides_existing_toast_when_disabled(self):
        window = MainWindow.__new__(MainWindow)
        window.toast_service = SimpleNamespace(hide_message=Mock())
        window.toast_duration_spin = _ValueWidget(0)

        window.handle_toast_duration_changed()

        window.toast_service.hide_message.assert_called_once_with()

    def test_start_update_check_uses_background_worker_without_freezing_main_actions(self):
        window = MainWindow.__new__(MainWindow)
        window.update_check_in_progress = False
        window.update_check_service = SimpleNamespace(check_latest_release=Mock(return_value="result"))
        window.refresh_update_check_ui = Mock()
        window.set_status = Mock()
        window.log = Mock()
        window.run_worker = Mock()
        window.current_app_version = lambda: "1.0.0"

        result = window.start_update_check(manual=True)

        self.assertTrue(result)
        self.assertTrue(window.update_check_in_progress)
        window.refresh_update_check_ui.assert_called_once_with()
        window.set_status.assert_called_once_with("update_checking_status")
        window.run_worker.assert_called_once()

    def test_handle_update_check_result_keeps_startup_up_to_date_checks_silent(self):
        window = MainWindow.__new__(MainWindow)
        window.update_check_in_progress = True
        window.refresh_update_check_ui = Mock()
        window.set_status = Mock()
        window.log = Mock()
        result = SimpleNamespace(kind="up_to_date", has_update=False, is_up_to_date=True, current_version="1.0.0", latest_version="1.0.0", release_url="https://example.test", error="")

        window._handle_update_check_result(result, manual=False)

        self.assertFalse(window.update_check_in_progress)
        self.assertIsNone(window._last_update_check_result)
        window.set_status.assert_not_called()
        window.refresh_update_check_ui.assert_called_once_with()

    @patch("app.ui.main_window.QTimer.singleShot")
    def test_schedule_startup_update_check_runs_once_and_uses_saved_preference(self, mock_single_shot):
        window = MainWindow.__new__(MainWindow)
        window._startup_update_check_scheduled = False
        window.is_quitting = False
        window.update_check_in_progress = False
        window.config = SimpleNamespace(check_updates_on_startup=True)
        window.check_updates_on_startup_checkbox = SimpleNamespace(isChecked=lambda: False)
        window.start_update_check = Mock()

        window.schedule_startup_update_check(delay_ms=3456)
        window.schedule_startup_update_check(delay_ms=9999)

        mock_single_shot.assert_called_once()
        delay, callback = mock_single_shot.call_args.args
        self.assertEqual(delay, 3456)
        callback()
        window.start_update_check.assert_called_once_with(manual=False)

    @patch("app.ui.main_window.QTimer.singleShot")
    def test_schedule_startup_update_check_ignores_unsaved_checkbox_enable_when_saved_preference_is_off(self, mock_single_shot):
        window = MainWindow.__new__(MainWindow)
        window._startup_update_check_scheduled = False
        window.is_quitting = False
        window.update_check_in_progress = False
        window.config = SimpleNamespace(check_updates_on_startup=False)
        window.check_updates_on_startup_checkbox = SimpleNamespace(isChecked=lambda: True)
        window.start_update_check = Mock()

        window.schedule_startup_update_check(delay_ms=3456)

        delay, callback = mock_single_shot.call_args.args
        self.assertEqual(delay, 3456)
        callback()
        window.start_update_check.assert_not_called()

    def test_refresh_update_check_hint_uses_result_when_manual_check_found_new_release(self):
        window = MainWindow.__new__(MainWindow)
        window.update_check_in_progress = False
        window._last_update_check_result = SimpleNamespace(kind="available", latest_version="1.1.0", current_version="1.0.0", release_url="https://example.test/release")
        window.check_updates_on_startup_checkbox = SimpleNamespace(isChecked=lambda: False)
        window.update_check_hint_label = _FakeWidget()
        window.current_app_version = lambda: "1.0.0"
        window.effective_theme_name = lambda: "light"
        window.tr = lambda key, **kwargs: key if not kwargs else f"{key}:{kwargs}"

        window.refresh_update_check_hint()

        self.assertIn("update_check_hint_available", window.update_check_hint_label.text)
        self.assertIn("1.1.0", window.update_check_hint_label.text)
        self.assertIn("<a href='https://example.test/release'", window.update_check_hint_label.text)

    def test_handle_update_check_result_skips_ui_updates_while_quitting(self):
        window = MainWindow.__new__(MainWindow)
        window.is_quitting = True
        window.update_check_in_progress = True
        window.refresh_update_check_ui = Mock()
        window.set_status = Mock()
        window.log = Mock()
        result = SimpleNamespace(kind="available", has_update=True, is_up_to_date=False, current_version="1.0.0", latest_version="1.1.0", release_url="https://example.test/release", error="")

        window._handle_update_check_result(result, manual=True)

        self.assertFalse(window.update_check_in_progress)
        self.assertIs(window._last_update_check_result, result)
        window.refresh_update_check_ui.assert_not_called()
        window.set_status.assert_not_called()

    def test_handle_error_clears_update_check_state_when_update_worker_fails(self):
        class _UpdateFailure(RuntimeError):
            operation = "update_check"
            task_id = 3

        window = MainWindow.__new__(MainWindow)
        window._handling_error = False
        window._safe_write_stderr = Mock()
        window._handle_stale_operation_error = Mock(return_value=False)
        window.update_check_in_progress = True
        window.operation_manager = SimpleNamespace(finish=lambda operation, task_id: setattr(window, "update_check_in_progress", False))
        window.capture_workflow_active = False
        window.restore_pinned_overlay_after_capture = False
        window.is_quitting = False
        window.status_label = object()
        window.isVisible = lambda: True
        window.finish_capture_workflow = Mock()
        window.set_status = Mock()
        window.log = Mock()
        window.tr = lambda key, **kwargs: key
        window.effective_theme_name = lambda: "light"
        window._show_error_dialog_safe = Mock()

        window.handle_error(_UpdateFailure("boom"))

        self.assertFalse(window.update_check_in_progress)


    def test_close_event_can_redirect_to_tray_even_before_startup_services_finish(self):
        window = MainWindow.__new__(MainWindow)
        event = SimpleNamespace(ignore=Mock(), accept=Mock())
        window.is_quitting = False
        window.config = SimpleNamespace(close_to_tray_on_close=True)
        window.tray = None
        window._startup_services_initialized = False
        window.complete_startup_services = Mock(side_effect=lambda: setattr(window, "tray", object()))
        window.log_tr = Mock()
        window.minimize_to_tray = Mock()

        window.closeEvent(event)

        window.complete_startup_services.assert_called_once_with()
        window.minimize_to_tray.assert_called_once_with()
        event.ignore.assert_called_once_with()

    @patch("app.ui.main_window.QTimer.singleShot")
    def test_schedule_idle_prewarm_arms_single_shot_only_once(self, mock_single_shot):
        window = MainWindow.__new__(MainWindow)
        window._startup_prewarm_completed = False
        window._startup_prewarm_pending = False
        window._startup_services_initialized = True

        window.schedule_idle_prewarm(delay_ms=123)
        window.schedule_idle_prewarm(delay_ms=456)

        mock_single_shot.assert_called_once()
        delay, callback = mock_single_shot.call_args.args
        self.assertEqual(delay, 123)
        self.assertTrue(callable(callback))
        self.assertTrue(window._startup_prewarm_pending)

    def test_idle_prewarm_waits_for_user_idle_before_running_step(self):
        window = MainWindow.__new__(MainWindow)
        window.is_quitting = False
        window._startup_prewarm_started = False
        window._startup_prewarm_completed = False
        window._startup_prewarm_pending = False
        window.isVisible = lambda: True
        window.capture_workflow_active = False
        window.background_busy = lambda: False
        window.log = Mock()
        window.schedule_idle_prewarm = Mock()
        window.startup_timing = SimpleNamespace(mark=Mock(), measure=lambda _name, callback: callback())
        window._startup_prewarm_steps = lambda: [{"name": "api", "callback": Mock(), "min_idle_ms": 600, "next_delay_ms": 90}]
        window._last_user_interaction_at = time.perf_counter()

        window._run_idle_prewarm_step()

        window.schedule_idle_prewarm.assert_called_once()
        self.assertFalse(window._startup_prewarm_completed)

    def test_idle_prewarm_runs_steps_incrementally_without_blocking(self):
        window = MainWindow.__new__(MainWindow)
        calls = []
        window.is_quitting = False
        window._startup_prewarm_started = False
        window._startup_prewarm_completed = False
        window._startup_prewarm_pending = False
        window.isVisible = lambda: True
        window.capture_workflow_active = False
        window.background_busy = lambda: False
        window.log = Mock()
        window.schedule_idle_prewarm = Mock()
        window._remove_startup_interaction_tracker = Mock()
        window._log_startup_prewarm_summary_if_ready = Mock()
        window.startup_timing = SimpleNamespace(mark=Mock(), measure=lambda _name, callback: callback())
        window._last_user_interaction_at = time.perf_counter() - 10
        window._startup_prewarm_steps = lambda: [
            {"name": "api", "callback": lambda: calls.append("api"), "min_idle_ms": 0, "next_delay_ms": 90},
            {"name": "overlay_class", "callback": lambda: calls.append("overlay_class"), "min_idle_ms": 0, "next_delay_ms": 0},
        ]

        window._run_idle_prewarm_step()
        self.assertEqual(calls, ["api"])
        self.assertFalse(window._startup_prewarm_completed)
        window.schedule_idle_prewarm.assert_called_once_with(delay_ms=90)

        window._run_idle_prewarm_step()
        self.assertEqual(calls, ["api", "overlay_class"])
        self.assertTrue(window._startup_prewarm_completed)
        window._remove_startup_interaction_tracker.assert_called_once_with()

    def test_idle_prewarm_continues_light_steps_while_window_is_hidden_but_pauses_heavy_steps(self):
        window = MainWindow.__new__(MainWindow)
        calls = []
        window.is_quitting = False
        window._startup_prewarm_started = False
        window._startup_prewarm_completed = False
        window._startup_prewarm_pending = False
        window.isVisible = lambda: False
        window.capture_workflow_active = False
        window.background_busy = lambda: False
        window.log = Mock()
        window.schedule_idle_prewarm = Mock()
        window._remove_startup_interaction_tracker = Mock()
        window._log_startup_prewarm_summary_if_ready = Mock()
        window.startup_timing = SimpleNamespace(mark=Mock(), measure=lambda _name, callback: callback())
        window._last_user_interaction_at = time.perf_counter() - 10
        window._startup_prewarm_steps = lambda: [
            {"name": "api", "callback": lambda: calls.append("api"), "min_idle_ms": 0, "next_delay_ms": 90, "allow_hidden": True},
            {"name": "overlay", "callback": lambda: calls.append("overlay"), "min_idle_ms": 0, "next_delay_ms": 0, "allow_hidden": False},
        ]

        window._run_idle_prewarm_step()

        self.assertEqual(calls, ["api"])
        self.assertFalse(window._startup_prewarm_completed)
        window.schedule_idle_prewarm.assert_called_once_with(delay_ms=90)

        window._run_idle_prewarm_step()

        self.assertEqual(calls, ["api"])
        self.assertFalse(window._startup_prewarm_completed)
        window._remove_startup_interaction_tracker.assert_not_called()


    def test_workspace_shadow_spec_uses_lighter_material_elevation_in_light_mode(self):
        window = MainWindow.__new__(MainWindow)
        window.effective_theme_name = lambda: "light"

        spec = window.workspace_shadow_spec()

        self.assertEqual(spec, {"blur": 12, "y_offset": 1, "alpha": 12})

    def test_workspace_shadow_spec_uses_subtle_but_clear_depth_in_dark_mode(self):
        window = MainWindow.__new__(MainWindow)
        window.effective_theme_name = lambda: "dark"

        spec = window.workspace_shadow_spec()

        self.assertEqual(spec, {"blur": 14, "y_offset": 2, "alpha": 18})

    def test_update_action_states_freezes_settings_during_translation(self):
        window = MainWindow.__new__(MainWindow)
        window.tr = lambda key, **kwargs: key
        window.fetch_models_in_progress = False
        window.test_profile_in_progress = False
        window.translation_in_progress = True
        window.capture_workflow_active = False
        window.operation_manager = SimpleNamespace(current_active=lambda order: "translation")
        window.selection_overlay = SimpleNamespace(isVisible=lambda: False)
        window.tray = object()
        window.tray_capture_action = _FakeWidget()
        window.tray_cancel_action = _FakeWidget()

        for name in (
            "profile_name_edit",
            "provider_combo",
            "base_url_edit",
            "model_combo",
            "api_keys_edit",
            "api_keys_toggle_button",
            "retry_count_spin",
            "retry_interval_spin",
            "target_language_edit",
            "ui_language_combo",
            "hotkey_edit",
            "hotkey_record_button",
            "theme_mode_switch",
            "selection_hotkey_edit",
            "selection_hotkey_record_button",
            "input_hotkey_edit",
            "input_hotkey_record_button",
            "overlay_font_combo",
            "overlay_font_size_spin",
            "mode_combo",
            "prompt_preset_combo",
            "new_prompt_preset_button",
            "delete_prompt_preset_button",
            "prompt_preset_name_edit",
            "image_prompt_edit",
            "text_prompt_edit",
            "temperature_spin",
            "overlay_width_spin",
            "overlay_height_spin",
            "overlay_margin_spin",
            "close_to_tray_on_close_checkbox",
            "fetch_models_button",
            "test_button",
            "save_button",
            "cancel_button",
            "hero_capture_button",
            "hero_tray_button",
            "preview_capture_button",
            "profile_combo",
            "new_profile_button",
            "delete_profile_button",
        ):
            setattr(window, name, _FakeWidget())

        window.update_action_states()

        self.assertFalse(window.target_language_edit.enabled)
        self.assertFalse(window.prompt_preset_combo.enabled)
        self.assertFalse(window.close_to_tray_on_close_checkbox.enabled)
        self.assertFalse(window.theme_mode_switch.enabled)
        self.assertTrue(window.hero_tray_button.enabled)
        self.assertFalse(window.profile_combo.enabled)
        self.assertFalse(window.tray_capture_action.enabled)
        self.assertTrue(window.cancel_button.enabled)
        self.assertEqual(window.hero_capture_button.text, "start_capture_busy")
        self.assertEqual(window.preview_capture_button.text, "start_capture_busy")

    def test_background_busy_includes_selected_text_capture(self):
        window = MainWindow.__new__(MainWindow)
        window.fetch_models_in_progress = False
        window.test_profile_in_progress = False
        window.translation_in_progress = False
        window.selected_text_capture_in_progress = True

        self.assertTrue(window.background_busy())

    def test_cancel_background_operation_cancels_selected_text_capture_session(self):
        window = MainWindow.__new__(MainWindow)
        window.operation_manager = SimpleNamespace(current_active=lambda order: None)
        window.selected_text_capture_in_progress = True
        window.selected_text_capture_session = object()
        window.request_workflow = SimpleNamespace(cancel_selected_text_capture=Mock(return_value=True))

        result = window.cancel_background_operation()

        self.assertTrue(result)
        window.request_workflow.cancel_selected_text_capture.assert_called_once_with()

    def test_cancel_background_operation_restores_capture_origin_state_while_request_is_pending(self):
        window = MainWindow.__new__(MainWindow)
        overlay = SimpleNamespace(restore_last_overlay=Mock())
        window.operation_manager = SimpleNamespace(current_active=lambda order: "translation", cancel=Mock())
        window.capture_workflow_active = False
        window.restore_window_after_capture = True
        window.restore_pinned_overlay_after_capture = True
        window.finish_capture_workflow = Mock()
        window.request_workflow = SimpleNamespace(clear_streaming_response_update_state=Mock())
        window.existing_translation_overlay = lambda: overlay
        window.show_tray_toast = Mock()
        window.tr = lambda key, **kwargs: key
        window.set_status = Mock()
        window.log = Mock()

        result = window.cancel_background_operation()

        self.assertTrue(result)
        window.operation_manager.cancel.assert_called_once_with("translation")
        window.finish_capture_workflow.assert_called_once_with(restore_window=True)
        window.request_workflow.clear_streaming_response_update_state.assert_called_once_with()
        overlay.restore_last_overlay.assert_called_once_with()
        self.assertFalse(window.restore_pinned_overlay_after_capture)
        window.show_tray_toast.assert_called_once_with("request_cancelled")
        window.set_status.assert_called_once_with("request_cancelled")

    def test_cancel_background_operation_marks_visible_partial_result_when_no_restore_target_exists(self):
        window = MainWindow.__new__(MainWindow)
        overlay = SimpleNamespace(has_partial_result=lambda: True, set_partial_result_state=Mock())
        window.operation_manager = SimpleNamespace(current_active=lambda order: "translation", cancel=Mock())
        window.capture_workflow_active = False
        window.restore_window_after_capture = False
        window.restore_pinned_overlay_after_capture = False
        window.finish_capture_workflow = Mock()
        window.request_workflow = SimpleNamespace(clear_streaming_response_update_state=Mock())
        window.existing_translation_overlay = lambda: overlay
        window.show_tray_toast = Mock()
        window.tr = lambda key, **kwargs: key
        window.set_status = Mock()
        window.log = Mock()

        result = window.cancel_background_operation()

        self.assertTrue(result)
        window.operation_manager.cancel.assert_called_once_with("translation")
        window.finish_capture_workflow.assert_called_once_with(restore_window=False)
        window.request_workflow.clear_streaming_response_update_state.assert_called_once_with()
        overlay.set_partial_result_state.assert_called_once_with("cancelled")
        window.show_tray_toast.assert_called_once_with("request_cancelled")
        window.set_status.assert_called_once_with("request_cancelled")

    def test_save_settings_aborts_when_hotkey_registration_fails(self):
        window = MainWindow.__new__(MainWindow)
        window.tr = lambda key, **kwargs: f"{key}: {kwargs.get('error')}" if kwargs else key
        window.validate_form_inputs = lambda focus_first_invalid=True, scope="save": (True, "")
        window.set_status = Mock()
        window.log = Mock()
        window.config = SimpleNamespace(ui_language="en", hotkey="Ctrl+X", selection_hotkey="Ctrl+C", input_hotkey="Ctrl+Z")
        candidate_config = SimpleNamespace(ui_language="zh-TW", hotkey="Ctrl+Shift+X", selection_hotkey="Ctrl+Shift+C", input_hotkey="Ctrl+Shift+Z")
        profile = SimpleNamespace(name="Demo", provider="openai", base_url="https://api.openai.com")
        window.sync_form_to_config = lambda: ("en", candidate_config, profile)
        window.setup_hotkey_listener = Mock(side_effect=[RuntimeError("hook failed"), True])

        with patch("app.ui.main_window_profiles.show_critical_message") as mock_critical, patch(
            "app.ui.main_window_profiles.save_config"
        ) as mock_save_config:
            result = window.save_settings()

        self.assertFalse(result)
        self.assertEqual(window.config.ui_language, "en")
        self.assertEqual(window.setup_hotkey_listener.call_count, 2)
        mock_save_config.assert_not_called()
        mock_critical.assert_called_once()

    def test_save_settings_restores_scroll_position_and_neutral_focus_after_success(self):
        window = MainWindow.__new__(MainWindow)
        scrollbar = SimpleNamespace(value=Mock(return_value=284), setValue=Mock())
        window.settings_scroll = SimpleNamespace(verticalScrollBar=lambda: scrollbar)
        window.save_button = SimpleNamespace()
        window.setFocus = Mock()
        window.tr = lambda key, **kwargs: key
        window.validate_form_inputs = lambda focus_first_invalid=True, scope="save": (True, "")
        window.set_status = Mock()
        window.log = Mock()
        window.apply_language = Mock()
        window.load_profile_to_form = Mock()
        window.load_prompt_preset_to_form = Mock()
        window.config = SimpleNamespace(ui_language="en", hotkey="Ctrl+X", selection_hotkey="Ctrl+C", input_hotkey="Ctrl+Z")
        candidate_config = SimpleNamespace(
            ui_language="en",
            hotkey="Ctrl+Shift+X",
            selection_hotkey="Ctrl+Shift+C",
            input_hotkey="Ctrl+Shift+Z",
            active_profile_name="Demo",
            active_prompt_preset_name="Translate",
        )
        profile = SimpleNamespace(name="Demo", provider="openai", base_url="https://api.openai.com")
        window.sync_form_to_config = lambda: ("en", candidate_config, profile)
        window.setup_hotkey_listener = Mock(return_value=True)

        with patch("app.ui.main_window_profiles.save_config"), patch("app.ui.main_window_profiles.clear_focus_if_alive") as mock_clear_focus, patch(
            "app.ui.main_window_profiles.QTimer.singleShot", side_effect=lambda _delay, callback: callback()
        ):
            result = window.save_settings()

        self.assertTrue(result)
        self.assertGreaterEqual(scrollbar.setValue.call_count, 2)
        mock_clear_focus.assert_any_call(window.save_button)
        mock_clear_focus.assert_any_call(None)
        window.setFocus.assert_called()

    def test_validate_hotkey_actions_rejects_subset_conflicts(self):
        window = MainWindow.__new__(MainWindow)
        window.tr = lambda key, **kwargs: f"{key}: {kwargs}"
        window.hotkey_has_modifier = lambda hotkey_text: True
        window.normalize_hotkey = lambda hotkey_text: hotkey_text.lower()

        with self.assertRaises(ValueError):
            window.validate_hotkey_actions({"capture": "Ctrl+X", "selection_text": "Ctrl+Shift+X", "manual_input": "Ctrl+Z"})

    def test_validate_hotkey_actions_rejects_unsupported_primary_tokens(self):
        window = MainWindow.__new__(MainWindow)
        window.tr = lambda key, **kwargs: f"{key}: {kwargs}"
        window.hotkey_has_modifier = lambda hotkey_text: True
        window.normalize_hotkey = lambda hotkey_text: hotkey_text.lower()

        with self.assertRaisesRegex(ValueError, "validation_hotkey_unsupported_key"):
            window.validate_hotkey_actions({"capture": "Ctrl+Foo", "selection_text": "Ctrl+Shift+C", "manual_input": "Ctrl+Z"})

    def test_validate_hotkey_actions_rejects_modifier_only_shortcuts(self):
        window = MainWindow.__new__(MainWindow)
        window.tr = lambda key, **kwargs: f"{key}: {kwargs}"
        window.hotkey_has_modifier = lambda hotkey_text: True
        window.normalize_hotkey = lambda hotkey_text: hotkey_text.lower()

        with self.assertRaisesRegex(ValueError, "validation_hotkey_requires_primary"):
            window.validate_hotkey_actions({"capture": "Ctrl+Shift", "selection_text": "Ctrl+Shift+C", "manual_input": "Ctrl+Z"})

    @patch("app.ui.main_window.show_critical_message")
    @patch("app.ui.main_window.show_non_blocking_critical_message", side_effect=RuntimeError("dialog failed"))
    def test_handle_error_falls_back_when_non_blocking_dialog_fails(self, _mock_non_blocking, mock_blocking):
        window = MainWindow.__new__(MainWindow)
        window._handling_error = False
        window._safe_write_stderr = Mock()
        window._handle_stale_operation_error = Mock(return_value=False)
        window.capture_workflow_active = False
        window.restore_pinned_overlay_after_capture = False
        window.is_quitting = False
        window.status_label = object()
        window.isVisible = lambda: True
        window.finish_capture_workflow = Mock()
        window.set_status = Mock()
        window.log = Mock()
        window.tr = lambda key, **kwargs: key
        window.effective_theme_name = lambda: "light"

        window.handle_error(RuntimeError("boom"))

        mock_blocking.assert_called_once()
        window.set_status.assert_called_once_with("operation_failed")
        window.log.assert_called()
        self.assertFalse(window._handling_error)

    def test_handle_error_restores_pinned_overlay_after_translation_failure_even_after_capture_ui_has_closed(self):
        class _TranslationFailure(RuntimeError):
            operation = "translation"
            task_id = None

        window = MainWindow.__new__(MainWindow)
        overlay = SimpleNamespace(restore_last_overlay=Mock())
        window._handling_error = False
        window._safe_write_stderr = Mock()
        window._handle_stale_operation_error = Mock(return_value=False)
        window.capture_workflow_active = False
        window.restore_pinned_overlay_after_capture = True
        window.is_quitting = False
        window.status_label = object()
        window.isVisible = lambda: True
        window.finish_capture_workflow = Mock()
        window.set_status = Mock()
        window.log = Mock()
        window.tr = lambda key, **kwargs: key
        window.effective_theme_name = lambda: "light"
        window._show_error_dialog_safe = Mock()
        window.operation_manager = SimpleNamespace(finish=Mock())
        window.existing_translation_overlay = lambda: overlay
        window.request_workflow = SimpleNamespace(clear_streaming_response_update_state=Mock())

        window.handle_error(_TranslationFailure("boom"))

        window.finish_capture_workflow.assert_called_once_with(restore_window=True)
        overlay.restore_last_overlay.assert_called_once_with()
        self.assertFalse(window.restore_pinned_overlay_after_capture)
        window.request_workflow.clear_streaming_response_update_state.assert_called_once_with()

    def test_handle_error_marks_visible_partial_result_failed_when_translation_stream_breaks_without_restore_target(self):
        class _TranslationFailure(RuntimeError):
            operation = "translation"
            task_id = None

        window = MainWindow.__new__(MainWindow)
        overlay = SimpleNamespace(has_partial_result=lambda: True, set_partial_result_state=Mock())
        window._handling_error = False
        window._safe_write_stderr = Mock()
        window._handle_stale_operation_error = Mock(return_value=False)
        window.capture_workflow_active = False
        window.restore_pinned_overlay_after_capture = False
        window.is_quitting = False
        window.status_label = object()
        window.isVisible = lambda: True
        window.finish_capture_workflow = Mock()
        window.set_status = Mock()
        window.log = Mock()
        window.tr = lambda key, **kwargs: key
        window.effective_theme_name = lambda: "light"
        window._show_error_dialog_safe = Mock()
        window.operation_manager = SimpleNamespace(finish=Mock())
        window.existing_translation_overlay = lambda: overlay
        window.request_workflow = SimpleNamespace(clear_streaming_response_update_state=Mock())

        window.handle_error(_TranslationFailure("boom"))

        overlay.set_partial_result_state.assert_called_once_with("failed")
        window.request_workflow.clear_streaming_response_update_state.assert_called_once_with()
        window.set_status.assert_called_once_with("translate_failed")

    def test_handle_error_marks_visible_partial_result_cancelled_for_translation_cancellation(self):
        cancelled = type("_Cancelled", (RuntimeError,), {"operation": "translation", "task_id": None})()
        cancelled.original = RequestCancelledError()
        window = MainWindow.__new__(MainWindow)
        overlay = SimpleNamespace(has_partial_result=lambda: True, set_partial_result_state=Mock())
        window._handling_error = False
        window._safe_write_stderr = Mock()
        window._handle_stale_operation_error = Mock(return_value=False)
        window.restore_pinned_overlay_after_capture = False
        window.status_label = object()
        window.toast_service = SimpleNamespace(hide_message=Mock())
        window.set_status = Mock()
        window.log = Mock()
        window.existing_translation_overlay = lambda: overlay
        window.request_workflow = SimpleNamespace(clear_streaming_response_update_state=Mock())

        window.handle_error(cancelled)

        overlay.set_partial_result_state.assert_called_once_with("cancelled")
        window.request_workflow.clear_streaming_response_update_state.assert_called_once_with()
        window.set_status.assert_called_once_with("request_cancelled")

    def test_handle_error_suppresses_recursive_reentry(self):
        window = MainWindow.__new__(MainWindow)
        window._handling_error = True
        window._safe_write_stderr = Mock()

        window.handle_error(RuntimeError("boom"))

        window._safe_write_stderr.assert_called_once()

    def test_run_exit_watchdog_forces_exit_only_while_quitting(self):
        window = MainWindow.__new__(MainWindow)
        window.is_quitting = True
        window._force_process_exit = Mock()
        window._safe_write_stderr = Mock()

        with patch("app.ui.main_window.time.sleep"):
            window._run_exit_watchdog(0)

        window._force_process_exit.assert_called_once_with(0)

    def test_start_selection_from_launch_uses_restore_window_override(self):
        window = MainWindow.__new__(MainWindow)
        window.capture_workflow_active = False
        window.is_quitting = False
        window.log = Mock()
        window.status_label = object()
        window.set_status = Mock()
        window.show_main_window = Mock()
        window.request_workflow = SimpleNamespace(start_selection=Mock(side_effect=lambda **kwargs: setattr(window, "capture_workflow_active", True)))
        window.handle_error = Mock()

        window.start_selection_from_launch()

        window.request_workflow.start_selection.assert_called_once_with(restore_window_after_capture=True)
        window.show_main_window.assert_not_called()
        window.set_status.assert_not_called()
        window.handle_error.assert_not_called()

    def test_start_selection_from_launch_shows_main_window_when_capture_does_not_start(self):
        window = MainWindow.__new__(MainWindow)
        window.capture_workflow_active = False
        window.is_quitting = False
        window.log = Mock()
        window.status_label = object()
        window.set_status = Mock()
        window.show_main_window = Mock()
        window.request_workflow = SimpleNamespace(start_selection=Mock())
        window.handle_error = Mock()

        window.start_selection_from_launch()

        window.set_status.assert_called_once_with("capture_launch_fallback")
        window.show_main_window.assert_called_once_with()
        window.handle_error.assert_not_called()

    @patch("app.ui.main_window.QApplication.instance")
    def test_emergency_shutdown_skips_unsaved_prompt_and_runs_cleanup(self, mock_app_instance):
        fake_app = SimpleNamespace(quit=Mock())
        mock_app_instance.return_value = fake_app
        window = MainWindow.__new__(MainWindow)
        window.is_quitting = False
        window._shutdown_cleanup_in_progress = False
        window._shutdown_cleanup_done = False
        window.resolve_unsaved_changes = Mock(return_value=False)
        window._remove_startup_interaction_tracker = Mock()
        window._start_exit_watchdog = Mock()
        window._safe_write_stderr = Mock()
        window.selected_text_capture_in_progress = False
        window.operation_manager = SimpleNamespace(cancel_all=Mock())
        window.selection_overlay = SimpleNamespace(hide=Mock())
        window.stop_hotkey_recording = Mock()
        window.hotkey_listener = None
        window.registered_hotkeys = {}
        window._active_error_dialogs = []
        window.instance_server_service = SimpleNamespace(close=Mock())
        window.tray_service = SimpleNamespace(close=Mock())
        window.toast_service = SimpleNamespace(close=Mock())
        window.existing_translation_overlay = lambda: None

        result = window.emergency_shutdown()

        self.assertTrue(result)
        window.resolve_unsaved_changes.assert_not_called()
        window._start_exit_watchdog.assert_called_once_with()
        fake_app.quit.assert_called_once_with()
        self.assertTrue(window._shutdown_cleanup_done)

    @patch("app.ui.main_window.QApplication.instance")
    def test_quit_app_does_not_restore_hotkeys_while_exiting(self, mock_app_instance):
        fake_app = SimpleNamespace(quit=Mock())
        mock_app_instance.return_value = fake_app
        window = MainWindow.__new__(MainWindow)
        window.is_quitting = False
        window.resolve_unsaved_changes = lambda for_exit=True: True
        window.log_tr = Mock()
        window._start_exit_watchdog = Mock()
        window.selected_text_capture_in_progress = False
        window.operation_manager = SimpleNamespace(cancel_all=Mock())
        window.selection_overlay = SimpleNamespace(hide=Mock())
        window.stop_hotkey_recording = Mock()
        window.hotkey_listener = None
        window.registered_hotkeys = {}
        window.instance_server_service = SimpleNamespace(close=Mock())
        window.translation_overlay = SimpleNamespace(close=Mock())
        window.tray_service = SimpleNamespace(close=Mock())

        result = window.quit_app()

        self.assertTrue(result)
        window.stop_hotkey_recording.assert_called_once_with(cancelled=False, restore_hotkey_listener=False)
        window._start_exit_watchdog.assert_called_once_with()
        fake_app.quit.assert_called_once_with()

    @patch("app.ui.main_window.QApplication.instance")
    def test_handle_about_to_quit_runs_cleanup_when_app_quit_bypasses_quit_app(self, mock_app_instance):
        fake_app = SimpleNamespace()
        mock_app_instance.return_value = fake_app
        window = MainWindow.__new__(MainWindow)
        window.is_quitting = False
        window._shutdown_cleanup_in_progress = False
        window._shutdown_cleanup_done = False
        window._remove_startup_interaction_tracker = Mock()
        window._start_exit_watchdog = Mock()
        window.selected_text_capture_in_progress = False
        window.operation_manager = SimpleNamespace(cancel_all=Mock())
        window.selection_overlay = SimpleNamespace(hide=Mock())
        window.stop_hotkey_recording = Mock()
        window.hotkey_listener = None
        window.registered_hotkeys = {}
        window._active_error_dialogs = []
        window.instance_server_service = SimpleNamespace(close=Mock())
        window.tray_service = SimpleNamespace(close=Mock())
        window.existing_translation_overlay = lambda: None

        window.handle_about_to_quit()

        window._start_exit_watchdog.assert_called_once_with()
        self.assertTrue(window._shutdown_cleanup_done)

if __name__ == "__main__":
    unittest.main()
