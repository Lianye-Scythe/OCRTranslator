import threading
import sys

from app.crash_reporter import format_crash_dialog_message, safe_record_exception


def show_error(message: str, *, prefer_native: bool = False):
    if prefer_native:
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, "OCRTranslator Error", 0x10)
            return
        except Exception:
            pass

    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        created_app = QApplication.instance() is None
        app = QApplication.instance() or QApplication([])
        QMessageBox.critical(None, "OCRTranslator Error", message)
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
        messagebox.showerror("OCRTranslator Error", message)
        root.destroy()
    except Exception:
        sys.stderr.write(message)


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    crash_log_path = safe_record_exception(exc_type, exc_value, exc_traceback, context="Unhandled main-thread exception")
    show_error(format_crash_dialog_message(exc_value, crash_log_path))


def handle_unhandled_thread_exception(args):
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


sys.excepthook = handle_unhandled_exception
threading.excepthook = handle_unhandled_thread_exception

from app.main import run_app

if __name__ == "__main__":
    run_app()
