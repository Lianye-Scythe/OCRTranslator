from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QFontComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QApplication,
    QWidget,
)

from ..app_metadata import APP_LICENSE_NAME, APP_VERSION, AUTHOR_NAME_EN, AUTHOR_NAME_ZH, REPOSITORY_NAME, REPOSITORY_URL
from .app_icons import load_app_icon
from .style_utils import load_style_sheet
from .theme_tokens import color, qcolor, set_theme_mode


class ScrollSafeComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):
        if self.hasFocus() or self.view().isVisible():
            super().wheelEvent(event)
        else:
            event.ignore()


class ScrollSafeFontComboBox(QFontComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):
        if self.hasFocus() or self.view().isVisible():
            super().wheelEvent(event)
        else:
            event.ignore()


class ScrollSafeSpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class ScrollSafeDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class MainWindowLayoutMixin:
    def build_ui(self):
        self.setWindowTitle(f"{self.tr('window_title')} v{APP_VERSION}")
        self.setWindowIcon(self.icon)
        self.resize(1080, 740)
        self.setMinimumSize(880, 660)
        self.setFocusPolicy(Qt.StrongFocus)
        no_shadow_hint = getattr(Qt, "NoDropShadowWindowHint", getattr(getattr(Qt, "WindowType", object), "NoDropShadowWindowHint", None))
        if no_shadow_hint is not None:
            self.setWindowFlag(no_shadow_hint, True)

        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)

        shell = QHBoxLayout(root)
        shell.setContentsMargins(18, 18, 18, 16)
        shell.setSpacing(16)

        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setObjectName("SidebarScrollArea")
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sidebar_scroll.setFrameShape(QFrame.NoFrame)
        self.sidebar_scroll.setMinimumWidth(280)
        self.sidebar_scroll.setMaximumWidth(360)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.sidebar_scroll.setWidget(self.sidebar)

        sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout = sidebar_layout
        sidebar_layout.setContentsMargins(16, 18, 16, 16)
        sidebar_layout.setSpacing(10)
        sidebar_layout.setSizeConstraint(QLayout.SetMinimumSize)

        self.brand_block = QFrame()
        self.brand_block.setObjectName("BrandBlock")
        self.brand_block.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        brand_layout = QVBoxLayout(self.brand_block)
        brand_layout.setContentsMargins(6, 0, 10, 0)
        brand_layout.setSpacing(4)

        self.title_label = QLabel()
        self.title_label.setObjectName("BrandTitle")
        self.title_label.setWordWrap(True)
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("BrandSubtitle")
        self.subtitle_label.setWordWrap(True)
        brand_layout.addWidget(self.title_label)
        brand_layout.addWidget(self.subtitle_label)
        sidebar_layout.addWidget(self.brand_block)

        self.navigation_label = QLabel()
        self.navigation_label.setObjectName("SidebarCaption")
        self.navigation_label.setWordWrap(True)
        sidebar_layout.addSpacing(14)
        sidebar_layout.addWidget(self.navigation_label)

        self.nav_settings_button = QPushButton()
        self.nav_settings_button.setObjectName("NavButton")
        self.nav_settings_button.setCheckable(True)
        self.nav_settings_button.clicked.connect(lambda: self.switch_page(0))
        self.nav_monitor_button = QPushButton()
        self.nav_monitor_button.setObjectName("NavButton")
        self.nav_monitor_button.setCheckable(True)
        self.nav_monitor_button.clicked.connect(lambda: self.switch_page(1))
        sidebar_layout.addWidget(self.nav_settings_button)
        sidebar_layout.addWidget(self.nav_monitor_button)

        sidebar_layout.addSpacing(24)

        self.quick_actions_label = QLabel()
        self.quick_actions_label.setObjectName("SidebarCaption")
        self.quick_actions_label.setWordWrap(True)
        sidebar_layout.addWidget(self.quick_actions_label)

        self.hero_capture_button = self.create_button(self.start_selection)
        self.hero_manual_input_button = self.create_button(self.open_prompt_input_dialog, secondary=True)
        self.hero_manual_input_button.setProperty("sidebarHeroTonal", True)
        self.hero_tray_button = self.create_button(self.minimize_to_tray, accent=False, compact=True)
        self.hero_tray_button.setEnabled(False)
        sidebar_layout.addWidget(self.hero_capture_button)
        sidebar_layout.addWidget(self.hero_manual_input_button)
        sidebar_layout.addWidget(self.hero_tray_button)
        sidebar_layout.addSpacing(16)
        sidebar_layout.addStretch(1)

        self.hint_card = QFrame()
        self.hint_card.setObjectName("HintCard")
        hint_layout = QVBoxLayout(self.hint_card)
        hint_layout.setContentsMargins(6, 0, 10, 0)
        hint_layout.setSpacing(8)
        self.hint_title_label = QLabel()
        self.hint_title_label.setObjectName("HintTitleLabel")
        self.hint_title_label.setWordWrap(True)
        self.hint_label = QLabel()
        self.hint_label.setObjectName("HintLabel")
        self.hint_label.setWordWrap(True)
        self.hint_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        hint_layout.addWidget(self.hint_title_label)
        hint_layout.addWidget(self.hint_label)
        sidebar_layout.addWidget(self.hint_card)

        self.about_card = QFrame()
        self.about_card.setObjectName("AboutCard")
        about_layout = QVBoxLayout(self.about_card)
        about_layout.setContentsMargins(6, 0, 10, 0)
        about_layout.setSpacing(8)
        self.about_title_label = QLabel()
        self.about_title_label.setObjectName("AboutTitleLabel")
        self.about_title_label.setWordWrap(True)
        self.about_meta_label = QLabel()
        self.about_meta_label.setObjectName("AboutMetaLabel")
        self.about_meta_label.setWordWrap(True)
        self.about_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.about_meta_label.setOpenExternalLinks(True)
        self.about_meta_label.setTextFormat(Qt.RichText)
        self.about_meta_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        about_layout.addWidget(self.about_title_label)
        about_layout.addWidget(self.about_meta_label)
        sidebar_layout.addWidget(self.about_card)

        shell.addWidget(self.sidebar_scroll)

        content_shell_layout = QVBoxLayout()
        content_shell_layout.setContentsMargins(0, 0, 0, 0)
        content_shell_layout.setSpacing(0)
        shell.addLayout(content_shell_layout, 1)

        self.workspace_surface = QFrame()
        self.workspace_surface.setObjectName("WorkspaceSurface")
        workspace_layout = QVBoxLayout(self.workspace_surface)
        workspace_layout.setContentsMargins(18, 14, 18, 14)
        workspace_layout.setSpacing(10)
        self.refresh_workspace_shadow()
        content_shell_layout.addWidget(self.workspace_surface, 1)

        self.header_card = QFrame()
        self.header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(self.header_card)
        header_layout.setContentsMargins(22, 20, 22, 12)
        header_layout.setSpacing(16)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(0)
        self.page_title_label = QLabel()
        self.page_title_label.setObjectName("PageTitleLabel")
        self.page_subtitle_label = QLabel()
        self.page_subtitle_label.setObjectName("PageSubtitleLabel")
        self.page_subtitle_label.setWordWrap(True)
        header_text_layout.addWidget(self.page_title_label)
        header_text_layout.addSpacing(4)
        header_text_layout.addWidget(self.page_subtitle_label)
        header_text_layout.addSpacing(8)
        self.page_context_label = QLabel()
        self.page_context_label.setObjectName("PageContextLabel")
        self.page_context_label.setWordWrap(True)
        self.page_context_label.setTextFormat(Qt.RichText)
        header_text_layout.addWidget(self.page_context_label)
        header_layout.addLayout(header_text_layout, 1)

        self.theme_mode_switch = self.create_theme_mode_switch()
        header_layout.addWidget(self.theme_mode_switch, alignment=Qt.AlignTop)

        workspace_layout.addWidget(self.header_card)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("PageStack")
        workspace_layout.addWidget(self.page_stack, 1)

        self.settings_tab = QWidget()
        self.settings_tab.setObjectName("SettingsTab")
        self.monitor_tab = QWidget()
        self.monitor_tab.setObjectName("MonitorTab")
        self.page_stack.addWidget(self.settings_tab)
        self.page_stack.addWidget(self.monitor_tab)

        self._build_settings_tab()
        self._build_monitor_tab()

        self.status_label = QLabel()
        self.status_label.setObjectName("StatusLabel")
        workspace_layout.addWidget(self.status_label)

        self.switch_page(0)


    def _build_monitor_tab(self):
        layout = QHBoxLayout(self.monitor_tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(16)

        self.preview_group, preview_layout, self.preview_group_title_label = self.create_section_card(role="monitor")
        preview_header = QHBoxLayout()
        preview_header.setSpacing(8)
        preview_header.addWidget(self.preview_group_title_label)
        preview_header.addStretch(1)
        self.preview_capture_button = self.create_button(self.start_selection, secondary=True, compact=True)
        preview_header.addWidget(self.preview_capture_button)
        preview_layout.insertLayout(0, preview_header)
        layout.addWidget(self.preview_group, 3)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.preview_label.setMinimumHeight(280)
        self.preview_label.setObjectName("PreviewViewport")
        self.preview_label.setTextFormat(Qt.PlainText)
        preview_layout.addWidget(self.preview_label)

        self.log_group, log_layout, self.log_group_title_label = self.create_section_card(role="monitor")
        log_header = QHBoxLayout()
        log_header.setSpacing(8)
        log_header.addWidget(self.log_group_title_label)
        log_header.addStretch(1)
        self.clear_logs_button = self.create_button(self.clear_logs, accent=False, compact=True)
        self.export_logs_button = self.create_button(self.export_logs, secondary=True, compact=True)
        log_header.addWidget(self.export_logs_button)
        log_header.addWidget(self.clear_logs_button)
        log_layout.insertLayout(0, log_header)
        layout.addWidget(self.log_group, 2)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("LogText")
        self.log_text.setMinimumHeight(280)
        self.log_text.setPlaceholderText("")
        log_layout.addWidget(self.log_text)

    def apply_styles(self):
        theme_name = set_theme_mode(self.current_theme_mode() if hasattr(self, "current_theme_mode") else getattr(self.config, "theme_mode", "system"))
        self.setStyleSheet(load_style_sheet("main_window.qss", theme_name=theme_name))
        overlay = self.existing_translation_overlay() if hasattr(self, "existing_translation_overlay") else None
        if overlay is not None:
            overlay.apply_styles()
        if hasattr(self, "selection_overlay"):
            self.selection_overlay.apply_theme()
        if hasattr(self, "refresh_workspace_shadow"):
            self.refresh_workspace_shadow()
        self.icon = self.create_app_icon()
        self.setWindowIcon(self.icon)
        app = QApplication.instance()
        if app:
            app.setWindowIcon(self.icon)
        if hasattr(self, "tray_service"):
            self.tray_service.apply_styles()
            self.tray_service.icon = self.icon
        if hasattr(self, "toast_service"):
            self.toast_service.widget.apply_styles()
            self.toast_service.reposition()
        if getattr(self, "tray", None):
            self.tray.setIcon(self.icon)

    def apply_language(self):
        self.apply_styles()
        self.setWindowTitle(f"{self.tr('window_title')} v{APP_VERSION}[*]")
        self.title_label.setText(self.tr("title"))
        self.subtitle_label.setText(self.tr("subtitle"))
        self.update_sidebar_width_for_language()
        self.navigation_label.setText(self.tr("navigation"))
        self.quick_actions_label.setText(self.tr("sidebar_start_here"))
        self.hero_capture_button.setText(self.tr("start_capture"))
        self.hero_manual_input_button.setText(self.tr("open_manual_input"))
        self.hero_tray_button.setText(self.tr("minimize_to_tray"))
        self.nav_settings_button.setText(self.tr("tab_settings"))
        self.nav_monitor_button.setText(self.tr("tab_monitor"))
        self.hint_title_label.setText(self.tr("sidebar_hint_title"))
        self.hint_label.setText(self.tr("hint"))
        self.about_title_label.setText(self.tr("sidebar_about_title"))
        self.about_meta_label.setText(self.build_about_meta_markup())
        self.connection_group_title_label.setText(self.tr("section_connection"))
        self.connection_intro_label.setText(self.tr("section_connection_intro"))
        self.translation_group_title_label.setText(self.tr("section_translation"))
        self.translation_intro_label.setText(self.tr("section_translation_intro"))
        self.advanced_group_title_label.setText(self.tr("section_advanced"))
        self.advanced_intro_label.setText(self.tr("section_advanced_intro"))
        self.preview_group_title_label.setText(self.tr("preview_panel"))
        self.log_group_title_label.setText(self.tr("activity_panel"))
        self.prompt_hint_label.setText(self.tr("prompt_hint"))
        self.advanced_hint_label.setText(self.tr("runtime_settings_hint"))
        self.preview_capture_button.setText(self.tr("start_capture"))
        self.clear_logs_button.setText(self.tr("clear_logs"))
        if not self.preview_pixmap:
            self.preview_label.setText(self.tr("preview_placeholder"))
        self.profile_selector_label.setText(self.tr("profile"))
        self.new_profile_button.setText(self.tr("new_profile"))
        self.delete_profile_button.setText(self.tr("delete_profile"))
        self.profile_name_label.setText(self.tr("profile_name"))
        self.provider_label.setText(self.tr("provider"))
        self.prompt_preset_selector_label.setText(self.tr("prompt_preset"))
        self.new_prompt_preset_button.setText(self.tr("new_prompt_preset"))
        self.delete_prompt_preset_button.setText(self.tr("delete_prompt_preset"))
        self.prompt_preset_name_label.setText(self.tr("prompt_preset_name"))
        self.base_url_label.setText(self.tr("base_url"))
        self.model_label.setText(self.tr("model"))
        self.retry_count_label.setText(self.tr("retry_count"))
        self.temperature_label.setText(self.tr("temperature"))
        self.overlay_width_label.setText(self.tr("overlay_width"))
        self.overlay_height_label.setText(self.tr("overlay_height"))
        self.overlay_margin_label.setText(self.tr("overlay_margin"))
        self.overlay_auto_expand_top_margin_label.setText(self.tr("overlay_auto_expand_top_margin"))
        self.overlay_auto_expand_bottom_margin_label.setText(self.tr("overlay_auto_expand_bottom_margin"))
        self.toast_duration_label.setText(self.tr("toast_duration_seconds"))
        self.retry_interval_label.setText(self.tr("retry_interval"))
        self.target_language_label.setText(self.tr("target_language"))
        self.ui_language_label.setText(self.tr("ui_language"))
        self.theme_mode_switch.setToolTip(self.tr("theme_mode"))
        self.theme_mode_switch.setAccessibleName(self.tr("theme_mode"))
        self.hotkey_label.setText(self.tr("capture_hotkey"))
        self.selection_hotkey_label.setText(self.tr("selection_hotkey"))
        self.input_hotkey_label.setText(self.tr("input_hotkey"))
        self.overlay_font_label.setText(self.tr("overlay_font_family"))
        self.overlay_font_size_label.setText(self.tr("overlay_font_size"))
        self.image_prompt_label.setText(self.tr("image_prompt"))
        self.text_prompt_label.setText(self.tr("text_prompt"))
        self.profile_name_edit.setPlaceholderText(self.tr("profile_name_placeholder"))
        self.prompt_preset_name_edit.setPlaceholderText(self.tr("prompt_preset_name_placeholder"))
        self.base_url_edit.setPlaceholderText(self.tr("base_url_placeholder"))
        self.target_language_edit.setPlaceholderText(self.tr("target_language_placeholder"))
        self.hotkey_edit.setPlaceholderText(self.tr("hotkey_placeholder"))
        self.selection_hotkey_edit.setPlaceholderText(self.tr("hotkey_placeholder"))
        self.input_hotkey_edit.setPlaceholderText(self.tr("hotkey_placeholder"))
        active_record_target = getattr(self, "hotkey_record_target", None)
        self.hotkey_record_button.setText(self.tr("recording_hotkey") if active_record_target == "capture" else self.tr("record_hotkey"))
        self.selection_hotkey_record_button.setText(self.tr("recording_hotkey") if active_record_target == "selection" else self.tr("record_hotkey"))
        self.input_hotkey_record_button.setText(self.tr("recording_hotkey") if active_record_target == "input" else self.tr("record_hotkey"))
        if hasattr(self, "refresh_api_keys_editor"):
            self.refresh_api_keys_editor()
        self.image_prompt_edit.setPlaceholderText(self.tr("prompt_template_placeholder"))
        self.text_prompt_edit.setPlaceholderText(self.tr("prompt_template_placeholder"))
        model_line_edit = self.model_combo.lineEdit()
        if model_line_edit:
            model_line_edit.setPlaceholderText(self.tr("model_placeholder"))
        self.preview_capture_button.setToolTip(self.tr("start_capture"))
        self.clear_logs_button.setToolTip(self.tr("clear_logs"))
        self.fetch_models_button.setToolTip(self.tr("fetch_models"))
        self.export_logs_button.setToolTip(self.tr("export_logs"))
        self.test_button.setToolTip(self.tr("test_api"))
        self.cancel_button.setToolTip(self.tr("cancel_request"))
        if hasattr(self, "discard_changes_button"):
            self.discard_changes_button.setToolTip(self.tr("unsaved_changes_discard"))
        self.save_button.setToolTip(self.tr("save_settings"))
        self.check_updates_now_button.setToolTip(self.tr("check_updates_now"))
        self.check_updates_on_startup_checkbox.setToolTip(self.tr("check_updates_on_startup_hint"))
        self.toast_duration_spin.setToolTip(self.tr("toast_duration_hint"))
        self.stream_responses_checkbox.setText(self.tr("stream_responses"))
        self.stream_responses_checkbox.setToolTip(self.tr("stream_responses_hint"))
        self.stream_responses_hint_label.setText(self.tr("stream_responses_hint"))
        self.debug_logging_checkbox.setText(self.tr("debug_logging"))
        self.debug_logging_checkbox.setToolTip(self.tr("debug_logging_hint"))
        self.debug_logging_hint_label.setText(self.tr("debug_logging_hint"))
        self.mode_label.setText(self.tr("display_mode"))
        self.fetch_models_button.setText(self.tr("fetch_models_action"))
        self.test_button.setText(self.tr("test_api_action"))
        self.cancel_button.setText(self.tr("cancel_request_action"))
        if hasattr(self, "discard_changes_button"):
            self.discard_changes_button.setText(self.tr("unsaved_changes_discard_action"))
        self.save_button.setText(self.tr("save_settings_action"))
        self.set_advanced_section_expanded(getattr(self, "advanced_section_expanded", False))
        self.close_to_tray_on_close_checkbox.setText(self.tr("close_to_tray_on_close"))
        self.check_updates_on_startup_checkbox.setText(self.tr("check_updates_on_startup"))
        self.check_updates_now_button.setText(self.tr("check_updates_now_busy") if getattr(self, "update_check_in_progress", False) else self.tr("check_updates_now"))
        self.export_logs_button.setText(self.tr("export_logs"))
        self.update_provider_options()
        self.update_mode_options()
        if hasattr(self, "update_theme_mode_options"):
            self.update_theme_mode_options(self.current_theme_mode() if hasattr(self, "current_theme_mode") else getattr(self.config, "theme_mode", "system"))
        self.refresh_page_header()
        self.refresh_shell_state()
        if hasattr(self, "tray"):
            self.update_tray_texts()
        if hasattr(self, "selection_overlay"):
            self.selection_overlay.set_hint_text(self.tr("selection_hint"))
        overlay = self.existing_translation_overlay() if hasattr(self, "existing_translation_overlay") else None
        if overlay is not None:
            overlay.refresh_language()
        if hasattr(self, "refresh_update_check_ui"):
            self.refresh_update_check_ui()
        self.set_status(self.current_status_key, **self.current_status_kwargs)
        if hasattr(self, "update_action_states"):
            self.update_action_states()
        self.refresh_save_button_emphasis()
        if hasattr(self, "refresh_sidebar_layout"):
            self.refresh_sidebar_layout()
        self.validate_form_inputs()

    def set_advanced_section_expanded(self, expanded: bool):
        self.advanced_section_expanded = bool(expanded)
        if hasattr(self, "advanced_content"):
            self.advanced_content.setVisible(self.advanced_section_expanded)
        if hasattr(self, "advanced_toggle_button"):
            self.advanced_toggle_button.setText(
                self.tr("hide_advanced_settings") if self.advanced_section_expanded else self.tr("show_advanced_settings")
            )

    def toggle_advanced_section(self):
        self.set_advanced_section_expanded(not getattr(self, "advanced_section_expanded", True))

    def switch_page(self, index: int):
        self.page_stack.setCurrentIndex(index)
        self.nav_settings_button.setChecked(index == 0)
        self.nav_monitor_button.setChecked(index == 1)
        if index == 1 and hasattr(self, "refresh_preview_pixmap") and getattr(self, "preview_pixmap", None):
            self.refresh_preview_pixmap()
        self.refresh_page_header()

    def refresh_page_header(self):
        if not hasattr(self, "page_stack"):
            return
        if self.page_stack.currentIndex() == 0:
            self.page_title_label.setText(self.tr("page_settings_title"))
            self.page_subtitle_label.setText(self.tr("page_settings_subtitle"))
        else:
            self.page_title_label.setText(self.tr("page_monitor_title"))
            self.page_subtitle_label.setText(self.tr("page_monitor_subtitle"))

    def refresh_shell_state(self):
        current_mode = self.current_mode() if hasattr(self, "current_mode") else self.config.mode
        current_target_language = self.current_target_language() if hasattr(self, "current_target_language") else self.config.target_language
        current_prompt_preset = self.current_prompt_preset_name() if hasattr(self, "current_prompt_preset_name") else self.config.active_prompt_preset_name
        mode_label = self.tr("mode_book_lr") if current_mode == "book_lr" else self.tr("mode_web_ud")
        summary_plain = self.tr(
            "header_summary",
            profile=self.current_profile_header_label(),
            prompt=current_prompt_preset,
            target=current_target_language,
            mode=mode_label,
            hotkeys=self.build_header_hotkeys_summary(),
        )

        summary_primary_rich = self.tr(
            "header_summary_primary",
            profile=self.format_header_summary_value(self.current_profile_header_label(), prominent=True),
            prompt=self.format_header_summary_value(current_prompt_preset),
            target=self.format_header_summary_value(current_target_language),
            mode=self.format_header_summary_value(mode_label),
        )
        hotkey_rich = self.build_header_hotkeys_summary(rich=True)
        summary_rich = (
            f"<span style='color:{color('muted_fg')};'>"
            f"{summary_primary_rich}"
            "</span>"
            "<br/>"
            f"<span style='color:{color('muted_fg')}; font-size:12px; font-weight:500;'>"
            f"{hotkey_rich}"
            "</span>"
        )
        self.page_context_label.setText(summary_rich)
        self.page_context_label.setToolTip(summary_plain)

    def build_header_hotkeys_summary(self, *, rich: bool = False) -> str:
        value_mapper = (lambda value: self.format_header_summary_value(value, prominent=True)) if rich else str
        capture_text = self.tr("meta_hotkey_capture", value=value_mapper(self.current_hotkey()))
        selection_text = self.tr(
            "meta_hotkey_selection",
            value=value_mapper(self.current_selection_hotkey()),
        )
        input_text = self.tr(
            "meta_hotkey_input",
            value=value_mapper(self.current_input_hotkey()),
        )
        return self.tr(
            "meta_hotkeys",
            capture=capture_text,
            selection=selection_text,
            input=input_text,
        )

    def build_about_meta_markup(self) -> str:
        version_and_license = (
            f"<span style='color:{color('text_secondary')}'>v{APP_VERSION}</span>"
            f"<span style='color:{color('text_tertiary')};'>&nbsp;&nbsp;&nbsp;</span>"
            f"<span style='color:{color('text_secondary')}'>License: {APP_LICENSE_NAME}</span><br/>"
        )
        if self.current_ui_language() == "en":
            return (
                f"{version_and_license}"
                f"<span style='color:{color('subtle_fg')};'>{self.tr('about_author_label')}:</span> "
                f"<span style='color:{color('text_primary')};'>{AUTHOR_NAME_ZH}</span> <span style='color:{color('text_tertiary')};'>/</span> <span style='color:{color('text_primary')};'>{AUTHOR_NAME_EN}</span><br/>"
                f"<span style='color:{color('subtle_fg')};'>{self.tr('about_repo_label')}:</span> "
                f"<a href='{REPOSITORY_URL}' style='color:{color('link')}; text-decoration:none;'>{REPOSITORY_NAME.replace('/', '/&#8203;')}</a>"
            )
        return (
            f"{version_and_license}"
            f"<span style='color:{color('text_secondary')};'>{self.tr('about_author_label')}：</span>"
            f"<span style='color:{color('text_primary')};'>{AUTHOR_NAME_ZH}</span>"
            f" <span style='color:{color('text_tertiary')};'>/</span> "
            f"<span style='color:{color('text_primary')};'>{AUTHOR_NAME_EN}</span><br/>"
            f"<span style='color:{color('text_secondary')};'>{self.tr('about_repo_label')}：</span>"
            f"<a href='{REPOSITORY_URL}' style='color:{color('link')}; text-decoration:none;'>{REPOSITORY_NAME}</a>"
        )

    def update_sidebar_width_for_language(self):
        if not hasattr(self, "sidebar_scroll"):
            return
        if self.current_ui_language() == "en":
            self.sidebar_scroll.setMinimumWidth(300)
            self.sidebar_scroll.setMaximumWidth(376)
            return
        self.sidebar_scroll.setMinimumWidth(280)
        self.sidebar_scroll.setMaximumWidth(360)

    def format_header_summary_value(self, value: str, *, prominent: bool = False) -> str:
        text_color = color("text_primary") if prominent else color("text_secondary")
        font_weight = 700 if prominent else 600
        return (
            f"<span style='color:{text_color}; font-weight:{font_weight};'>"
            f"{escape(str(value))}"
            "</span>"
        )

    def current_profile_header_label(self) -> str:
        profile = self.get_active_profile() if getattr(self.config, "api_profiles", None) else None
        if profile and hasattr(self, "profile_name_edit"):
            return self.profile_name_edit.text().strip() or self.tr("untitled_profile")
        if profile:
            return profile.name
        return self.tr("untitled_profile")

    def create_field_block(self, label_widget, field_widget):
        block = QFrame()
        layout = QVBoxLayout(block)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        label_widget.setObjectName("FieldLabel")
        layout.addWidget(label_widget)
        layout.addWidget(field_widget)
        return block

    def create_theme_mode_switch(self):
        shell = QFrame()
        shell.setObjectName("ThemeModeSwitch")
        shell.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QHBoxLayout(shell)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        self.theme_mode_button_group = QButtonGroup(shell)
        self.theme_mode_button_group.setExclusive(True)
        self.theme_mode_buttons = {}
        icon_font = QFont("Segoe UI Symbol", 12)

        for mode in ("system", "light", "dark"):
            button = QPushButton()
            button.setObjectName("ThemeModeSwitchButton")
            button.setCheckable(True)
            button.setAutoDefault(False)
            button.setFont(icon_font)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.setFixedSize(38, 32)
            button.clicked.connect(lambda _checked=False, value=mode: self.on_theme_mode_changed(value))
            self.theme_mode_button_group.addButton(button)
            self.theme_mode_buttons[mode] = button
            layout.addWidget(button)

        shell.setFixedHeight(38)

        return shell

    def create_section_card(self, *, role: str = "settings"):
        card = QFrame()
        card.setObjectName("SectionCard")
        card.setProperty("sectionRole", role)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(20)
        title_label = QLabel()
        title_label.setObjectName("SectionTitleLabel")
        title_label.setProperty("sectionRole", role)
        layout.addWidget(title_label)
        body_layout = QVBoxLayout()
        body_layout.setSpacing(16)
        layout.addLayout(body_layout)
        return card, body_layout, title_label

    def create_button(self, callback, accent=True, secondary=False, success=False, warning=False, danger=False, compact=False):
        button = QPushButton()
        button.clicked.connect(callback)
        variant = "primary"
        if secondary:
            variant = "secondary"
        elif success:
            variant = "success"
        elif warning:
            variant = "warning"
        elif danger:
            variant = "danger"
        elif not accent:
            variant = "neutral"
        self.set_button_variant(button, variant)
        if compact:
            button.setProperty("compact", True)
        return button

    def set_button_variant(self, button, variant: str):
        if not hasattr(button, "setProperty"):
            return
        button.setProperty("variant", variant)
        if hasattr(button, "style"):
            style = button.style()
            if style:
                style.unpolish(button)
                style.polish(button)
        if hasattr(button, "update"):
            button.update()

    def refresh_save_button_emphasis(self):
        if hasattr(self, "save_button"):
            self.set_button_variant(self.save_button, "primary" if getattr(self, "has_unsaved_changes", False) else "neutral")
        if hasattr(self, "discard_changes_button"):
            self.set_button_variant(self.discard_changes_button, "secondary" if getattr(self, "has_unsaved_changes", False) else "neutral")

    def workspace_shadow_spec(self) -> dict[str, int]:
        theme_name = self.effective_theme_name() if hasattr(self, "effective_theme_name") else "dark"
        if theme_name == "light":
            return {"blur": 12, "y_offset": 1, "alpha": 12}
        return {"blur": 14, "y_offset": 2, "alpha": 18}

    def add_shadow(self, widget, blur=32, y_offset=10, alpha=90, *, theme_name: str | None = None):
        shadow = widget.graphicsEffect() if hasattr(widget, "graphicsEffect") else None
        if not isinstance(shadow, QGraphicsDropShadowEffect):
            shadow = QGraphicsDropShadowEffect(self)
            widget.setGraphicsEffect(shadow)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, y_offset)
        shadow.setColor(qcolor("shadow", alpha=alpha, theme_name=theme_name or (self.effective_theme_name() if hasattr(self, "effective_theme_name") else None)))
        return shadow

    def refresh_workspace_shadow(self):
        if not hasattr(self, "workspace_surface"):
            return
        spec = self.workspace_shadow_spec()
        self.add_shadow(
            self.workspace_surface,
            blur=spec["blur"],
            y_offset=spec["y_offset"],
            alpha=spec["alpha"],
        )

    def refresh_sidebar_layout(self):
        for widget in (self.title_label, self.subtitle_label, self.navigation_label, self.quick_actions_label, self.hint_title_label, self.hint_label, self.about_title_label, self.about_meta_label, self.hint_card, self.about_card, self.sidebar):
            widget.updateGeometry()
        if hasattr(self, "sidebar_layout"):
            self.sidebar_layout.invalidate()
            self.sidebar_layout.activate()
        if hasattr(self, "sidebar_scroll"):
            self.sidebar_scroll.ensureVisible(0, 0, 0, 0)

    def create_app_icon(self) -> QIcon:
        icon = load_app_icon()
        if not icon.isNull():
            return icon

        pix = QPixmap(64, 64)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(qcolor("primary"))
        painter.drawRoundedRect(4, 4, 56, 56, 18, 18)
        painter.setBrush(qcolor("surface_container_low"))
        painter.drawRoundedRect(13, 10, 38, 44, 13, 13)
        painter.setPen(QPen(qcolor("on_surface"), 4))
        painter.drawLine(23, 19, 23, 45)
        painter.setPen(QPen(qcolor("warning"), 4))
        painter.drawLine(23, 19, 38, 19)
        painter.setPen(QPen(qcolor("on_surface"), 3))
        painter.drawLine(23, 31, 44, 31)
        painter.setPen(QPen(qcolor("primary_container"), 3))
        painter.drawLine(23, 41, 39, 41)
        painter.end()
        return QIcon(pix)
