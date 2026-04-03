from collections import deque
from pathlib import Path
import time


class RuntimeLogStore:
    def __init__(self, *, max_entries: int = 100):
        self._entries = deque(maxlen=max_entries)

    def add(self, message: str) -> str:
        entry = f"[{time.strftime('%H:%M:%S')}] {message}"
        self._entries.append(entry)
        return entry

    def clear(self):
        self._entries.clear()

    def has_entries(self) -> bool:
        return bool(self._entries)

    def export(self, target_path: str | Path):
        Path(target_path).write_text(self.as_text() + "\n", encoding="utf-8")

    def lines(self) -> list[str]:
        return list(reversed(self._entries))

    def as_text(self) -> str:
        return "\n".join(self.lines())
