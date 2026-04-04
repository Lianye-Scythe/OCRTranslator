from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication

from ..app_defaults import DEFAULT_THEME_MODE, normalize_theme_mode

LIGHT_MATERIAL_SCHEME = {
    "primary": "#334155",
    "on_primary": "#ffffff",
    "primary_container": "#f1f5f9",
    "on_primary_container": "#0f172a",
    "primary_hover": "#1e293b",
    "primary_focus": "#94a3b8",
    "secondary": "#475569",
    "on_secondary": "#ffffff",
    "secondary_container": "#e2e8f0",
    "on_secondary_container": "#1e293b",
    "secondary_hover": "#cbd5e1",
    "secondary_border": "#94a3b8",
    "tertiary": "#64748b",
    "on_tertiary": "#ffffff",
    "tertiary_container": "#f8fafc",
    "on_tertiary_container": "#334155",
    "tertiary_border": "#cbd5e1",
    "surface_dim": "#f8fafc",
    "surface": "#ffffff",
    "surface_bright": "#ffffff",
    "surface_container_lowest": "#ffffff",
    "surface_container_low": "#f8fafc",
    "surface_container": "#f1f5f9",
    "surface_container_high": "#e2e8f0",
    "surface_container_highest": "#cbd5e1",
    "on_surface": "#0f172a",
    "on_surface_variant": "#475569",
    "outline": "#94a3b8",
    "outline_variant": "#cbd5e1",
    "error": "#a4495b",
    "on_error": "#ffffff",
    "error_container": "#fff7f8",
    "on_error_container": "#7d3041",
    "warning": "#936006",
    "warning_container": "#fff7eb",
    "on_warning_container": "#6f4700",
    "warning_border": "#ddb26a",
    "success": "#2f7d58",
    "success_container": "#e3f1e8",
    "on_success_container": "#255d43",
    "success_border": "#b7d8c7",
    "shadow": "#a4aec7",
    "scrim": "rgba(92, 103, 200, 0.12)",
    "scrollbar_handle": "#c6cede",
    "pin_idle_bg": "#f5f5f7",
    "pin_idle_fg": "#5b6472",
    "pin_idle_border": "#d9dee5",
    "pin_hover_bg": "#eeeff2",
    "pin_hover_fg": "#374151",
    "pin_hover_border": "#c6ccd4",
    "pin_checked_bg": "#e7e9ed",
    "pin_checked_fg": "#2f3844",
    "pin_checked_border": "#c5cbd4",
    "menu_bg": "#fbfbfc",
    "menu_fg": "#1f2937",
    "menu_border": "#d8dde4",
    "menu_hover_bg": "#eceff3",
    "menu_hover_fg": "#111827",
    "menu_separator": "#dfe3e8",
    "menu_disabled_fg": "#94a3b8",
}

DARK_MATERIAL_SCHEME = {
    "primary": "#EDEDED",
    "on_primary": "#121316",
    "primary_container": "#2A2D35",
    "on_primary_container": "#EDEDED",
    "primary_hover": "#FFFFFF",
    "primary_focus": "#8B92A0",
    "secondary": "#A0A6B1",
    "on_secondary": "#121316",
    "secondary_container": "#24272E",
    "on_secondary_container": "#D1D5DB",
    "secondary_hover": "#30343D",
    "secondary_border": "#434854",
    "tertiary": "#7A8291",
    "on_tertiary": "#EDEDED",
    "tertiary_container": "#1D1F25",
    "on_tertiary_container": "#B6BCC6",
    "tertiary_border": "#363A45",
    "surface_dim": "#121316",
    "surface": "#191B20",
    "surface_bright": "#22252B",
    "surface_container_lowest": "#0D0E11",
    "surface_container_low": "#16181D",
    "surface_container": "#1E2026",
    "surface_container_high": "#262931",
    "surface_container_highest": "#2E323A",
    "on_surface": "#D1D5DB",
    "on_surface_variant": "#8B92A0",
    "outline": "#3D424E",
    "outline_variant": "#2A2D35",
    "error": "#D9625D",
    "on_error": "#121316",
    "error_container": "#2D1618",
    "on_error_container": "#F5A8AD",
    "warning": "#D49A4C",
    "warning_container": "#2E2111",
    "on_warning_container": "#F2D099",
    "warning_border": "#704E22",
    "success": "#44B58A",
    "success_container": "#112B22",
    "on_success_container": "#A2E4CA",
    "success_border": "#1F6147",
    "shadow": "#000000",
    "scrim": "rgba(0, 0, 0, 0.45)",
    "scrollbar_handle": "#404552",
    "pin_idle_bg": "#17191f",
    "pin_idle_fg": "#8f97a4",
    "pin_idle_border": "#2d3139",
    "pin_hover_bg": "#1e2229",
    "pin_hover_fg": "#cfd5de",
    "pin_hover_border": "#3a404a",
    "pin_checked_bg": "#23272f",
    "pin_checked_fg": "#d8dde5",
    "pin_checked_border": "#454b56",
    "menu_bg": "#1b1e24",
    "menu_fg": "#d6dbe3",
    "menu_border": "#2f343d",
    "menu_hover_bg": "#262b33",
    "menu_hover_fg": "#f1f5f9",
    "menu_separator": "#2c3139",
    "menu_disabled_fg": "#6b7380",
}

