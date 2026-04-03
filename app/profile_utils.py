from collections.abc import Iterable

from .app_defaults import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_OPENAI_BASE_URL,
    MODEL_PREFIX,
    PROVIDER_LABELS,
)


def default_base_url_for_provider(provider: str) -> str:
    return DEFAULT_BASE_URL if provider == "gemini" else DEFAULT_OPENAI_BASE_URL


def default_model_for_provider(provider: str) -> str:
    return DEFAULT_MODEL if provider == "gemini" else ""


def normalize_provider_name(provider: str) -> str:
    return provider if provider in PROVIDER_LABELS else "gemini"


def normalize_model_value(model_name: str, provider: str) -> str:
    provider = normalize_provider_name(provider)
    value = (model_name or "").strip()
    if provider == "gemini":
        if not value:
            return DEFAULT_MODEL
        return value if value.startswith(MODEL_PREFIX) else f"{MODEL_PREFIX}{value}"
    return value[len(MODEL_PREFIX):] if value.startswith(MODEL_PREFIX) else value


def display_model_value(model_name: str, provider: str) -> str:
    provider = normalize_provider_name(provider)
    value = (model_name or "").strip()
    if provider == "gemini" and value.startswith(MODEL_PREFIX):
        return value[len(MODEL_PREFIX):]
    return value


def unique_non_empty(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value or "").strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
