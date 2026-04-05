from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QInputMethodEvent, QPainter, QPalette
from PySide6.QtWidgets import QPlainTextEdit


class ImeAwarePlainTextEdit(QPlainTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._placeholder_text = ""
        self._has_preedit_text = False
        self.textChanged.connect(self._refresh_placeholder_state)
        super().setPlaceholderText("")

    def setPlaceholderText(self, text: str) -> None:  # noqa: N802
        self._placeholder_text = str(text or "")
        super().setPlaceholderText("")
        self._refresh_placeholder_state()

    def placeholderText(self) -> str:  # noqa: N802
        return self._placeholder_text

    def placeholder_visible(self) -> bool:
        return bool(self._placeholder_text) and not self._has_preedit_text and not bool(self.toPlainText())

    def inputMethodEvent(self, event: QInputMethodEvent) -> None:
        self._has_preedit_text = bool(event.preeditString())
        super().inputMethodEvent(event)
        self._refresh_placeholder_state()

    def focusOutEvent(self, event) -> None:
        self._has_preedit_text = False
        super().focusOutEvent(event)
        self._refresh_placeholder_state()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self.placeholder_visible():
            return
        painter = QPainter(self.viewport())
        painter.setPen(self._placeholder_color())
        painter.setFont(self.font())
        document_margin = int(self.document().documentMargin())
        placeholder_rect = self.viewport().rect().adjusted(document_margin + 1, document_margin, -document_margin, -document_margin)
        painter.drawText(placeholder_rect, Qt.AlignTop | Qt.AlignLeft | Qt.TextWordWrap, self._placeholder_text)

    def _refresh_placeholder_state(self) -> None:
        viewport = getattr(self, "viewport", None)
        if callable(viewport):
            area = viewport()
            if area is not None:
                area.update()
                return
        self.update()

    def _placeholder_color(self) -> QColor:
        palette = self.palette()
        placeholder_role = getattr(QPalette.ColorRole, "PlaceholderText", None)
        if placeholder_role is not None:
            color = palette.color(placeholder_role)
            if color.isValid():
                return color
        color = palette.color(QPalette.ColorRole.Text)
        color.setAlpha(120)
        return color


__all__ = ["ImeAwarePlainTextEdit"]
