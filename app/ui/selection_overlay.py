from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QMouseEvent, QPainter, QPen, QPixmap
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
        self.origin = QPoint()
        self.hint_text = ""
        self.virtual_rect = self._get_virtual_rect()
        self.setGeometry(self.virtual_rect)
        self.background_pixmap = QPixmap()
        self.apply_theme()

    def _get_virtual_rect(self) -> QRect:
        screens = QGuiApplication.screens()
        if not screens:
            return QRect(0, 0, 1920, 1080)
        rect = screens[0].geometry()
        for screen in screens[1:]:
            rect = rect.united(screen.geometry())
        return rect

    def _rubber_band_style_sheet(self) -> str:
        return (
            "QRubberBand {"
            f"border:2px solid {color('secondary_border')};"
            f"background:{color('scrim')};"
            "border-radius:12px;"
            "}"
        )

    def apply_theme(self):
        self.rubber_band.setStyleSheet(self._rubber_band_style_sheet())
        self.update()

    def set_snapshot_background(self, pixmap: QPixmap | None, *, virtual_rect=None):
        if virtual_rect is not None:
            self.virtual_rect = QRect(*virtual_rect) if not isinstance(virtual_rect, QRect) else QRect(virtual_rect)
            self.setGeometry(self.virtual_rect)
        self.background_pixmap = QPixmap(pixmap) if pixmap is not None else QPixmap()
        self.update()

    def clear_snapshot_background(self):
        self.background_pixmap = QPixmap()
        self.update()

    def show_overlay(self):
        if self.background_pixmap.isNull():
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
        selection = (rect.left(), rect.top(), rect.right() + 1, rect.bottom() + 1)
        self.selected.emit(selection)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            self.cancelled.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background_pixmap.isNull():
            painter.drawPixmap(self.rect(), self.background_pixmap)
        painter.fillRect(self.rect(), QColor(7, 11, 17, 160))
        painter.setPen(QPen(qcolor("primary_container", alpha=180), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        if self.hint_text:
            painter.setPen(qcolor("on_surface", alpha=220, theme_name="dark"))
            hint_rect = self.rect().adjusted(24, 24, -24, -24)
            painter.drawText(
                hint_rect,
                Qt.AlignTop | Qt.AlignHCenter,
                self.hint_text,
            )
