import os
import platform
import sys
import threading
import time
import traceback
from pathlib import Path
from types import TracebackType

CRASH_LOG_PREFIX = "ocrtranslator-crash"


def get_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def build_crash_log_path(base_dir: Path | None = None) -> Path:
    target_dir = (base_dir or get_runtime_base_dir()).resolve()
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return target_dir / f"{CRASH_LOG_PREFIX}-{timestamp}.log"


def format_exception_report(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
    *,
    context: str = "Unhandled exception",
    thread_name: str | None = None,
) -> str:
    formatted_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)).rstrip()
    lines = [
        "OCRTranslator Crash Report",
        "=" * 80,
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Context: {context}",
        f"Thread: {thread_name or threading.current_thread().name}",
        f"PID: {os.getpid()}",
        f"Python: {sys.version.replace(os.linesep, ' ')}",
        f"Platform: {platform.platform()}",
        f"Frozen: {getattr(sys, 'frozen', False)}",
        f"Executable: {getattr(sys, 'executable', '')}",
        f"Current Working Directory: {Path.cwd()}",
        f"Base Directory: {get_runtime_base_dir()}",
        f"Arguments: {sys.argv}",
        "",
        "Traceback:",
        formatted_traceback,
        "",
    ]
    return "\n".join(lines)


def write_crash_report(report: str, *, base_dir: Path | None = None) -> Path:
    crash_log_path = build_crash_log_path(base_dir)
    crash_log_path.parent.mkdir(parents=True, exist_ok=True)
    crash_log_path.write_text(report + "\n", encoding="utf-8")
    return crash_log_path


def record_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
    *,
    context: str = "Unhandled exception",
    thread_name: str | None = None,
    base_dir: Path | None = None,
) -> Path:
    report = format_exception_report(
        exc_type,
        exc_value,
        exc_traceback,
        context=context,
        thread_name=thread_name,
    )
    return write_crash_report(report, base_dir=base_dir)


def safe_record_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
    *,
    context: str = "Unhandled exception",
    thread_name: str | None = None,
    base_dir: Path | None = None,
) -> Path | None:
    try:
        return record_exception(
            exc_type,
            exc_value,
            exc_traceback,
            context=context,
            thread_name=thread_name,
            base_dir=base_dir,
        )
    except Exception:
        return None


def format_crash_dialog_message(exc_value: BaseException, crash_log_path: Path | None) -> str:
    summary = str(exc_value).strip() or exc_value.__class__.__name__
    if crash_log_path:
        return (
            "程式發生未處理錯誤，已自動保存 crash log。\n\n"
            f"檔案：{crash_log_path.name}\n"
            f"位置：{crash_log_path}\n\n"
            f"錯誤摘要：{summary}"
        )
    return f"程式發生未處理錯誤，但 crash log 寫入失敗。\n\n錯誤摘要：{summary}"
