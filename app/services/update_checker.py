from __future__ import annotations

from dataclasses import dataclass
import re

import requests

from ..app_metadata import APP_NAME, APP_VERSION, REPOSITORY_NAME, REPOSITORY_URL

LATEST_RELEASE_API_URL = f"https://api.github.com/repos/{REPOSITORY_NAME}/releases/latest"
_VERSION_PART_RE = re.compile(r"(\d+)")


@dataclass(slots=True)
class UpdateCheckResult:
    kind: str
    current_version: str
    latest_version: str = ""
    release_url: str = f"{REPOSITORY_URL}/releases"
    error: str = ""

    @property
    def has_update(self) -> bool:
        return self.kind == "available"

    @property
    def is_up_to_date(self) -> bool:
        return self.kind == "up_to_date"

    @property
    def is_error(self) -> bool:
        return self.kind == "error"


def normalize_version_text(value: str | None) -> str:
    text = str(value or "").strip()
    if text.lower().startswith("v"):
        text = text[1:]
    return text.strip()


def version_tuple(value: str | None) -> tuple[int, ...]:
    normalized = normalize_version_text(value)
    if not normalized:
        return ()
    parts: list[int] = []
    for chunk in normalized.split("."):
        match = _VERSION_PART_RE.match(chunk.strip())
        if not match:
            break
        parts.append(int(match.group(1)))
    return tuple(parts)


def compare_versions(left: str | None, right: str | None) -> int:
    left_tuple = version_tuple(left)
    right_tuple = version_tuple(right)
    if not left_tuple or not right_tuple:
        return 0
    max_len = max(len(left_tuple), len(right_tuple))
    padded_left = left_tuple + (0,) * (max_len - len(left_tuple))
    padded_right = right_tuple + (0,) * (max_len - len(right_tuple))
    return (padded_left > padded_right) - (padded_left < padded_right)


class UpdateCheckService:
    def __init__(self, *, api_url: str = LATEST_RELEASE_API_URL, timeout_seconds: float = 5.0, log_func=None):
        self.api_url = api_url
        self.timeout_seconds = float(timeout_seconds)
        self.log = log_func or (lambda message: None)

    def check_latest_release(self, *, current_version: str = APP_VERSION) -> UpdateCheckResult:
        release_url = f"{REPOSITORY_URL}/releases"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{APP_NAME}/{normalize_version_text(current_version) or APP_VERSION}",
        }
        try:
            response = requests.get(self.api_url, headers=headers, timeout=self.timeout_seconds)
        except Exception as exc:  # noqa: BLE001
            return UpdateCheckResult(kind="error", current_version=normalize_version_text(current_version) or APP_VERSION, release_url=release_url, error=str(exc) or exc.__class__.__name__)

        release_url = str(getattr(response, "url", "") or release_url)
        if response.status_code != 200:
            return UpdateCheckResult(
                kind="error",
                current_version=normalize_version_text(current_version) or APP_VERSION,
                release_url=release_url,
                error=self._response_error_message(response),
            )

        try:
            payload = response.json()
        except Exception:  # noqa: BLE001
            return UpdateCheckResult(
                kind="error",
                current_version=normalize_version_text(current_version) or APP_VERSION,
                release_url=release_url,
                error="GitHub returned invalid release metadata.",
            )

        latest_version = normalize_version_text(payload.get("tag_name") or payload.get("name"))
        release_url = str(payload.get("html_url") or release_url)
        if not version_tuple(latest_version):
            return UpdateCheckResult(
                kind="error",
                current_version=normalize_version_text(current_version) or APP_VERSION,
                release_url=release_url,
                error="The latest release tag could not be parsed.",
            )

        normalized_current_version = normalize_version_text(current_version) or APP_VERSION
        if compare_versions(latest_version, normalized_current_version) > 0:
            return UpdateCheckResult(
                kind="available",
                current_version=normalized_current_version,
                latest_version=latest_version,
                release_url=release_url,
            )
        return UpdateCheckResult(
            kind="up_to_date",
            current_version=normalized_current_version,
            latest_version=latest_version,
            release_url=release_url,
        )

    @staticmethod
    def _response_error_message(response) -> str:
        status_code = getattr(response, "status_code", "?")
        default_message = f"GitHub update check returned HTTP {status_code}."
        try:
            payload = response.json()
        except Exception:  # noqa: BLE001
            return default_message
        message = str(payload.get("message") or "").strip()
        if not message:
            return default_message
        return f"GitHub update check failed: {message}"


__all__ = [
    "LATEST_RELEASE_API_URL",
    "UpdateCheckResult",
    "UpdateCheckService",
    "compare_versions",
    "normalize_version_text",
    "version_tuple",
]
