import ctypes
import time

from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication


COPY_TRIGGER_SETTLE_SECONDS = 0.08
COPY_TRIGGER_TIMEOUT_SECONDS = 0.65
COPY_TRIGGER_POLL_SECONDS = 0.02
HOTKEY_RELEASE_TIMEOUT_SECONDS = 1.0

USER32 = ctypes.windll.user32
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_RETURN = 0x0D
VK_TAB = 0x09
VK_SPACE = 0x20
VK_BACK = 0x08
VK_DELETE = 0x2E
VK_INSERT = 0x2D
VK_HOME = 0x24
VK_END = 0x23
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_UP = 0x26
VK_DOWN = 0x28
VK_ESCAPE = 0x1B

SPECIAL_VIRTUAL_KEYS = {
    "ctrl": [VK_CONTROL],
    "control": [VK_CONTROL],
    "alt": [VK_MENU],
    "shift": [VK_SHIFT],
    "win": [VK_LWIN, VK_RWIN],
    "windows": [VK_LWIN, VK_RWIN],
    "cmd": [VK_LWIN, VK_RWIN],
    "meta": [VK_LWIN, VK_RWIN],
    "enter": [VK_RETURN],
    "return": [VK_RETURN],
    "tab": [VK_TAB],
    "space": [VK_SPACE],
    "backspace": [VK_BACK],
    "delete": [VK_DELETE],
    "insert": [VK_INSERT],
    "home": [VK_HOME],
    "end": [VK_END],
    "pageup": [VK_PRIOR],
    "page_up": [VK_PRIOR],
    "pagedown": [VK_NEXT],
    "page_down": [VK_NEXT],
    "left": [VK_LEFT],
    "right": [VK_RIGHT],
    "up": [VK_UP],
    "down": [VK_DOWN],
    "esc": [VK_ESCAPE],
    "escape": [VK_ESCAPE],
}


def _clone_mime_data(mime_data) -> tuple[QMimeData, bool]:
    clone = QMimeData()
    if not mime_data:
        return clone, False
    has_payload = False
    for fmt in mime_data.formats():
        clone.setData(fmt, mime_data.data(fmt))
        has_payload = True
    return clone, has_payload


def _clipboard_sequence_number() -> int | None:
    try:
        return int(USER32.GetClipboardSequenceNumber())
    except Exception:  # noqa: BLE001
        return None


def _clipboard_state_matches_capture(
    *,
    expected_sequence: int | None,
    current_sequence: int | None,
    expected_text: str | None,
    current_text: str,
) -> bool:
    if expected_sequence is not None and current_sequence is not None and current_sequence != expected_sequence:
        return False
    if expected_text is not None and current_text != expected_text:
        return False
    return True


def _restore_clipboard(clipboard, mime_data: QMimeData, had_payload: bool) -> None:
    if had_payload:
        clipboard.setMimeData(mime_data)
    else:
        clipboard.clear()


def _restore_clipboard_if_unchanged(clipboard, mime_data: QMimeData, had_payload: bool, *, expected_sequence: int | None, expected_text: str | None) -> bool:
    current_sequence = _clipboard_sequence_number()
    current_text = clipboard.text()
    if not _clipboard_state_matches_capture(expected_sequence=expected_sequence, current_sequence=current_sequence, expected_text=expected_text, current_text=current_text):
        return False
    _restore_clipboard(clipboard, mime_data, had_payload)
    return True


def _virtual_key_codes_for_hotkey(hotkey_text: str) -> list[int]:
    parts = [part.strip().lower() for part in str(hotkey_text or "").replace("-", "+").split("+") if part.strip()]
    codes: list[int] = []
    for part in parts:
        if part in SPECIAL_VIRTUAL_KEYS:
            codes.extend(SPECIAL_VIRTUAL_KEYS[part])
            continue
        if len(part) == 1 and part.isalnum():
            codes.append(ord(part.upper()))
            continue
        if part.startswith("f") and part[1:].isdigit():
            index = int(part[1:])
            if 1 <= index <= 24:
                codes.append(0x6F + index)
    return list(dict.fromkeys(codes))


def _is_virtual_key_pressed(virtual_key: int) -> bool:
    try:
        return bool(USER32.GetAsyncKeyState(int(virtual_key)) & 0x8000)
    except Exception:  # noqa: BLE001
        return False


def _wait_for_hotkey_release(hotkey_text: str, *, timeout_seconds: float, poll_seconds: float) -> None:
    virtual_keys = _virtual_key_codes_for_hotkey(hotkey_text)
    if not virtual_keys:
        return
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if not any(_is_virtual_key_pressed(virtual_key) for virtual_key in virtual_keys):
            return
        time.sleep(poll_seconds)


def capture_selected_text(
    *,
    hotkey_text: str = "",
    settle_seconds: float = COPY_TRIGGER_SETTLE_SECONDS,
    timeout_seconds: float = COPY_TRIGGER_TIMEOUT_SECONDS,
    poll_seconds: float = COPY_TRIGGER_POLL_SECONDS,
) -> str:
    app = QApplication.instance()
    if app is None:
        raise RuntimeError("A QApplication instance is required to capture selected text.")

    clipboard = app.clipboard()
    backup_mime, had_backup_payload = _clone_mime_data(clipboard.mimeData())
    backup_text = clipboard.text()
    initial_sequence = _clipboard_sequence_number()
    captured_sequence = None
    captured_text = None

    try:
        _wait_for_hotkey_release(
            hotkey_text,
            timeout_seconds=HOTKEY_RELEASE_TIMEOUT_SECONDS,
            poll_seconds=poll_seconds,
        )

        deadline = time.monotonic() + max(0.0, settle_seconds)
        while time.monotonic() < deadline:
            QApplication.processEvents()
            time.sleep(min(poll_seconds, max(0.0, deadline - time.monotonic())))

        from pynput.keyboard import Controller, Key

        controller = Controller()
        with controller.pressed(Key.ctrl):
            controller.press("c")
            controller.release("c")

        changed = False
        deadline = time.monotonic() + max(0.0, timeout_seconds)
        while time.monotonic() < deadline:
            QApplication.processEvents()
            time.sleep(poll_seconds)
            current_sequence = _clipboard_sequence_number()
            current_text = clipboard.text()
            if initial_sequence is not None and current_sequence is not None:
                if current_sequence != initial_sequence:
                    changed = True
                    captured_sequence = current_sequence
                    captured_text = current_text
                    break
            elif current_text != backup_text:
                changed = True
                captured_sequence = current_sequence
                captured_text = current_text
                break

        copied_text = clipboard.text().strip() if changed else ""
    finally:
        if captured_sequence is None and captured_text is None:
            _restore_clipboard(clipboard, backup_mime, had_backup_payload)
        else:
            _restore_clipboard_if_unchanged(
                clipboard,
                backup_mime,
                had_backup_payload,
                expected_sequence=captured_sequence,
                expected_text=captured_text,
            )
    QApplication.processEvents()
    return copied_text
