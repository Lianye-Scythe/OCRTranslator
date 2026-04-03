DEFAULT_TARGET_LANGUAGE = "繁體中文"
DEFAULT_UI_LANGUAGE = "en"
DEFAULT_OVERLAY_FONT_FAMILY = "Microsoft JhengHei UI"

DEFAULT_TARGET_LANGUAGE_BY_UI_LANGUAGE = {
    "zh-TW": "繁體中文",
    "zh-CN": "简体中文",
    "en": "English",
}


def default_target_language_for_ui_language(ui_language: str) -> str:
    return DEFAULT_TARGET_LANGUAGE_BY_UI_LANGUAGE.get(str(ui_language or "").strip(), DEFAULT_TARGET_LANGUAGE_BY_UI_LANGUAGE[DEFAULT_UI_LANGUAGE])

DEFAULT_MODEL = "models/gemini-3.1-flash-lite-preview"
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
