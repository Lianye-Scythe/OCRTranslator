from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QCursor, QFontMetrics, QGuiApplication
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget

from ..ui.theme_tokens import BASE_STYLE_TOKENS, color, qcolor


class _TransientToastWidget(QFrame):
    HORIZONTAL_PADDING = 14
    VERTICAL_PADDING = 10
    MAX_WIDTH = 360
    MIN_WIDTH = 180
    MIN_HEIGHT = 42
    MARGIN = 20

    def __init__(self, window):
        super().__init__(None)
        self.window = window
        self.setObjectName("TransientToast")
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.HORIZONTAL_PADDING, self.VERTICAL_PADDING, self.HORIZONTAL_PADDING, self.VERTICAL_PADDING)
        layout.setSpacing(0)

        self.label = QLabel()
        self.label.setObjectName("TransientToastLabel")
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.PlainText)
        layout.addWidget(self.label)

        self._apply_shadow()
        self.apply_styles()
        self.hide()

    def _theme_name(self) -> str:
        if hasattr(self.window, "effective_theme_name"):
            try:
                return self.window.effective_theme_name()
            except Exception:  # noqa: BLE001
                pass
        return "dark"

    def _apply_shadow(self) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(qcolor("shadow", alpha=52, theme_name=self._theme_name()))
        self.setGraphicsEffect(shadow)

    def apply_styles(self) -> None:
        theme_name = self._theme_name()
        self.setStyleSheet(
            "\n".join(
                [
                    "QFrame#TransientToast {",
                    f"    background:{color('surface_container_high', theme_name=theme_name)};",
                    f"    border:1px solid {color('outline_variant', theme_name=theme_name)};",
                    "    border-radius:14px;",
                    "}",
                    "QLabel#TransientToastLabel {",
                    "    background:transparent;",
                    f"    color:{color('text_primary', theme_name=theme_name)};",
                    f"    font-family:{BASE_STYLE_TOKENS['font_ui']};",
                    "    font-size:12px;",
                    "    font-weight:600;",
                    "}",
                ]
            )
        )
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setColor(qcolor("shadow", alpha=52, theme_name=theme_name))

    def set_message(self, message: str) -> None:
        text = str(message or "").strip()
        self.label.setText(text)
        self._resize_to_fit(text)
        self.reposition()

    def reposition(self) -> None:
        target_rect = self._anchor_rect()
        x = target_rect.right() - self.width() - self.MARGIN
        y = target_rect.bottom() - self.height() - self.MARGIN
        min_x = target_rect.left() + self.MARGIN
        min_y = target_rect.top() + self.MARGIN
        self.move(max(min_x, x), max(min_y, y))

    def _anchor_rect(self) -> QRect:
        workspace = getattr(self.window, "workspace_surface", None)
        if (
            isinstance(workspace, QWidget)
            and workspace.isVisible()
            and getattr(self.window, "isVisible", lambda: False)()
            and not getattr(self.window, "isMinimized", lambda: False)()
        ):
            top_left = workspace.mapToGlobal(QPoint(0, 0))
            return QRect(top_left, workspace.size())
        cursor_screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if cursor_screen is not None:
            return cursor_screen.availableGeometry()
        return QRect(0, 0, 1920, 1080)

    def _resize_to_fit(self, text: str) -> None:
        metrics = QFontMetrics(self.label.font())
        text_rect = metrics.boundingRect(
            QRect(0, 0, self.MAX_WIDTH - self.HORIZONTAL_PADDING * 2, 1000),
            int(Qt.TextWordWrap),
            text,
        )
        width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, text_rect.width() + self.HORIZONTAL_PADDING * 2 + 6))
        height = max(self.MIN_HEIGHT, text_rect.height() + self.VERTICAL_PADDING * 2 + 4)
        self.resize(width, height)


class TransientToastService:
    def __init__(self, window, *, log_func=None):
        self.window = window
        self.log = log_func or (lambda message: None)
        self.widget = _TransientToastWidget(window)
        self._hide_timer = QTimer(self.widget)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.widget.hide)

    def show_message(self, message: str, *, duration_ms: int = 1500) -> bool:
        text = str(message or "").strip()
        if not text or getattr(self.window, "is_quitting", False):
            return False
        self.widget.apply_styles()
        self.widget.set_message(text)
        self.widget.show()
        self.widget.raise_()
        self._hide_timer.start(max(200, int(duration_ms)))
        return True

    def hide_message(self) -> None:
        self._hide_timer.stop()
        self.widget.hide()

    def reposition(self) -> None:
        if self.widget.isVisible():
            self.widget.reposition()

    def close(self) -> None:
        self.hide_message()
        try:
            self.widget.close()
        except Exception:  # noqa: BLE001
            pass


__all__ = ["TransientToastService"]
