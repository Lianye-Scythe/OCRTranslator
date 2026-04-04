from __future__ import annotations

from PySide6.QtGui import QColor

THEME_COLORS = {
    "accent": "#7489ff",
    "accent_soft": "#93a3ff",
    "accent_focus": "#90a4ff",
    "accent_hover": "#899cff",
    "accent_border": "#7085ff",
    "text_primary": "#eef3fb",
    "text_base": "#e7edf7",
    "text_secondary": "#90a0b6",
    "text_tertiary": "#70809b",
    "text_emphasis": "#f4efe6",
    "text_chip": "#d9e3f8",
    "surface_app": "#0b1017",
    "surface_base": "#101720",
    "surface_alt": "#111722",
    "surface_panel": "#121a26",
    "surface_input": "#0c131c",
    "surface_hover": "#141d29",
    "surface_button_secondary": "#202d41",
    "surface_button_neutral": "#161f2b",
    "surface_button_success": "#1f6a49",
    "surface_button_danger": "#402029",
    "border_base": "#253244",
    "border_soft": "#31425a",
    "border_focus": "#273345",
    "overlay_scrim": "rgba(116, 137, 255, 0.16)",
    "shadow": "#020614",
    "warning": "#d7bf88",
    "danger_text": "#ffb4c1",
    "danger_surface": "#24131a",
    "danger_border": "#5c2b39",
    "scroll_handle": "#2d3a4c",
}

STYLE_TOKENS = {
    "font_ui": "'Segoe UI Variable Text','Segoe UI','Microsoft JhengHei UI'",
    "font_code": "'Cascadia Code','Consolas'",
    "accent": THEME_COLORS["accent"],
    "accent_soft": THEME_COLORS["accent_soft"],
    "accent_focus": THEME_COLORS["accent_focus"],
    "accent_hover": THEME_COLORS["accent_hover"],
    "accent_border": THEME_COLORS["accent_border"],
    "text_primary": THEME_COLORS["text_primary"],
    "text_base": THEME_COLORS["text_base"],
    "text_secondary": THEME_COLORS["text_secondary"],
    "text_tertiary": THEME_COLORS["text_tertiary"],
    "text_emphasis": THEME_COLORS["text_emphasis"],
    "text_chip": THEME_COLORS["text_chip"],
    "surface_app": THEME_COLORS["surface_app"],
    "surface_base": THEME_COLORS["surface_base"],
    "surface_alt": THEME_COLORS["surface_alt"],
    "surface_panel": THEME_COLORS["surface_panel"],
    "surface_input": THEME_COLORS["surface_input"],
    "surface_hover": THEME_COLORS["surface_hover"],
    "surface_button_secondary": THEME_COLORS["surface_button_secondary"],
    "surface_button_neutral": THEME_COLORS["surface_button_neutral"],
    "surface_button_success": THEME_COLORS["surface_button_success"],
    "surface_button_danger": THEME_COLORS["surface_button_danger"],
    "border_base": THEME_COLORS["border_base"],
    "border_soft": THEME_COLORS["border_soft"],
    "border_focus": THEME_COLORS["border_focus"],
    "warning": THEME_COLORS["warning"],
    "danger_text": THEME_COLORS["danger_text"],
    "danger_surface": THEME_COLORS["danger_surface"],
    "danger_border": THEME_COLORS["danger_border"],
    "scroll_handle": THEME_COLORS["scroll_handle"],
}


def color(name: str) -> str:
    return THEME_COLORS[name]


def qcolor(name: str, *, alpha: int | None = None) -> QColor:
    value = QColor(THEME_COLORS[name])
    if alpha is not None:
        value.setAlpha(alpha)
    return value


def style_tokens() -> dict[str, str]:
    return dict(STYLE_TOKENS)
