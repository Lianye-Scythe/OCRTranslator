from PySide6.QtCore import QEvent, QPoint, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QMouseEvent, QTextDocument
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


class TranslationOverlay(QWidget):
    request_font_zoom = Signal(int)

    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.last_bbox = None
        self.last_text = ""
        self.last_geometry = None
        self.manual_positioned = False
        self._drag_offset = QPoint()
        self.setup_ui()

    @property
    def is_pinned(self) -> bool:
        return bool(getattr(self.app_window.config, "overlay_pinned", False))

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setObjectName("overlayCard")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(3, 8, 18, 190))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self.header = QFrame()
        self.header.setObjectName("overlayHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(16, 12, 12, 12)
        header_layout.setSpacing(8)

        self.title_label = QLabel()
        self.title_label.setObjectName("overlayTitleLabel")

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
        self.body.viewport().installEventFilter(self)
        self.body.installEventFilter(self)

        card_layout.addWidget(self.header)
        card_layout.addWidget(self.body)
        outer.addWidget(self.card)

        self.apply_styles()
        self.refresh_language()
        self.apply_surface_state()

    def apply_styles(self):
        self.setStyleSheet(
            """
            #overlayCard {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #141c28, stop:1 #101720);
                border:1px solid #253244;
                border-radius:22px;
            }
            #overlayHeader {
                background:#151f2e;
                border-top-left-radius:22px;
                border-top-right-radius:22px;
                border-bottom:1px solid #263448;
            }
            #overlayTitleLabel {
                color:#f4efe6;
                font-size:14px;
                font-weight:700;
            }
            #overlayValueChip {
                background:#121c2a;
                color:#dbe5f8;
                border:1px solid #31425a;
                border-radius:12px;
                padding:0 10px;
                font-size:12px;
                font-weight:700;
            }
            #overlayBody {
                background:#101720;
                color:#eef3fb;
                border:none;
                padding:14px 16px 16px 16px;
                border-bottom-left-radius:22px;
                border-bottom-right-radius:22px;
                selection-background-color:#7489ff;
            }
            #overlayCloseButton {
                background:#182130;
                color:#e8eef9;
                border:1px solid #2d3b4f;
                border-radius:12px;
                font-size:18px;
                font-weight:600;
            }
            #overlayActionButton {
                background:#1d293a;
                color:#edf2fb;
                border:1px solid #31425a;
                border-radius:12px;
                padding:0 12px;
                font-weight:700;
            }
            #overlayActionButton:checked {
                background:#7489ff;
                color:#0f1420;
                border:1px solid #93a3ff;
            }
            #overlayCloseButton:hover {
                background:#1d2839;
            }
            #overlayActionButton:focus,
            #overlayCloseButton:focus {
                border:1px solid #90a4ff;
            }
            #overlayActionButton:hover {
                background:#243245;
            }
            QScrollBar:vertical {
                width:10px;
                margin:2px;
                background:transparent;
            }
            QScrollBar::handle:vertical {
                background:#2d3a4c;
                border-radius:5px;
                min-height:28px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background:none;
                border:none;
                height:0;
            }
            """
        )

    def refresh_language(self):
        self.title_label.setText(self.app_window.tr("overlay_title"))
        self.copy_button.setText(self.app_window.tr("copy_translation"))
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
        configured_width = max(380, int(getattr(self.app_window.config, "overlay_width", 440) or 440))
        configured_height = max(240, int(getattr(self.app_window.config, "overlay_height", 520) or 520))
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

    def remember_context(self, bbox, text: str):
        self.last_bbox = bbox
        self.last_text = text

    def copy_text(self):
        if not self.last_text.strip():
            return
        QApplication.clipboard().setText(self.last_text)
        self.app_window.set_status("overlay_copied")

    def toggle_pin(self, checked: bool):
        self.app_window.config.overlay_pinned = bool(checked)
        self.app_window.schedule_config_persist()
        self.apply_surface_state()
        self.app_window.set_status("overlay_pinned" if checked else "overlay_unpinned")

    def adjust_opacity(self, delta: int):
        current = int(getattr(self.app_window.config, "overlay_opacity", 96) or 96)
        next_value = max(55, min(100, current + delta))
        if next_value == current:
            return
        self.app_window.config.overlay_opacity = next_value
        self.app_window.schedule_config_persist()
        self.apply_surface_state()
        self.app_window.set_status("overlay_opacity_set", value=next_value)

    def show_text(self, text: str, x: int, y: int, width: int, height: int, *, keep_manual_position: bool = False):
        self.apply_surface_state()
        self.setGeometry(x, y, width, height)
        self.last_geometry = self.geometry()
        self.body.setPlainText(text)
        self.last_text = text
        self.manual_positioned = bool(keep_manual_position)
        self.show()
        self.raise_()

    def restore_last_overlay(self):
        if not self.last_text.strip() or self.last_geometry is None:
            return
        self.apply_surface_state()
        self.setGeometry(self.last_geometry)
        self.body.setPlainText(self.last_text)
        self.show()
        self.raise_()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            self.manual_positioned = True
            self.last_geometry = self.geometry()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Wheel and QApplication.keyboardModifiers() & Qt.ControlModifier:
            direction = 1 if event.angleDelta().y() > 0 else -1
            self.request_font_zoom.emit(direction)
            return True
        return super().eventFilter(watched, event)
