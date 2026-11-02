import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from tools.profile_startup import summarize


ROOT_DIR = Path(__file__).resolve().parent.parent


class StartupProfileTests(unittest.TestCase):
    def test_summary_uses_medians_for_each_timing(self):
        samples = [
            {"timings_ms": {"first_paint": paint, "entry_import": entry}}
            for paint, entry in ((100, 10), (400, 30), (200, 20))
        ]
        self.assertEqual(summarize(samples), {"first_paint": 200, "entry_import": 20})

    def test_profile_is_isolated_and_reaches_first_paint_and_prewarm(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "startup.json"
            result = subprocess.run(
                [sys.executable, "tools/profile_startup.py", "--offscreen", "--samples", "1", "--output", str(output)],
                cwd=ROOT_DIR, env=dict(os.environ, PYTHON_LAZY_IMPORTS="normal"),
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(len(report["samples"]), 1)
        self.assertFalse(report["desktop_services"])
        self.assertGreater(report["median_ms"]["first_paint"], 0)
        self.assertGreater(report["median_ms"]["startup_prewarm_completed"], report["median_ms"]["mainwindow_first_show"])
        self.assertFalse(report["samples"][0]["requests_at_first_paint"])
        self.assertIn("prewarm.api_client", report["samples"][0]["prewarm_ms"])


if __name__ == "__main__":
    unittest.main()
