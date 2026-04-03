from urllib.parse import quote

import requests

from ..models import ApiProfile


def gemini_content_url(profile: ApiProfile, api_key: str) -> str:
    base = (profile.base_url or "").rstrip("/")
    if base.endswith("/v1beta"):
        return f"{base}/{quote(profile.model, safe='/:.-_')}:generateContent?key={api_key}"
    return f"{base}/v1beta/{quote(profile.model, safe='/:.-_')}:generateContent?key={api_key}"


def gemini_models_url(base_url: str, api_key: str) -> str:
    base = (base_url or "").rstrip("/")
    if base.endswith("/v1beta"):
        return f"{base}/models?key={api_key}"
    return f"{base}/v1beta/models?key={api_key}"


def gemini_finish_reason_text(finish_reason: str | None) -> str:
    if not finish_reason:
        return ""
    return str(finish_reason).strip()


class GeminiCompatibleAdapter:
    provider_name = "gemini"

    def __init__(self, ensure_success, error_factory):
        self._ensure_success = ensure_success
        self._error_factory = error_factory

    def list_models(self, profile: ApiProfile, api_key: str) -> list[str]:
        response = requests.get(gemini_models_url(profile.base_url, api_key), timeout=30)
        self._ensure_success(response)
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
    ) -> str:
        parts = [{"text": prompt}]
        if image_base64:
            parts.append({"inline_data": {"mime_type": "image/png", "data": image_base64}})
        response = requests.post(
            gemini_content_url(profile, api_key),
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": parts}],
                "generationConfig": {"temperature": temperature},
            },
            timeout=120,
        )
        self._ensure_success(response)
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
