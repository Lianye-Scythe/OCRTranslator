import hashlib
import sys
from pathlib import Path

from .default_prompts import (
    DEFAULT_ANSWER_IMAGE_PROMPT,
    DEFAULT_ANSWER_TEXT_PROMPT,
    DEFAULT_POLISH_IMAGE_PROMPT,
    DEFAULT_POLISH_TEXT_PROMPT,
    DEFAULT_PROMPT,
    DEFAULT_PROMPT_PRESET_DEFINITIONS,
    DEFAULT_TRANSLATION_IMAGE_PROMPT,
    DEFAULT_TRANSLATION_TEXT_PROMPT,
)
from .i18n import I18N


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config.json"
DEFAULT_MODEL = "models/gemini-3.1-flash-lite-preview"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com"
APP_LOCK_PATH = str(BASE_DIR / ".ocrtranslator.lock")
LOCK_STALE_MS = 15000
APP_SERVER_NAME = f"ocrtranslator-{hashlib.md5(str(BASE_DIR).encode('utf-8')).hexdigest()}"
MODEL_PREFIX = "models/"
DEFAULT_CAPTURE_HOTKEY = "Shift+Win+X"
DEFAULT_SELECTION_HOTKEY = "Shift+Win+C"
DEFAULT_INPUT_HOTKEY = "Shift+Win+Z"
PROVIDER_LABELS = {
    "gemini": {"zh-TW": "Gemini 相容", "en": "Gemini Compatible"},
    "openai": {"zh-TW": "OpenAI 相容", "en": "OpenAI Compatible"},
}
AUTHOR_NAME_ZH = "鐮夜"
AUTHOR_NAME_EN = "scythenight"
REPOSITORY_NAME = "Lianye-Scythe/OCRTranslator"
REPOSITORY_URL = "https://github.com/Lianye-Scythe/OCRTranslator"
