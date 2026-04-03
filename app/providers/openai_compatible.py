import requests

from ..models import ApiProfile
from ..operation_control import RequestContext


def openai_url(base_url: str, path: str) -> str:
    base = (base_url or "").rstrip("/")
    if base.endswith("/v1"):
        return f"{base}{path}"
    return f"{base}/v1{path}"


def openai_content_text(content) -> str:
    if isinstance(content, list):
        return "\n".join(item.get("text", "") for item in content if isinstance(item, dict) and item.get("text")).strip()
    return content.strip() if isinstance(content, str) else ""


class OpenAICompatibleAdapter:
    provider_name = "openai"

    def __init__(self, ensure_success, error_factory):
        self._ensure_success = ensure_success
        self._error_factory = error_factory

    def list_models(self, profile: ApiProfile, api_key: str, *, request_context: RequestContext | None = None) -> list[str]:
        http_client = request_context.session if request_context else requests
        response = http_client.get(openai_url(profile.base_url, "/models"), headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
        self._ensure_success(response)
        data = response.json()
        return [item.get("id", "") for item in data.get("data", []) if isinstance(item, dict) and item.get("id")]

    def request_prompt(
        self,
        profile: ApiProfile,
        api_key: str,
        prompt: str,
        temperature: float,
        *,
        image_base64: str | None = None,
        request_context: RequestContext | None = None,
    ) -> str:
        content = (
            [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
            ]
            if image_base64
            else prompt
        )
        http_client = request_context.session if request_context else requests
        response = http_client.post(
            openai_url(profile.base_url, "/chat/completions"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": profile.model,
                "temperature": temperature,
                "messages": [{"role": "user", "content": content}],
            },
            timeout=120,
        )
        self._ensure_success(response)
        return self.extract_translation_text(response.json())

    def extract_translation_text(self, data: dict) -> str:
        if not isinstance(data, dict):
            raise self._error_factory("OpenAI returned an unexpected payload")
        choices = data.get("choices", [])
        if not choices or not isinstance(choices[0], dict):
            raise self._error_factory("OpenAI returned no choices")
        choice = choices[0]
        content = openai_content_text(choice.get("message", {}).get("content", ""))
        if content:
            return content
        finish_reason = str(choice.get("finish_reason") or "").strip()
        if finish_reason == "content_filter":
            raise self._error_factory(
                "OpenAI blocked the response with content_filter",
                user_message="OpenAI 因內容安全策略拒絕了這次請求。請縮小範圍、調整內容，或改用其他模型 / Provider 再試一次。",
                retryable=False,
                retry_same_key=False,
            )
        if finish_reason:
            raise self._error_factory(
                f"OpenAI finished without text (finish_reason={finish_reason})",
                user_message=f"OpenAI 沒有回傳可顯示的內容（finish_reason={finish_reason}）。",
            )
        raise self._error_factory("OpenAI returned an empty message", user_message="OpenAI 沒有回傳可顯示的內容。")
