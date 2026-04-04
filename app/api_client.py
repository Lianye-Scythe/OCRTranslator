import base64
import io
import time

import requests
from PIL import Image

from .models import ApiProfile
from .operation_control import RequestCancelledError, RequestContext
from .providers import GeminiCompatibleAdapter, OpenAICompatibleAdapter


class ApiClientError(RuntimeError):
    def __init__(
        self,
        technical_message: str,
        *,
        user_message: str | None = None,
        retryable: bool = True,
        retry_same_key: bool = True,
    ):
        super().__init__(technical_message)
        self.user_message = user_message or technical_message
        self.retryable = retryable
        self.retry_same_key = retry_same_key


class ApiClient:
    def __init__(self, log_func):
        self.log = log_func
        self.profile_key_index: dict[str, int] = {}
        self._providers = {
            "openai": OpenAICompatibleAdapter(self._ensure_success, ApiClientError),
            "gemini": GeminiCompatibleAdapter(self._ensure_success, ApiClientError),
        }


    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def _http_retry_policy(status_code: int) -> tuple[bool, bool]:
        retryable = status_code in {401, 403, 408, 409, 425, 429} or 500 <= status_code < 600
        retry_same_key = status_code not in {401, 403}
        return retryable, retry_same_key

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
            retryable, retry_same_key = self._http_retry_policy(status_code)
            raise ApiClientError(
                f"HTTP {status_code}: {detail}",
                user_message=self._http_error_user_message(status_code, detail),
                retryable=retryable,
                retry_same_key=retry_same_key,
            ) from exc

    def _provider_adapter(self, provider: str):
        return self._providers.get(provider, self._providers["gemini"])

    @staticmethod
    def _is_retryable_exception(exc: Exception) -> bool:
        if isinstance(exc, requests.RequestException):
            return True
        return bool(getattr(exc, "retryable", True))

    @staticmethod
    def _should_retry_same_key(exc: Exception) -> bool:
        return bool(getattr(exc, "retry_same_key", True))

    @staticmethod
    def _check_cancelled(request_context: RequestContext | None) -> None:
        if request_context and request_context.is_cancelled():
            raise RequestCancelledError()

    @staticmethod
    def _profile_rotation_key(profile: ApiProfile) -> str:
        return f"{profile.provider}|{profile.base_url}|{profile.name}"

    def _sleep_with_cancellation(
        self,
        seconds: float,
        *,
        request_context: RequestContext | None = None,
        poll_interval: float = 0.1,
    ) -> None:
        deadline = time.monotonic() + max(0.0, float(seconds or 0.0))
        while time.monotonic() < deadline:
            self._check_cancelled(request_context)
            remaining = deadline - time.monotonic()
            time.sleep(min(max(0.01, poll_interval), max(0.0, remaining)))

    def _rotation_start_index(self, profile: ApiProfile, keys: list[str]) -> tuple[str, int]:
        profile_key = self._profile_rotation_key(profile)
        return profile_key, self.profile_key_index.get(profile_key, 0) % len(keys)

    def _advance_rotation_index(self, profile_key: str, key_index: int, total_keys: int) -> None:
        self.profile_key_index[profile_key] = (key_index + 1) % total_keys

    @staticmethod
    def _active_keys(profile: ApiProfile) -> list[str]:
        return [key.strip() for key in profile.api_keys if key.strip()]

    def _raise_last_error(self, error: Exception | None, *, default_message: str, user_message: str):
        if error:
            if isinstance(error, ApiClientError):
                raise error
            raise ApiClientError(str(error), user_message=str(error)) from error
        raise ApiClientError(default_message, user_message=user_message)

    def _execute_keyed_operation(
        self,
        profile: ApiProfile,
        *,
        request_label: str,
        request_callable,
        attempts_total: int,
        require_non_empty: bool,
        require_model: bool,
        empty_user_message: str,
        failure_message: str,
        failure_user_message: str,
        request_context: RequestContext | None = None,
    ):
        keys = self._active_keys(profile)
        if not keys:
            raise ApiClientError("No API key configured", user_message="目前設定檔沒有可用的 API Key。", retryable=False, retry_same_key=False)
        if require_model and not profile.model.strip():
            raise ApiClientError("No model configured", user_message="目前設定檔沒有設定模型名稱。", retryable=False, retry_same_key=False)

        profile_key, start_index = self._rotation_start_index(profile, keys)
        last_error = None
        last_key_index = None
        attempts_total = max(1, int(attempts_total or 1))

        for attempt in range(attempts_total):
            self._check_cancelled(request_context)
            key_index = (start_index + attempt) % len(keys)
            if last_error is not None and last_key_index == key_index and not self._should_retry_same_key(last_error):
                self.log(f"{request_label} retries stopped because same-key retry is not allowed")
                break

            api_key = keys[key_index]
            self._advance_rotation_index(profile_key, key_index, len(keys))
            try:
                self.log(
                    f"{request_label} attempt {attempt + 1}/{attempts_total} | "
                    f"provider={profile.provider} | model={profile.model} | key#{key_index + 1}"
                )
                result = request_callable(api_key)
                self._check_cancelled(request_context)
                if require_non_empty and isinstance(result, str):
                    self._check_cancelled(request_context)
                    cleaned = result.strip()
                    if not cleaned:
                        raise ApiClientError("Empty response", user_message=empty_user_message)
                    return cleaned
                return result
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if isinstance(exc, RequestCancelledError):
                    raise
                last_key_index = key_index
                self.log(f"{request_label} failed on attempt {attempt + 1}: {exc}")
                if not self._is_retryable_exception(exc):
                    self.log(f"{request_label} retries stopped because the error is non-retryable")
                    break
                if attempt >= attempts_total - 1:
                    break
                next_key_index = (start_index + attempt + 1) % len(keys)
                if next_key_index == key_index and not self._should_retry_same_key(exc):
                    self.log(f"{request_label} retries stopped because same-key retry is not allowed")
                    break
                if profile.retry_interval > 0:
                    self._sleep_with_cancellation(profile.retry_interval, request_context=request_context)
        self._check_cancelled(request_context)

        self._raise_last_error(last_error, default_message=failure_message, user_message=failure_user_message)

    def _request_openai_models(self, profile: ApiProfile, api_key: str, *, request_context: RequestContext | None = None) -> list[str]:
        return self._provider_adapter("openai").list_models(profile, api_key, request_context=request_context)

    def _request_gemini_models(self, profile: ApiProfile, api_key: str, *, request_context: RequestContext | None = None) -> list[str]:
        return self._provider_adapter("gemini").list_models(profile, api_key, request_context=request_context)

    def list_models(self, profile: ApiProfile, *, request_context: RequestContext | None = None) -> list[str]:
        keys = self._active_keys(profile)
        attempts_total = max(len(keys), 1 + max(0, int(profile.retry_count))) if keys else 1
        return self._execute_keyed_operation(
            profile,
            request_label="List models",
            request_callable=lambda api_key: (
                self._request_openai_models(profile, api_key, request_context=request_context)
                if profile.provider == "openai"
                else self._request_gemini_models(profile, api_key, request_context=request_context)
            ),
            attempts_total=attempts_total,
            require_non_empty=False,
            require_model=False,
            empty_user_message="模型列表是空的。",
            failure_message="Failed to load models",
            failure_user_message="無法載入模型列表。",
            request_context=request_context,
        )

    def test_profile(self, profile: ApiProfile, *, request_context: RequestContext | None = None) -> str:
        response = self.request_text(
            "Reply with the single word OK.",
            profile,
            temperature=0.0,
            request_context=request_context,
        )
        preview = self._response_preview(response)
        return f"OK | provider={profile.provider} | model={profile.model} | response={preview}"

    def request_image(self, image: Image.Image, profile: ApiProfile, prompt: str, temperature: float, *, request_context: RequestContext | None = None) -> str:
        prompt_text = str(prompt or "").strip()
        if not prompt_text:
            raise ApiClientError("No prompt configured", user_message="目前提示詞不可為空。", retryable=False, retry_same_key=False)
        image_base64 = self._image_to_base64(image)
        return self._execute_keyed_operation(
            profile,
            request_label="Image request",
            request_callable=lambda api_key: (
                self._translate_openai(profile, api_key, prompt_text, image_base64, temperature, request_context=request_context)
                if profile.provider == "openai"
                else self._translate_gemini(profile, api_key, prompt_text, image_base64, temperature, request_context=request_context)
            ),
            attempts_total=1 + max(0, int(profile.retry_count)),
            require_non_empty=True,
            require_model=True,
            empty_user_message="模型沒有回傳可顯示的內容。",
            failure_message="Request failed",
            failure_user_message="請求失敗。",
            request_context=request_context,
        )

    def request_text(self, prompt: str, profile: ApiProfile, temperature: float, *, request_context: RequestContext | None = None) -> str:
        prompt_text = str(prompt or "").strip()
        if not prompt_text:
            raise ApiClientError("No prompt configured", user_message="目前提示詞不可為空。", retryable=False, retry_same_key=False)
        return self._execute_keyed_operation(
            profile,
            request_label="Text request",
            request_callable=lambda api_key: (
                self._request_openai_prompt(profile, api_key, prompt_text, temperature, request_context=request_context)
                if profile.provider == "openai"
                else self._request_gemini_prompt(profile, api_key, prompt_text, temperature, request_context=request_context)
            ),
            attempts_total=1 + max(0, int(profile.retry_count)),
            require_non_empty=True,
            require_model=True,
            empty_user_message="模型沒有回傳可顯示的內容。",
            failure_message="Request failed",
            failure_user_message="請求失敗。",
            request_context=request_context,
        )

    def _request_openai_prompt(
        self,
        profile: ApiProfile,
        api_key: str,
        prompt: str,
        temperature: float,
        *,
        image_base64: str | None = None,
        request_context: RequestContext | None = None,
    ) -> str:
        return self._provider_adapter("openai").request_prompt(
            profile,
            api_key,
            prompt,
            temperature,
            image_base64=image_base64,
            request_context=request_context,
        )

    def _translate_openai(self, profile: ApiProfile, api_key: str, prompt: str, image_base64: str, temperature: float, *, request_context: RequestContext | None = None) -> str:
        return self._request_openai_prompt(
            profile,
            api_key,
            prompt,
            temperature,
            request_context=request_context,
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
        request_context: RequestContext | None = None,
    ) -> str:
        return self._provider_adapter("gemini").request_prompt(
            profile,
            api_key,
            prompt,
            temperature,
            image_base64=image_base64,
            request_context=request_context,
        )

    def _translate_gemini(self, profile: ApiProfile, api_key: str, prompt: str, image_base64: str, temperature: float, *, request_context: RequestContext | None = None) -> str:
        return self._request_gemini_prompt(
            profile,
            api_key,
            prompt,
            temperature,
            request_context=request_context,
            image_base64=image_base64,
        )
