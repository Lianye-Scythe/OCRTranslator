import os
import hashlib
import sys
from pathlib import Path


def get_resource_dir() -> Path:
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parent.parent


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_user_config_dir() -> Path:
    local_app_data = str(os.getenv("LOCALAPPDATA", "")).strip()
    if local_app_data:
        return Path(local_app_data).expanduser().resolve() / "OCRTranslator"
    return Path.home().resolve() / ".ocrtranslator"


BASE_DIR = get_base_dir()
RESOURCE_DIR = get_resource_dir()
CONFIG_PATH = BASE_DIR / "config.json"
FALLBACK_CONFIG_PATH = get_user_config_dir() / "config.json"
APP_LOCK_PATH = str(BASE_DIR / ".ocrtranslator.lock")
LOCK_STALE_MS = 15000
APP_SERVER_NAME = f"ocrtranslator-{hashlib.md5(str(BASE_DIR).encode('utf-8')).hexdigest()}"


def resource_path(*parts: str) -> Path:
    return RESOURCE_DIR.joinpath(*parts)


__all__ = [
    "APP_LOCK_PATH",
    "APP_SERVER_NAME",
    "BASE_DIR",
    "CONFIG_PATH",
    "FALLBACK_CONFIG_PATH",
    "LOCK_STALE_MS",
    "RESOURCE_DIR",
    "get_base_dir",
    "get_resource_dir",
    "get_user_config_dir",
    "resource_path",
]
