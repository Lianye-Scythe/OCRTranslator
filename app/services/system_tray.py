import time

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ..ui.theme_tokens import color, resolve_theme_name


class SystemTrayService:
    def __init__(self, window, icon, *, log_func=None):
        self.window = window
        self.icon = icon
        self.log = log_func or (lambda message: None)
        self.tray: QSystemTrayIcon | None = None
        self.show_action: QAction | None = None
        self.capture_action: QAction | None = None
        self.manual_input_action: QAction | None = None
        self.cancel_action: QAction | None = None
        self.quit_action: QAction | None = None
        self.menu: QMenu | None = None
        self._last_message = ""
        self._last_message_at = 0.0

    def _theme_name(self) -> str:
        if hasattr(self.window, "effective_theme_name"):
            try:
                return self.window.effective_theme_name()
            except Exception:  # noqa: BLE001
                pass
        return resolve_theme_name(getattr(getattr(self.window, "config", None), "theme_mode", None))

    def _menu_style_sheet(self) -> str:
        theme_name = self._theme_name()
        return "\n".join(
            [
                "QMenu {",
                f"    background:{color('menu_bg', theme_name=theme_name)};",
                f"    color:{color('menu_fg', theme_name=theme_name)};",
                f"    border:1px solid {color('menu_border', theme_name=theme_name)};",
                "    border-radius:10px; padding:6px;",
                "}",
                "QMenu::item { padding:8px 12px; margin:2px 0; border-radius:8px; background:transparent; }",
                f"QMenu::item:selected {{ background:{color('menu_hover_bg', theme_name=theme_name)}; color:{color('menu_hover_fg', theme_name=theme_name)}; }}",
                f"QMenu::item:disabled {{ color:{color('menu_disabled_fg', theme_name=theme_name)}; background:transparent; }}",
                f"QMenu::separator {{ height:1px; margin:6px 8px; background:{color('menu_separator', theme_name=theme_name)}; }}",
            ]
        )

    def apply_styles(self):
        if self.menu:
            self.menu.setStyleSheet(self._menu_style_sheet())

    def setup(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.window.tray = None
            self.log("System tray is not available on this environment")
            return None
        self.tray = QSystemTrayIcon(self.icon, self.window)
        self.show_action = QAction(self.window)
        self.capture_action = QAction(self.window)
        self.manual_input_action = QAction(self.window)
        self.cancel_action = QAction(self.window)
        self.quit_action = QAction(self.window)
        self.show_action.triggered.connect(self.window.show_main_window)
        self.capture_action.triggered.connect(self.window.start_selection)
        self.manual_input_action.triggered.connect(self.window.open_prompt_input_dialog)
        self.cancel_action.triggered.connect(self.window.cancel_background_operation)
        self.quit_action.triggered.connect(self.window.quit_app)

        self.menu = QMenu(self.window)
        self.menu.addAction(self.show_action)
        self.menu.addAction(self.capture_action)
        self.menu.addAction(self.manual_input_action)
        self.menu.addAction(self.cancel_action)
        if self.menu.actions():
            self.menu.addSeparator()
        self.menu.addAction(self.quit_action)
        self.apply_styles()
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)

        self.window.tray = self.tray
        self.window.tray_show_action = self.show_action
        self.window.tray_capture_action = self.capture_action
        self.window.tray_manual_input_action = self.manual_input_action
        self.window.tray_cancel_action = self.cancel_action
        self.window.tray_quit_action = self.quit_action

        self.update_texts()
        self.tray.show()
        return self.tray

    def update_texts(self):
        if not self.tray:
            return
        self.apply_styles()
        self.tray.setToolTip(self.window.tr("tray_title"))
        self.show_action.setText(self.window.tr("tray_show"))
        self.capture_action.setText(self.window.tr("tray_capture"))
        self.manual_input_action.setText(self.window.tr("tray_manual_input"))
        self.cancel_action.setText(self.window.tr("cancel_request"))
        self.quit_action.setText(self.window.tr("tray_quit"))

    def show_message(self, message: str, *, duration_ms: int = 1500) -> bool:
        text = str(message or "").strip()
        if not self.tray or not text:
            return False
        now = time.monotonic()
        if text == self._last_message and (now - self._last_message_at) < 1.6:
            self.log(f"Suppressed duplicate tray message: {text}")
            return False
        self._last_message = text
        self._last_message_at = now
        self.tray.showMessage(self.window.tr("tray_title"), text, self.icon, int(duration_ms))
        return True

    def close(self):
        if self.tray:
            self.tray.hide()
        self.menu = None
        self._last_message = ""
        self._last_message_at = 0.0

    def _on_activated(self, reason):
        if not self.tray:
            return
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.window.show_main_window()
