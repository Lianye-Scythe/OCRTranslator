from dataclasses import dataclass, field

from .constants import (
    DEFAULT_BASE_URL,
    DEFAULT_CAPTURE_HOTKEY,
    DEFAULT_INPUT_HOTKEY,
    DEFAULT_MODEL,
    DEFAULT_PROMPT_PRESET_DEFINITIONS,
    DEFAULT_SELECTION_HOTKEY,
)


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
    name: str = "翻譯"
    builtin_id: str = "translate"
    image_prompt: str = ""
    text_prompt: str = ""


def default_prompt_presets() -> list[PromptPreset]:
    return [PromptPreset(**definition) for definition in DEFAULT_PROMPT_PRESET_DEFINITIONS]


@dataclass
class AppConfig:
    target_language: str = "繁體中文"
    mode: str = "book_lr"
    temperature: float = 0.2
    overlay_width: int = 440
    overlay_height: int = 520
    margin: int = 18
    ui_language: str = "zh-TW"
    hotkey: str = DEFAULT_CAPTURE_HOTKEY
    selection_hotkey: str = DEFAULT_SELECTION_HOTKEY
    input_hotkey: str = DEFAULT_INPUT_HOTKEY
    overlay_font_family: str = "Microsoft JhengHei UI"
    overlay_font_size: int = 12
    overlay_opacity: int = 96
    overlay_pinned: bool = False
    close_to_tray_on_close: bool = False
    active_profile_name: str = "Default Gemini"
    active_prompt_preset_name: str = DEFAULT_PROMPT_PRESET_DEFINITIONS[0]["name"]
    api_profiles: list[ApiProfile] = field(default_factory=lambda: [ApiProfile()])
    prompt_presets: list[PromptPreset] = field(default_factory=default_prompt_presets)
