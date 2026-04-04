import ctypes
import time

from PySide6.QtCore import QObject, QMimeData, QTimer, Signal
from PySide6.QtWidgets import QApplication

from ...hotkey_utils import canonical_hotkey_parts


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
    "alt": [VK_MENU],
    "shift": [VK_SHIFT],
    "win": [VK_LWIN, VK_RWIN],
    "enter": [VK_RETURN],
    "tab": [VK_TAB],
    "space": [VK_SPACE],
    "backspace": [VK_BACK],
    "delete": [VK_DELETE],
    "insert": [VK_INSERT],
    "home": [VK_HOME],
    "end": [VK_END],
    "page_up": [VK_PRIOR],
    "page_down": [VK_NEXT],
    "left": [VK_LEFT],
    "right": [VK_RIGHT],
    "up": [VK_UP],
    "down": [VK_DOWN],
    "escape": [VK_ESCAPE],
}


class SelectedTextCaptureSession(QObject):
    finished = Signal(str)
    failed = Signal(object)
    cancelled = Signal()

    def __init__(
        self,
        *,
        hotkey_text: str = "",
        settle_seconds: float = COPY_TRIGGER_SETTLE_SECONDS,
        timeout_seconds: float = COPY_TRIGGER_TIMEOUT_SECONDS,
        poll_seconds: float = COPY_TRIGGER_POLL_SECONDS,
        release_timeout_seconds: float = HOTKEY_RELEASE_TIMEOUT_SECONDS,
        copy_sender=None,
        monotonic_func=None,
        parent=None,
    ):
        super().__init__(parent)
        self.hotkey_text = hotkey_text
        self.settle_seconds = max(0.0, float(settle_seconds or 0.0))
        self.timeout_seconds = max(0.0, float(timeout_seconds or 0.0))
        self.poll_seconds = max(0.01, float(poll_seconds or 0.0))
        self.release_timeout_seconds = max(0.0, float(release_timeout_seconds or 0.0))
        self._copy_sender = copy_sender or _send_copy_shortcut
        self._monotonic = monotonic_func or time.monotonic
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._advance)
        self._phase = "idle"
        self._phase_deadline = 0.0
        self._clipboard = None
        self._backup_mime = QMimeData()
        self._had_backup_payload = False
        self._backup_text = ""
        self._initial_sequence = None
        self._captured_sequence = None
        self._captured_text = None
        self._virtual_keys: list[int] = []

    def start(self) -> None:
        if self._phase != "idle":
            return
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("A QApplication instance is required to capture selected text.")
        self._clipboard = app.clipboard()
        self._backup_mime, self._had_backup_payload = _clone_mime_data(self._clipboard.mimeData())
        self._backup_text = self._clipboard.text()
        self._initial_sequence = _clipboard_sequence_number()
        self._captured_sequence = None
        self._captured_text = None
        self._virtual_keys = _virtual_key_codes_for_hotkey(self.hotkey_text)
        if self._virtual_keys:
            self._phase = "wait_release"
            self._phase_deadline = self._monotonic() + self.release_timeout_seconds
        else:
            self._phase = "settle"
            self._phase_deadline = self._monotonic() + self.settle_seconds
        self._schedule_next(0.0)

    def cancel(self) -> bool:
        if self._phase in {"idle", "done"}:
            return False
        self._restore_clipboard_state()
        self._finish(signal_name="cancelled")
        return True

    def _advance(self) -> None:
        if self._phase == "wait_release":
            self._advance_wait_release()
            return
        if self._phase == "settle":
            self._advance_settle()
            return
        if self._phase == "wait_clipboard":
            self._advance_wait_clipboard()

    def _advance_wait_release(self) -> None:
        try:
            if not any(_is_virtual_key_pressed(virtual_key) for virtual_key in self._virtual_keys) or self._monotonic() >= self._phase_deadline:
                self._phase = "settle"
                self._phase_deadline = self._monotonic() + self.settle_seconds
                self._schedule_until_deadline()
                return
            self._schedule_until_deadline()
        except Exception as exc:  # noqa: BLE001
            self._finish_failed(exc)

    def _advance_settle(self) -> None:
        if self._monotonic() < self._phase_deadline:
            self._schedule_until_deadline()
            return
        try:
            self._copy_sender()
        except Exception as exc:  # noqa: BLE001
            self._finish_failed(exc)
            return
        self._phase = "wait_clipboard"
        self._phase_deadline = self._monotonic() + self.timeout_seconds
        self._schedule_until_deadline()

    def _advance_wait_clipboard(self) -> None:
        try:
            current_sequence = _clipboard_sequence_number()
            current_text = self._clipboard.text() if self._clipboard else ""
            changed = False
            if self._initial_sequence is not None and current_sequence is not None:
                changed = current_sequence != self._initial_sequence
            elif current_text != self._backup_text:
                changed = True
            if changed:
                self._captured_sequence = current_sequence
                self._captured_text = current_text
                self._finish_success(current_text.strip())
                return
            if self._monotonic() >= self._phase_deadline:
                self._finish_success("")
                return
            self._schedule_until_deadline()
        except Exception as exc:  # noqa: BLE001
            self._finish_failed(exc)

    def _schedule_next(self, seconds: float) -> None:
        if self._phase == "done":
            return
        self._timer.start(max(0, int(max(0.0, seconds) * 1000)))

    def _schedule_until_deadline(self) -> None:
        remaining = max(0.0, self._phase_deadline - self._monotonic())
        self._schedule_next(min(self.poll_seconds, remaining))

    def _finish_success(self, text: str) -> None:
        self._restore_clipboard_state()
        self._finish(signal_name="finished", payload=text)

    def _finish_failed(self, exc: Exception) -> None:
        self._restore_clipboard_state()
        self._finish(signal_name="failed", payload=exc)

    def _restore_clipboard_state(self) -> None:
        if self._clipboard is None:
            return
        try:
            if self._captured_sequence is None and self._captured_text is None:
                _restore_clipboard(self._clipboard, self._backup_mime, self._had_backup_payload)
            else:
                _restore_clipboard_if_unchanged(
                    self._clipboard,
                    self._backup_mime,
                    self._had_backup_payload,
                    expected_sequence=self._captured_sequence,
                    expected_text=self._captured_text,
                )
        except Exception:  # noqa: BLE001
            pass

    def _finish(self, *, signal_name: str, payload=None) -> None:
        if self._phase == "done":
            return
        self._timer.stop()
        self._phase = "done"
        if signal_name == "finished":
            self.finished.emit(str(payload or ""))
            return
        if signal_name == "failed":
            self.failed.emit(payload)
            return
        self.cancelled.emit()



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
    codes: list[int] = []
    for part in canonical_hotkey_parts(hotkey_text):
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


def _send_copy_shortcut() -> None:
    from pynput.keyboard import Controller, Key

    controller = Controller()
    with controller.pressed(Key.ctrl):
        controller.press("c")
        controller.release("c")


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

        _send_copy_shortcut()

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
