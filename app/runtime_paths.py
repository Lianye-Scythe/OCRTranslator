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


BASE_DIR = get_base_dir()
RESOURCE_DIR = get_resource_dir()
CONFIG_PATH = BASE_DIR / "config.json"
APP_LOCK_PATH = str(BASE_DIR / ".ocrtranslator.lock")
LOCK_STALE_MS = 15000
APP_SERVER_NAME = f"ocrtranslator-{hashlib.md5(str(BASE_DIR).encode('utf-8')).hexdigest()}"


def resource_path(*parts: str) -> Path:
    return RESOURCE_DIR.joinpath(*parts)
