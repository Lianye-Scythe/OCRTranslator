from PySide6.QtCore import QEvent, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QKeySequence, QMouseEvent, QShortcut, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .style_utils import load_style_sheet
from .overlay_positioning import clamp_rect_to_visible_screen
from .theme_tokens import qcolor


class TranslationOverlay(QWidget):
    request_font_zoom = Signal(int)
    overlay_resized = Signal(int, int)

    MIN_WIDTH = 240
    MIN_HEIGHT = 220
    RESIZE_MARGIN = 18

    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.last_bbox = None
        self.last_anchor_point = None
        self.last_text = ""
        self.last_preset_name = ""
        self.last_geometry = None
        self.manual_positioned = False
        self._drag_offset = QPoint()
        self._dragging = False
        self._resize_mode = None
        self._resize_start_pos = QPoint()
        self._resize_start_geometry = QRect()
        self.setup_ui()

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

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self.header = QFrame()
        self.header.setObjectName("overlayHeader")
        self.header.setMouseTracking(True)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(16, 12, 12, 12)
        header_layout.setSpacing(8)

        self.title_label = QLabel()
        self.title_label.setObjectName("overlayTitleLabel")
        self.title_label.setMouseTracking(True)

        self.pin_button = QPushButton()
        self.pin_button.setObjectName("overlayActionButton")
        self.pin_button.setCheckable(True)
        self.pin_button.setFixedHeight(32)
        self.pin_button.clicked.connect(self.toggle_pin)

        self.opacity_down_button = QPushButton("−")
        self.opacity_down_button.setObjectName("overlayActionButton")
        self.opacity_down_button.setFixedSize(32, 32)
        self.opacity_down_button.clicked.connect(lambda: self.adjust_opacity(-4))

        self.opacity_value_label = QLabel()
        self.opacity_value_label.setObjectName("overlayValueChip")
        self.opacity_value_label.setAlignment(Qt.AlignCenter)
        self.opacity_value_label.setMinimumWidth(58)

        self.opacity_up_button = QPushButton("+")
        self.opacity_up_button.setObjectName("overlayActionButton")
        self.opacity_up_button.setFixedSize(32, 32)
        self.opacity_up_button.clicked.connect(lambda: self.adjust_opacity(4))

        self.copy_button = QPushButton()
        self.copy_button.setObjectName("overlayActionButton")
        self.copy_button.setMinimumWidth(92)
        self.copy_button.setFixedHeight(32)
        self.copy_button.clicked.connect(self.copy_text)

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
        header_layout.addWidget(self.close_button)

        self.body = QTextEdit()
        self.body.setReadOnly(True)
        self.body.setObjectName("overlayBody")
        self.body.setMouseTracking(True)
        self.body.viewport().setMouseTracking(True)

        card_layout.addWidget(self.header)
        card_layout.addWidget(self.body)
        outer.addWidget(self.card)

        for widget in (self, self.card, self.header, self.title_label, self.body, self.body.viewport()):
            widget.installEventFilter(self)

        self.apply_styles()
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

    def apply_styles(self):
        self.setStyleSheet(load_style_sheet("translation_overlay.qss", theme_name=self.app_window.effective_theme_name()))

    def refresh_language(self):
        title = self.app_window.tr("overlay_title")
        if self.last_preset_name:
            title = f"{title} · {self.last_preset_name}"
        self.title_label.setText(title)
        self.copy_button.setText(self.app_window.tr("copy_response"))
        self.pin_button.setToolTip(self.app_window.tr("toggle_overlay_pin"))
        self.opacity_down_button.setToolTip(self.app_window.tr("decrease_overlay_opacity"))
        self.opacity_up_button.setToolTip(self.app_window.tr("increase_overlay_opacity"))
        self.apply_surface_state()
        self.apply_typography()

    def apply_surface_state(self):
        opacity = int(getattr(self.app_window.config, "overlay_opacity", 96) or 96)
        self.setWindowOpacity(max(0.55, min(1.0, opacity / 100)))
        self.pin_button.setChecked(self.is_pinned)
        self.pin_button.setText(self.app_window.tr("overlay_pinned_short") if self.is_pinned else self.app_window.tr("overlay_pin_short"))
        self.opacity_value_label.setText(f"{opacity}%")
        self.opacity_down_button.setEnabled(opacity > 55)
        self.opacity_up_button.setEnabled(opacity < 100)

    def apply_typography(self):
        self.body.setFont(QFont(self.app_window.current_overlay_font_family(), self.app_window.current_overlay_font_size()))

    def calculate_size(self, text: str):
        lines = text.splitlines() or [text]
        metrics = QFontMetrics(self.body.font())
        longest_width = max((metrics.horizontalAdvance(line or " ") for line in lines), default=240)
        line_spacing = metrics.lineSpacing()
        configured_width = max(self.MIN_WIDTH, int(self.app_window.current_overlay_width() or 440))
        configured_height = max(self.MIN_HEIGHT, int(self.app_window.current_overlay_height() or 520))
        width = min(860, max(configured_width, longest_width + 136))
        height = min(900, max(configured_height, len(lines) * line_spacing + 132))
        return width, height

    def measure_content_height(self, text: str, width: int) -> int:
        doc = QTextDocument()
        doc.setDefaultFont(self.body.font())
        doc.setPlainText(text)
        text_width = max(220, width - 42)
        doc.setTextWidth(text_width)
        header_height = 58
        body_padding = 48
        return int(doc.size().height()) + header_height + body_padding

    def remember_context(self, bbox, text: str, *, anchor_point=None, preset_name: str = ""):
        self.last_bbox = bbox
        self.last_anchor_point = anchor_point
        self.last_text = text
        self.last_preset_name = preset_name or ""

    def copy_text(self):
        if not self.last_text.strip():
            return
        QApplication.clipboard().setText(self.last_text)
        self.app_window.set_status("overlay_copied")

    def toggle_pin(self, checked: bool):
        self.app_window.config.overlay_pinned = bool(checked)
        self.app_window.note_runtime_preference_changed()
        self.apply_surface_state()
        self.app_window.set_status("overlay_pinned" if checked else "overlay_unpinned")

    def adjust_opacity(self, delta: int):
        current = int(getattr(self.app_window.config, "overlay_opacity", 96) or 96)
        next_value = max(55, min(100, current + delta))
        if next_value == current:
            return
        self.app_window.config.overlay_opacity = next_value
        self.app_window.note_runtime_preference_changed()
        self.apply_surface_state()
        self.app_window.set_status("overlay_opacity_set", value=next_value)

    def show_text(self, text: str, x: int, y: int, width: int, height: int, *, keep_manual_position: bool = False):
        self.refresh_language()
        self.setGeometry(x, y, width, height)
        self.last_geometry = self.geometry()
        self.body.setPlainText(text)
        self.last_text = text
        self.manual_positioned = bool(keep_manual_position)
        self.show()
        self.raise_()
        self.activateWindow()

    def restore_last_overlay(self):
        if not self.last_text.strip() or self.last_geometry is None:
            return
        self.refresh_language()
        self.setGeometry(clamp_rect_to_visible_screen(self.last_geometry))
        self.last_geometry = self.geometry()
        self.body.setPlainText(self.last_text)
        self.show()
        self.raise_()
        self.activateWindow()

    def _header_rect(self) -> QRect:
        top_left = self.header.mapTo(self, QPoint(0, 0))
        return QRect(top_left, self.header.size())

    def _event_pos_in_self(self, watched, event: QMouseEvent) -> QPoint:
        local_pos = event.position().toPoint()
        if watched is self:
            return local_pos
        return watched.mapTo(self, local_pos)

    def _resize_mode_at(self, pos: QPoint) -> str | None:
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
            self.last_geometry = self.geometry()
            self.manual_positioned = True
            self._update_cursor(pos)
            return True
        if self._dragging and event.buttons() & Qt.LeftButton:
            self.move(self._clamped_drag_position(event.globalPosition().toPoint()))
            self.manual_positioned = True
            self.last_geometry = self.geometry()
            return True
        self._update_cursor(pos)
        return False

    def _handle_mouse_release(self, watched, event: QMouseEvent) -> bool:
        if event.button() != Qt.LeftButton:
            return False
        released_resize = bool(self._resize_mode)
        self._dragging = False
        self._resize_mode = None
        self.last_geometry = self.geometry()
        self._update_cursor(self._event_pos_in_self(watched, event))
        if released_resize:
            self.overlay_resized.emit(self.width(), self.height())
            return True
        return False

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
        if event.type() == QEvent.Type.Wheel and watched in {self.body, self.body.viewport()}:
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                direction = 1 if event.angleDelta().y() > 0 else -1
                self.request_font_zoom.emit(direction)
                return True
        if isinstance(event, QMouseEvent) and watched in {self.card, self.header, self.title_label, self.body, self.body.viewport()}:
            if event.type() == QEvent.Type.MouseButtonPress and self._handle_mouse_press(watched, event):
                return True
            if event.type() == QEvent.Type.MouseMove and self._handle_mouse_move(watched, event):
                return True
            if event.type() == QEvent.Type.MouseButtonRelease and self._handle_mouse_release(watched, event):
                return True
        if event.type() == QEvent.Type.Leave and watched in {self, self.card, self.header, self.title_label, self.body, self.body.viewport()}:
            if not self._resize_mode and not self._dragging:
                self.unsetCursor()
        return super().eventFilter(watched, event)
