import os
import platform
import re
import sys
import threading
import time
import traceback
from pathlib import Path
from types import TracebackType

CRASH_LOG_PREFIX = "ocrtranslator-crash"

_SENSITIVE_VALUE_PATTERNS = [
    (re.compile(r"(?i)([?&](?:api[_-]?key|key|token|access[_-]?token|refresh[_-]?token|password|secret|signature)=)([^&#\s]+)"), r"\1<redacted>"),
    (re.compile(r"(?i)([\"'](?:api[_-]?key|key|token|access[_-]?token|refresh[_-]?token|password|secret|signature)[\"']\s*[:=]\s*[\"'])([^\"']+)([\"'])"), r"\1<redacted>\3"),
    (re.compile(r"(?i)(\b(?:api[_-]?key|token|password|secret)\b\s*[:=]\s*)([^\s,;]+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(\bAuthorization\b\s*[:=]\s*Bearer\s+)([^\s,;]+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(\bx-goog-api-key\b\s*[:=]\s*)([^\s,;]+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(\bBearer\s+)([A-Za-z0-9._\-+/=]+)"), r"\1<redacted>"),
]


def _sanitize_sensitive_text(value: object) -> str:
    text = _redact_path_text(value)
    for pattern, replacement in _SENSITIVE_VALUE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def get_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def build_crash_log_path(base_dir: Path | None = None) -> Path:
    target_dir = (base_dir or get_runtime_base_dir()).resolve()
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    unique_suffix = f"{time.time_ns() % 1_000_000_000:09d}"
    return target_dir / f"{CRASH_LOG_PREFIX}-{timestamp}-{unique_suffix}.log"


def _redact_path_text(value: object) -> str:
    text = str(value or "")
    home = str(Path.home())
    if home:
        text = text.replace(home, "~")
    return text


def _sanitize_argument(arg: object) -> str:
    return _sanitize_sensitive_text(arg)


def _sanitize_arguments(args: list[object]) -> list[str]:
    return [_sanitize_argument(arg) for arg in args]


def format_exception_report(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
    *,
    context: str = "Unhandled exception",
    thread_name: str | None = None,
) -> str:
    formatted_traceback = _sanitize_sensitive_text("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)).rstrip())
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
        f"Executable: {_redact_path_text(getattr(sys, 'executable', ''))}",
        f"Current Working Directory: {_redact_path_text(Path.cwd())}",
        f"Base Directory: {_redact_path_text(get_runtime_base_dir())}",
        f"Arguments: {_sanitize_arguments(sys.argv)}",
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
    summary = _sanitize_sensitive_text(str(exc_value).strip() or exc_value.__class__.__name__)
    if crash_log_path:
        return (
            "程式發生未處理錯誤，已自動保存 crash log。\n\n"
            f"檔案：{crash_log_path.name}\n"
            f"位置：{_redact_path_text(crash_log_path)}\n\n"
            f"錯誤摘要：{summary}"
        )
    return f"程式發生未處理錯誤，但 crash log 寫入失敗。\n\n錯誤摘要：{summary}"
