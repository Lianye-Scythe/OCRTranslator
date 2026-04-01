import sys
import traceback


def show_error(message: str):
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        created_app = QApplication.instance() is None
        app = QApplication.instance() or QApplication([])
        QMessageBox.critical(None, "OCRTranslator Startup Error", message)
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
        messagebox.showerror("OCRTranslator Startup Error", message)
        root.destroy()
    except Exception:
        sys.stderr.write(message)


try:
    from app.main import run_app

    if __name__ == "__main__":
        run_app()
except Exception:
    show_error(traceback.format_exc())
