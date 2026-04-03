from urllib.parse import quote

import requests

from ..models import ApiProfile
from ..operation_control import RequestContext


def gemini_content_url(profile: ApiProfile) -> str:
    base = (profile.base_url or "").rstrip("/")
    if base.endswith("/v1beta"):
        return f"{base}/{quote(profile.model, safe='/:.-_')}:generateContent"
    return f"{base}/v1beta/{quote(profile.model, safe='/:.-_')}:generateContent"


def gemini_models_url(base_url: str) -> str:
    base = (base_url or "").rstrip("/")
    if base.endswith("/v1beta"):
        return f"{base}/models"
    return f"{base}/v1beta/models"


def gemini_headers(api_key: str) -> dict[str, str]:
    return {"Content-Type": "application/json", "x-goog-api-key": api_key}


def gemini_query_params(api_key: str) -> dict[str, str]:
    return {"key": api_key}


def gemini_finish_reason_text(finish_reason: str | None) -> str:
    if not finish_reason:
        return ""
    return str(finish_reason).strip()


class GeminiCompatibleAdapter:
    provider_name = "gemini"

    def __init__(self, ensure_success, error_factory):
        self._ensure_success = ensure_success
        self._error_factory = error_factory

    def _request_with_auth_fallback(self, method: str, url: str, api_key: str, *, request_context: RequestContext | None = None, **kwargs):
        http_client = request_context.session if request_context else requests
        base_url = str(kwargs.pop("_base_url", "") or "")
        response = http_client.request(method, url, headers=gemini_headers(api_key), **kwargs)
        try:
            self._ensure_success(response)
            return response
        except Exception:
            status_code = int(getattr(response, "status_code", 0) or 0)
            if status_code not in {401, 403} or "googleapis.com" in base_url:
                raise
        response = http_client.request(method, url, headers={"Content-Type": "application/json"}, params=gemini_query_params(api_key), **kwargs)
        self._ensure_success(response)
        return response

    def list_models(self, profile: ApiProfile, api_key: str, *, request_context: RequestContext | None = None) -> list[str]:
        response = self._request_with_auth_fallback(
            "GET",
            gemini_models_url(profile.base_url),
            api_key,
            request_context=request_context,
            timeout=30,
            _base_url=profile.base_url,
        )
        data = response.json()
        models = []
        for item in data.get("models", []):
            if not isinstance(item, dict) or not item.get("name"):
                continue
            supported_methods = item.get("supportedGenerationMethods")
            if isinstance(supported_methods, list) and supported_methods and "generateContent" not in supported_methods:
                continue
            models.append(item.get("name", ""))
        return models

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
        parts = [{"text": prompt}]
        if image_base64:
            parts.append({"inline_data": {"mime_type": "image/png", "data": image_base64}})
        response = self._request_with_auth_fallback(
            "POST",
            gemini_content_url(profile),
            api_key,
            request_context=request_context,
            json={
                "contents": [{"parts": parts}],
                "generationConfig": {"temperature": temperature},
            },
            timeout=120,
            _base_url=profile.base_url,
        )
        return self.extract_translation_text(response.json())

    def extract_translation_text(self, data: dict) -> str:
        if not isinstance(data, dict):
            raise self._error_factory("Gemini returned an unexpected payload")
        prompt_feedback = data.get("promptFeedback") if isinstance(data, dict) else None
        if isinstance(prompt_feedback, dict):
            block_reason = str(prompt_feedback.get("blockReason") or "").strip()
            if block_reason:
                raise self._error_factory(
                    f"Gemini blocked the request: {block_reason}",
                    user_message=(
                        f"Gemini 因內容安全策略拒絕了這次請求（{block_reason}）。"
                        "請縮小範圍、避開敏感內容，或改用其他模型 / Provider 再試一次。"
                    ),
                    retryable=False,
                    retry_same_key=False,
                )
        candidates = data.get("candidates", [])
        if not candidates or not isinstance(candidates[0], dict):
            raise self._error_factory("Gemini returned no candidates", user_message="Gemini 沒有回傳可用候選結果。")
        candidate = candidates[0]
        parts = candidate.get("content", {}).get("parts", [])
        text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text")).strip()
        if text:
            return text
        finish_reason = gemini_finish_reason_text(candidate.get("finishReason"))
        if finish_reason == "PROHIBITED_CONTENT":
            raise self._error_factory(
                "Gemini finished without text (finishReason=PROHIBITED_CONTENT)",
                user_message="Gemini 因內容安全策略拒絕了這次請求。請縮小範圍、避開敏感內容，或改用其他模型 / Provider 再試一次。",
                retryable=False,
                retry_same_key=False,
            )
        if finish_reason and finish_reason != "STOP":
            raise self._error_factory(
                f"Gemini finished without text (finishReason={finish_reason})",
                user_message=f"Gemini 沒有回傳可顯示的內容（finishReason={finish_reason}）。",
            )
        raise self._error_factory("Gemini returned an empty response", user_message="Gemini 沒有回傳可顯示的內容。")
