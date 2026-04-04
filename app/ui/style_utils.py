from functools import lru_cache
from importlib import resources

from .theme_tokens import style_tokens


def _render_style_tokens(content: str) -> str:
    rendered = content
    for key, value in style_tokens().items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


@lru_cache(maxsize=None)
def load_style_sheet(filename: str) -> str:
    content = resources.files("app.ui.styles").joinpath(filename).read_text(encoding="utf-8")
    return _render_style_tokens(content)
