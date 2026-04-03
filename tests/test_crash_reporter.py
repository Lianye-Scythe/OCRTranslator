from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app.crash_reporter import CRASH_LOG_PREFIX, build_crash_log_path, format_crash_dialog_message, record_exception


class CrashReporterTests(unittest.TestCase):
    def test_record_exception_writes_report_to_root_directory(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            try:
                raise RuntimeError("boom")
            except RuntimeError as exc:
                crash_log_path = record_exception(type(exc), exc, exc.__traceback__, context="unit test", base_dir=base_dir)

            self.assertTrue(crash_log_path.exists())
            self.assertTrue(crash_log_path.name.startswith(CRASH_LOG_PREFIX))
            content = crash_log_path.read_text(encoding="utf-8")
            self.assertIn("OCRTranslator Crash Report", content)
            self.assertIn("Context: unit test", content)
            self.assertIn("RuntimeError: boom", content)

    def test_format_crash_dialog_message_includes_saved_path(self):
        path = Path("ocrtranslator-crash-20260101-010101.log")
        message = format_crash_dialog_message(RuntimeError("boom"), path)
        self.assertIn(path.name, message)
        self.assertIn("boom", message)

    def test_build_crash_log_path_adds_unique_suffix(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            with patch("app.crash_reporter.time.strftime", return_value="20260101-010101"), patch(
                "app.crash_reporter.time.time_ns",
                side_effect=[111, 222],
            ):
                first = build_crash_log_path(base_dir)
                second = build_crash_log_path(base_dir)
        self.assertNotEqual(first, second)
        self.assertRegex(first.name, rf"^{CRASH_LOG_PREFIX}-20260101-010101-\d{{9}}\.log$")


if __name__ == "__main__":
    unittest.main()