_THEME_SCHEMES = {
    "light": LIGHT_MATERIAL_SCHEME,
    "dark": DARK_MATERIAL_SCHEME,
}

_ACTIVE_THEME_NAME = "dark"

BASE_STYLE_TOKENS = {
    "font_ui": "'Segoe UI Variable Text','Segoe UI','Microsoft JhengHei UI'",
    "font_code": "'Cascadia Code','Consolas'",
}


def system_theme_name(*, default: str = "dark") -> str:
    app = QGuiApplication.instance()
    if app is None:
        return default
    hints = app.styleHints()
    if hints is None or not hasattr(hints, "colorScheme"):
        return default
    scheme = hints.colorScheme()
    return "dark" if scheme == Qt.ColorScheme.Dark else "light"


def resolve_theme_name(theme_mode: str | None = None) -> str:
    normalized = normalize_theme_mode(theme_mode, default=DEFAULT_THEME_MODE)
    return system_theme_name() if normalized == "system" else normalized


def set_theme_mode(theme_mode: str | None = None) -> str:
    global _ACTIVE_THEME_NAME
    _ACTIVE_THEME_NAME = resolve_theme_name(theme_mode)
    return _ACTIVE_THEME_NAME


def current_theme_name() -> str:
    return _ACTIVE_THEME_NAME


def _compatibility_tokens(scheme: dict[str, str]) -> dict[str, str]:
    return {
        "accent": scheme["primary"],
        "accent_soft": scheme["primary_container"],
        "accent_focus": scheme["primary_focus"],
        "accent_hover": scheme["primary_hover"],
        "accent_border": scheme["secondary_border"],
        "on_accent": scheme["on_primary"],
        "accent_text": scheme["on_secondary_container"],
        "text_primary": scheme["on_surface"],
        "text_base": scheme["on_surface"],
        "text_secondary": scheme["on_surface_variant"],
        "text_tertiary": scheme["outline"],
        "text_emphasis": scheme["on_surface"],
        "text_chip": scheme["on_secondary_container"],
        "surface_app": scheme["surface_dim"],
        "surface_base": scheme["surface"],
        "surface_alt": scheme["surface_container_low"],
        "surface_panel": scheme["surface_container"],
        "surface_input": scheme["surface_container_lowest"],
        "surface_hover": scheme["surface_container_high"],
        "surface_sidebar": scheme["surface_dim"],
        "surface_header": scheme["surface_container_low"],
        "surface_button_secondary": scheme["secondary_container"],
        "surface_button_neutral": scheme["surface_container_low"],
        "surface_button_warning": scheme["warning_container"],
        "surface_button_success": scheme["success_container"],
        "surface_button_danger": scheme["error_container"],
        "surface_selected": scheme["secondary_hover"],
        "surface_badge": scheme["tertiary_container"],
        "border_base": scheme["outline_variant"],
        "border_soft": scheme["outline"],
        "border_focus": scheme["primary_focus"],
        "overlay_scrim": scheme["scrim"],
        "shadow": scheme["shadow"],
        "warning": scheme["warning"],
        "warning_border": scheme["warning_border"],
        "danger_text": scheme["error"],
        "danger_surface": scheme["error_container"],
        "danger_border": scheme["error"],
        "scroll_handle": scheme["scrollbar_handle"],
        "link": scheme["primary"],
    }


