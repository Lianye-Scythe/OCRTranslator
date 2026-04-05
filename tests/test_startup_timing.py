import unittest

from app.services.startup_timing import StartupTimingTracker


class _FakeClock:
    def __init__(self, *values):
        self._values = list(values)
        self._index = 0

    def __call__(self):
        value = self._values[min(self._index, len(self._values) - 1)]
        self._index += 1
        return value


class StartupTimingTrackerTests(unittest.TestCase):
    def test_describe_segments_formats_known_marks(self):
        clock = _FakeClock(10.0, 10.01, 10.03)
        tracker = StartupTimingTracker(origin_name="start", clock=clock, verbose=False)
        tracker.mark("middle")
        tracker.mark("end")

        summary = tracker.describe_segments("Startup timing", (("phase", "start", "middle"), ("total", "start", "end")))

        self.assertIn("phase=10.0ms", summary)
        self.assertIn("total=30.0ms", summary)

    def test_measure_records_named_duration(self):
        clock = _FakeClock(5.0, 5.0, 5.025)
        tracker = StartupTimingTracker(origin_name="start", clock=clock, verbose=False)

        result = tracker.measure("prewarm.api", lambda: "ok")

        self.assertEqual(result, "ok")
        summary = tracker.describe_durations("Startup prewarm", prefix="prewarm.")
        self.assertIn("api=25.0ms", summary)


if __name__ == "__main__":
    unittest.main()
