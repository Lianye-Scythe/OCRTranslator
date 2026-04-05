from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from shiboken6 import isValid


def clear_focus_if_alive(widget) -> None:
    if widget is None:
        return
    try:
        if not isValid(widget):
            return
        widget.clearFocus()
    except (RuntimeError, TypeError, AttributeError):
        return


def schedule_clear_focus(widget) -> None:
    QTimer.singleShot(0, lambda watched=widget: clear_focus_if_alive(watched))


class _MouseClickFocusClearFilter(QObject):
    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonRelease and getattr(event, "button", lambda: None)() == Qt.LeftButton:
            schedule_clear_focus(watched)
        return False


def install_mouse_click_focus_clear(widget):
    if widget is None or not hasattr(widget, "installEventFilter"):
        return None
    filter_obj = _MouseClickFocusClearFilter(widget)
    widget.installEventFilter(filter_obj)
    setattr(widget, "_mouse_click_focus_clear_filter", filter_obj)
    return filter_obj


def install_mouse_click_focus_clear_many(*widgets):
    installed = []
    for widget in widgets:
        filter_obj = install_mouse_click_focus_clear(widget)
        if filter_obj is not None:
            installed.append(filter_obj)
    return installed
