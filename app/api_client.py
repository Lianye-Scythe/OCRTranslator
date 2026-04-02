import base64
import io
import time
from urllib.parse import quote

import requests
from PIL import Image

from .constants import DEFAULT_PROMPT
from .models import ApiProfile


class ApiClient:
    def __init__(self, log_func):
        self.log = log_func
        self.profile_key_index: dict[str, int] = {}

    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def _normalize_base(base_url: str) -> str:
        return (base_url or "").rstrip("/")

    @staticmethod
    def _response_error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            text = response.text.strip()
            return text[:240] if text else response.reason or f"HTTP {response.status_code}"

        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                return str(error.get("message") or error.get("status") or error)
            if isinstance(error, str) and error.strip():
                return error.strip()
            message = payload.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        return response.reason or f"HTTP {response.status_code}"

    def _ensure_success(self, response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = self._response_error_message(response)
            raise RuntimeError(f"HTTP {response.status_code}: {detail}") from exc

    def _openai_url(self, base_url: str, path: str) -> str:
        base = self._normalize_base(base_url)
        if base.endswith("/v1"):
            return f"{base}{path}"
        return f"{base}/v1{path}"

    def _gemini_content_url(self, profile: ApiProfile, api_key: str) -> str:
        base = self._normalize_base(profile.base_url)
        if base.endswith("/v1beta"):
            return f"{base}/{quote(profile.model, safe='/:.-_')}:generateContent?key={api_key}"
        return f"{base}/v1beta/{quote(profile.model, safe='/:.-_')}:generateContent?key={api_key}"

    def _gemini_models_url(self, base_url: str, api_key: str) -> str:
        base = self._normalize_base(base_url)
        if base.endswith("/v1beta"):
            return f"{base}/models?key={api_key}"
        return f"{base}/v1beta/models?key={api_key}"

    @staticmethod
    def _openai_content_text(content) -> str:
        if isinstance(content, list):
            return "\n".join(item.get("text", "") for item in content if isinstance(item, dict) and item.get("text")).strip()
        return content.strip() if isinstance(content, str) else ""

    @staticmethod
    def _gemini_finish_reason_text(finish_reason: str | None) -> str:
        if not finish_reason:
            return ""
        return str(finish_reason).strip()

    def _extract_openai_translation_text(self, data: dict) -> str:
        if not isinstance(data, dict):
            raise RuntimeError("OpenAI returned an unexpected payload")
        choices = data.get("choices", [])
        if not choices or not isinstance(choices[0], dict):
            raise RuntimeError("OpenAI returned no choices")
        choice = choices[0]
        content = self._openai_content_text(choice.get("message", {}).get("content", ""))
        if content:
            return content
        finish_reason = str(choice.get("finish_reason") or "").strip()
        if finish_reason == "content_filter":
            raise RuntimeError("OpenAI blocked the response with content_filter")
        if finish_reason:
            raise RuntimeError(f"OpenAI finished without text (finish_reason={finish_reason})")
        raise RuntimeError("OpenAI returned an empty message")

    def _extract_gemini_translation_text(self, data: dict) -> str:
        if not isinstance(data, dict):
            raise RuntimeError("Gemini returned an unexpected payload")
        prompt_feedback = data.get("promptFeedback") if isinstance(data, dict) else None
        if isinstance(prompt_feedback, dict):
            block_reason = str(prompt_feedback.get("blockReason") or "").strip()
            if block_reason:
                raise RuntimeError(f"Gemini blocked the request: {block_reason}")
        candidates = data.get("candidates", [])
        if not candidates or not isinstance(candidates[0], dict):
            raise RuntimeError("Gemini returned no candidates")
        candidate = candidates[0]
        parts = candidate.get("content", {}).get("parts", [])
        text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text")).strip()
        if text:
            return text
        finish_reason = self._gemini_finish_reason_text(candidate.get("finishReason"))
        if finish_reason and finish_reason != "STOP":
            raise RuntimeError(f"Gemini finished without text (finishReason={finish_reason})")
        raise RuntimeError("Gemini returned an empty response")

    def _request_openai_models(self, profile: ApiProfile, api_key: str) -> list[str]:
        response = requests.get(self._openai_url(profile.base_url, "/models"), headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
        self._ensure_success(response)
        data = response.json()
        return [item.get("id", "") for item in data.get("data", []) if isinstance(item, dict) and item.get("id")]

    def _request_gemini_models(self, profile: ApiProfile, api_key: str) -> list[str]:
        response = requests.get(self._gemini_models_url(profile.base_url, api_key), timeout=30)
        self._ensure_success(response)
        data = response.json()
        return [item.get("name", "") for item in data.get("models", []) if isinstance(item, dict) and item.get("name")]

    def list_models(self, profile: ApiProfile) -> list[str]:
        keys = [key.strip() for key in profile.api_keys if key.strip()]
        if not keys:
            raise RuntimeError("No API key configured")
        last_error = None
        for key in keys:
            try:
                return self._request_openai_models(profile, key) if profile.provider == "openai" else self._request_gemini_models(profile, key)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.log(f"List models failed with one key: {exc}")
        raise RuntimeError(str(last_error) if last_error else "Failed to load models")

    def test_profile(self, profile: ApiProfile) -> str:
        models = self.list_models(profile)
        preview = ", ".join(models[:5]) if models else "(no models)"
        return f"OK | provider={profile.provider} | models={len(models)} | {preview}"

    def translate_image(self, image: Image.Image, profile: ApiProfile, target_language: str, temperature: float) -> str:
        keys = [key.strip() for key in profile.api_keys if key.strip()]
        if not keys:
            raise RuntimeError("No API key configured")
        if not profile.model.strip():
            raise RuntimeError("No model configured")

        prompt = f"{DEFAULT_PROMPT}\n\nTarget language: {target_language}"
        image_base64 = self._image_to_base64(image)
        attempts_total = max(1, profile.retry_count + 1) * len(keys)
        profile_key = f"{profile.provider}|{profile.base_url}|{profile.name}"
        start_index = self.profile_key_index.get(profile_key, 0) % len(keys)
        last_error = None

        for attempt in range(attempts_total):
            key_index = (start_index + attempt) % len(keys)
            api_key = keys[key_index]
            self.profile_key_index[profile_key] = (key_index + 1) % len(keys)
            try:
                self.log(f"Translate attempt {attempt + 1}/{attempts_total} | provider={profile.provider} | model={profile.model} | key#{key_index + 1}")
                if profile.provider == "openai":
                    result = self._translate_openai(profile, api_key, prompt, image_base64, temperature)
                else:
                    result = self._translate_gemini(profile, api_key, prompt, image_base64, temperature)
                if result:
                    return result.strip()
                raise RuntimeError("Empty response")
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.log(f"Translate failed on attempt {attempt + 1}: {exc}")
                if attempt < attempts_total - 1 and profile.retry_interval > 0:
                    time.sleep(profile.retry_interval)
        raise RuntimeError(str(last_error) if last_error else "Translation failed")

    def _translate_openai(self, profile: ApiProfile, api_key: str, prompt: str, image_base64: str, temperature: float) -> str:
        response = requests.post(
            self._openai_url(profile.base_url, "/chat/completions"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": profile.model,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                        ],
                    }
                ],
            },
            timeout=120,
        )
        self._ensure_success(response)
        data = response.json()
        return self._extract_openai_translation_text(data)

    def _translate_gemini(self, profile: ApiProfile, api_key: str, prompt: str, image_base64: str, temperature: float) -> str:
        response = requests.post(
            self._gemini_content_url(profile, api_key),
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/png", "data": image_base64}}]}],
                "generationConfig": {"temperature": temperature},
            },
            timeout=120,
        )
        self._ensure_success(response)
        data = response.json()
        return self._extract_gemini_translation_text(data)
