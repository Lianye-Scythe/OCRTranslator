import json

import requests

from ..models import ApiProfile
from ..operation_control import RequestCancelledError, RequestContext


def openai_url(base_url: str, path: str) -> str:
    base = (base_url or "").rstrip("/")
    if base.endswith("/v1"):
        return f"{base}{path}"
    return f"{base}/v1{path}"


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


def openai_content_text(content) -> str:
    if isinstance(content, list):
        return "\n".join(item.get("text", "") for item in content if isinstance(item, dict) and item.get("text")).strip()
    return content.strip() if isinstance(content, str) else ""


def openai_stream_delta_text(content) -> str:
    if isinstance(content, list):
        return "\n".join(item.get("text", "") for item in content if isinstance(item, dict) and item.get("text"))
    return content if isinstance(content, str) else ""


class OpenAICompatibleAdapter:
    provider_name = "openai"

    def __init__(self, ensure_success, error_factory):
        self._ensure_success = ensure_success
        self._error_factory = error_factory

    @staticmethod
    def _mark_stream_fallback_allowed(exc: Exception):
        status_code = int(getattr(exc, "status_code", 0) or 0)
        if status_code in {400, 404, 405, 406, 415, 422, 501}:
            setattr(exc, "stream_fallback_allowed", True)
        return exc

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
        stream: bool = False,
        stream_callback=None,
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
        payload = {
            "model": profile.model, "temperature": temperature, "messages": [{"role": "user", "content": content}], "stream": bool(stream)
        }
        try:
            response = http_client.post(
                openai_url(profile.base_url, "/chat/completions"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=120,
                stream=bool(stream),
            )
            self._ensure_success(response)
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
        last_finish_reason = ""
        for event_data in _iter_sse_data(response, request_context=request_context):
            if event_data == "[DONE]":
                break
            try:
                data = json.loads(event_data)
            except json.JSONDecodeError as exc:
                raise self._error_factory(
                    "OpenAI returned an invalid streaming chunk",
                    user_message="OpenAI Compatible 流式响应格式无效。",
                    stream_fallback_allowed=True,
                ) from exc
            if not isinstance(data, dict):
                raise self._error_factory(
                    "OpenAI returned an unexpected streaming payload",
                    user_message="OpenAI Compatible 流式响应格式不兼容。",
                    stream_fallback_allowed=True,
                )
            choices = data.get("choices", [])
            if not choices or not isinstance(choices[0], dict):
                continue
            choice = choices[0]
            delta = choice.get("delta", {}) if isinstance(choice, dict) else {}
            piece = openai_stream_delta_text(delta.get("content", "")) if isinstance(delta, dict) else ""
            if piece:
                current_text = _merge_stream_text(current_text, piece)
                if callable(stream_callback):
                    stream_callback(current_text)
            finish_reason = str(choice.get("finish_reason") or "").strip()
            if finish_reason:
                last_finish_reason = finish_reason
        if current_text.strip():
            return current_text
        if last_finish_reason == "content_filter":
            raise self._error_factory(
                "OpenAI blocked the response with content_filter",
                user_message="OpenAI 因內容安全策略拒絕了這次請求。請縮小範圍、調整內容，或改用其他模型 / Provider 再試一次。",
                retryable=False,
                retry_same_key=False,
            )
        if last_finish_reason:
            raise self._error_factory(
                f"OpenAI finished without text (finish_reason={last_finish_reason})",
                user_message=f"OpenAI 沒有回傳可顯示的內容（finish_reason={last_finish_reason}）。",
            )
        raise self._error_factory(
            "OpenAI returned an empty streamed message",
            user_message="OpenAI Compatible 沒有回傳可顯示的流式內容。",
            stream_fallback_allowed=True,
        )

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
