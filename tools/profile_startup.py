"""Measure startup in fresh processes without reading personal configuration."""

import argparse
import faulthandler
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time


ROOT_DIR = Path(__file__).resolve().parent.parent
MARK_NAMES = (
    "ui_application_created", "main_window_imported", "mainwindow_init_start",
    "mainwindow_ui_built", "mainwindow_profile_loaded", "mainwindow_prompt_loaded",
    "mainwindow_language_applied", "mainwindow_init_complete", "mainwindow_first_show",
    "startup_services_ready", "startup_prewarm_completed",
)


def summarize(samples: list[dict]) -> dict:
    timings = samples[0]["timings_ms"]
    return {
        name: round(statistics.median(sample["timings_ms"][name] for sample in samples), 2)
        for name in timings
    }


def measure_once(*, offscreen: bool, screenshot: str | None = None) -> dict:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    if offscreen:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    with tempfile.TemporaryDirectory(prefix="ocrtranslator-startup-") as directory:
        config_path = Path(directory) / "config.json"
        config_path.write_text(json.dumps({
            "ui_language": "en", "theme_mode": "light",
            "check_updates_on_startup": False, "debug_logging_enabled": False,
            "hotkey": "Ctrl+Alt+Shift+F9", "selection_hotkey": "Ctrl+Alt+Shift+F10",
            "input_hotkey": "Ctrl+Alt+Shift+F11",
        }), encoding="utf-8")
        started = time.perf_counter()
        from app import runtime_paths

        runtime_paths.CONFIG_PATH = config_path
        runtime_paths.FALLBACK_CONFIG_PATH = config_path
        runtime_paths.APP_LOCK_PATH = str(Path(directory) / "instance.lock")
        runtime_paths.APP_SERVER_NAME = f"ocrtranslator-benchmark-{os.getpid()}"
        from app import main as application
        module_import_ms = (time.perf_counter() - started) * 1000
        original_create = application.create_ui_application
        original_schedule = application.schedule_initial_window_action
        result = {"timings_ms": {"entry_import": module_import_ms}}
        errors = []
        active_app = None
        last_poll = None
        event_gaps = []

        def schedule_window(window, *, pending_capture):
            if offscreen:
                window.setup_hotkey_listener = lambda *args, **kwargs: True
                window.tray_service.setup = lambda: None
            original_schedule(window, pending_capture=pending_capture)

        def create_application():
            nonlocal active_app
            from PySide6.QtCore import QEvent, QObject, QTimer
            app = original_create()
            active_app = app

            class Observer(QObject):
                def eventFilter(self, watched, event):
                    if event.type() == QEvent.Paint and watched is getattr(app, "main_window", None):
                        if "first_paint" not in result["timings_ms"]:
                            result["timings_ms"]["first_paint"] = (time.perf_counter() - started) * 1000
                            result["requests_at_first_paint"] = "requests" in sys.modules
                    return False

            observer = Observer(app)
            app.installEventFilter(observer)

            def finish(*, timed_out=False):
                poll.stop()
                deadline.stop()
                window = getattr(app, "main_window", None)
                if window is not None:
                    tracker = window.startup_timing
                    result["timings_ms"].update({
                        name: tracker.elapsed_ms(name) for name in MARK_NAMES
                        if tracker.elapsed_ms(name) is not None
                    })
                    result["prewarm_ms"] = dict(tracker.durations_with_prefix("prewarm."))
                    result["max_prewarm_event_gap_ms"] = max(event_gaps, default=0)
                    if window._active_error_dialogs:
                        errors.append("Startup opened an error dialog")
                    if not timed_out and (window._api_client is None or window.existing_translation_overlay() is None):
                        errors.append("Startup prewarm did not prepare API and overlay components")
                    if screenshot:
                        target = Path(screenshot)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if not window.grab().save(str(target)):
                            errors.append("Screenshot could not be saved")
                    window._perform_shutdown_cleanup()
                    window.is_quitting = True
                    window.hide()
                if timed_out:
                    errors.append("Startup prewarm timed out")
                app.quit()

            def check_ready():
                nonlocal last_poll
                now = time.perf_counter()
                if last_poll is not None:
                    event_gaps.append((now - last_poll) * 1000)
                if "first_paint" in result["timings_ms"]:
                    last_poll = now
                window = getattr(app, "main_window", None)
                if window is not None and window._startup_prewarm_completed:
                    finish()

            poll = QTimer(app)
            poll.timeout.connect(check_ready)
            poll.start(10)
            deadline = QTimer(app)
            deadline.setSingleShot(True)
            deadline.timeout.connect(lambda: finish(timed_out=True))
            deadline.start(12000)
            app._startup_benchmark_observer = observer
            return app

        application.create_ui_application = create_application
        application.schedule_initial_window_action = schedule_window
        sys.excepthook = sys.__excepthook__
        try:
            application.run_app()
        finally:
            if active_app is not None and getattr(active_app, "instance_lock", None) is not None:
                active_app.instance_lock.unlock()
                active_app.instance_lock = None
        if errors:
            raise RuntimeError("; ".join(errors))
        required = {"first_paint", "startup_services_ready", "startup_prewarm_completed"}
        if not required.issubset(result["timings_ms"]):
            raise RuntimeError("Startup did not reach all measured stages")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--offscreen", action="store_true", help="Disable desktop hotkeys/tray and use Qt offscreen")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--screenshot", help="Capture the final sample's main window")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    if args.worker:
        faulthandler.dump_traceback_later(18, exit=True)
        print(json.dumps(measure_once(offscreen=args.offscreen, screenshot=args.screenshot)))
        faulthandler.cancel_dump_traceback_later()
        return
    samples = []
    for index in range(args.samples):
        command = [sys.executable, str(Path(__file__).resolve()), "--worker"]
        if args.offscreen:
            command.append("--offscreen")
        if args.screenshot and index == args.samples - 1:
            command.extend(["--screenshot", args.screenshot])
        process = subprocess.run(
            command, cwd=ROOT_DIR, env=dict(os.environ, PYTHON_LAZY_IMPORTS="normal"),
            capture_output=True, text=True, timeout=25,
        )
        if process.returncode:
            raise RuntimeError(f"Startup sample failed ({process.returncode}):\n{process.stderr}")
        samples.append(json.loads(process.stdout))
    report = {
        "python": sys.version.split()[0], "platform": sys.platform,
        "offscreen": args.offscreen, "desktop_services": not args.offscreen,
        "cache_note": "Fresh processes; filesystem and OS caches are not cleared.",
        "timing_note": "first_paint includes entry imports; application marks start at run_app entry.",
        "median_ms": summarize(samples), "samples": samples,
    }
    content = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")


if __name__ == "__main__":
    main()
