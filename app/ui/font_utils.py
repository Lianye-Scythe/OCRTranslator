from PySide6.QtGui import QFontDatabase, QGuiApplication

from ..app_defaults import default_overlay_font_family


FONT_FALLBACKS = {
    "Noto Sans TC": ("Noto Sans CJK TC", "Microsoft JhengHei UI", "Microsoft JhengHei"),
    "Noto Sans SC": ("Noto Sans CJK SC", "Microsoft YaHei UI", "Microsoft YaHei"),
    "Noto Sans JP": ("Noto Sans CJK JP", "Yu Gothic UI", "Yu Gothic", "Meiryo UI", "Meiryo"),
    "Noto Sans": ("Segoe UI", "Segoe UI Variable Text"),
}


def resolve_overlay_font_family(requested_family: str | None, *, target_language: str | None = None) -> str:
    """Choose one installed face; keep the stored preference independent of availability."""
    preferred = default_overlay_font_family(target_language)
    requested = str(requested_family or "").strip() or preferred
    for family, aliases in FONT_FALLBACKS.items():
        if requested.casefold() in {family.casefold(), aliases[0].casefold()}:
            preferred = family
            break
    app = QGuiApplication.instance()
    if app is None:
        return requested

    available = {family.casefold(): family for family in QFontDatabase.families()}
    for candidate in (
        requested,
        preferred,
        *FONT_FALLBACKS[preferred],
        app.font().family(),
    ):
        if candidate.casefold() in available:
            return available[candidate.casefold()]
    return app.font().family()
