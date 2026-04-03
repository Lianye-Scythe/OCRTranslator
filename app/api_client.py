import base64
import io
import time
from urllib.parse import quote

import requests
from PIL import Image

from .constants import DEFAULT_PROMPT
from .models import ApiProfile


class ApiClientError(RuntimeError):
    def __init__(self, technical_message: str, *, user_message: str | None = None, retryable: bool = True):
        super().__init__(technical_message)
        self.user_message = user_message or technical_message
        self.retryable = retryable


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
    def _http_status_retryable(status_code: int) -> bool:
        return status_code in {401, 403, 408, 409, 425, 429} or 500 <= status_code < 600

    @staticmethod
    def _http_error_user_message(status_code: int, detail: str) -> str:
        detail_text = str(detail or "").strip()
        if status_code in {401, 403}:
            return f"API 認證失敗（HTTP {status_code}）。請檢查 API Key、Provider、Base URL 與模型設定是否正確。"
        if status_code == 404:
            return "找不到對應的 API 端點或模型資源。請檢查 Base URL、Provider 與模型名稱是否正確。"
        if status_code == 429:
            return "API 目前觸發速率限制或配額限制。請稍後再試，或切換其他 Key / 模型。"
        if 500 <= status_code < 600:
            return f"服務端暫時不可用（HTTP {status_code}）。請稍後重試。"
        if detail_text:
            return f"請求失敗（HTTP {status_code}）：{detail_text}"
        return f"請求失敗（HTTP {status_code}）。"

    @staticmethod
    def _response_preview(text: str, *, limit: int = 80) -> str:
        preview = " ".join(str(text or "").split())
        if not preview:
            return "(empty)"
        if len(preview) <= limit:
            return preview
        return preview[: max(1, limit - 1)].rstrip() + "…"

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
            status_code = int(getattr(response, "status_code", 0) or 0)
            detail = self._response_error_message(response)
            raise ApiClientError(
                f"HTTP {status_code}: {detail}",
                user_message=self._http_error_user_message(status_code, detail),
                retryable=self._http_status_retryable(status_code),
            ) from exc

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
            raise ApiClientError("OpenAI returned an unexpected payload")
        choices = data.get("choices", [])
        if not choices or not isinstance(choices[0], dict):
            raise ApiClientError("OpenAI returned no choices")
        choice = choices[0]
        content = self._openai_content_text(choice.get("message", {}).get("content", ""))
        if content:
            return content
        finish_reason = str(choice.get("finish_reason") or "").strip()
        if finish_reason == "content_filter":
            raise ApiClientError(
                "OpenAI blocked the response with content_filter",
                user_message="OpenAI 因內容安全策略拒絕了這次請求。請縮小範圍、調整內容，或改用其他模型 / Provider 再試一次。",
                retryable=False,
            )
        if finish_reason:
            raise ApiClientError(
                f"OpenAI finished without text (finish_reason={finish_reason})",
                user_message=f"OpenAI 沒有回傳可顯示的內容（finish_reason={finish_reason}）。",
            )
        raise ApiClientError("OpenAI returned an empty message", user_message="OpenAI 沒有回傳可顯示的內容。")

    def _extract_gemini_translation_text(self, data: dict) -> str:
        if not isinstance(data, dict):
            raise ApiClientError("Gemini returned an unexpected payload")
        prompt_feedback = data.get("promptFeedback") if isinstance(data, dict) else None
        if isinstance(prompt_feedback, dict):
            block_reason = str(prompt_feedback.get("blockReason") or "").strip()
            if block_reason:
                raise ApiClientError(
                    f"Gemini blocked the request: {block_reason}",
                    user_message=(
                        f"Gemini 因內容安全策略拒絕了這次請求（{block_reason}）。"
                        "請縮小範圍、避開敏感內容，或改用其他模型 / Provider 再試一次。"
                    ),
                    retryable=False,
                )
        candidates = data.get("candidates", [])
        if not candidates or not isinstance(candidates[0], dict):
            raise ApiClientError("Gemini returned no candidates", user_message="Gemini 沒有回傳可用候選結果。")
        candidate = candidates[0]
        parts = candidate.get("content", {}).get("parts", [])
        text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text")).strip()
        if text:
            return text
        finish_reason = self._gemini_finish_reason_text(candidate.get("finishReason"))
        if finish_reason == "PROHIBITED_CONTENT":
            raise ApiClientError(
                "Gemini finished without text (finishReason=PROHIBITED_CONTENT)",
                user_message="Gemini 因內容安全策略拒絕了這次請求。請縮小範圍、避開敏感內容，或改用其他模型 / Provider 再試一次。",
                retryable=False,
            )
        if finish_reason and finish_reason != "STOP":
            raise ApiClientError(
                f"Gemini finished without text (finishReason={finish_reason})",
                user_message=f"Gemini 沒有回傳可顯示的內容（finishReason={finish_reason}）。",
            )
        raise ApiClientError("Gemini returned an empty response", user_message="Gemini 沒有回傳可顯示的內容。")

    @staticmethod
    def _is_retryable_exception(exc: Exception) -> bool:
        return bool(getattr(exc, "retryable", True))

    @staticmethod
    def _profile_rotation_key(profile: ApiProfile) -> str:
        return f"{profile.provider}|{profile.base_url}|{profile.name}"

    def _rotation_start_index(self, profile: ApiProfile, keys: list[str]) -> tuple[str, int]:
        profile_key = self._profile_rotation_key(profile)
        return profile_key, self.profile_key_index.get(profile_key, 0) % len(keys)

    def _advance_rotation_index(self, profile_key: str, key_index: int, total_keys: int) -> None:
        self.profile_key_index[profile_key] = (key_index + 1) % total_keys

    @staticmethod
    def _active_keys(profile: ApiProfile) -> list[str]:
        return [key.strip() for key in profile.api_keys if key.strip()]

    def _request_openai_models(self, profile: ApiProfile, api_key: str) -> list[str]:
        response = requests.get(self._openai_url(profile.base_url, "/models"), headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
        self._ensure_success(response)
        data = response.json()
        return [item.get("id", "") for item in data.get("data", []) if isinstance(item, dict) and item.get("id")]

    def _request_gemini_models(self, profile: ApiProfile, api_key: str) -> list[str]:
        response = requests.get(self._gemini_models_url(profile.base_url, api_key), timeout=30)
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

    def list_models(self, profile: ApiProfile) -> list[str]:
        keys = self._active_keys(profile)
        if not keys:
            raise ApiClientError("No API key configured", user_message="目前設定檔沒有可用的 API Key。", retryable=False)
        last_error = None
        profile_key, start_index = self._rotation_start_index(profile, keys)
        for attempt in range(len(keys)):
            key_index = (start_index + attempt) % len(keys)
            key = keys[key_index]
            self._advance_rotation_index(profile_key, key_index, len(keys))
            try:
                self.log(f"List models attempt {attempt + 1}/{len(keys)} | provider={profile.provider} | key#{key_index + 1}")
                return self._request_openai_models(profile, key) if profile.provider == "openai" else self._request_gemini_models(profile, key)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.log(f"List models failed on attempt {attempt + 1}: {exc}")
                if not self._is_retryable_exception(exc):
                    self.log("List models retries stopped because the error is non-retryable")
                    break
        if last_error:
            if isinstance(last_error, ApiClientError):
                raise last_error
            raise ApiClientError(str(last_error), user_message=str(last_error)) from last_error
        raise ApiClientError("Failed to load models", user_message="無法載入模型列表。")

    def test_profile(self, profile: ApiProfile) -> str:
        response = self.request_text(
            "Reply with the single word OK.",
            profile,
            temperature=0.0,
        )
        preview = self._response_preview(response)
        return f"OK | provider={profile.provider} | model={profile.model} | response={preview}"

    def _request_with_rotation(self, profile: ApiProfile, *, request_label: str, request_callable) -> str:
        keys = self._active_keys(profile)
        if not keys:
            raise ApiClientError("No API key configured", user_message="目前設定檔沒有可用的 API Key。")
        if not profile.model.strip():
            raise ApiClientError("No model configured", user_message="目前設定檔沒有設定模型名稱。")

        retry_count = max(0, int(profile.retry_count))
        attempts_total = 1 + retry_count
        profile_key, start_index = self._rotation_start_index(profile, keys)
        last_error = None

        for attempt in range(attempts_total):
            key_index = (start_index + attempt) % len(keys)
            api_key = keys[key_index]
            self._advance_rotation_index(profile_key, key_index, len(keys))
            try:
                self.log(
                    f"{request_label} attempt {attempt + 1}/{attempts_total} | "
                    f"provider={profile.provider} | model={profile.model} | key#{key_index + 1}"
                )
                result = request_callable(api_key)
                if result:
                    return result.strip()
                raise ApiClientError("Empty response", user_message="模型沒有回傳可顯示的內容。")
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.log(f"{request_label} failed on attempt {attempt + 1}: {exc}")
                if not self._is_retryable_exception(exc):
                    self.log(f"{request_label} retries stopped because the error is non-retryable")
                    break
                if attempt < attempts_total - 1 and profile.retry_interval > 0:
                    time.sleep(profile.retry_interval)
        if last_error:
            if isinstance(last_error, ApiClientError):
                raise last_error
            raise ApiClientError(str(last_error), user_message=str(last_error)) from last_error
        raise ApiClientError("Request failed", user_message="請求失敗。")

    def request_image(self, image: Image.Image, profile: ApiProfile, prompt: str, temperature: float) -> str:
        prompt_text = str(prompt or "").strip()
        if not prompt_text:
            raise ApiClientError("No prompt configured", user_message="目前提示詞不可為空。")
        image_base64 = self._image_to_base64(image)
        return self._request_with_rotation(
            profile,
            request_label="Image request",
            request_callable=lambda api_key: (
                self._translate_openai(profile, api_key, prompt_text, image_base64, temperature)
                if profile.provider == "openai"
                else self._translate_gemini(profile, api_key, prompt_text, image_base64, temperature)
            ),
        )

    def request_text(self, prompt: str, profile: ApiProfile, temperature: float) -> str:
        prompt_text = str(prompt or "").strip()
        if not prompt_text:
            raise ApiClientError("No prompt configured", user_message="目前提示詞不可為空。")
        return self._request_with_rotation(
            profile,
            request_label="Text request",
            request_callable=lambda api_key: (
                self._request_openai_prompt(profile, api_key, prompt_text, temperature)
                if profile.provider == "openai"
                else self._request_gemini_prompt(profile, api_key, prompt_text, temperature)
            ),
        )

    def translate_image(self, image: Image.Image, profile: ApiProfile, target_language: str, temperature: float) -> str:
        prompt = f"{DEFAULT_PROMPT}\n\nTarget language: {target_language}"
        return self.request_image(image, profile, prompt, temperature)

    def _request_openai_prompt(
        self,
        profile: ApiProfile,
        api_key: str,
        prompt: str,
        temperature: float,
        *,
        image_base64: str | None = None,
    ) -> str:
        content = (
            [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
            ]
            if image_base64
            else prompt
        )
        response = requests.post(
            self._openai_url(profile.base_url, "/chat/completions"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": profile.model,
                "temperature": temperature,
                "messages": [{"role": "user", "content": content}],
            },
            timeout=120,
        )
        self._ensure_success(response)
        data = response.json()
        return self._extract_openai_translation_text(data)

    def _translate_openai(self, profile: ApiProfile, api_key: str, prompt: str, image_base64: str, temperature: float) -> str:
        return self._request_openai_prompt(
            profile,
            api_key,
            prompt,
            temperature,
            image_base64=image_base64,
        )

    def _request_gemini_prompt(
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
            self._gemini_content_url(profile, api_key),
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": parts}],
                "generationConfig": {"temperature": temperature},
            },
            timeout=120,
        )
        self._ensure_success(response)
        data = response.json()
        return self._extract_gemini_translation_text(data)

    def _translate_gemini(self, profile: ApiProfile, api_key: str, prompt: str, image_base64: str, temperature: float) -> str:
        return self._request_gemini_prompt(
            profile,
            api_key,
            prompt,
            temperature,
            image_base64=image_base64,
        )
