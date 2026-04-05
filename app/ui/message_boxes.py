from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialogButtonBox, QLabel, QMessageBox

from .focus_utils import clear_focus_if_alive, install_mouse_click_focus_clear_many
from .style_utils import load_style_sheet
from .theme_tokens import current_theme_name


@dataclass(frozen=True)
class MessageBoxAction:
    text: str
    role: QMessageBox.ButtonRole
    result: Any
    variant: str = "neutral"
    is_default: bool = False
    is_escape: bool = False


def _resolve_theme_name(parent=None, theme_name: str | None = None) -> str:
    if theme_name:
        return theme_name
    if parent is not None and hasattr(parent, "effective_theme_name"):
        try:
            resolved = parent.effective_theme_name()
            if resolved:
                return resolved
        except Exception:  # noqa: BLE001
            pass
    return current_theme_name()


def _dialog_style_sheet(parent=None, *, theme_name: str | None = None) -> str:
    if parent is not None and hasattr(parent, "styleSheet"):
        try:
            inherited = parent.styleSheet()
            if inherited:
                return inherited
        except Exception:  # noqa: BLE001
            pass
    return load_style_sheet("main_window.qss", theme_name=_resolve_theme_name(parent, theme_name))


def _refresh_style(widget) -> None:
    if widget is None or not hasattr(widget, "style"):
        return
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    if hasattr(widget, "update"):
        widget.update()


def _set_button_variant(button, variant: str) -> None:
    if button is None or not hasattr(button, "setProperty"):
        return
    button.setProperty("variant", variant)
    _refresh_style(button)


def _clear_dialog_initial_focus(dialog, buttons: Iterable) -> None:
    for button in buttons:
        clear_focus_if_alive(button)
    clear_focus_if_alive(dialog)


def _strip_button_mnemonics(text: str) -> str:
    return text.replace("&&", "&").replace("&", "")


def _fit_dialog_buttons(dialog: QMessageBox, button_box: QDialogButtonBox | None, buttons: list) -> None:
    if not buttons:
        return

    required_widths = []
    for button in buttons:
        label = _strip_button_mnemonics(button.text())
        text_width = button.fontMetrics().horizontalAdvance(label)
        estimated_width = len(label) * 7 + 28
        hinted_width = button.sizeHint().width()
        target_width = max(96, text_width + 48, estimated_width, hinted_width)
        button.setMinimumWidth(target_width)
        required_widths.append(target_width)

    if button_box is None or button_box.layout() is None:
        return
    spacing = max(0, button_box.layout().spacing())
    dialog_margins = dialog.layout().contentsMargins() if dialog.layout() is not None else None
    extra_width = (dialog_margins.left() + dialog_margins.right() + 40) if dialog_margins is not None else 40
    button_row_width = sum(required_widths) + spacing * max(0, len(required_widths) - 1)
    dialog.setMinimumWidth(max(dialog.minimumWidth(), button_row_width + extra_width))


def _center_dialog_text_block(dialog: QMessageBox) -> None:
    layout = dialog.layout()
    if layout is None:
        return

    for object_name in ("qt_msgbox_label", "qt_msgbox_informativelabel"):
        label = dialog.findChild(QLabel, object_name)
        if label is None:
            continue
        label.setContentsMargins(10, 8, 10, 8)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.setAlignment(label, Qt.AlignHCenter | Qt.AlignVCenter)

    icon_label = dialog.findChild(QLabel, "qt_msgboxex_icon_label")
    if icon_label is not None:
        icon_label.setContentsMargins(8, 2, 4, 0)


