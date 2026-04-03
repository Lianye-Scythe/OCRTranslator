from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFontComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..app_metadata import AUTHOR_NAME_EN, AUTHOR_NAME_ZH, REPOSITORY_NAME, REPOSITORY_URL
from ..profile_utils import normalize_provider_name
from .style_utils import load_style_sheet


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
        self.setWindowTitle(self.tr("window_title"))
        self.setWindowIcon(self.icon)
        self.resize(1080, 740)
        self.setMinimumSize(860, 620)
        self.setFocusPolicy(Qt.StrongFocus)

        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)

        shell = QHBoxLayout(root)
        shell.setContentsMargins(18, 18, 18, 16)
        shell.setSpacing(16)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setMinimumWidth(208)
        self.sidebar.setMaximumWidth(248)
        self.add_shadow(self.sidebar, blur=42, y_offset=16, alpha=90)
        self.sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(18, 20, 18, 18)
        sidebar_layout.setSpacing(14)

        self.title_label = QLabel()
        self.title_label.setObjectName("BrandTitle")
        self.title_label.setWordWrap(True)
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("BrandSubtitle")
        self.subtitle_label.setWordWrap(True)
        sidebar_layout.addWidget(self.title_label)
        sidebar_layout.addWidget(self.subtitle_label)

        self.navigation_label = QLabel()
        self.navigation_label.setObjectName("SidebarCaption")
        sidebar_layout.addSpacing(8)
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

        sidebar_layout.addStretch(1)

        self.quick_actions_label = QLabel()
        self.quick_actions_label.setObjectName("SidebarCaption")
        sidebar_layout.addWidget(self.quick_actions_label)

        self.hero_capture_button = self.create_button(self.start_selection)
        self.hero_tray_button = self.create_button(self.minimize_to_tray, accent=False)
        sidebar_layout.addWidget(self.hero_capture_button)
        sidebar_layout.addWidget(self.hero_tray_button)

        self.hint_card = QFrame()
        self.hint_card.setObjectName("HintCard")
        hint_layout = QVBoxLayout(self.hint_card)
        hint_layout.setContentsMargins(14, 14, 14, 14)
        hint_layout.setSpacing(8)
        self.hint_title_label = QLabel()
        self.hint_title_label.setObjectName("HintTitleLabel")
        self.hint_label = QLabel()
        self.hint_label.setObjectName("HintLabel")
        self.hint_label.setWordWrap(True)
        hint_layout.addWidget(self.hint_title_label)
        hint_layout.addWidget(self.hint_label)
        sidebar_layout.addWidget(self.hint_card)

        self.about_card = QFrame()
        self.about_card.setObjectName("AboutCard")
        about_layout = QVBoxLayout(self.about_card)
        about_layout.setContentsMargins(14, 14, 14, 14)
        about_layout.setSpacing(8)
        self.about_title_label = QLabel()
        self.about_title_label.setObjectName("AboutTitleLabel")
        self.about_meta_label = QLabel()
        self.about_meta_label.setObjectName("AboutMetaLabel")
        self.about_meta_label.setWordWrap(True)
        self.about_meta_label.setOpenExternalLinks(True)
        self.about_meta_label.setTextFormat(Qt.RichText)
        self.about_meta_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        about_layout.addWidget(self.about_title_label)
        about_layout.addWidget(self.about_meta_label)
        sidebar_layout.addWidget(self.about_card)

        shell.addWidget(self.sidebar)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(14)
        shell.addLayout(content_layout, 1)

        self.header_card = QFrame()
        self.header_card.setObjectName("HeaderCard")
        self.add_shadow(self.header_card, blur=48, y_offset=18, alpha=92)
        header_layout = QHBoxLayout(self.header_card)
        header_layout.setContentsMargins(22, 20, 22, 20)
        header_layout.setSpacing(16)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(6)
        self.page_title_label = QLabel()
        self.page_title_label.setObjectName("PageTitleLabel")
        self.page_subtitle_label = QLabel()
        self.page_subtitle_label.setObjectName("PageSubtitleLabel")
        self.page_subtitle_label.setWordWrap(True)
        header_text_layout.addWidget(self.page_title_label)
        header_text_layout.addWidget(self.page_subtitle_label)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)
        self.hotkey_chip = QLabel()
        self.hotkey_chip.setObjectName("InfoChip")
        self.target_chip = QLabel()
        self.target_chip.setObjectName("InfoChip")
        self.prompt_chip = QLabel()
        self.prompt_chip.setObjectName("InfoChip")
        self.mode_chip = QLabel()
        self.mode_chip.setObjectName("InfoChip")
        for chip in (self.hotkey_chip, self.target_chip, self.prompt_chip, self.mode_chip):
            meta_row.addWidget(chip)
        meta_row.addStretch(1)
        header_text_layout.addLayout(meta_row)
        header_layout.addLayout(header_text_layout, 1)

        self.active_profile_badge = QLabel()
        self.active_profile_badge.setObjectName("ActiveProfileBadge")
        self.active_profile_badge.setAlignment(Qt.AlignCenter)
        self.active_profile_badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        header_layout.addWidget(self.active_profile_badge, alignment=Qt.AlignTop)

        content_layout.addWidget(self.header_card)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("PageStack")
        content_layout.addWidget(self.page_stack, 1)

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
        content_layout.addWidget(self.status_label)

        self.switch_page(0)


    def _build_monitor_tab(self):
        layout = QHBoxLayout(self.monitor_tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(16)

        self.preview_group, preview_layout, self.preview_group_title_label = self.create_section_card()
        preview_header = QHBoxLayout()
        preview_header.setSpacing(8)
        preview_header.addWidget(self.preview_group_title_label)
        preview_header.addStretch(1)
        self.preview_capture_button = self.create_button(self.start_selection, compact=True)
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

        self.log_group, log_layout, self.log_group_title_label = self.create_section_card()
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
        self.setStyleSheet(load_style_sheet("main_window.qss"))

    def apply_language(self):
        self.setWindowTitle(f"{self.tr('window_title')}[*]")
        self.title_label.setText(self.tr("title"))
        self.subtitle_label.setText(self.tr("subtitle"))
        self.navigation_label.setText(self.tr("navigation"))
        self.quick_actions_label.setText(self.tr("quick_actions"))
        self.hero_capture_button.setText(self.tr("start_capture"))
        self.hero_tray_button.setText(self.tr("minimize_to_tray"))
        self.nav_settings_button.setText(self.tr("tab_settings"))
        self.nav_monitor_button.setText(self.tr("tab_monitor"))
        self.hint_title_label.setText(self.tr("sidebar_hint_title"))
        self.hint_label.setText(self.tr("hint"))
        self.about_title_label.setText(self.tr("sidebar_about_title"))
        self.about_meta_label.setText(
            "<span style='color:#90a0b6;'>"
            f"{self.tr('about_author_label')}：</span>"
            f"<span style='color:#eef3fb;'>{AUTHOR_NAME_ZH}</span>"
            f" <span style='color:#70809b;'>/</span> "
            f"<span style='color:#cfdaf0;'>{AUTHOR_NAME_EN}</span>"
            "<br/>"
            f"<span style='color:#90a0b6;'>{self.tr('about_repo_label')}：</span>"
            f"<a href='{REPOSITORY_URL}' style='color:#9db1ff; text-decoration:none;'>{REPOSITORY_NAME}</a>"
        )
        self.profile_group_title_label.setText(self.tr("section_profiles"))
        self.api_group_title_label.setText(self.tr("section_api"))
        self.reading_group_title_label.setText(self.tr("section_reading"))
        self.prompts_group_title_label.setText(self.tr("section_prompts"))
        self.advanced_group_title_label.setText(self.tr("section_advanced"))
        self.quick_group_title_label.setText(self.tr("quick_actions"))
        self.preview_group_title_label.setText(self.tr("preview_panel"))
        self.log_group_title_label.setText(self.tr("activity_panel"))
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
        self.api_keys_label_row.setText(self.tr("api_keys_hidden") if not self.api_keys_visible else self.tr("api_keys"))
        self.api_keys_hint.setText(self.tr("api_keys_mask_hint") if not self.api_keys_visible else self.tr("api_keys_hint"))
        self.retry_count_label.setText(self.tr("retry_count"))
        self.temperature_label.setText(self.tr("temperature"))
        self.overlay_width_label.setText(self.tr("overlay_width"))
        self.overlay_height_label.setText(self.tr("overlay_height"))
        self.overlay_margin_label.setText(self.tr("overlay_margin"))
        self.retry_interval_label.setText(self.tr("retry_interval"))
        self.target_language_label.setText(self.tr("target_language"))
        self.ui_language_label.setText(self.tr("ui_language"))
        self.hotkey_label.setText(self.tr("capture_hotkey"))
        self.selection_hotkey_label.setText(self.tr("selection_hotkey"))
        self.input_hotkey_label.setText(self.tr("input_hotkey"))
        self.overlay_font_label.setText(self.tr("overlay_font_family"))
        self.overlay_font_size_label.setText(self.tr("overlay_font_size"))
        self.image_prompt_label.setText(self.tr("image_prompt"))
        self.text_prompt_label.setText(self.tr("text_prompt"))
        self.prompt_hint_label.setText(self.tr("prompt_hint"))
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
        self.api_keys_edit.setPlaceholderText(self.tr("api_keys_placeholder"))
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
        self.save_button.setToolTip(self.tr("save_settings"))
        self.mode_label.setText(self.tr("display_mode"))
        self.fetch_models_button.setText(self.tr("fetch_models"))
        self.test_button.setText(self.tr("test_api"))
        self.save_button.setText(self.tr("save_settings"))
        self.set_advanced_section_expanded(getattr(self, "advanced_section_expanded", False))
        self.close_to_tray_on_close_checkbox.setText(self.tr("close_to_tray_on_close"))
        self.api_keys_toggle_button.setText(self.tr("show_api_keys") if not self.api_keys_visible else self.tr("hide_api_keys"))
        self.export_logs_button.setText(self.tr("export_logs"))
        self.update_provider_options()
        self.update_mode_options()
        self.refresh_page_header()
        self.refresh_shell_state()
        if hasattr(self, "tray"):
            self.update_tray_texts()
        if hasattr(self, "selection_overlay"):
            self.selection_overlay.set_hint_text(self.tr("selection_hint"))
        self.translation_overlay.refresh_language()
        self.set_status(self.current_status_key, **self.current_status_kwargs)
        if hasattr(self, "update_action_states"):
            self.update_action_states()
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
        if not hasattr(self, "active_profile_badge"):
            return
        current_mode = self.current_mode() if hasattr(self, "current_mode") else self.config.mode
        current_hotkey = self.current_hotkey() if hasattr(self, "current_hotkey") else self.config.hotkey
        current_target_language = self.current_target_language() if hasattr(self, "current_target_language") else self.config.target_language
        current_prompt_preset = self.current_prompt_preset_name() if hasattr(self, "current_prompt_preset_name") else self.config.active_prompt_preset_name
        mode_label = self.tr("mode_book_lr") if current_mode == "book_lr" else self.tr("mode_web_ud")
        self.hotkey_chip.setText(self.tr("meta_hotkey", value=current_hotkey))
        self.target_chip.setText(self.tr("meta_target", value=current_target_language))
        self.prompt_chip.setText(self.tr("meta_prompt", value=current_prompt_preset))
        self.mode_chip.setText(self.tr("meta_mode", value=mode_label))
        profile = self.get_active_profile() if getattr(self.config, "api_profiles", None) else None
        if profile and hasattr(self, "profile_name_edit") and hasattr(self, "provider_combo"):
            profile_name = self.profile_name_edit.text().strip() or self.tr("untitled_profile")
            provider = normalize_provider_name(self.provider_combo.currentData() or profile.provider)
            self.active_profile_badge.setText(f"{profile_name} · {self.provider_display(provider)}")
        elif profile:
            self.active_profile_badge.setText(f"{profile.name} · {self.provider_display(profile.provider)}")
        else:
            self.active_profile_badge.setText(self.tr("untitled_profile"))

    def create_field_block(self, label_widget, field_widget):
        block = QFrame()
        layout = QVBoxLayout(block)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        label_widget.setObjectName("FieldLabel")
        layout.addWidget(label_widget)
        layout.addWidget(field_widget)
        return block

    def create_section_card(self):
        card = QFrame()
        card.setObjectName("SectionCard")
        self.add_shadow(card, blur=34, y_offset=12, alpha=74)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)
        title_label = QLabel()
        title_label.setObjectName("SectionTitleLabel")
        layout.addWidget(title_label)
        body_layout = QVBoxLayout()
        body_layout.setSpacing(14)
        layout.addLayout(body_layout)
        return card, body_layout, title_label

    def create_button(self, callback, accent=True, secondary=False, success=False, danger=False, compact=False):
        button = QPushButton()
        button.clicked.connect(callback)
        variant = "primary"
        if secondary:
            variant = "secondary"
        elif success:
            variant = "success"
        elif danger:
            variant = "danger"
        elif not accent:
            variant = "neutral"
        button.setProperty("variant", variant)
        if compact:
            button.setProperty("compact", True)
        return button

    def add_shadow(self, widget, blur=32, y_offset=10, alpha=90):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, y_offset)
        shadow.setColor(QColor(2, 6, 20, alpha))
        widget.setGraphicsEffect(shadow)

    def create_app_icon(self) -> QIcon:
        pix = QPixmap(64, 64)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#7489ff"))
        painter.drawRoundedRect(4, 4, 56, 56, 18, 18)
        painter.setBrush(QColor("#111722"))
        painter.drawRoundedRect(13, 10, 38, 44, 13, 13)
        painter.setPen(QPen(QColor("#f3efe5"), 4))
        painter.drawLine(23, 19, 23, 45)
        painter.setPen(QPen(QColor("#d7bf88"), 4))
        painter.drawLine(23, 19, 38, 19)
        painter.setPen(QPen(QColor("#f3efe5"), 3))
        painter.drawLine(23, 31, 44, 31)
        painter.setPen(QPen(QColor("#a8b7ff"), 3))
        painter.drawLine(23, 41, 39, 41)
        painter.end()
        return QIcon(pix)
