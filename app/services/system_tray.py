from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


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

        menu = QMenu(self.window)
        menu.addAction(self.show_action)
        menu.addAction(self.capture_action)
        menu.addAction(self.manual_input_action)
        menu.addAction(self.cancel_action)
        if menu.actions():
            menu.addSeparator()
        menu.addAction(self.quit_action)
        self.tray.setContextMenu(menu)
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
        self.tray.setToolTip(self.window.tr("tray_title"))
        self.show_action.setText(self.window.tr("tray_show"))
        self.capture_action.setText(self.window.tr("tray_capture"))
        self.manual_input_action.setText(self.window.tr("tray_manual_input"))
        self.cancel_action.setText(self.window.tr("cancel_request"))
        self.quit_action.setText(self.window.tr("tray_quit"))

    def show_message(self, message: str):
        if self.tray:
            self.tray.showMessage(self.window.tr("tray_title"), message, self.icon, 2500)

    def close(self):
        if self.tray:
            self.tray.hide()

    def _on_activated(self, reason):
        if not self.tray:
            return
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.window.show_main_window()
