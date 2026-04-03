import hashlib
import sys
from pathlib import Path


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config.json"
APP_LOCK_PATH = str(BASE_DIR / ".ocrtranslator.lock")
LOCK_STALE_MS = 15000
APP_SERVER_NAME = f"ocrtranslator-{hashlib.md5(str(BASE_DIR).encode('utf-8')).hexdigest()}"
