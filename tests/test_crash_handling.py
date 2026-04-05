from pathlib import Path
import unittest
from unittest.mock import patch

import app.crash_handling as crash_handling


class CrashHandlingTests(unittest.TestCase):
    def tearDown(self):
        crash_handling._HANDLING_MAIN_THREAD_EXCEPTION = False
        crash_handling._LAST_MAIN_THREAD_EXCEPTION_SIGNATURE = None
        crash_handling._LAST_MAIN_THREAD_EXCEPTION_AT = 0.0

    def test_main_thread_exception_handler_suppresses_nested_reentry(self):
        try:
            raise RuntimeError("primary boom")
        except RuntimeError as primary_exc:
            primary_error = primary_exc
            primary_type = type(primary_exc)
            primary_traceback = primary_exc.__traceback__

        try:
            raise RuntimeError("nested boom")
        except RuntimeError as nested_exc:
            nested_error = nested_exc
            nested_type = type(nested_exc)
            nested_traceback = nested_exc.__traceback__

        def nested_show_error(_message, **_kwargs):
            crash_handling._handle_main_thread_exception(nested_type, nested_error, nested_traceback)

        with patch("app.crash_handling.safe_record_exception", return_value=Path("ocrtranslator-crash-test.log")) as mock_record, patch(
            "app.crash_handling.show_error",
            side_effect=nested_show_error,
        ):
            crash_handling._handle_main_thread_exception(primary_type, primary_error, primary_traceback)

        mock_record.assert_called_once_with(primary_type, primary_error, primary_traceback, context="Unhandled main-thread exception")
        self.assertFalse(crash_handling._HANDLING_MAIN_THREAD_EXCEPTION)

    def test_main_thread_exception_handler_throttles_duplicate_reports_within_window(self):
        try:
            raise RuntimeError("same boom")
        except RuntimeError as exc:
            error = exc
            error_type = type(exc)
            error_traceback = exc.__traceback__

        with patch("app.crash_handling.time.monotonic", side_effect=[100.0, 100.3]), patch(
            "app.crash_handling.safe_record_exception",
            return_value=Path("ocrtranslator-crash-test.log"),
        ) as mock_record, patch("app.crash_handling.show_error") as mock_show_error:
            crash_handling._handle_main_thread_exception(error_type, error, error_traceback)
            crash_handling._handle_main_thread_exception(error_type, error, error_traceback)

        mock_record.assert_called_once_with(error_type, error, error_traceback, context="Unhandled main-thread exception")
        mock_show_error.assert_called_once()
        self.assertIsNotNone(crash_handling._LAST_MAIN_THREAD_EXCEPTION_SIGNATURE)
        self.assertEqual(crash_handling._LAST_MAIN_THREAD_EXCEPTION_AT, 100.0)


if __name__ == "__main__":
    unittest.main()
