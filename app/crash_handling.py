from __future__ import annotations

import sys
import time
import threading

from .crash_reporter import format_crash_dialog_message, safe_record_exception


_ERROR_TITLE = "OCRTranslator Error"
_HANDLING_MAIN_THREAD_EXCEPTION = False
_LAST_MAIN_THREAD_EXCEPTION_SIGNATURE = None
_LAST_MAIN_THREAD_EXCEPTION_AT = 0.0
_MAIN_THREAD_EXCEPTION_THROTTLE_SECONDS = 1.5


def show_error(message: str, *, prefer_native: bool = False):
    if prefer_native:
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, _ERROR_TITLE, 0x10)
            return
        except Exception:
            pass

    try:
        from PySide6.QtWidgets import QApplication
        from .ui.message_boxes import show_critical_message

        created_app = QApplication.instance() is None
        app = QApplication.instance() or QApplication([])
        show_critical_message(None, _ERROR_TITLE, message)
        if created_app:
            app.quit()
        return
    except Exception:
        pass

    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(_ERROR_TITLE, message)
        root.destroy()
    except Exception:
        sys.stderr.write(message)


def _main_thread_exception_signature(exc_type, exc_value, exc_traceback):
    last_traceback = exc_traceback
    while getattr(last_traceback, "tb_next", None) is not None:
        last_traceback = last_traceback.tb_next
    frame = getattr(last_traceback, "tb_frame", None)
    code = getattr(frame, "f_code", None)
    return (
        getattr(exc_type, "__name__", str(exc_type)),
        str(exc_value),
        getattr(code, "co_filename", ""),
        getattr(code, "co_name", ""),
        int(getattr(last_traceback, "tb_lineno", 0) or 0),
    )


def _should_suppress_duplicate_main_thread_exception(exc_type, exc_value, exc_traceback) -> bool:
    global _LAST_MAIN_THREAD_EXCEPTION_SIGNATURE, _LAST_MAIN_THREAD_EXCEPTION_AT
    signature = _main_thread_exception_signature(exc_type, exc_value, exc_traceback)
    now = time.monotonic()
    if (
        signature == _LAST_MAIN_THREAD_EXCEPTION_SIGNATURE
        and now - _LAST_MAIN_THREAD_EXCEPTION_AT < _MAIN_THREAD_EXCEPTION_THROTTLE_SECONDS
    ):
        return True
    _LAST_MAIN_THREAD_EXCEPTION_SIGNATURE = signature
    _LAST_MAIN_THREAD_EXCEPTION_AT = now
    return False


def _handle_main_thread_exception(exc_type, exc_value, exc_traceback):
    global _HANDLING_MAIN_THREAD_EXCEPTION
    if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    if _HANDLING_MAIN_THREAD_EXCEPTION:
        try:
            sys.stderr.write(f"Suppressed nested main-thread exception while crash handling: {exc_value}\n")
            sys.stderr.flush()
        except Exception:  # noqa: BLE001
            pass
        return
    if _should_suppress_duplicate_main_thread_exception(exc_type, exc_value, exc_traceback):
        try:
            sys.stderr.write(f"Suppressed duplicate main-thread exception crash report: {exc_value}\n")
            sys.stderr.flush()
        except Exception:  # noqa: BLE001
            pass
        return
    _HANDLING_MAIN_THREAD_EXCEPTION = True
    try:
        crash_log_path = safe_record_exception(exc_type, exc_value, exc_traceback, context="Unhandled main-thread exception")
        show_error(format_crash_dialog_message(exc_value, crash_log_path))
    finally:
        _HANDLING_MAIN_THREAD_EXCEPTION = False


def _handle_thread_exception(args):
    if issubclass(args.exc_type, (KeyboardInterrupt, SystemExit)):
        if hasattr(threading, "__excepthook__"):
            threading.__excepthook__(args)
        return
    crash_log_path = safe_record_exception(
        args.exc_type,
        args.exc_value,
        args.exc_traceback,
        context="Unhandled background-thread exception",
        thread_name=args.thread.name if args.thread else None,
    )
    show_error(format_crash_dialog_message(args.exc_value, crash_log_path), prefer_native=True)


def install_crash_hooks():
    sys.excepthook = _handle_main_thread_exception
    threading.excepthook = _handle_thread_exception
