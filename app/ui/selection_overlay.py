from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QRubberBand, QWidget

from .theme_tokens import color, qcolor


class SelectionOverlay(QWidget):
    selected = Signal(tuple)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.rubber_band.setStyleSheet(
            """
            QRubberBand {
                border:2px solid BORDER_COLOR;
                background:OVERLAY_SCRIM;
                border-radius:10px;
            }
            """
            .replace("BORDER_COLOR", color("accent")).replace("OVERLAY_SCRIM", color("overlay_scrim"))
        )
        self.origin = QPoint()
        self.hint_text = ""
        self.virtual_rect = self._get_virtual_rect()
        self.setGeometry(self.virtual_rect)

    def _get_virtual_rect(self) -> QRect:
        screens = QGuiApplication.screens()
        if not screens:
            return QRect(0, 0, 1920, 1080)
        rect = screens[0].geometry()
        for screen in screens[1:]:
            rect = rect.united(screen.geometry())
        return rect

    def show_overlay(self):
        self.virtual_rect = self._get_virtual_rect()
        self.setGeometry(self.virtual_rect)
        self.rubber_band.hide()
        self.show()
        self.raise_()
        self.setFocus(Qt.ActiveWindowFocusReason)
        self.activateWindow()

    def set_hint_text(self, text: str):
        self.hint_text = text
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self.hide()
            self.cancelled.emit()
            return
        if event.button() == Qt.LeftButton:
            self.origin = event.globalPosition().toPoint()
            self.rubber_band.setGeometry(QRect(self.origin - self.pos(), QSize()))
            self.rubber_band.show()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.rubber_band.isVisible():
            return
        current = event.globalPosition().toPoint()
        rect = QRect(self.origin, current).normalized()
        self.rubber_band.setGeometry(QRect(rect.topLeft() - self.pos(), rect.size()))

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton or not self.rubber_band.isVisible():
            return
        current = event.globalPosition().toPoint()
        rect = QRect(self.origin, current).normalized()
        self.rubber_band.hide()
        self.hide()
        if rect.width() < 20 or rect.height() < 20:
            self.cancelled.emit()
            return
        self.selected.emit((rect.left(), rect.top(), rect.right() + 1, rect.bottom() + 1))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            self.cancelled.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(7, 11, 17, 160))
        painter.setPen(QPen(qcolor("accent_soft", alpha=180), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        if self.hint_text:
            painter.setPen(qcolor("text_primary", alpha=220))
            hint_rect = self.rect().adjusted(24, 24, -24, -24)
            painter.drawText(
                hint_rect,
                Qt.AlignTop | Qt.AlignHCenter,
                self.hint_text,
            )
