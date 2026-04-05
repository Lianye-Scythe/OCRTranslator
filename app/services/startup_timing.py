from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterable


_VERBOSE_ENV = "OCRTRANSLATOR_STARTUP_TIMING_VERBOSE"
_TRUTHY_VALUES = {"1", "true", "yes", "on"}


class StartupTimingTracker:
    def __init__(self, *, origin_name: str = "run_app_enter", clock: Callable[[], float] | None = None, verbose: bool | None = None):
        self._clock = clock or time.perf_counter
        self._origin = self._clock()
        self._marks: dict[str, float] = {}
        self._mark_order: list[tuple[str, float]] = []
        self._durations: dict[str, float] = {}
        if verbose is None:
            verbose = str(os.getenv(_VERBOSE_ENV, "")).strip().lower() in _TRUTHY_VALUES
        self.verbose = bool(verbose)
        self._marks[origin_name] = 0.0
        self._mark_order.append((origin_name, 0.0))

    def mark(self, name: str) -> float:
        elapsed_ms = max(0.0, (self._clock() - self._origin) * 1000.0)
        if name not in self._marks:
            self._mark_order.append((name, elapsed_ms))
        self._marks[name] = elapsed_ms
        return elapsed_ms

    def measure(self, name: str, callback: Callable[[], object]):
        started_at = self._clock()
        try:
            return callback()
        finally:
            self._durations[name] = max(0.0, (self._clock() - started_at) * 1000.0)

    def elapsed_ms(self, name: str) -> float | None:
        return self._marks.get(name)

    def duration_ms(self, start_name: str, end_name: str) -> float | None:
        start = self._marks.get(start_name)
        end = self._marks.get(end_name)
        if start is None or end is None:
            return None
        return max(0.0, end - start)

    def durations_with_prefix(self, prefix: str) -> list[tuple[str, float]]:
        items = []
        for name, value in self._durations.items():
            if name.startswith(prefix):
                items.append((name, value))
        return items

    def mark_lines(self, names: Iterable[str] | None = None) -> list[str]:
        selected = set(names or [])
        lines: list[str] = []
        for name, value in self._mark_order:
            if selected and name not in selected:
                continue
            lines.append(f"{name}={self._format_ms(value)}")
        return lines

    def describe_segments(self, title: str, segments: Iterable[tuple[str, str, str]]) -> str:
        parts: list[str] = []
        for label, start_name, end_name in segments:
            value = self.duration_ms(start_name, end_name)
            if value is None:
                continue
            parts.append(f"{label}={self._format_ms(value)}")
        if not parts:
            return ""
        return f"{title}｜" + "｜".join(parts)

    def describe_durations(self, title: str, *, prefix: str = "") -> str:
        parts: list[str] = []
        for name, value in self.durations_with_prefix(prefix):
            label = name[len(prefix) :] if prefix and name.startswith(prefix) else name
            parts.append(f"{label}={self._format_ms(value)}")
        if not parts:
            return ""
        return f"{title}｜" + "｜".join(parts)

    @staticmethod
    def _format_ms(value: float) -> str:
        return f"{value:.0f}ms" if value >= 100 else f"{value:.1f}ms"


__all__ = ["StartupTimingTracker"]
