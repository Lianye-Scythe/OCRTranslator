from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from ..runtime_paths import resource_path


APP_ICON_RELATIVE_DIR = ("app", "assets", "icons")
APP_ICON_PNG_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
APP_ICON_ICO_NAME = "app-icon.ico"
APP_ICON_SOURCE_NAME = "app-icon-source.png"


def app_icon_asset_path(filename: str) -> Path:
    return resource_path(*APP_ICON_RELATIVE_DIR, filename)


def app_icon_ico_path() -> Path:
    return app_icon_asset_path(APP_ICON_ICO_NAME)


def app_icon_source_path() -> Path:
    return app_icon_asset_path(APP_ICON_SOURCE_NAME)


def app_icon_png_path(size: int) -> Path:
    return app_icon_asset_path(f"app-icon-{int(size)}.png")


@lru_cache(maxsize=1)
def load_app_icon() -> QIcon:
    icon = QIcon()
    ico_path = app_icon_ico_path()
    if ico_path.exists():
        icon = QIcon(str(ico_path))

    for size in APP_ICON_PNG_SIZES:
        png_path = app_icon_png_path(size)
        if png_path.exists():
            icon.addFile(str(png_path), QSize(size, size))

    return icon