def _ui_role_tokens(scheme: dict[str, str]) -> dict[str, str]:
    return {
        "app_bg": scheme["surface_dim"],
        "window_fg": scheme["on_surface"],
        "dialog_bg": scheme["surface"],
        "workspace_bg": scheme["surface"],
        "workspace_border": scheme["outline_variant"],
        "sidebar_divider": scheme["outline_variant"],
        "muted_fg": scheme["on_surface_variant"],
        "muted_fg_url": scheme["on_surface_variant"].replace("#", "%23"),
        "subtle_fg": scheme["outline"],
        "subtle_fg_url": scheme["outline"].replace("#", "%23"),
        "link_fg": scheme["primary"],
        "hint_title_fg": scheme["warning"],
        "header_divider": scheme["outline_variant"],
        "section_divider": scheme["outline_variant"],
        "badge_bg": scheme["tertiary_container"],
        "badge_border": scheme["tertiary_border"],
        "badge_fg": scheme["on_tertiary_container"],
        "nav_fg": scheme["on_surface_variant"],
        "nav_hover_bg": scheme["surface_container_high"],
        "nav_hover_border": scheme["outline_variant"],
        "nav_selected_bg": scheme["secondary_container"],
        "nav_selected_border": scheme["secondary_border"],
        "nav_selected_fg": scheme["on_secondary_container"],
        "nav_focus_border": scheme["primary_focus"],
        "panel_bg": scheme["surface_container_low"],
        "panel_border": scheme["outline_variant"],
        "monitor_card_bg": scheme["surface_container"],
        "monitor_card_border": scheme["outline_variant"],
        "field_bg": scheme["surface_container_lowest"],
        "field_fg": scheme["on_surface"],
        "field_border": scheme["outline"],
        "field_focus_bg": scheme["surface_bright"],
        "field_focus_border": scheme["primary_focus"],
        "field_invalid_bg": scheme["error_container"],
        "field_invalid_border": scheme["error"],
        "selection_bg": scheme["primary_container"],
        "button_primary_bg": scheme["primary"],
        "button_primary_fg": scheme["on_primary"],
        "button_primary_hover_bg": scheme["primary_hover"],
        "button_tonal_bg": scheme["secondary_container"],
        "button_tonal_fg": scheme["on_secondary_container"],
        "button_tonal_border": scheme["secondary_border"],
        "button_tonal_hover_bg": scheme["secondary_hover"],
        "button_outline_fg": scheme["on_surface"],
        "button_outline_border": scheme["outline_variant"],
        "button_outline_hover_bg": scheme["surface_container_high"],
        "button_warning_bg": scheme["warning_container"],
        "button_warning_fg": scheme["on_warning_container"],
        "button_warning_border": scheme["warning_border"],
        "button_warning_hover_bg": scheme["surface_container_low"],
        "button_danger_bg": scheme["error_container"],
        "button_danger_fg": scheme["error"],
        "button_danger_border": scheme["error"],
        "button_danger_hover_bg": scheme["surface_container_low"],
        "button_disabled_bg": scheme["surface_container_low"],
        "button_disabled_fg": scheme["outline"],
        "button_disabled_border": scheme["outline_variant"],
        "preview_bg": scheme["surface_container_low"],
        "preview_border": scheme["outline_variant"],
        "status_bg": scheme["surface_container_low"],
        "status_border": scheme["outline_variant"],
        "validation_bg": "transparent",
        "validation_fg": scheme["on_error_container"],
        "validation_border": scheme["error"],
        "list_bg": scheme["surface_container"],
        "list_border": scheme["outline_variant"],
        "list_selected_bg": scheme["secondary_container"],
        "overlay_card_bg": scheme["surface_container_low"],
        "overlay_card_border": scheme["outline_variant"],
        "overlay_header_border": scheme["outline_variant"],
        "overlay_value_bg": scheme["surface_container"],
        "overlay_value_fg": scheme["on_surface_variant"],
        "overlay_body_fg": scheme["on_surface"],
        "overlay_action_fg": scheme["on_surface_variant"],
        "overlay_action_checked_bg": scheme["secondary_container"],
        "overlay_action_checked_fg": scheme["on_secondary_container"],
        "overlay_action_checked_border": scheme["secondary_border"],
        "overlay_action_hover_bg": scheme["surface_container_high"],
        "overlay_action_hover_border": scheme["outline_variant"],
        "overlay_action_hover_fg": scheme["on_surface"],
        "overlay_pin_bg": scheme["pin_idle_bg"],
        "overlay_pin_fg": scheme["pin_idle_fg"],
        "overlay_pin_border": scheme["pin_idle_border"],
        "overlay_pin_hover_bg": scheme["pin_hover_bg"],
        "overlay_pin_hover_fg": scheme["pin_hover_fg"],
        "overlay_pin_hover_border": scheme["pin_hover_border"],
        "overlay_pin_checked_bg": scheme["pin_checked_bg"],
        "overlay_pin_checked_fg": scheme["pin_checked_fg"],
        "overlay_pin_checked_border": scheme["pin_checked_border"],
        "menu_bg": scheme["menu_bg"],
        "menu_fg": scheme["menu_fg"],
        "menu_border": scheme["menu_border"],
        "menu_hover_bg": scheme["menu_hover_bg"],
        "menu_hover_fg": scheme["menu_hover_fg"],
        "menu_separator": scheme["menu_separator"],
        "menu_disabled_fg": scheme["menu_disabled_fg"],
        "overlay_focus_border": scheme["primary_focus"],
        "scrollbar_handle": scheme["scrollbar_handle"],
    }


def theme_colors(theme_name: str | None = None) -> dict[str, str]:
    resolved = _ACTIVE_THEME_NAME if theme_name is None else resolve_theme_name(theme_name)
    scheme = dict(_THEME_SCHEMES.get(resolved, DARK_MATERIAL_SCHEME))
    return {
        **scheme,
        **_compatibility_tokens(scheme),
        **_ui_role_tokens(scheme),
    }


def color(name: str, *, theme_name: str | None = None) -> str:
    return theme_colors(theme_name)[name]


def qcolor(name: str, *, alpha: int | None = None, theme_name: str | None = None) -> QColor:
    value = QColor(color(name, theme_name=theme_name))
    if alpha is not None:
        value.setAlpha(alpha)
    return value


def style_tokens(theme_name: str | None = None) -> dict[str, str]:
    return {
        **BASE_STYLE_TOKENS,
        **theme_colors(theme_name),
    }
