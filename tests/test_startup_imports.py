"""Use fresh processes so test discovery cannot hide eager dependency imports."""

import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT_DIR = Path(__file__).resolve().parent.parent


class StartupImportTests(unittest.TestCase):
    def run_isolated(self, code):
        env = dict(os.environ, PYTHON_LAZY_IMPORTS="normal")
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT_DIR, env=env,
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_main_window_import_does_not_load_http_or_image_backends(self):
        self.run_isolated("""
import sys
from app.ui.main_window import MainWindow
assert 'requests' not in sys.modules
assert 'PIL.Image' not in sys.modules
assert 'app.api_client' not in sys.modules
assert 'app.services.image_capture' not in sys.modules
assert 'app.ui.translation_overlay' not in sys.modules
""")

    def test_application_respects_an_explicit_offscreen_platform_and_reuses_it(self):
        self.run_isolated("""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from app.main import create_ui_application
app = create_ui_application()
assert app.platformName() == 'offscreen'
assert create_ui_application() is app
assert os.environ['QT_QPA_PLATFORM'] == 'offscreen'
""")

    @unittest.skipUnless(sys.platform == "win32", "Checks the native Windows font database")
    def test_windows_application_preserves_symbol_and_emoji_font_fallback(self):
        self.run_isolated("""
import os
os.environ.pop('QT_QPA_PLATFORM', None)
from app.main import create_ui_application
from PySide6.QtGui import QFont, QFontDatabase, QTextLayout
app = create_ui_application()
assert app.platformName() == 'windows'
families = set(QFontDatabase.families())
for family in ('Segoe UI', 'Noto Sans TC', 'Microsoft JhengHei UI'):
    if family not in families:
        continue
    font = QFont(family, 20)
    assert not font.styleStrategy() & QFont.NoFontMerging
    layout = QTextLayout('A\u2705\U0001f600', font)
    layout.beginLayout()
    layout.createLine().setLineWidth(300)
    layout.endLayout()
    runs = layout.glyphRuns()
    glyphs = [glyph for run in runs for glyph in run.glyphIndexes()]
    assert len(glyphs) == 3 and all(glyphs), (family, glyphs)
    assert any(run.rawFont().familyName() != family for run in runs), family
""")

    def test_cancellation_primitives_do_not_load_requests_but_context_does(self):
        self.run_isolated("""
import sys
from app.operation_control import CancellationToken, RequestContext, RequestCancelledError
token = CancellationToken()
assert token.cancel()
assert isinstance(RequestCancelledError(), RuntimeError)
assert 'requests' not in sys.modules
context = RequestContext()
assert 'requests' in sys.modules
assert not context.is_cancelled()
context.cancel()
assert context.is_cancelled()
context.close()
""")

    def test_update_helpers_stay_lazy_and_http_error_handling_still_works(self):
        self.run_isolated("""
import sys
from app.services.update_checker import UpdateCheckService, compare_versions
service = UpdateCheckService()
assert compare_versions('1.0.1', '1.0.0') > 0
assert 'requests' not in sys.modules
from unittest.mock import patch
with patch('app.services.update_checker.requests.get', side_effect=RuntimeError('offline')):
    result = service.check_latest_release()
assert result.is_error
assert result.error == 'offline'
assert 'requests' in sys.modules
""")


if __name__ == "__main__":
    unittest.main()
