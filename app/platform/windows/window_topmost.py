from __future__ import annotations

import sys

if sys.platform.startswith("win"):
    import ctypes

    USER32 = ctypes.windll.user32
else:
    USER32 = None

HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040


def ensure_window_topmost(widget, *, activate: bool = False) -> bool:
    if USER32 is None or widget is None:
        return False
    try:
        hwnd = int(widget.winId())
    except Exception:  # noqa: BLE001
        return False
    flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
    if not activate:
        flags |= SWP_NOACTIVATE
    try:
        return bool(USER32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags))
    except Exception:  # noqa: BLE001
        return False
