from PySide6.QtGui import QFontDatabase, QGuiApplication

from ..app_defaults import DEFAULT_OVERLAY_FONT_FAMILY


def resolve_overlay_font_family(requested_family: str | None) -> str:
    """Choose one installed face; keep the stored preference independent of availability."""
    requested = str(requested_family or "").strip() or DEFAULT_OVERLAY_FONT_FAMILY
    app = QGuiApplication.instance()
    if app is None:
        return requested

    available = {family.casefold(): family for family in QFontDatabase.families()}
    for candidate in (
        requested,
        DEFAULT_OVERLAY_FONT_FAMILY,
        "Noto Sans CJK TC",
        "Microsoft JhengHei UI",
        "Microsoft JhengHei",
        "Microsoft YaHei UI",
        app.font().family(),
    ):
        if candidate.casefold() in available:
            return available[candidate.casefold()]
    return app.font().family()