def _refine_dialog_layout(dialog: QMessageBox, buttons: list, *, center_text: bool = False) -> None:
    layout = dialog.layout()
    if layout is not None:
        layout.setContentsMargins(24, 20, 24, 18)
        if hasattr(layout, "setHorizontalSpacing"):
            layout.setHorizontalSpacing(14)
        if hasattr(layout, "setVerticalSpacing"):
            layout.setVerticalSpacing(10)

    text_label = dialog.findChild(QLabel, "qt_msgbox_label")
    if text_label is not None:
        text_label.setWordWrap(True)
        text_label.setMinimumWidth(max(text_label.minimumWidth(), 320))
        text_label.setAlignment((Qt.AlignLeft | Qt.AlignVCenter) if center_text else (Qt.AlignLeft | Qt.AlignTop))

    info_label = dialog.findChild(QLabel, "qt_msgbox_informativelabel")
    if info_label is not None:
        info_label.setWordWrap(True)
        info_label.setAlignment((Qt.AlignLeft | Qt.AlignVCenter) if center_text else (Qt.AlignLeft | Qt.AlignTop))

    icon_label = dialog.findChild(QLabel, "qt_msgboxex_icon_label")
    if icon_label is not None:
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        icon_label.setContentsMargins(0, 2, 12, 0)
        pixmap = icon_label.pixmap()
        if pixmap is not None and not pixmap.isNull():
            icon_label.setPixmap(
                pixmap.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            icon_label.setAlignment(Qt.AlignCenter)

    button_box = dialog.findChild(QDialogButtonBox)
    if button_box is not None and button_box.layout() is not None:
        button_box.layout().setContentsMargins(0, 14, 0, 0)
        button_box.layout().setSpacing(10)

    for button in buttons:
        button.setProperty("compact", True)
        _refresh_style(button)


def _polish_dialog(dialog: QMessageBox, buttons: list, *, parent=None, theme_name: str | None = None, preserve_initial_focus: bool = False, tone: str = "neutral", center_text: bool = False) -> None:
    dialog.setProperty("messageBox", True)
    dialog.setProperty("messageBoxTone", tone)
    _refine_dialog_layout(dialog, buttons, center_text=center_text)
    dialog.setStyleSheet(_dialog_style_sheet(parent, theme_name=theme_name))
    dialog.ensurePolished()
    for button in buttons:
        button.ensurePolished()
    if center_text:
        _center_dialog_text_block(dialog)
    dialog._mouse_focus_clear_filters = install_mouse_click_focus_clear_many(*buttons)
    _fit_dialog_buttons(dialog, dialog.findChild(QDialogButtonBox), buttons)
    if not preserve_initial_focus:
        QTimer.singleShot(0, lambda dlg=dialog, btns=tuple(buttons): _clear_dialog_initial_focus(dlg, btns))


def show_standard_message_box(
    parent,
    title: str,
    text: str,
    *,
    icon: QMessageBox.Icon,
    buttons: Iterable[QMessageBox.StandardButton],
    default_button: QMessageBox.StandardButton | None = None,
    escape_button: QMessageBox.StandardButton | None = None,
    button_variants: dict[QMessageBox.StandardButton, str] | None = None,
    informative_text: str = "",
    detailed_text: str = "",
    theme_name: str | None = None,
    prefer_native: bool = False,
    tone: str = "neutral",
    preserve_initial_focus: bool = False,
    center_text: bool = False,
) -> QMessageBox.StandardButton:
    dialog = QMessageBox(parent)
    dialog.setIcon(icon)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    if informative_text:
        dialog.setInformativeText(informative_text)
    if detailed_text:
        dialog.setDetailedText(detailed_text)

    button_map: dict[QMessageBox.StandardButton, object] = {}
    for standard_button in buttons:
        button = dialog.addButton(standard_button)
        button_map[standard_button] = button
        if not prefer_native:
            _set_button_variant(button, (button_variants or {}).get(standard_button, "neutral"))

    if default_button in button_map:
        dialog.setDefaultButton(button_map[default_button])
    if escape_button in button_map:
        dialog.setEscapeButton(button_map[escape_button])

    if not prefer_native:
        _polish_dialog(
            dialog,
            list(button_map.values()),
            parent=parent,
            theme_name=theme_name,
            tone=tone,
            preserve_initial_focus=preserve_initial_focus,
            center_text=center_text,
        )

    dialog.exec()
    clicked = dialog.clickedButton()
    if clicked is None:
        return escape_button or QMessageBox.NoButton
    return dialog.standardButton(clicked)


def show_custom_message_box(
    parent,
    title: str,
    text: str,
    *,
    icon: QMessageBox.Icon,
    actions: list[MessageBoxAction],
    informative_text: str = "",
    detailed_text: str = "",
    theme_name: str | None = None,
    prefer_native: bool = False,
    preserve_initial_focus: bool = False,
    tone: str = "neutral",
    escape_result: Any = None,
    center_text: bool = False,
):
    dialog = QMessageBox(parent)
    dialog.setIcon(icon)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    if informative_text:
        dialog.setInformativeText(informative_text)
    if detailed_text:
        dialog.setDetailedText(detailed_text)

    result_map: dict[object, Any] = {}
    buttons = []
    resolved_escape_result = escape_result
    for action in actions:
        button = dialog.addButton(action.text, action.role)
        buttons.append(button)
        result_map[button] = action.result
        if action.is_default:
            dialog.setDefaultButton(button)
        if action.is_escape:
            dialog.setEscapeButton(button)
            resolved_escape_result = action.result
        if not prefer_native:
            _set_button_variant(button, action.variant)

    if not prefer_native:
        _polish_dialog(
            dialog,
            buttons,
            parent=parent,
            theme_name=theme_name,
            tone=tone,
            preserve_initial_focus=preserve_initial_focus,
            center_text=center_text,
        )

    dialog.exec()
    clicked = dialog.clickedButton()
    if clicked is None:
        return resolved_escape_result
    return result_map.get(clicked, resolved_escape_result)


def show_information_message(parent, title: str, text: str, *, theme_name: str | None = None, prefer_native: bool = False) -> QMessageBox.StandardButton:
    return show_standard_message_box(
        parent,
        title,
        text,
        icon=QMessageBox.Information,
        buttons=[QMessageBox.Ok],
        default_button=QMessageBox.Ok,
        escape_button=QMessageBox.Ok,
        button_variants={QMessageBox.Ok: "primary"},
        theme_name=theme_name,
        prefer_native=prefer_native,
        tone="information",
    )


def show_warning_message(parent, title: str, text: str, *, theme_name: str | None = None, prefer_native: bool = False) -> QMessageBox.StandardButton:
    return show_standard_message_box(
        parent,
        title,
        text,
        icon=QMessageBox.Warning,
        buttons=[QMessageBox.Ok],
        default_button=QMessageBox.Ok,
        escape_button=QMessageBox.Ok,
        button_variants={QMessageBox.Ok: "primary"},
        theme_name=theme_name,
        prefer_native=prefer_native,
        tone="warning",
    )


def show_critical_message(parent, title: str, text: str, *, theme_name: str | None = None, prefer_native: bool = False) -> QMessageBox.StandardButton:
    return show_standard_message_box(
        parent,
        title,
        text,
        icon=QMessageBox.Critical,
        buttons=[QMessageBox.Ok],
        default_button=QMessageBox.Ok,
        escape_button=QMessageBox.Ok,
        button_variants={QMessageBox.Ok: "primary"},
        theme_name=theme_name,
        prefer_native=prefer_native,
        tone="critical",
    )


def show_question_message(
    parent,
    title: str,
    text: str,
    *,
    yes_variant: str = "primary",
    no_variant: str = "neutral",
    theme_name: str | None = None,
    prefer_native: bool = False,
    preserve_initial_focus: bool = False,
) -> QMessageBox.StandardButton:
    return show_standard_message_box(
        parent,
        title,
        text,
        icon=QMessageBox.Question,
        buttons=[QMessageBox.Yes, QMessageBox.No],
        default_button=QMessageBox.No,
        escape_button=QMessageBox.No,
        button_variants={
            QMessageBox.Yes: yes_variant,
            QMessageBox.No: no_variant,
        },
        theme_name=theme_name,
        prefer_native=prefer_native,
        tone="question",
        preserve_initial_focus=preserve_initial_focus,
    )


def show_destructive_confirmation(
    parent,
    title: str,
    text: str,
    *,
    confirm_text: str,
    cancel_text: str,
    theme_name: str | None = None,
    prefer_native: bool = False,
    preserve_initial_focus: bool = False,
) -> bool:
    return bool(
        show_custom_message_box(
            parent,
            title,
            text,
            icon=QMessageBox.Warning,
            actions=[
                MessageBoxAction(cancel_text, QMessageBox.RejectRole, False, variant="neutral", is_default=True, is_escape=True),
                MessageBoxAction(confirm_text, QMessageBox.DestructiveRole, True, variant="danger"),
            ],
            theme_name=theme_name,
            prefer_native=prefer_native,
            tone="destructive",
            preserve_initial_focus=preserve_initial_focus,
            escape_result=False,
        )
    )


def show_non_blocking_critical_message(parent, title: str, text: str, *, theme_name: str | None = None):
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Critical)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    button = dialog.addButton(QMessageBox.Ok)
    dialog.setDefaultButton(button)
    dialog.setEscapeButton(button)
    dialog.setAttribute(Qt.WA_DeleteOnClose, True)
    dialog.setModal(False)
    dialog.setWindowModality(Qt.NonModal)
    dialog.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    _set_button_variant(button, "primary")
    _polish_dialog(
        dialog,
        [button],
        parent=parent,
        theme_name=theme_name,
        tone="critical",
        preserve_initial_focus=False,
    )
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    return dialog
