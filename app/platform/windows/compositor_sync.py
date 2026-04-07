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


def flush_window_composition() -> bool:
    if DWMAPI is None:
        return False
    try:
        return int(DWMAPI.DwmFlush()) == 0
    except Exception:  # noqa: BLE001
        return False


__all__ = ["flush_window_composition", "DWMAPI"]
