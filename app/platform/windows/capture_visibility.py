from __future__ import annotations

import sys

if sys.platform.startswith("win"):
    import ctypes

    try:
        DWMAPI = ctypes.windll.dwmapi
    except Exception:  # noqa: BLE001
        DWMAPI = None
else:
    DWMAPI = None

DWMWA_CLOAK = 13


def begin_temporary_capture_conceal(widget):
    if widget is None:
        return None
    if DWMAPI is not None:
        try:
            hwnd = int(widget.winId())
            value = ctypes.c_int(1)
            result = int(DWMAPI.DwmSetWindowAttribute(hwnd, DWMWA_CLOAK, ctypes.byref(value), ctypes.sizeof(value)))
            if result == 0:
                return {"widget": widget, "method": "cloak", "hwnd": hwnd}
        except Exception:  # noqa: BLE001
            pass
    try:
        current_opacity = float(widget.windowOpacity())
        widget.setWindowOpacity(0.0)
        return {"widget": widget, "method": "opacity", "opacity": current_opacity}
    except Exception:  # noqa: BLE001
        return None


def restore_temporary_capture_conceal(state) -> bool:
    if not state:
        return False
    widget = state.get("widget")
    method = state.get("method")
    if widget is None:
        return False
    if method == "cloak" and DWMAPI is not None:
        try:
            hwnd = int(state.get("hwnd") or widget.winId())
            value = ctypes.c_int(0)
            return int(DWMAPI.DwmSetWindowAttribute(hwnd, DWMWA_CLOAK, ctypes.byref(value), ctypes.sizeof(value))) == 0
        except Exception:  # noqa: BLE001
            return False
    if method == "opacity":
        try:
            widget.setWindowOpacity(float(state.get("opacity", 1.0)))
            return True
        except Exception:  # noqa: BLE001
            return False
    return False


__all__ = [
    "begin_temporary_capture_conceal",
    "restore_temporary_capture_conceal",
    "DWMAPI",
    "DWMWA_CLOAK",
]
