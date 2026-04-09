from dataclasses import dataclass, field

from .app_defaults import (
    DEFAULT_BASE_URL,
    DEFAULT_CAPTURE_HOTKEY,
    DEFAULT_INPUT_HOTKEY,
    DEFAULT_MODEL,
    DEFAULT_OVERLAY_FONT_FAMILY,
    DEFAULT_SELECTION_HOTKEY,
    DEFAULT_TARGET_LANGUAGE,
    DEFAULT_THEME_MODE,
    DEFAULT_UI_LANGUAGE,
)
from .default_prompts import DEFAULT_PROMPT_PRESET_DEFINITIONS


@dataclass
class ApiProfile:
    name: str = "Default Gemini"
    provider: str = "gemini"
    base_url: str = DEFAULT_BASE_URL
    api_keys: list[str] = field(default_factory=list)
    model: str = DEFAULT_MODEL
    available_models: list[str] = field(default_factory=lambda: [DEFAULT_MODEL])
    retry_count: int = 1
    retry_interval: float = 2.0


@dataclass
class PromptPreset:
    name: str = "翻譯 (Translate)"
    builtin_id: str = "translate"
    image_prompt: str = ""
    text_prompt: str = ""


def default_prompt_presets() -> list[PromptPreset]:
    return [PromptPreset(**definition) for definition in DEFAULT_PROMPT_PRESET_DEFINITIONS]


@dataclass
class AppConfig:
    target_language: str = DEFAULT_TARGET_LANGUAGE
    mode: str = "book_lr"
    temperature: float = 0.2
    overlay_width: int = 440
    overlay_height: int = 520
    margin: int = 18
    overlay_auto_expand_top_margin: int = 42
    overlay_auto_expand_bottom_margin: int = 24
    toast_duration_seconds: float = 1.5
    stream_responses: bool = True
    debug_logging_enabled: bool = False
    check_updates_on_startup: bool = False
    ui_language: str = DEFAULT_UI_LANGUAGE
    theme_mode: str = DEFAULT_THEME_MODE
    hotkey: str = DEFAULT_CAPTURE_HOTKEY
    selection_hotkey: str = DEFAULT_SELECTION_HOTKEY
    input_hotkey: str = DEFAULT_INPUT_HOTKEY
    overlay_font_family: str = DEFAULT_OVERLAY_FONT_FAMILY
    overlay_font_size: int = 16
    overlay_opacity: int = 95
    overlay_pinned: bool = False
    overlay_pinned_x: int | None = None
    overlay_pinned_y: int | None = None
    overlay_pinned_width: int | None = None
    overlay_pinned_height: int | None = None
    overlay_unpinned_width: int | None = None
    overlay_unpinned_width_source: str = ""
    close_to_tray_on_close: bool = False
    active_profile_name: str = "Default Gemini"
    active_prompt_preset_name: str = DEFAULT_PROMPT_PRESET_DEFINITIONS[0]["name"]
    api_profiles: list[ApiProfile] = field(default_factory=lambda: [ApiProfile()])
    prompt_presets: list[PromptPreset] = field(default_factory=default_prompt_presets)
