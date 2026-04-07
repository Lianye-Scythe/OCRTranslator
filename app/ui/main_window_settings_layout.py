from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QScrollArea, QVBoxLayout, QWidget

from .focus_utils import install_mouse_click_focus_clear_many
from .ime_aware_text_edit import ImeAwarePlainTextEdit
from .main_window_layout import ScrollSafeComboBox, ScrollSafeDoubleSpinBox, ScrollSafeFontComboBox, ScrollSafeSpinBox


class MainWindowSettingsLayoutMixin:
    def _build_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        self.settings_scroll = scroll
        scroll.setObjectName("SettingsScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll)

        content = QWidget()
        content.setObjectName("SettingsScrollContent")
        scroll.setWidget(content)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 4, 12, 48)
        content_layout.setSpacing(32)

        self._build_connection_section(content_layout)
        self._build_translation_section(content_layout)
        self._build_advanced_section(content_layout)
        self._multiline_editor_surfaces = getattr(self, "_multiline_editor_surfaces", {})
        self._install_settings_button_focus_clear()
        self._connect_settings_form_signals()

        self.image_prompt_edit.setTabChangesFocus(True)
        self.text_prompt_edit.setTabChangesFocus(True)
        content_layout.addStretch(1)

    def _install_settings_button_focus_clear(self):
        button_names = (
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
        )
        buttons = []
        for name in button_names:
            widget = getattr(self, name, None)
            if widget is not None and hasattr(widget, "setFocusPolicy"):
                widget.setFocusPolicy(Qt.TabFocus)
            if widget is not None:
                buttons.append(widget)
        self._settings_mouse_focus_clear_filters = install_mouse_click_focus_clear_many(*buttons)

    def _build_connection_section(self, content_layout):
        self.connection_group, connection_layout, self.connection_group_title_label = self.create_section_card()
        content_layout.addWidget(self.connection_group)

        self.connection_intro_label = QLabel()
        self.connection_intro_label.setObjectName("SectionIntroLabel")
        self.connection_intro_label.setWordWrap(True)
        connection_layout.addWidget(self.connection_intro_label)

        selector_shell = QFrame()
        selector_shell.setObjectName("InlinePanel")
        selector_layout = QHBoxLayout(selector_shell)
        selector_layout.setContentsMargins(14, 14, 14, 14)
        selector_layout.setSpacing(10)

        self.profile_selector_label = QLabel()
        self.profile_selector_label.setObjectName("FieldLabel")
        self.profile_combo = ScrollSafeComboBox()
        self.profile_combo.currentTextChanged.connect(self.on_profile_selected)
        self.new_profile_button = self.create_button(self.create_new_profile, accent=False, compact=True)
        self.delete_profile_button = self.create_button(self.delete_current_profile, accent=False, danger=True, compact=True)

        selector_layout.addWidget(self.profile_selector_label)
        selector_layout.addWidget(self.profile_combo, 1)
        selector_layout.addWidget(self.new_profile_button)
        selector_layout.addWidget(self.delete_profile_button)
        connection_layout.addWidget(selector_shell)

        api_grid = QGridLayout()
        api_grid.setHorizontalSpacing(16)
        api_grid.setVerticalSpacing(10)
        api_grid.setColumnStretch(0, 1)
        api_grid.setColumnStretch(1, 1)
        connection_layout.addLayout(api_grid)

        self.profile_name_label = QLabel()
        self.profile_name_edit = QLineEdit()
        self.provider_label = QLabel()
        self.provider_combo = ScrollSafeComboBox()
        self.provider_combo.currentTextChanged.connect(self.on_provider_selected)
        self.base_url_label = QLabel()
        self.base_url_edit = QLineEdit()
        self.model_label = QLabel()
        self.model_combo = ScrollSafeComboBox()
        self.model_combo.setEditable(True)
        self.retry_count_label = QLabel()
        self.retry_count_spin = ScrollSafeSpinBox()
        self.retry_count_spin.setRange(0, 10)
        self.retry_interval_label = QLabel()
        self.retry_interval_spin = ScrollSafeDoubleSpinBox()
        self.retry_interval_spin.setRange(0, 60)
        self.retry_interval_spin.setSingleStep(0.5)

        api_grid.addWidget(self.create_field_block(self.profile_name_label, self.profile_name_edit), 0, 0)
        api_grid.addWidget(self.create_field_block(self.provider_label, self.provider_combo), 0, 1)
        api_grid.addWidget(self.create_field_block(self.base_url_label, self.base_url_edit), 1, 0, 1, 2)
        api_grid.addWidget(self.create_field_block(self.model_label, self.model_combo), 2, 0, 1, 2)
        api_grid.addWidget(self.create_field_block(self.retry_count_label, self.retry_count_spin), 3, 0)
        api_grid.addWidget(self.create_field_block(self.retry_interval_label, self.retry_interval_spin), 3, 1)
        api_grid.addWidget(self._build_api_keys_panel(), 4, 0, 1, 2)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        runtime_actions_shell = QFrame()
        runtime_actions_shell.setObjectName("ActionClusterPanel")
        runtime_actions_layout = QHBoxLayout(runtime_actions_shell)
        runtime_actions_layout.setContentsMargins(0, 0, 0, 0)
        runtime_actions_layout.setSpacing(8)

        self.fetch_models_button = self.create_button(self.fetch_models, accent=False, compact=True)
        self.test_button = self.create_button(self.test_profile, accent=False, compact=True)
        self.cancel_button = self.create_button(self.cancel_background_operation, accent=False, warning=True, compact=True)
        self.discard_changes_button = self.create_button(self.discard_unsaved_changes, secondary=True, compact=True)
        self.save_button = self.create_button(self.save_settings, accent=True, compact=True)

        for button in [self.fetch_models_button, self.test_button, self.cancel_button]:
            runtime_actions_layout.addWidget(button)

        save_actions_shell = QFrame()
        save_actions_shell.setObjectName("CommitPanel")
        save_actions_layout = QHBoxLayout(save_actions_shell)
        save_actions_layout.setContentsMargins(0, 0, 0, 0)
        save_actions_layout.setSpacing(6)
        self.discard_changes_button.setProperty("commitSecondary", True)
        save_actions_layout.addWidget(self.discard_changes_button)
        self.save_button.setProperty("commit", True)
        save_actions_layout.addWidget(self.save_button)

        action_row.addWidget(runtime_actions_shell)
        action_row.addStretch(1)
        action_row.addWidget(save_actions_shell)
        connection_layout.addLayout(action_row)

        self.api_validation_label = QLabel()
        self.api_validation_label.setObjectName("ValidationLabel")
        self.api_validation_label.setWordWrap(True)
        self.api_validation_label.hide()
        connection_layout.addWidget(self.api_validation_label)

    def _register_multiline_editor_surface(self, editor: QPlainTextEdit, surface: QFrame) -> None:
        if not hasattr(self, "_multiline_editor_surfaces"):
            self._multiline_editor_surfaces = {}
        self._multiline_editor_surfaces[editor] = surface

    def _build_multiline_editor_surface(self, *, minimum_height: int) -> tuple[QFrame, QPlainTextEdit]:
        surface = QFrame()
        surface.setObjectName("MultiLineFieldSurface")
        surface.setProperty("focused", False)
        surface.setProperty("invalid", False)
        layout = QVBoxLayout(surface)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        editor = ImeAwarePlainTextEdit()
        editor.setObjectName("FramelessFieldEditor")
        editor.setFrameShape(QFrame.NoFrame)
        editor.setMinimumHeight(minimum_height)
        editor.document().setDocumentMargin(10)
        editor.installEventFilter(self)
        layout.addWidget(editor)
        self._register_multiline_editor_surface(editor, surface)
        return surface, editor

    def _build_api_keys_panel(self):
        api_keys_shell = QFrame()
        api_keys_shell.setObjectName("InlinePanel")
        api_keys_shell.setProperty("panelRole", "apiKeys")
        self.api_keys_shell = api_keys_shell
        api_keys_layout = QVBoxLayout(api_keys_shell)
        api_keys_layout.setContentsMargins(14, 14, 14, 14)
        api_keys_layout.setSpacing(10)

        api_keys_header = QHBoxLayout()
        api_keys_header.setSpacing(8)
        self.api_keys_label_row = QLabel()
        self.api_keys_label_row.setObjectName("FieldLabel")
        self.api_keys_toggle_button = self.create_button(self.toggle_api_keys_visibility, accent=False, compact=True)
        self.api_keys_toggle_button.setProperty("apiKeysRevealState", "idle")
        self.api_keys_toggle_button.setMinimumWidth(118)
        api_keys_header.addWidget(self.api_keys_label_row)
        api_keys_header.addStretch(1)
        api_keys_header.addWidget(self.api_keys_toggle_button)

        self.api_keys_editor_surface, self.api_keys_edit = self._build_multiline_editor_surface(minimum_height=104)
        self.api_keys_edit.setProperty("concealed", False)
        self.api_keys_editor_surface.setProperty("concealed", False)
        self.api_keys_editor_surface.installEventFilter(self)
        self.api_keys_edit.viewport().installEventFilter(self)
        self.api_keys_edit.textChanged.connect(self.on_api_keys_text_changed)
        self.api_keys_hint = QLabel()
        self.api_keys_hint.setObjectName("HintLabel")
        self.api_keys_hint.setWordWrap(True)

        api_keys_layout.addLayout(api_keys_header)
        api_keys_layout.addWidget(self.api_keys_editor_surface)
        api_keys_layout.addWidget(self.api_keys_hint)
        return api_keys_shell

    def _build_update_check_panel(self):
        update_shell = QFrame()
        update_shell.setObjectName("InlinePanel")
        update_shell.setProperty("panelRole", "updateCheck")
        update_layout = QVBoxLayout(update_shell)
        update_layout.setContentsMargins(14, 14, 14, 14)
        update_layout.setSpacing(10)

        update_row = QHBoxLayout()
        update_row.setSpacing(10)
        self.check_updates_on_startup_checkbox = QCheckBox()
        self.check_updates_on_startup_checkbox.setChecked(bool(getattr(self.config, "check_updates_on_startup", False)))
        self.check_updates_now_button = self.create_button(self.check_for_updates_now, secondary=True, compact=True)
        update_row.addWidget(self.check_updates_on_startup_checkbox, 1)
        update_row.addWidget(self.check_updates_now_button)

        self.update_check_hint_label = QLabel()
        self.update_check_hint_label.setObjectName("HintLabel")
        self.update_check_hint_label.setWordWrap(True)
        self.update_check_hint_label.setOpenExternalLinks(True)
        self.update_check_hint_label.setTextFormat(Qt.AutoText)
        self.update_check_hint_label.setTextInteractionFlags(Qt.TextBrowserInteraction)

        update_layout.addLayout(update_row)
        update_layout.addWidget(self.update_check_hint_label)
        return update_shell

    def _build_translation_section(self, content_layout):
        self.translation_group, translation_layout, self.translation_group_title_label = self.create_section_card()
        content_layout.addWidget(self.translation_group)

        self.translation_intro_label = QLabel()
        self.translation_intro_label.setObjectName("SectionIntroLabel")
        self.translation_intro_label.setWordWrap(True)
        translation_layout.addWidget(self.translation_intro_label)

        translation_grid = QGridLayout()
        translation_grid.setHorizontalSpacing(16)
        translation_grid.setVerticalSpacing(10)
        translation_grid.setColumnStretch(0, 1)
        translation_grid.setColumnStretch(1, 1)
        translation_layout.addLayout(translation_grid)

        self.target_language_label = QLabel()
        self.target_language_edit = QLineEdit(self.config.target_language)
        self.mode_label = QLabel()
        self.mode_combo = ScrollSafeComboBox()
        self.mode_combo.addItems(["book_lr", "web_ud"])
        self.hotkey_label = QLabel()
        self.hotkey_input_shell, self.hotkey_edit, self.hotkey_record_button = self._build_hotkey_input(
            self.config.hotkey,
            lambda: self.start_hotkey_recording("capture"),
        )
        self.selection_hotkey_label = QLabel()
        self.selection_hotkey_input_shell, self.selection_hotkey_edit, self.selection_hotkey_record_button = self._build_hotkey_input(
            getattr(self.config, "selection_hotkey", ""),
            lambda: self.start_hotkey_recording("selection"),
        )
        self.input_hotkey_label = QLabel()
        self.input_hotkey_input_shell, self.input_hotkey_edit, self.input_hotkey_record_button = self._build_hotkey_input(
            getattr(self.config, "input_hotkey", ""),
            lambda: self.start_hotkey_recording("input"),
        )

        translation_grid.addWidget(self.create_field_block(self.target_language_label, self.target_language_edit), 0, 0)
        translation_grid.addWidget(self.create_field_block(self.mode_label, self.mode_combo), 0, 1)
        translation_grid.addWidget(self.create_field_block(self.hotkey_label, self.hotkey_input_shell), 1, 0, 1, 2)
        translation_grid.addWidget(self.create_field_block(self.selection_hotkey_label, self.selection_hotkey_input_shell), 2, 0, 1, 2)
        translation_grid.addWidget(self.create_field_block(self.input_hotkey_label, self.input_hotkey_input_shell), 3, 0, 1, 2)

        self.reading_validation_label = QLabel()
        self.reading_validation_label.setObjectName("ValidationLabel")
        self.reading_validation_label.setWordWrap(True)
        self.reading_validation_label.hide()
        translation_layout.addWidget(self.reading_validation_label)

        prompt_selector_shell = QFrame()
        prompt_selector_shell.setObjectName("InlinePanel")
        prompt_selector_layout = QHBoxLayout(prompt_selector_shell)
        prompt_selector_layout.setContentsMargins(14, 14, 14, 14)
        prompt_selector_layout.setSpacing(10)
        self.prompt_preset_selector_label = QLabel()
        self.prompt_preset_selector_label.setObjectName("FieldLabel")
        self.prompt_preset_combo = ScrollSafeComboBox()
        self.prompt_preset_combo.currentTextChanged.connect(self.on_prompt_preset_selected)
        self.new_prompt_preset_button = self.create_button(self.create_new_prompt_preset, accent=False, compact=True)
        self.delete_prompt_preset_button = self.create_button(self.delete_current_prompt_preset, accent=False, danger=True, compact=True)
        prompt_selector_layout.addWidget(self.prompt_preset_selector_label)
        prompt_selector_layout.addWidget(self.prompt_preset_combo, 1)
        prompt_selector_layout.addWidget(self.new_prompt_preset_button)
        prompt_selector_layout.addWidget(self.delete_prompt_preset_button)
        translation_layout.addWidget(prompt_selector_shell)

        self.prompt_preset_name_label = QLabel()
        self.prompt_preset_name_edit = QLineEdit()
        translation_layout.addWidget(self.create_field_block(self.prompt_preset_name_label, self.prompt_preset_name_edit))

        self.image_prompt_label = QLabel()
        self.image_prompt_surface, self.image_prompt_edit = self._build_multiline_editor_surface(minimum_height=120)
        translation_layout.addWidget(self.create_field_block(self.image_prompt_label, self.image_prompt_surface))

        self.text_prompt_label = QLabel()
        self.text_prompt_surface, self.text_prompt_edit = self._build_multiline_editor_surface(minimum_height=120)
        translation_layout.addWidget(self.create_field_block(self.text_prompt_label, self.text_prompt_surface))

        self.prompt_hint_label = QLabel()
        self.prompt_hint_label.setObjectName("HintLabel")
        self.prompt_hint_label.setWordWrap(True)
        translation_layout.addWidget(self.prompt_hint_label)

        self.prompt_validation_label = QLabel()
        self.prompt_validation_label.setObjectName("ValidationLabel")
        self.prompt_validation_label.setWordWrap(True)
        self.prompt_validation_label.hide()
        translation_layout.addWidget(self.prompt_validation_label)

    def _build_hotkey_input(self, initial_text: str, callback):
        shell = QWidget()
        layout = QHBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        edit = QLineEdit(initial_text)
        edit.installEventFilter(self)
        button = self.create_button(callback, accent=False, compact=True)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        return shell, edit, button

    def _build_advanced_section(self, content_layout):
        self.advanced_group, advanced_layout, self.advanced_group_title_label = self.create_section_card()
        content_layout.addWidget(self.advanced_group)

        self.advanced_intro_label = QLabel()
        self.advanced_intro_label.setObjectName("SectionIntroLabel")
        self.advanced_intro_label.setWordWrap(True)
        advanced_layout.addWidget(self.advanced_intro_label)

        self.advanced_toggle_button = self.create_button(self.toggle_advanced_section, accent=False, compact=True)
        advanced_layout.addWidget(self.advanced_toggle_button, alignment=Qt.AlignLeft)

        self.advanced_content = QWidget()
        advanced_content_layout = QVBoxLayout(self.advanced_content)
        advanced_content_layout.setContentsMargins(0, 0, 0, 0)
        advanced_content_layout.setSpacing(14)
        advanced_grid = QGridLayout()
        advanced_grid.setHorizontalSpacing(16)
        advanced_grid.setVerticalSpacing(10)
        advanced_grid.setColumnStretch(0, 1)
        advanced_grid.setColumnStretch(1, 1)
        advanced_content_layout.addLayout(advanced_grid)

        self.ui_language_label = QLabel()
        self.ui_language_combo = ScrollSafeComboBox()
        self.ui_language_combo.addItems(["zh-TW", "zh-CN", "en"])
        self.ui_language_combo.currentTextChanged.connect(self.on_ui_language_changed)
        self.overlay_font_label = QLabel()
        self.overlay_font_combo = ScrollSafeFontComboBox()
        self.overlay_font_combo.setCurrentFont(QFont(self.config.overlay_font_family))
        self.overlay_font_size_label = QLabel()
        self.overlay_font_size_spin = ScrollSafeSpinBox()
        self.overlay_font_size_spin.setRange(10, 32)
        self.overlay_font_size_spin.setValue(self.config.overlay_font_size)
        self.temperature_label = QLabel()
        self.temperature_spin = ScrollSafeDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.overlay_width_label = QLabel()
        self.overlay_width_spin = ScrollSafeSpinBox()
        self.overlay_width_spin.setRange(240, 1600)
        self.overlay_height_label = QLabel()
        self.overlay_height_spin = ScrollSafeSpinBox()
        self.overlay_height_spin.setRange(220, 1600)
        self.overlay_margin_label = QLabel()
        self.overlay_margin_spin = ScrollSafeSpinBox()
        self.overlay_margin_spin.setRange(8, 120)
        self.overlay_auto_expand_top_margin_label = QLabel()
        self.overlay_auto_expand_top_margin_spin = ScrollSafeSpinBox()
        self.overlay_auto_expand_top_margin_spin.setRange(0, 200)
        self.overlay_auto_expand_top_margin_spin.setValue(int(getattr(self.config, "overlay_auto_expand_top_margin", 42)))
        self.overlay_auto_expand_bottom_margin_label = QLabel()
        self.overlay_auto_expand_bottom_margin_spin = ScrollSafeSpinBox()
        self.overlay_auto_expand_bottom_margin_spin.setRange(8, 200)
        self.overlay_auto_expand_bottom_margin_spin.setValue(int(getattr(self.config, "overlay_auto_expand_bottom_margin", 24)))
        self.toast_duration_label = QLabel()
        self.toast_duration_spin = ScrollSafeDoubleSpinBox()
        self.toast_duration_spin.setRange(0.0, 10.0)
        self.toast_duration_spin.setSingleStep(0.1)
        self.toast_duration_spin.setValue(float(getattr(self.config, "toast_duration_seconds", 1.5)))
        self.stream_responses_checkbox = QCheckBox()
        self.stream_responses_checkbox.setChecked(bool(getattr(self.config, "stream_responses", True)))
        self.stream_responses_hint_label = QLabel()
        self.stream_responses_hint_label.setObjectName("HintLabel")
        self.stream_responses_hint_label.setWordWrap(True)
        self.close_to_tray_on_close_checkbox = QCheckBox()
        self.close_to_tray_on_close_checkbox.setChecked(bool(getattr(self.config, "close_to_tray_on_close", False)))

        advanced_grid.addWidget(self.create_field_block(self.ui_language_label, self.ui_language_combo), 0, 0)
        advanced_grid.addWidget(self.create_field_block(self.overlay_font_label, self.overlay_font_combo), 0, 1)
        advanced_grid.addWidget(self.create_field_block(self.overlay_font_size_label, self.overlay_font_size_spin), 1, 0)
        advanced_grid.addWidget(self.create_field_block(self.temperature_label, self.temperature_spin), 1, 1)
        advanced_grid.addWidget(self.create_field_block(self.overlay_width_label, self.overlay_width_spin), 2, 0)
        advanced_grid.addWidget(self.create_field_block(self.overlay_height_label, self.overlay_height_spin), 2, 1)
        advanced_grid.addWidget(self.create_field_block(self.overlay_auto_expand_top_margin_label, self.overlay_auto_expand_top_margin_spin), 3, 0)
        advanced_grid.addWidget(self.create_field_block(self.overlay_auto_expand_bottom_margin_label, self.overlay_auto_expand_bottom_margin_spin), 3, 1)
        advanced_grid.addWidget(self.create_field_block(self.overlay_margin_label, self.overlay_margin_spin), 4, 0)
        advanced_grid.addWidget(self.create_field_block(self.toast_duration_label, self.toast_duration_spin), 4, 1)
        advanced_content_layout.addWidget(self.stream_responses_checkbox)
        advanced_content_layout.addWidget(self.stream_responses_hint_label)
        advanced_content_layout.addWidget(self.close_to_tray_on_close_checkbox)
        self.advanced_hint_label = QLabel()
        self.advanced_hint_label.setObjectName("HintLabel")
        self.advanced_hint_label.setWordWrap(True)
        advanced_content_layout.addWidget(self.advanced_hint_label)
        advanced_content_layout.addWidget(self._build_update_check_panel())
        advanced_layout.addWidget(self.advanced_content)
        self.advanced_section_expanded = True
        self.set_advanced_section_expanded(False)

    def _connect_settings_form_signals(self):
        self.profile_name_edit.textChanged.connect(self.on_form_input_changed)
        self.base_url_edit.textChanged.connect(self.on_form_input_changed)
        self.model_combo.currentTextChanged.connect(self.on_form_input_changed)
        self.prompt_preset_name_edit.textChanged.connect(self.on_form_input_changed)
        self.image_prompt_edit.textChanged.connect(self.on_form_input_changed)
        self.text_prompt_edit.textChanged.connect(self.on_form_input_changed)
        self.target_language_edit.textChanged.connect(self.on_form_input_changed)
        self.hotkey_edit.textChanged.connect(self.on_form_input_changed)
        self.selection_hotkey_edit.textChanged.connect(self.on_form_input_changed)
        self.input_hotkey_edit.textChanged.connect(self.on_form_input_changed)
        self.mode_combo.currentTextChanged.connect(self.on_form_input_changed)
        self.ui_language_combo.currentTextChanged.connect(self.on_form_input_changed)
        self.overlay_font_combo.currentFontChanged.connect(self.on_form_input_changed)
        self.overlay_font_size_spin.valueChanged.connect(self.on_form_input_changed)
        self.retry_count_spin.valueChanged.connect(self.on_form_input_changed)
        self.temperature_spin.valueChanged.connect(self.on_form_input_changed)
        self.overlay_width_spin.valueChanged.connect(self.on_form_input_changed)
        self.overlay_width_spin.valueChanged.connect(self.handle_overlay_width_setting_changed)
        self.overlay_height_spin.valueChanged.connect(self.on_form_input_changed)
        self.overlay_margin_spin.valueChanged.connect(self.on_form_input_changed)
        self.overlay_auto_expand_top_margin_spin.valueChanged.connect(self.on_form_input_changed)
        self.overlay_auto_expand_bottom_margin_spin.valueChanged.connect(self.on_form_input_changed)
        self.toast_duration_spin.valueChanged.connect(self.on_form_input_changed)
        self.toast_duration_spin.valueChanged.connect(self.handle_toast_duration_changed)
        self.check_updates_on_startup_checkbox.stateChanged.connect(self.on_form_input_changed)
        self.check_updates_on_startup_checkbox.stateChanged.connect(self.on_update_check_preference_changed)
        self.stream_responses_checkbox.stateChanged.connect(self.on_form_input_changed)
        self.close_to_tray_on_close_checkbox.stateChanged.connect(self.on_form_input_changed)
        self.retry_interval_spin.valueChanged.connect(self.on_form_input_changed)
