from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=None)
def load_style_sheet(filename: str) -> str:
    return resources.files("app.ui.styles").joinpath(filename).read_text(encoding="utf-8")
