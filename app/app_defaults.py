DEFAULT_TARGET_LANGUAGE = "繁體中文"
DEFAULT_UI_LANGUAGE = "en"
DEFAULT_THEME_MODE = "system"
DEFAULT_OVERLAY_FONT_FAMILY = "Noto Sans TC"


def default_overlay_font_family(target_language: str | None) -> str:
    language = str(target_language or DEFAULT_TARGET_LANGUAGE).strip().casefold().replace("_", "-")
    if language in {"繁體中文", "繁体中文", "traditional chinese", "chinese (traditional)", "zh-tw", "zh-hk", "zh-mo"} or language.startswith("zh-hant"):
        return "Noto Sans TC"
    if language in {"简体中文", "簡體中文", "simplified chinese", "chinese (simplified)", "zh-cn", "zh-sg", "zh", "chinese", "中文"} or language.startswith("zh-hans"):
        return "Noto Sans SC"
    if language in {"日本語", "日文", "日語", "日语", "japanese", "ja", "jp"} or language.startswith("ja-"):
        return "Noto Sans JP"
    return "Noto Sans"

VALID_THEME_MODES = ("system", "light", "dark")

DEFAULT_TARGET_LANGUAGE_BY_UI_LANGUAGE = {
    "zh-TW": "繁體中文",
    "zh-CN": "简体中文",
    "en": "English",
}


COMMON_TARGET_LANGUAGES = (
    "繁體中文",
    "简体中文",
    "English",
    "日本語",
    "한국어",
    "Français",
    "Deutsch",
    "Español",
    "Italiano",
    "Português",
    "Русский",
    "العربية",
    "ไทย",
    "Tiếng Việt",
)


def default_target_language_for_ui_language(ui_language: str) -> str:
    return DEFAULT_TARGET_LANGUAGE_BY_UI_LANGUAGE.get(str(ui_language or "").strip(), DEFAULT_TARGET_LANGUAGE_BY_UI_LANGUAGE[DEFAULT_UI_LANGUAGE])


def normalize_theme_mode(value, *, default: str = DEFAULT_THEME_MODE) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in VALID_THEME_MODES else default


DEFAULT_MODEL = "models/gemini-flash-lite-latest"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com"
MODEL_PREFIX = "models/"

DEFAULT_CAPTURE_HOTKEY = "Shift+Win+X"
DEFAULT_SELECTION_HOTKEY = "Shift+Win+C"
DEFAULT_INPUT_HOTKEY = "Shift+Win+Z"

PROVIDER_LABELS = {
    "gemini": {"zh-TW": "Gemini 相容", "zh-CN": "Gemini 兼容", "en": "Gemini Compatible"},
    "openai": {"zh-TW": "OpenAI 相容", "zh-CN": "OpenAI 兼容", "en": "OpenAI Compatible"},
}
