from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QFontMetrics, QGuiApplication, QIcon, QIntValidator, QKeySequence, QMouseEvent, QPainter, QPainterPath, QPen, QPixmap, QShortcut, QTextCursor, QTextDocument, QTransform
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .focus_utils import clear_focus_if_alive, install_mouse_click_focus_clear_many
from .style_utils import load_style_sheet
from .overlay_positioning import clamp_rect_to_visible_screen
from .theme_tokens import qcolor
from ..platform.windows.window_topmost import ensure_window_topmost


class OpacityValueChip(QLineEdit):
    value_submitted = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._display_value = 95
        self._editing = False
        self.setAlignment(Qt.AlignCenter)
        self.setFrame(False)
        self.setReadOnly(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setValidator(QIntValidator(1, 100, self))

    @property
    def editing(self) -> bool:
        return self._editing

    def set_display_value(self, value: int):
        self._display_value = max(1, min(100, int(value)))
        if not self._editing:
            self.setText(f"{self._display_value}%")

    def start_editing(self):
        if self._editing:
            return
        self._editing = True
        self.setReadOnly(False)
        self.setCursor(Qt.IBeamCursor)
        self.setText(str(self._display_value))
        self.setFocus(Qt.MouseFocusReason)
        self.selectAll()

    def cancel_editing(self):
        if not self._editing:
            return
        self._editing = False
        self.setReadOnly(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(f"{self._display_value}%")
        self.clearFocus()

    def _commit_value(self):
        if not self._editing:
            return
        text = self.text().strip()
        value = self._display_value if text == "" else int(text)
        self._display_value = max(1, min(100, value))
        self._editing = False
        self.setReadOnly(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(f"{self._display_value}%")
        self.clearFocus()
        self.value_submitted.emit(self._display_value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self._editing:
            self.start_editing()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if self._editing and event.key() in {Qt.Key_Return, Qt.Key_Enter}:
            self._commit_value()
            event.accept()
            return
        if self._editing and event.key() == Qt.Key_Escape:
            self.cancel_editing()
            event.accept()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        was_editing = self._editing
        super().focusOutEvent(event)
        if was_editing and self._editing:
            self._commit_value()


class TranslationOverlay(QWidget):
    request_font_zoom = Signal(int)
    overlay_resized = Signal(int, int)

    MIN_WIDTH = 240
    MIN_HEIGHT = 220
    RESIZE_MARGIN = 18
    DEFAULT_OPACITY = 95
    HEADER_MARGINS = (16, 12, 12, 12)
    HEADER_MINIMIZED_MARGINS = (12, 4, 8, 4)
    HEADER_SPACING = 8
    HEADER_MINIMIZED_SPACING = 6
    ACTION_BUTTON_SIZE = 32
    ACTION_BUTTON_MINIMIZED_SIZE = 24

    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.last_bbox = None
        self.last_anchor_point = None
        self.last_text = ""
        self._body_source_text = ""
        self._body_renders_markdown = False
        self._is_minimized = False
        self._pre_minimized_geometry = None
        self.last_preset_name = ""
        self.last_geometry = None
        self._partial_result_state = None
        self._partial_preset_name = ""
        self.manual_positioned = False
        self._drag_offset = QPoint()
        self._dragging = False
        self._resize_mode = None
        self._resize_start_pos = QPoint()
        self._resize_start_geometry = QRect()
        self._shadow_effect = None
        self._topbar_hovered = False
        self._drag_event_widgets = set()
        self._header_hover_widgets = set()
        self._first_show_primed = False
        self.setup_ui()
        self.sync_last_geometry_from_pinned_config()

    @property
    def is_pinned(self) -> bool:
        return bool(getattr(self.app_window.config, "overlay_pinned", False))

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setObjectName("overlayCard")
        self.card.setMouseTracking(True)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(26)
        shadow.setOffset(0, 8)
        shadow.setColor(qcolor("shadow", alpha=90))
        self.card.setGraphicsEffect(shadow)
        self._shadow_effect = shadow

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self.header = QFrame()
        self.header.setObjectName("overlayHeader")
        self.header.setMouseTracking(True)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(*self.HEADER_MARGINS)
        header_layout.setSpacing(self.HEADER_SPACING)

        self.title_label = QLabel()
        self.title_label.setObjectName("overlayTitleLabel")
        self.title_label.setMouseTracking(True)

        self.pin_button = QPushButton()
        self.pin_button.setObjectName("overlayActionButton")
        self.pin_button.setProperty("iconOnly", True)
        self.pin_button.setProperty("pinToggle", True)
        self.pin_button.setCheckable(True)
        self.pin_button.setFixedSize(32, 32)
        self.pin_button.clicked.connect(self.toggle_pin)
        self.pin_button.setIconSize(QSize(18, 18))

        self.opacity_down_button = QPushButton("−")
        self.opacity_down_button.setObjectName("overlayActionButton")
        self.opacity_down_button.setFixedSize(32, 32)
        self.opacity_down_button.clicked.connect(lambda: self.adjust_opacity(-5))

        self.opacity_value_label = OpacityValueChip()
        self.opacity_value_label.setObjectName("overlayValueChip")
        self.opacity_value_label.setMinimumWidth(58)
        self.opacity_value_label.setFixedHeight(32)
        self.opacity_value_label.value_submitted.connect(self.set_overlay_opacity)

        self.opacity_up_button = QPushButton("+")
        self.opacity_up_button.setObjectName("overlayActionButton")
        self.opacity_up_button.setFixedSize(32, 32)
        self.opacity_up_button.clicked.connect(lambda: self.adjust_opacity(5))

        self.copy_button = QPushButton()
        self.copy_button.setObjectName("overlayActionButton")
        self.copy_button.setMinimumWidth(92)
        self.copy_button.setFixedHeight(32)
        self.copy_button.clicked.connect(self.copy_text)

        self.minimize_button = QPushButton("▴")
        self.minimize_button.setObjectName("overlayActionButton")
        self.minimize_button.setProperty("iconOnly", True)
        self.minimize_button.setFixedSize(32, 32)
        self.minimize_button.clicked.connect(self.toggle_minimized)

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("overlayCloseButton")
        self.close_button.setFixedSize(32, 32)
        self.close_button.clicked.connect(self.hide)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.pin_button)
        header_layout.addWidget(self.opacity_down_button)
        header_layout.addWidget(self.opacity_value_label)
        header_layout.addWidget(self.opacity_up_button)
        header_layout.addWidget(self.copy_button)
        header_layout.addWidget(self.minimize_button)
        header_layout.addWidget(self.close_button)

        self.body = QTextEdit()
        self.body.setReadOnly(True)
        self.body.setObjectName("overlayBody")
        self.body.setMouseTracking(True)
        self.body.viewport().setMouseTracking(True)

        card_layout.addWidget(self.header)
        card_layout.addWidget(self.body)
        outer.addWidget(self.card)

        self.resize_grip = QLabel(self.card)
        self.resize_grip.setObjectName("overlayResizeGrip")
        self.resize_grip.setFixedSize(16, 16)
        self.resize_grip.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._drag_event_widgets = {self, self.card, self.header, self.title_label, self.body, self.body.viewport()}
        self._header_hover_widgets = {
            self.header,
            self.title_label,
            self.pin_button,
            self.opacity_down_button,
            self.opacity_value_label,
            self.opacity_up_button,
            self.copy_button,
            self.minimize_button,
            self.close_button,
        }
        for widget in self._drag_event_widgets | self._header_hover_widgets:
            widget.installEventFilter(self)
        self._mouse_focus_clear_filters = install_mouse_click_focus_clear_many(
            self.pin_button,
            self.opacity_down_button,
            self.opacity_up_button,
            self.copy_button,
            self.minimize_button,
            self.close_button,
        )

        self.apply_styles()
        self._apply_minimized_chrome_state()
        self._shortcuts = [
            QShortcut(QKeySequence("Esc"), self),
            QShortcut(QKeySequence("Ctrl+C"), self),
            QShortcut(QKeySequence("Ctrl+W"), self),
        ]
        self._shortcuts[0].activated.connect(self.hide)
        self._shortcuts[1].activated.connect(self.copy_text)
        self._shortcuts[2].activated.connect(self.hide)
        self.refresh_language()
        self.apply_surface_state()

    def _current_overlay_opacity(self) -> int:
        raw_value = getattr(self.app_window.config, "overlay_opacity", self.DEFAULT_OPACITY)
        try:
            opacity = int(raw_value)
        except (TypeError, ValueError):
            opacity = self.DEFAULT_OPACITY
        return max(1, min(100, opacity))

    @staticmethod
    def _alpha_from_percent(percent: int) -> int:
        return max(0, min(255, round(255 * max(0, min(100, percent)) / 100)))

    def _rgba(self, token: str, *, alpha: int | None = None, theme_name: str | None = None) -> str:
        color = QColor(qcolor(token, theme_name=theme_name))
        if alpha is not None:
            color.setAlpha(max(0, min(255, alpha)))
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"

    def _build_dynamic_style_sheet(self, theme_name: str | None = None) -> str:
        opacity = self._current_overlay_opacity()
        header_opacity = 100 if self._topbar_hovered else opacity
        card_alpha = self._alpha_from_percent(opacity)
        header_alpha = self._alpha_from_percent(header_opacity)
        pin_idle_alpha = max(30, round(header_alpha * 0.20))
        pin_idle_border_alpha = max(54, round(header_alpha * 0.28))
        pin_hover_alpha = max(42, round(header_alpha * 0.28))
        pin_hover_border_alpha = max(72, round(header_alpha * 0.38))
        pin_checked_alpha = max(54, round(header_alpha * 0.34))
        pin_checked_border_alpha = max(86, round(header_alpha * 0.46))
        return "\n".join(
            [
                "#overlayCard {",
                f"    background:{self._rgba('overlay_card_bg', alpha=card_alpha, theme_name=theme_name)};",
                f"    border-color:{self._rgba('overlay_card_border', alpha=card_alpha, theme_name=theme_name)};",
                "}",
                "#overlayHeader {",
                f"    background:{self._rgba('overlay_card_bg', alpha=header_alpha, theme_name=theme_name)};",
                f"    border-bottom-color:{self._rgba('overlay_header_border', alpha=header_alpha, theme_name=theme_name)};",
                "}",
                "#overlayBody {",
                f"    selection-background-color:{self._rgba('primary', theme_name=theme_name)};",
                f"    selection-color:{self._rgba('on_primary', theme_name=theme_name)};",
                "}",
                "#overlayValueChip {",
                f"    background:{self._rgba('overlay_value_bg', alpha=header_alpha, theme_name=theme_name)};",
                f"    border-color:{self._rgba('overlay_header_border', alpha=header_alpha, theme_name=theme_name)};",
                "}",
                "#overlayActionButton:checked {",
                f"    background:{self._rgba('overlay_action_checked_bg', alpha=header_alpha, theme_name=theme_name)};",
                f"    border-color:{self._rgba('overlay_action_checked_border', alpha=header_alpha, theme_name=theme_name)};",
                "}",
                "#overlayCloseButton:hover,",
                "#overlayActionButton:hover {",
                f"    background:{self._rgba('overlay_action_hover_bg', alpha=header_alpha, theme_name=theme_name)};",
                f"    border-color:{self._rgba('overlay_action_hover_border', alpha=header_alpha, theme_name=theme_name)};",
                "}",
                "#overlayActionButton[pinToggle=\"true\"] {",
                f"    background:{self._rgba('overlay_pin_bg', alpha=pin_idle_alpha, theme_name=theme_name)};",
                f"    color:{self._rgba('overlay_pin_fg', theme_name=theme_name)};",
                f"    border-color:{self._rgba('overlay_pin_border', alpha=pin_idle_border_alpha, theme_name=theme_name)};",
                "}",
                "#overlayActionButton[pinToggle=\"true\"]:hover {",
                f"    background:{self._rgba('overlay_pin_hover_bg', alpha=pin_hover_alpha, theme_name=theme_name)};",
                f"    color:{self._rgba('overlay_pin_hover_fg', theme_name=theme_name)};",
                f"    border-color:{self._rgba('overlay_pin_hover_border', alpha=pin_hover_border_alpha, theme_name=theme_name)};",
                "}",
                "#overlayActionButton[pinToggle=\"true\"]:checked {",
                f"    background:{self._rgba('overlay_pin_checked_bg', alpha=pin_checked_alpha, theme_name=theme_name)};",
                f"    color:{self._rgba('overlay_pin_checked_fg', theme_name=theme_name)};",
                f"    border-color:{self._rgba('overlay_pin_checked_border', alpha=pin_checked_border_alpha, theme_name=theme_name)};",
                "}",
                "#overlayActionButton[pinToggle=\"true\"]:checked:hover {",
                f"    background:{self._rgba('overlay_pin_checked_bg', alpha=min(255, pin_checked_alpha + 8), theme_name=theme_name)};",
                f"    color:{self._rgba('overlay_pin_checked_fg', theme_name=theme_name)};",
                f"    border-color:{self._rgba('overlay_pin_checked_border', alpha=min(255, pin_checked_border_alpha + 8), theme_name=theme_name)};",
                "}",
                "#overlayActionButton[pinToggle=\"true\"]:focus {",
                f"    border-color:{self._rgba('overlay_focus_border', alpha=header_alpha, theme_name=theme_name)};",
                "}",
            ]
        )

    def _header_contains_global_pos(self, global_pos: QPoint | None = None) -> bool:
        if not self.isVisible():
            return False
        point = global_pos or QCursor.pos()
        return self._header_rect().contains(self.mapFromGlobal(point))

    def _set_topbar_hovered(self, hovered: bool):
        hovered = bool(hovered)
        if hovered == self._topbar_hovered:
            return
        self._topbar_hovered = hovered
        self.apply_styles()

    def _sync_topbar_hover_state(self, global_pos: QPoint | None = None):
        self._set_topbar_hovered(self._header_contains_global_pos(global_pos))

    def apply_styles(self):
        theme_name = self.app_window.effective_theme_name()
        base_style = load_style_sheet("translation_overlay.qss", theme_name=theme_name)
        self.setStyleSheet(f"{base_style}\n{self._build_dynamic_style_sheet(theme_name)}")

    def _build_pin_icon(self, checked: bool) -> QIcon:
        color_token = "overlay_pin_checked_fg" if checked else "overlay_pin_hover_fg" if self.pin_button.underMouse() else "overlay_pin_fg"
        color = qcolor(color_token, theme_name=self.app_window.effective_theme_name())
        pixmap = QPixmap(18, 18)
        pixmap.fill(Qt.transparent)

        base_path = QPainterPath()
        base_path.moveTo(7.0, 2.0)
        base_path.lineTo(17.0, 2.0)
        base_path.lineTo(17.0, 4.0)
        base_path.lineTo(16.0, 4.0)
        base_path.lineTo(16.0, 12.0)
        base_path.lineTo(18.0, 14.0)
        base_path.lineTo(18.0, 16.0)
        base_path.lineTo(13.0, 16.0)
        base_path.lineTo(13.0, 22.0)
        base_path.lineTo(11.0, 22.0)
        base_path.lineTo(11.0, 16.0)
        base_path.lineTo(6.0, 16.0)
        base_path.lineTo(6.0, 14.0)
        base_path.lineTo(8.0, 12.0)
        base_path.lineTo(8.0, 4.0)
        base_path.lineTo(7.0, 4.0)
        base_path.closeSubpath()

        scale = 16.0 / 24.0
        offset = (18.0 - (24.0 * scale)) / 2.0
        transform = QTransform()
        transform.translate(offset, offset)
        transform.scale(scale, scale)
        path = transform.map(base_path)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if checked:
            painter.fillPath(path, color)
        else:
            ghost_fill = QColor(color)
            ghost_fill.setAlpha(40)
            painter.fillPath(path, ghost_fill)
        painter.drawPath(path)

        painter.end()
        return QIcon(pixmap)

    def _refresh_pin_button(self):
        self.pin_button.setIcon(self._build_pin_icon(self.is_pinned))
        self.pin_button.setText("")
        self.pin_button.setAccessibleName(self.app_window.tr("overlay_pinned_short") if self.is_pinned else self.app_window.tr("overlay_pin_short"))

    @property
    def is_minimized_overlay(self) -> bool:
        return self._is_minimized

    def _refresh_minimize_button(self):
        if self._is_minimized:
            self.minimize_button.setText("▾")
            self.minimize_button.setToolTip(self.app_window.tr("restore_overlay"))
            self.minimize_button.setAccessibleName(self.app_window.tr("overlay_restore_short"))
            return
        self.minimize_button.setText("▴")
        self.minimize_button.setToolTip(self.app_window.tr("minimize_overlay"))
        self.minimize_button.setAccessibleName(self.app_window.tr("overlay_minimize_short"))

    def _apply_minimized_chrome_state(self):
        compact = bool(self._is_minimized)
        header_layout = self.header.layout()
        if header_layout is not None:
            margins = self.HEADER_MINIMIZED_MARGINS if compact else self.HEADER_MARGINS
            header_layout.setContentsMargins(*margins)
            header_layout.setSpacing(self.HEADER_MINIMIZED_SPACING if compact else self.HEADER_SPACING)

        hidden_when_compact = (
            self.pin_button,
            self.opacity_down_button,
            self.opacity_value_label,
            self.opacity_up_button,
            self.copy_button,
        )
        for widget in hidden_when_compact:
            widget.setVisible(not compact)

        compact_button_size = self.ACTION_BUTTON_MINIMIZED_SIZE if compact else self.ACTION_BUTTON_SIZE
        for button in (self.minimize_button, self.close_button):
            button.setFixedSize(compact_button_size, compact_button_size)

        if compact:
            compact_height = self._header_only_height()
            self.setMinimumHeight(compact_height)
            self.setMaximumHeight(compact_height)
            self.card.setMinimumHeight(compact_height)
            self.card.setMaximumHeight(compact_height)
            self.header.setFixedHeight(self._header_only_height())
            self.body.hide()
            self.body.setMinimumHeight(0)
            self.body.setMaximumHeight(0)
            self.resize_grip.hide()
        else:
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self.card.setMinimumHeight(0)
            self.card.setMaximumHeight(16777215)
            self.header.setMaximumHeight(16777215)
            self.header.setMinimumHeight(0)
            self.body.show()
            self.body.setMinimumHeight(0)
            self.body.setMaximumHeight(16777215)
            self.resize_grip.show()

    def has_partial_result(self) -> bool:
        return bool(getattr(self, "_partial_result_state", None) and self.body.toPlainText().strip())

    def set_partial_result_state(self, state: str | None, *, preset_name: str | None = None):
        normalized = str(state or "").strip().lower() or None
        next_preset_name = str(preset_name or self._partial_preset_name or "").strip() if normalized else ""
        if normalized == self._partial_result_state and next_preset_name == self._partial_preset_name:
            return
        self._partial_result_state = normalized
        self._partial_preset_name = next_preset_name
        self.refresh_language()

    def _clear_partial_result_state(self):
        self._partial_result_state = None
        self._partial_preset_name = ""

    def _title_text_for_state(self, *, preset_name: str | None = None, partial_state: str | None = None) -> str:
        normalized_partial = self._partial_result_state if partial_state is None else (str(partial_state or "").strip().lower() or None)
        if normalized_partial:
            resolved_preset_name = str(preset_name or self._partial_preset_name or self.last_preset_name or "").strip()
        else:
            resolved_preset_name = str(self.last_preset_name if preset_name is None else (preset_name or "")).strip()

        title = self.app_window.tr("overlay_title")
        if resolved_preset_name:
            title = f"{title} · {resolved_preset_name}"
        if normalized_partial:
            partial_label = self.app_window.tr(f"overlay_partial_{normalized_partial}")
            title = f"{title} · {partial_label}"
        return title

    def _measure_header_width(self, title_text: str) -> int:
        previous_title = self.title_label.text()
        title_changed = previous_title != title_text
        header_layout = self.header.layout()
        card_layout = self.card.layout()
        if title_changed:
            self.title_label.setText(title_text)
        try:
            for widget in (
                self,
                self.card,
                self.header,
                self.title_label,
                self.pin_button,
                self.opacity_down_button,
                self.opacity_value_label,
                self.opacity_up_button,
                self.copy_button,
                self.minimize_button,
                self.close_button,
            ):
                ensure_polished = getattr(widget, "ensurePolished", None)
                if callable(ensure_polished):
                    ensure_polished()
            if header_layout is not None:
                header_layout.activate()
            if card_layout is not None:
                card_layout.activate()
            return max(self.MIN_WIDTH, self.header.minimumSizeHint().width(), self.header.sizeHint().width(), self.card.minimumSizeHint().width(), self.card.sizeHint().width())
        finally:
            if title_changed:
                self.title_label.setText(previous_title)

    def refresh_language(self):
        self.title_label.setText(self._title_text_for_state())
        self.copy_button.setText(self.app_window.tr("copy_response"))
        self.pin_button.setToolTip(self.app_window.tr("toggle_overlay_pin"))
        self.opacity_down_button.setToolTip(self.app_window.tr("decrease_overlay_opacity"))
        self.opacity_up_button.setToolTip(self.app_window.tr("increase_overlay_opacity"))
        self.opacity_value_label.setToolTip(self.app_window.tr("overlay_opacity_set", value=self._current_overlay_opacity()))
        self._refresh_minimize_button()
        self._apply_minimized_chrome_state()
        self.apply_surface_state()
        self.apply_typography()

    def apply_surface_state(self):
        opacity = self._current_overlay_opacity()
        self.setWindowOpacity(1.0)
        self.apply_styles()
        if self._shadow_effect is not None:
            shadow_alpha = max(0, min(90, round(90 * opacity / 100)))
            self._shadow_effect.setColor(qcolor("shadow", alpha=shadow_alpha))
        self.pin_button.setChecked(self.is_pinned)
        self._refresh_pin_button()
        self._refresh_minimize_button()
        self.opacity_value_label.set_display_value(opacity)
        self.opacity_value_label.setToolTip(self.app_window.tr("overlay_opacity_set", value=opacity))
        self.opacity_down_button.setEnabled(opacity > 1)
        self.opacity_up_button.setEnabled(opacity < 100)

    def apply_typography(self):
        font = QFont(self.app_window.current_overlay_font_family(), self.app_window.current_overlay_font_size())
        self.body.setFont(font)
        document_getter = getattr(self.body, "document", None)
        if callable(document_getter):
            document = document_getter()
            if document is not None:
                document.setDefaultFont(font)

    @staticmethod
    def _normalized_text(text: str | None) -> str:
        return str(text or "")

    @staticmethod
    def _has_partial_state(partial_state: str | None) -> bool:
        return bool(str(partial_state or "").strip())

    def _build_content_document(self, text: str, *, render_markdown: bool) -> QTextDocument:
        document = QTextDocument()
        document.setDefaultFont(self.body.font())
        normalized_text = self._normalized_text(text)
        set_markdown = getattr(document, "setMarkdown", None)
        if render_markdown and callable(set_markdown):
            set_markdown(normalized_text)
        else:
            document.setPlainText(normalized_text)
        return document

    def _content_plain_text(self, text: str, *, render_markdown: bool) -> str:
        return self._build_content_document(text, render_markdown=render_markdown).toPlainText()

    def _set_body_content(self, text: str, *, render_markdown: bool):
        normalized_text = self._normalized_text(text)
        set_markdown = getattr(self.body, "setMarkdown", None)
        used_markdown = bool(render_markdown and callable(set_markdown))
        if used_markdown:
            set_markdown(normalized_text)
        else:
            self.body.setPlainText(normalized_text)
        self._body_source_text = normalized_text
        self._body_renders_markdown = used_markdown

    def _body_matches_source(self, text: str, *, render_markdown: bool) -> bool:
        normalized_text = self._normalized_text(text)
        if self._body_source_text == normalized_text and self._body_renders_markdown == bool(render_markdown):
            return True
        if not render_markdown:
            return self.body.toPlainText() == normalized_text
        return False

    def calculate_size(self, text: str, *, base_width: int | None = None, preset_name: str | None = None, partial_state: str | None = None):
        render_markdown = not self._has_partial_state(partial_state)
        plain_text = self._content_plain_text(text, render_markdown=render_markdown)
        lines = plain_text.splitlines() or [plain_text]
        metrics = QFontMetrics(self.body.font())
        longest_width = max((metrics.horizontalAdvance(line or " ") for line in lines), default=240)
        line_spacing = metrics.lineSpacing()
        configured_width = max(self.MIN_WIDTH, int(base_width if base_width is not None else (self.app_window.current_overlay_width() or 440)))
        configured_height = max(self.MIN_HEIGHT, int(self.app_window.current_overlay_height() or 520))
        title_text = self._title_text_for_state(preset_name=preset_name, partial_state=partial_state)
        header_width = self._measure_header_width(title_text)
        width = min(860, max(configured_width, longest_width + 136, header_width))
        height = min(900, max(configured_height, len(lines) * line_spacing + 132))
        return width, height

    def measure_content_height(self, text: str, width: int, *, render_markdown: bool = True) -> int:
        doc = self._build_content_document(text, render_markdown=render_markdown)
        text_width = max(220, width - 42)
        doc.setTextWidth(text_width)
        header_height = 58
        body_padding = 48
        return int(doc.size().height()) + header_height + body_padding

    def _header_only_height(self) -> int:
        header_layout = self.header.layout()
        if header_layout is not None:
            margins = header_layout.contentsMargins()
            header_layout.activate()
        else:
            margins = None
        title_height = self.title_label.sizeHint().height()
        action_height = max(
            self.minimize_button.sizeHint().height(),
            self.close_button.sizeHint().height(),
        )
        if margins is None:
            return max(30, max(title_height, action_height) + 8)
        return max(30, max(title_height, action_height) + margins.top() + margins.bottom())

    def _expanded_geometry_for_current_position(self) -> QRect | None:
        base_geometry = QRect(self._pre_minimized_geometry) if self._pre_minimized_geometry is not None else QRect(self.last_geometry) if self.last_geometry is not None else None
        current_rect = QRect(self.geometry())
        if base_geometry is None:
            if current_rect.width() <= 0:
                return None
            base_height = current_rect.height()
            if self._is_minimized:
                base_height = max(self.MIN_HEIGHT, int(self.app_window.current_overlay_height() or self.MIN_HEIGHT))
            base_geometry = QRect(current_rect.x(), current_rect.y(), max(self.MIN_WIDTH, current_rect.width()), max(self.MIN_HEIGHT, base_height))
        if current_rect.width() > 0 and current_rect.height() > 0:
            base_geometry.moveTopLeft(current_rect.topLeft())
        return clamp_rect_to_visible_screen(base_geometry)

    def _remember_runtime_geometry(self, rect: QRect | None = None):
        geometry = QRect(rect) if rect is not None else QRect(self.geometry())
        if geometry.width() <= 0 or geometry.height() <= 0:
            return
        if self._is_minimized:
            expanded_geometry = self._expanded_geometry_for_current_position()
            if expanded_geometry is None:
                return
            self._pre_minimized_geometry = QRect(expanded_geometry)
            self.last_geometry = QRect(expanded_geometry)
            return
        self.last_geometry = clamp_rect_to_visible_screen(geometry)

    def _minimized_target_geometry(self, expanded_geometry: QRect | None = None) -> QRect:
        base_geometry = QRect(expanded_geometry) if expanded_geometry is not None else QRect(self.geometry())
        if base_geometry.width() <= 0:
            base_geometry.setWidth(max(self.MIN_WIDTH, int(self.app_window.current_overlay_width() or self.MIN_WIDTH)))
        target = QRect(base_geometry.x(), base_geometry.y(), max(self.MIN_WIDTH, base_geometry.width()), self._header_only_height())
        return clamp_rect_to_visible_screen(target)

    def _set_minimized(self, minimized: bool, *, restore_geometry: bool = True, emit_status: bool = False) -> bool:
        minimized = bool(minimized)
        if minimized == self._is_minimized:
            return False

        if minimized:
            # 最小化时只折叠 body，保留展开态几何用于后续恢复和 Pin 持久化。
            expanded_geometry = self._expanded_geometry_for_current_position()
            self._pre_minimized_geometry = QRect(expanded_geometry) if expanded_geometry is not None else None
            self._is_minimized = True
            self._apply_minimized_chrome_state()
            self.setGeometry(self._minimized_target_geometry(expanded_geometry))
            self._remember_runtime_geometry()
        else:
            expanded_geometry = self._expanded_geometry_for_current_position()
            self._is_minimized = False
            self._pre_minimized_geometry = None
            self._apply_minimized_chrome_state()
            if restore_geometry and expanded_geometry is not None:
                self.setGeometry(expanded_geometry)
                self._remember_runtime_geometry()

        self._refresh_minimize_button()
        self._update_cursor()
        if emit_status:
            self.app_window.set_status("overlay_minimized" if minimized else "overlay_restored")
        return True

    def toggle_minimized(self):
        self._set_minimized(not self._is_minimized, restore_geometry=True, emit_status=True)

    def pinned_geometry_from_config(self) -> QRect | None:
        config = getattr(self.app_window, "config", None)
        if config is None:
            return None
        x = getattr(config, "overlay_pinned_x", None)
        y = getattr(config, "overlay_pinned_y", None)
        width = getattr(config, "overlay_pinned_width", None)
        height = getattr(config, "overlay_pinned_height", None)
        if None in {x, y, width, height}:
            return None
        rect = QRect(int(x), int(y), max(self.MIN_WIDTH, int(width)), max(self.MIN_HEIGHT, int(height)))
        return clamp_rect_to_visible_screen(rect)

    def sync_last_geometry_from_pinned_config(self):
        if not self.is_pinned:
            return
        geometry = self.pinned_geometry_from_config()
        if geometry is not None:
            self.last_geometry = QRect(geometry)

    def resolved_pinned_geometry(self) -> QRect | None:
        if self.last_geometry is not None:
            return clamp_rect_to_visible_screen(QRect(self.last_geometry))
        return self.pinned_geometry_from_config()

    def persist_pinned_geometry_rect(self, rect: QRect | None):
        config = getattr(self.app_window, "config", None)
        if config is None:
            return
        if rect is None:
            config.overlay_pinned_x = None
            config.overlay_pinned_y = None
            config.overlay_pinned_width = None
            config.overlay_pinned_height = None
            return
        clamped = clamp_rect_to_visible_screen(QRect(rect))
        self.last_geometry = QRect(clamped)
        config.overlay_pinned_x = int(clamped.x())
        config.overlay_pinned_y = int(clamped.y())
        config.overlay_pinned_width = int(clamped.width())
        config.overlay_pinned_height = int(clamped.height())

    def persist_current_geometry_as_pinned(self):
        current_rect = self._expanded_geometry_for_current_position() or QRect(self.geometry())
        if current_rect.width() > 0 and current_rect.height() > 0:
            pass
        elif self.last_geometry is not None:
            current_rect = self.last_geometry
        else:
            current_rect = self.pinned_geometry_from_config()
        if current_rect is None:
            return
        self.persist_pinned_geometry_rect(current_rect)

    def _persist_runtime_overlay_state(self):
        persist = getattr(self.app_window, "persist_runtime_overlay_state", None)
        if callable(persist):
            persist()

    def remember_context(self, bbox, text: str, *, anchor_point=None, preset_name: str = ""):
        self.last_bbox = bbox
        self.last_anchor_point = anchor_point
        self.last_text = text
        self.last_preset_name = preset_name or ""

    def copy_text(self):
        text = self.body.toPlainText().strip() if self.has_partial_result() else self.last_text.strip()
        if not text:
            return
        QApplication.clipboard().setText(text)
        self.app_window.set_status("overlay_copied")

    def toggle_pin(self, checked: bool):
        self.app_window.config.overlay_pinned = bool(checked)
        if checked:
            self.persist_current_geometry_as_pinned()
        else:
            self.persist_pinned_geometry_rect(None)
        self._persist_runtime_overlay_state()
        self.apply_surface_state()
        self.app_window.set_status("overlay_pinned" if checked else "overlay_unpinned")

    def set_overlay_opacity(self, value: int):
        next_value = max(1, min(100, int(value)))
        current = self._current_overlay_opacity()
        if next_value == current:
            self.apply_surface_state()
            return
        self.app_window.config.overlay_opacity = next_value
        self.app_window.note_runtime_preference_changed()
        self.apply_surface_state()
        self.app_window.set_status("overlay_opacity_set", value=next_value)

    def adjust_opacity(self, delta: int):
        self.set_overlay_opacity(self._current_overlay_opacity() + delta)

    def show_text(self, text: str, x: int, y: int, width: int, height: int, *, keep_manual_position: bool = False, remember_state: bool = True):
        normalized_text = self._normalized_text(text)
        render_markdown = bool(remember_state)
        if remember_state and self._is_minimized:
            self._set_minimized(False, restore_geometry=False, emit_status=False)
        if remember_state:
            self._clear_partial_result_state()
            self.refresh_language()
        target_rect = QRect(int(x), int(y), int(width), int(height))
        geometry_changed = self.geometry() != target_rect
        if geometry_changed:
            self.setGeometry(target_rect)
        if remember_state:
            self._remember_runtime_geometry()
        if not self._body_matches_source(normalized_text, render_markdown=render_markdown):
            current_plain_text = self.body.toPlainText()
            can_append_partial = bool(
                not render_markdown
                and self._partial_result_state
                and current_plain_text
                and normalized_text.startswith(current_plain_text)
            )
            if can_append_partial:
                suffix = normalized_text[len(current_plain_text) :]
                if suffix:
                    cursor = self.body.textCursor()
                    cursor.movePosition(QTextCursor.End)
                    cursor.insertText(suffix)
                    self._body_source_text = normalized_text
                    self._body_renders_markdown = False
            else:
                self._set_body_content(normalized_text, render_markdown=render_markdown)
        if remember_state:
            self.last_text = normalized_text
        self.manual_positioned = bool(keep_manual_position)
        should_raise_overlay = remember_state or not self.isVisible()
        if should_raise_overlay:
            self._show_as_topmost()
            self._sync_topbar_hover_state(QCursor.pos())

    def restore_last_overlay(self):
        if not self.last_text.strip() or self.last_geometry is None:
            return
        if self._is_minimized:
            self._set_minimized(False, restore_geometry=False, emit_status=False)
        self._clear_partial_result_state()
        self.refresh_language()
        self.setGeometry(clamp_rect_to_visible_screen(self.last_geometry))
        self._remember_runtime_geometry()
        self._set_body_content(self.last_text, render_markdown=True)
        self._show_as_topmost()
        self._sync_topbar_hover_state(QCursor.pos())

    def _clear_initial_focus(self):
        for widget in (
            self.pin_button,
            self.opacity_down_button,
            self.opacity_value_label,
            self.opacity_up_button,
            self.copy_button,
            self.minimize_button,
            self.close_button,
        ):
            clear_focus_if_alive(widget)
        if self.isVisible():
            self.setFocus(Qt.OtherFocusReason)

    def prime_first_show(self) -> bool:
        if self._first_show_primed:
            return False
        if self.isVisible():
            self._first_show_primed = True
            return False

        current_rect = QRect(self.geometry())
        width = current_rect.width() if current_rect.width() > 0 else max(self.MIN_WIDTH, int(self.app_window.current_overlay_width() or self.MIN_WIDTH))
        height = current_rect.height() if current_rect.height() > 0 else max(self.MIN_HEIGHT, int(self.app_window.current_overlay_height() or self.MIN_HEIGHT))
        warmup_rect = QRect(-32000, -32000, int(width), int(height))
        restore_rect = QRect(current_rect) if current_rect.width() > 0 and current_rect.height() > 0 else None
        previous_opacity = float(self.windowOpacity())
        had_show_without_activate = self.testAttribute(Qt.WA_ShowWithoutActivating)

        try:
            self.setAttribute(Qt.WA_ShowWithoutActivating, True)
            self.setWindowOpacity(0.0)
            self.setGeometry(warmup_rect)
            self.show()
            QApplication.processEvents()
            return True
        finally:
            try:
                self.hide()
            except Exception:  # noqa: BLE001
                pass
            if restore_rect is not None:
                try:
                    self.setGeometry(restore_rect)
                except Exception:  # noqa: BLE001
                    pass
            try:
                self.setWindowOpacity(previous_opacity if previous_opacity > 0 else 1.0)
            except Exception:  # noqa: BLE001
                pass
            self.setAttribute(Qt.WA_ShowWithoutActivating, had_show_without_activate)
            self._set_topbar_hovered(False)
            self._first_show_primed = True

    def _show_as_topmost(self):
        self.show()
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(0, self._clear_initial_focus)

        self._ensure_native_topmost()

    def _ensure_native_topmost(self):
        ensure_window_topmost(self, activate=False)
        QTimer.singleShot(0, lambda: ensure_window_topmost(self, activate=False))

    def _header_rect(self) -> QRect:
        top_left = self.header.mapTo(self, QPoint(0, 0))
        return QRect(top_left, self.header.size())

    def _event_pos_in_self(self, watched, event: QMouseEvent) -> QPoint:
        local_pos = event.position().toPoint()
        if watched is self:
            return local_pos
        return watched.mapTo(self, local_pos)

    def _resize_mode_at(self, pos: QPoint) -> str | None:
        if self._is_minimized:
            return None
        rect = self.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return None
        margin = self.RESIZE_MARGIN
        near_left = pos.x() <= margin
        near_right = pos.x() >= rect.width() - margin
        near_top = pos.y() <= margin
        near_bottom = pos.y() >= rect.height() - margin
        if near_left and near_top:
            return "top_left"
        if near_right and near_top:
            return "top_right"
        if near_left and near_bottom:
            return "bottom_left"
        if near_right and near_bottom:
            return "bottom_right"
        return None

    def _update_cursor(self, pos: QPoint | None = None):
        mode = self._resize_mode if self._resize_mode else self._resize_mode_at(pos) if pos is not None else None
        if mode in {"top_left", "bottom_right"}:
            self.setCursor(Qt.SizeFDiagCursor)
        elif mode in {"top_right", "bottom_left"}:
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.unsetCursor()

    def _screen_rect_for_global_pos(self, global_pos: QPoint) -> QRect:
        screen = QGuiApplication.screenAt(global_pos) or QGuiApplication.primaryScreen()
        return screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

    def _clamped_drag_position(self, global_pos: QPoint) -> QPoint:
        target = global_pos - self._drag_offset
        screen_rect = self._screen_rect_for_global_pos(global_pos)
        x = max(screen_rect.left(), min(target.x(), screen_rect.right() - self.width() + 1))
        y = max(screen_rect.top(), min(target.y(), screen_rect.bottom() - self.height() + 1))
        return QPoint(x, y)

    def _resize_geometry(self, global_pos: QPoint) -> QRect:
        delta = global_pos - self._resize_start_pos
        geometry = QRect(self._resize_start_geometry)
        screen_rect = self._screen_rect_for_global_pos(global_pos)

        if self._resize_mode in {"top_left", "bottom_left"}:
            new_left = min(geometry.right() - self.MIN_WIDTH + 1, geometry.left() + delta.x())
            geometry.setLeft(max(screen_rect.left(), new_left))
        if self._resize_mode in {"top_right", "bottom_right"}:
            new_right = max(geometry.left() + self.MIN_WIDTH - 1, geometry.right() + delta.x())
            geometry.setRight(min(screen_rect.right(), new_right))
        if self._resize_mode in {"top_left", "top_right"}:
            new_top = min(geometry.bottom() - self.MIN_HEIGHT + 1, geometry.top() + delta.y())
            geometry.setTop(max(screen_rect.top(), new_top))
        if self._resize_mode in {"bottom_left", "bottom_right"}:
            new_bottom = max(geometry.top() + self.MIN_HEIGHT - 1, geometry.bottom() + delta.y())
            geometry.setBottom(min(screen_rect.bottom(), new_bottom))

        if geometry.width() < self.MIN_WIDTH:
            if self._resize_mode in {"top_left", "bottom_left"}:
                geometry.setLeft(geometry.right() - self.MIN_WIDTH + 1)
            else:
                geometry.setRight(geometry.left() + self.MIN_WIDTH - 1)
        if geometry.height() < self.MIN_HEIGHT:
            if self._resize_mode in {"top_left", "top_right"}:
                geometry.setTop(geometry.bottom() - self.MIN_HEIGHT + 1)
            else:
                geometry.setBottom(geometry.top() + self.MIN_HEIGHT - 1)
        return geometry

    def _handle_mouse_press(self, watched, event: QMouseEvent) -> bool:
        if event.button() != Qt.LeftButton:
            return False
        pos = self._event_pos_in_self(watched, event)
        resize_mode = self._resize_mode_at(pos)
        if resize_mode:
            self._resize_mode = resize_mode
            self._resize_start_pos = event.globalPosition().toPoint()
            self._resize_start_geometry = self.geometry()
            self._dragging = False
            self._update_cursor(pos)
            return True
        if self._header_rect().contains(pos):
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragging = True
            return True
        return False

    def _handle_mouse_move(self, watched, event: QMouseEvent) -> bool:
        pos = self._event_pos_in_self(watched, event)
        if self._resize_mode and event.buttons() & Qt.LeftButton:
            geometry = self._resize_geometry(event.globalPosition().toPoint())
            self.setGeometry(geometry)
            self._remember_runtime_geometry()
            self.manual_positioned = True
            self._update_cursor(pos)
            return True
        if self._dragging and event.buttons() & Qt.LeftButton:
            self.move(self._clamped_drag_position(event.globalPosition().toPoint()))
            self.manual_positioned = True
            self._remember_runtime_geometry()
            return True
        self._update_cursor(pos)
        return False

    def _handle_mouse_release(self, watched, event: QMouseEvent) -> bool:
        if event.button() != Qt.LeftButton:
            return False
        released_drag = bool(self._dragging)
        released_resize = bool(self._resize_mode)
        self._dragging = False
        self._resize_mode = None
        self._remember_runtime_geometry()
        if released_drag and self.is_pinned:
            self.persist_current_geometry_as_pinned()
            self._persist_runtime_overlay_state()
        self._update_cursor(self._event_pos_in_self(watched, event))
        if released_resize:
            self.overlay_resized.emit(self.width(), self.height())
            return True
        return released_drag

    def mousePressEvent(self, event: QMouseEvent):
        if not self._handle_mouse_press(self, event):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self._handle_mouse_move(self, event):
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if not self._handle_mouse_release(self, event):
            super().mouseReleaseEvent(event)

    def eventFilter(self, watched, event):
        if watched in self._header_hover_widgets:
            if event.type() == QEvent.Type.Enter:
                self._sync_topbar_hover_state(QCursor.pos())
            elif event.type() == QEvent.Type.Leave:
                QTimer.singleShot(0, self._sync_topbar_hover_state)
            if watched is self.pin_button and event.type() in {QEvent.Type.Enter, QEvent.Type.Leave}:
                self._refresh_pin_button()
            elif isinstance(event, QMouseEvent) and event.type() == QEvent.Type.MouseMove:
                self._sync_topbar_hover_state(event.globalPosition().toPoint())
        if event.type() == QEvent.Type.Wheel and watched in {self.body, self.body.viewport()}:
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                direction = 1 if event.angleDelta().y() > 0 else -1
                self.request_font_zoom.emit(direction)
                return True
        if isinstance(event, QMouseEvent) and watched in self._drag_event_widgets:
            if event.type() == QEvent.Type.MouseButtonPress and self._handle_mouse_press(watched, event):
                return True
            if event.type() == QEvent.Type.MouseMove and self._handle_mouse_move(watched, event):
                return True
            if event.type() == QEvent.Type.MouseButtonRelease and self._handle_mouse_release(watched, event):
                return True
        if event.type() == QEvent.Type.Leave and watched in self._drag_event_widgets:
            if not self._resize_mode and not self._dragging:
                self.unsetCursor()
        return super().eventFilter(watched, event)

    def hideEvent(self, event):
        self._set_topbar_hovered(False)
        super().hideEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_grip.move(self.card.width() - 16, self.card.height() - 16)
