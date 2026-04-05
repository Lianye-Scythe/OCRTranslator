from collections.abc import Iterator, Mapping
import json
from functools import lru_cache
from importlib import resources

from PySide6.QtCore import QLocale

from .app_defaults import DEFAULT_UI_LANGUAGE

SUPPORTED_UI_LANGUAGES = ("zh-TW", "zh-CN", "en")
_TRADITIONAL_MARKERS = {"tw", "hk", "mo", "hant"}
_SIMPLIFIED_MARKERS = {"cn", "sg", "hans"}


def _locale_candidates() -> list[str]:
    locale = QLocale.system()
    candidates: list[str] = []
    try:
        candidates.extend(locale.uiLanguages())
    except Exception:  # noqa: BLE001
        pass
    for getter in (getattr(locale, "bcp47Name", None), getattr(locale, "name", None)):
        if not callable(getter):
            continue
        try:
            value = getter()
        except Exception:  # noqa: BLE001
            continue
        if value:
            candidates.append(str(value))
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = str(candidate or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def normalize_ui_language(value: str | None, *, default: str = DEFAULT_UI_LANGUAGE) -> str:
    normalized = str(value or "").strip()
    if normalized in SUPPORTED_UI_LANGUAGES:
        return normalized

    marker_text = normalized.lower().replace("_", "-")
    if marker_text.startswith("zh"):
        tokens = {token for token in marker_text.split("-") if token}
        if tokens & _TRADITIONAL_MARKERS:
            return "zh-TW"
        if tokens & _SIMPLIFIED_MARKERS:
            return "zh-CN"
        return "zh-CN"
    if marker_text.startswith("en"):
        return "en"
    return default


def detect_system_ui_language() -> str:
    for candidate in _locale_candidates():
        normalized = normalize_ui_language(candidate, default="")
        if normalized:
            return normalized
    return DEFAULT_UI_LANGUAGE


@lru_cache(maxsize=None)
def load_locale(language: str) -> dict[str, str]:
    normalized = normalize_ui_language(language)
    content = resources.files("app.locales").joinpath(f"{normalized}.json").read_text(encoding="utf-8")
    return json.loads(content)


class LazyTranslations(Mapping[str, dict[str, str]]):
    def __getitem__(self, language: str) -> dict[str, str]:
        return load_locale(language)

    def __iter__(self) -> Iterator[str]:
        return iter(SUPPORTED_UI_LANGUAGES)

    def __len__(self) -> int:
        return len(SUPPORTED_UI_LANGUAGES)

    def materialize(self) -> dict[str, dict[str, str]]:
        return {language: load_locale(language) for language in SUPPORTED_UI_LANGUAGES}


@lru_cache(maxsize=1)
def load_translations() -> dict[str, dict[str, str]]:
    return LazyTranslations().materialize()


I18N: Mapping[str, dict[str, str]] = LazyTranslations()
