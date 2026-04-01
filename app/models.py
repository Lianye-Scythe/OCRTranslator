from dataclasses import dataclass, field

from .constants import DEFAULT_BASE_URL, DEFAULT_MODEL


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
class AppConfig:
    target_language: str = "繁體中文"
    mode: str = "book_lr"
    temperature: float = 0.2
    overlay_width: int = 440
    overlay_height: int = 520
    margin: int = 18
    ui_language: str = "zh-TW"
    hotkey: str = "Shift+Win+A"
    overlay_font_family: str = "Microsoft JhengHei UI"
    overlay_font_size: int = 12
    overlay_opacity: int = 96
    overlay_pinned: bool = False
    active_profile_name: str = "Default Gemini"
    api_profiles: list[ApiProfile] = field(default_factory=lambda: [ApiProfile()])
