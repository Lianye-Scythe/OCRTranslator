from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication

from ..app_defaults import DEFAULT_THEME_MODE, normalize_theme_mode

LIGHT_MATERIAL_SCHEME = {
    "primary": "#5c67c8",
    "on_primary": "#ffffff",
    "primary_container": "#e6eaff",
    "on_primary_container": "#334498",
    "primary_hover": "#535fbe",
    "primary_focus": "#8d9aea",
    "secondary": "#5f6781",
    "on_secondary": "#ffffff",
    "secondary_container": "#dde4fb",
    "on_secondary_container": "#3d4f9d",
    "secondary_hover": "#d2daf7",
    "secondary_border": "#b7c2ea",
    "tertiary": "#5467b6",
    "on_tertiary": "#ffffff",
    "tertiary_container": "#eef2ff",
    "on_tertiary_container": "#46589a",
    "tertiary_border": "#d7def8",
    "surface_dim": "#f4f6fb",
    "surface": "#fbfcff",
    "surface_bright": "#ffffff",
    "surface_container_lowest": "#ffffff",
    "surface_container_low": "#f8faff",
    "surface_container": "#f2f5fb",
    "surface_container_high": "#e9edf7",
    "surface_container_highest": "#e3e8f3",
    "on_surface": "#1f2330",
    "on_surface_variant": "#677186",
    "outline": "#c3cce0",
    "outline_variant": "#d8deeb",
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
}

DARK_MATERIAL_SCHEME = {
    "primary": "#97abff",
    "on_primary": "#0f1728",
    "primary_container": "#31407a",
    "on_primary_container": "#dce4ff",
    "primary_hover": "#a6b7ff",
    "primary_focus": "#c0cbff",
    "secondary": "#bbc5e2",
    "on_secondary": "#1d2941",
    "secondary_container": "#28334a",
    "on_secondary_container": "#dce4ff",
    "secondary_hover": "#31405a",
    "secondary_border": "#435578",
    "tertiary": "#a8b8ff",
    "on_tertiary": "#142038",
    "tertiary_container": "#252f43",
    "on_tertiary_container": "#d7e0ff",
    "tertiary_border": "#3a4864",
    "surface_dim": "#0f1319",
    "surface": "#161b23",
    "surface_bright": "#1d232c",
    "surface_container_lowest": "#11161d",
    "surface_container_low": "#171d26",
    "surface_container": "#1c222c",
    "surface_container_high": "#212835",
    "surface_container_highest": "#273043",
    "on_surface": "#eef2f8",
    "on_surface_variant": "#a7b1bf",
    "outline": "#445066",
    "outline_variant": "#313949",
    "error": "#ffb9c5",
    "on_error": "#3b0714",
    "error_container": "#27191d",
    "on_error_container": "#ffdde3",
    "warning": "#f0c47a",
    "warning_container": "#342918",
    "on_warning_container": "#f8e2b0",
    "warning_border": "#8f712e",
    "success": "#87d2ab",
    "success_container": "#1e5b45",
    "on_success_container": "#d9f7e6",
    "success_border": "#2c7555",
    "shadow": "#05080d",
    "scrim": "rgba(151, 171, 255, 0.16)",
    "scrollbar_handle": "#59647b",
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
        "subtle_fg": scheme["outline"],
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
        "field_focus_border": scheme["primary"],
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
        "validation_bg": scheme["error_container"],
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
