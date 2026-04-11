import json
from urllib.parse import quote

import requests

from ..models import ApiProfile
from ..operation_control import RequestCancelledError, RequestContext


def _merge_stream_text(current_text: str, chunk_text: str) -> str:
    if not chunk_text:
        return current_text
    if not current_text:
        return chunk_text
    if chunk_text == current_text or current_text.endswith(chunk_text):
        return current_text
    if chunk_text.startswith(current_text):
        return chunk_text
    return current_text + chunk_text


def _iter_sse_data(response: requests.Response, *, request_context: RequestContext | None = None):
    event_lines: list[str] = []
    # SSE payloads are UTF-8. Requests may otherwise decode text/event-stream as ISO-8859-1,
    # which turns CJK streaming output into mojibake before we see it.
    for raw_line in response.iter_lines(decode_unicode=False):
        if request_context and request_context.is_cancelled():
            raise RequestCancelledError()
        if raw_line is None:
            continue
        line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else str(raw_line)
        line = line.strip()
        if not line:
            if event_lines:
                yield "\n".join(event_lines)
                event_lines = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            event_lines.append(line[5:].lstrip())
    if event_lines:
        yield "\n".join(event_lines)


def gemini_content_url(profile: ApiProfile) -> str:
    base = (profile.base_url or "").rstrip("/")
    if base.endswith("/v1beta"):
        return f"{base}/{quote(profile.model, safe='/:.-_')}:generateContent"
    return f"{base}/v1beta/{quote(profile.model, safe='/:.-_')}:generateContent"


def gemini_stream_content_url(profile: ApiProfile) -> str:
    base = (profile.base_url or "").rstrip("/")
    if base.endswith("/v1beta"):
        return f"{base}/{quote(profile.model, safe='/:.-_')}:streamGenerateContent"
    return f"{base}/v1beta/{quote(profile.model, safe='/:.-_')}:streamGenerateContent"


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

    @staticmethod
    def _mark_stream_fallback_allowed(exc: Exception):
        status_code = int(getattr(exc, "status_code", 0) or 0)
        if status_code in {400, 404, 405, 406, 415, 422, 501}:
            setattr(exc, "stream_fallback_allowed", True)
        return exc

    def _request_with_auth_fallback(self, method: str, url: str, api_key: str, *, request_context: RequestContext | None = None, **kwargs):
        http_client = request_context.session if request_context else requests
        base_url = str(kwargs.pop("_base_url", "") or "")
        params = kwargs.pop("params", None)
        response = http_client.request(method, url, headers=gemini_headers(api_key), params=params, **kwargs)
        try:
            self._ensure_success(response)
            return response
        except Exception:
            status_code = int(getattr(response, "status_code", 0) or 0)
            if status_code not in {401, 403} or "googleapis.com" in base_url:
                raise
        merged_params = dict(params or {})
        merged_params.update(gemini_query_params(api_key))
        response = http_client.request(method, url, headers={"Content-Type": "application/json"}, params=merged_params, **kwargs)
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
        stream: bool = False,
        stream_callback=None,
        request_context: RequestContext | None = None,
    ) -> str:
        parts = [{"text": prompt}]
        if image_base64:
            parts.append({"inline_data": {"mime_type": "image/png", "data": image_base64}})
        try:
            response = self._request_with_auth_fallback(
                "POST",
                gemini_stream_content_url(profile) if stream else gemini_content_url(profile),
                api_key,
                request_context=request_context,
                json={
                    "contents": [{"role": "user", "parts": parts}],
                    "generationConfig": {"temperature": temperature},
                },
                params={"alt": "sse"} if stream else None,
                timeout=120,
                stream=bool(stream),
                _base_url=profile.base_url,
            )
        except self._error_factory as exc:
            if stream:
                raise self._mark_stream_fallback_allowed(exc)
            raise
        if stream:
            try:
                return self.extract_stream_translation_text(response, request_context=request_context, stream_callback=stream_callback)
            finally:
                response.close()
        return self.extract_translation_text(response.json())

    def extract_stream_translation_text(self, response: requests.Response, *, request_context: RequestContext | None = None, stream_callback=None) -> str:
        current_text = ""
        last_payload: dict | None = None
        for event_data in _iter_sse_data(response, request_context=request_context):
            try:
                data = json.loads(event_data)
            except json.JSONDecodeError as exc:
                raise self._error_factory(
                    "Gemini returned an invalid streaming chunk",
                    user_message="Gemini Compatible 流式响应格式无效。",
                    stream_fallback_allowed=True,
                ) from exc
            if not isinstance(data, dict):
                raise self._error_factory(
                    "Gemini returned an unexpected streaming payload",
                    user_message="Gemini Compatible 流式响应格式不兼容。",
                    stream_fallback_allowed=True,
                )
            last_payload = data
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
                continue
            candidate = candidates[0]
            parts = candidate.get("content", {}).get("parts", [])
            piece = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text"))
            if piece.strip():
                current_text = _merge_stream_text(current_text, piece)
                if callable(stream_callback):
                    stream_callback(current_text)
        if current_text.strip():
            return current_text
        if last_payload is not None:
            return self.extract_translation_text(last_payload)
        raise self._error_factory(
            "Gemini returned an empty streaming response",
            user_message="Gemini Compatible 沒有回傳可顯示的流式內容。",
            stream_fallback_allowed=True,
        )

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
