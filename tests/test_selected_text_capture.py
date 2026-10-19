import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.platform.windows.selected_text import SelectedTextCaptureSession

from app.selected_text_capture import (
    VK_CONTROL,
    VK_LWIN,
    VK_RWIN,
    VK_SHIFT,
    _clipboard_state_matches_capture,
    _virtual_key_codes_for_hotkey,
)


class SelectedTextCaptureTests(unittest.TestCase):
    def test_clipboard_capture_preserves_source_whitespace_but_rejects_blank_text(self):
        for source, expected in (("\n  First line\n\nLast line  \n", "\n  First line\n\nLast line  \n"), (" \n\t", "")):
            with self.subTest(source=source):
                session = SimpleNamespace(
                    _clipboard=SimpleNamespace(text=lambda: source),
                    _initial_sequence=1,
                    _finish_success=Mock(),
                    _finish_failed=Mock(),
                )
                with patch("app.platform.windows.selected_text._clipboard_sequence_number", return_value=2):
                    SelectedTextCaptureSession._advance_wait_clipboard(session)

                session._finish_success.assert_called_once_with(expected)
                session._finish_failed.assert_not_called()
                self.assertEqual(session._captured_text, source)

    def test_virtual_key_codes_for_hotkey_maps_modifiers_and_letter(self):
        codes = _virtual_key_codes_for_hotkey("Shift+Win+T")
        self.assertIn(VK_SHIFT, codes)
        self.assertIn(ord("T"), codes)
        self.assertTrue(VK_LWIN in codes or VK_RWIN in codes)

    def test_virtual_key_codes_for_hotkey_deduplicates_aliases(self):
        codes = _virtual_key_codes_for_hotkey("Ctrl+Control+A")
        self.assertEqual(codes.count(VK_CONTROL), 1)
        self.assertEqual(codes.count(ord("A")), 1)

    def test_clipboard_state_matches_capture_when_sequence_and_text_match(self):
        self.assertTrue(
            _clipboard_state_matches_capture(expected_sequence=5, current_sequence=5, expected_text="captured", current_text="captured")
        )

    def test_clipboard_state_matches_capture_rejects_external_changes(self):
        self.assertFalse(
            _clipboard_state_matches_capture(expected_sequence=5, current_sequence=6, expected_text="captured", current_text="changed")
        )
        self.assertFalse(
            _clipboard_state_matches_capture(expected_sequence=None, current_sequence=None, expected_text="captured", current_text="changed")
        )

if __name__ == "__main__":
    unittest.main()
