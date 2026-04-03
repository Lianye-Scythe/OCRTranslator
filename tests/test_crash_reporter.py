from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.crash_reporter import CRASH_LOG_PREFIX, format_crash_dialog_message, record_exception


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


if __name__ == "__main__":
    unittest.main()
