import threading
import unittest
from unittest.mock import Mock, patch

import requests

from app.api_client import ApiClient, ApiClientError
from app.models import ApiProfile
from app.operation_control import RequestCancelledError, RequestContext


class ApiClientTests(unittest.TestCase):
    def setUp(self):
        self.client = ApiClient(lambda message: None)
        self.profile = ApiProfile(
            name="Test",
            provider="openai",
            base_url="https://api.openai.com",
            api_keys=["demo-key"],
            model="gpt-4o-mini",
        )

    def test_ensure_success_uses_json_error_message(self):
        response = Mock()
        response.status_code = 401
        response.reason = "Unauthorized"
        response.raise_for_status.side_effect = requests.HTTPError("boom")
        response.json.return_value = {"error": {"message": "invalid api key"}}

        with self.assertRaises(ApiClientError) as context:
            self.client._ensure_success(response)

        self.assertEqual(str(context.exception), "HTTP 401: invalid api key")
        self.assertTrue(context.exception.retryable)
        self.assertFalse(context.exception.retry_same_key)

    def test_ensure_success_marks_bad_request_as_non_retryable(self):
        response = Mock()
        response.status_code = 400
        response.reason = "Bad Request"
        response.raise_for_status.side_effect = requests.HTTPError("boom")
        response.json.return_value = {"error": {"message": "invalid model"}}

        with self.assertRaises(ApiClientError) as context:
            self.client._ensure_success(response)

        self.assertEqual(str(context.exception), "HTTP 400: invalid model")
        self.assertFalse(context.exception.retryable)

    def test_test_profile_uses_real_text_request_chain(self):
        with patch.object(self.client, "request_text", return_value="OK") as mock_request_text:
            result = self.client.test_profile(self.profile)

        mock_request_text.assert_called_once_with("Reply with the single word OK.", self.profile, temperature=0.0, stream=False, request_label="Test request", request_context=None)
        self.assertEqual(result, "OK | provider=openai | model=gpt-4o-mini | response=OK")

    def test_test_profile_can_use_streaming_request_chain(self):
        with patch.object(self.client, "request_text", return_value="OK") as mock_request_text:
            result = self.client.test_profile(self.profile, stream=True)

        mock_request_text.assert_called_once_with("Reply with the single word OK.", self.profile, temperature=0.0, stream=True, request_label="Test request", request_context=None)
        self.assertEqual(result, "OK | provider=openai | model=gpt-4o-mini | response=OK")

    def test_request_text_stream_falls_back_to_non_stream_for_third_party_compatible_backend(self):
        profile = ApiProfile(
            name="Compat OpenAI",
            provider="openai",
            base_url="https://compat.example.com/openai",
            api_keys=["demo-key"],
            model="gpt-4o-mini",
        )
        logs = []
        status_events = []
        client = ApiClient(logs.append)
        client.status_notifier = lambda event_name, payload: status_events.append((event_name, payload))
        stream_modes = []

        def fake_request(profile_obj, api_key, prompt, temperature, **kwargs):
            stream_modes.append(bool(kwargs.get("stream")))
            if kwargs.get("stream"):
                raise ApiClientError("HTTP 404: stream unsupported", user_message="stream unsupported", retryable=False, retry_same_key=False, status_code=404, stream_fallback_allowed=True)
            return "OK"

        with patch.object(client, "_request_openai_prompt", side_effect=fake_request):
            result = client.request_text("plain prompt", profile, 0.2, stream=True)

        self.assertEqual(result, "OK")
        self.assertEqual(stream_modes, [True, False])
        self.assertTrue(any("retrying without stream" in message for message in logs))
        self.assertTrue(any("fallback succeeded without stream" in message for message in logs))
        self.assertEqual(
            [event_name for event_name, _payload in status_events],
            ["retrying", "succeeded"],
        )
        self.assertEqual(status_events[0][1]["provider"], "openai")
        self.assertEqual(status_events[0][1]["request_kind"], "text")
        self.assertEqual(status_events[0][1]["base_url"], "https://compat.example.com/openai")

    def test_request_text_stream_fallback_checks_cancellation_before_retrying_non_stream(self):
        profile = ApiProfile(
            name="Compat OpenAI",
            provider="openai",
            base_url="https://compat.example.com/openai",
            api_keys=["demo-key"],
            model="gpt-4o-mini",
        )
        stream_modes = []
        request_context = RequestContext()
        status_events = []
        self.client.status_notifier = lambda event_name, payload: status_events.append((event_name, payload))

        def fake_request(profile_obj, api_key, prompt, temperature, **kwargs):
            stream_modes.append(bool(kwargs.get("stream")))
            if kwargs.get("stream"):
                request_context.cancel()
                raise ApiClientError("HTTP 404: stream unsupported", user_message="stream unsupported", retryable=False, retry_same_key=False, status_code=404, stream_fallback_allowed=True)
            return "OK"

        with patch.object(self.client, "_request_openai_prompt", side_effect=fake_request):
            with self.assertRaises(RequestCancelledError):
                self.client.request_text("plain prompt", profile, 0.2, stream=True, request_context=request_context)

        self.assertEqual(stream_modes, [True])
        self.assertEqual(status_events, [])

    def test_request_text_stream_error_adds_disable_stream_hint_for_third_party_compatible_backend(self):
        profile = ApiProfile(
            name="Compat OpenAI",
            provider="openai",
            base_url="https://compat.example.com/openai",
            api_keys=["demo-key"],
            model="gpt-4o-mini",
        )

        with patch.object(self.client, "_request_openai_prompt", side_effect=ApiClientError("stream broke", user_message="请求失败", retryable=False, retry_same_key=False)):
            with self.assertRaises(ApiClientError) as context:
                self.client.request_text("plain prompt", profile, 0.2, stream=True)

        self.assertIn("关闭「流式响应」", context.exception.user_message)

    @patch("app.api_client.requests.post")
    def test_request_text_openai_stream_forces_utf8_for_cjk_chunks(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.iter_lines.return_value = [
            'data: {"choices":[{"delta":{"content":"繁體"},"finish_reason":null}]}'.encode("utf-8"),
            b"",
            'data: {"choices":[{"delta":{"content":"中文"},"finish_reason":"stop"}]}'.encode("utf-8"),
            b"",
            b"data: [DONE]",
            b"",
        ]
        mock_post.return_value = response
        streamed = []

        result = self.client.request_text("plain prompt", self.profile, 0.2, stream=True, stream_callback=streamed.append)

        self.assertEqual(result, "繁體中文")
        self.assertEqual(streamed, ["繁體", "繁體中文"])

    @patch("app.providers.gemini_compatible.requests.request")
    def test_request_text_gemini_stream_forces_utf8_for_cjk_chunks(self, mock_request):
        profile = ApiProfile(name="Gemini", provider="gemini", base_url="https://generativelanguage.googleapis.com", api_keys=["demo-key"], model="models/gemini-1.5-flash")
        response = Mock()
        response.raise_for_status.return_value = None
        response.iter_lines.return_value = [
            'data: {"candidates":[{"content":{"parts":[{"text":"简体"}]}}]}'.encode("utf-8"),
            b"",
            'data: {"candidates":[{"content":{"parts":[{"text":"中文"}]},"finishReason":"STOP"}]}'.encode("utf-8"),
            b"",
        ]
        mock_request.return_value = response
        streamed = []

        result = self.client.request_text("plain prompt", profile, 0.2, stream=True, stream_callback=streamed.append)

        self.assertEqual(result, "简体中文")
        self.assertEqual(streamed, ["简体", "简体中文"])

    @patch("app.api_client.requests.post")
    def test_request_text_openai_streams_chunks_when_enabled(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.iter_lines.return_value = [
            'data: {"choices":[{"delta":{"content":"Hel"},"finish_reason":null}]}',
            "",
            'data: {"choices":[{"delta":{"content":"lo"},"finish_reason":null}]}',
            "",
            'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}',
            "",
            "data: [DONE]",
            "",
        ]
        mock_post.return_value = response
        streamed = []

        result = self.client.request_text("plain prompt", self.profile, 0.2, stream=True, stream_callback=streamed.append)

        self.assertEqual(result, "Hello")
        self.assertEqual(streamed, ["Hel", "Hello"])
        self.assertTrue(mock_post.call_args.kwargs["json"]["stream"])
        self.assertTrue(mock_post.call_args.kwargs["stream"])

    @patch("app.providers.gemini_compatible.requests.request")
    def test_request_text_gemini_streams_chunks_when_enabled(self, mock_request):
        profile = ApiProfile(name="Gemini", provider="gemini", base_url="https://generativelanguage.googleapis.com", api_keys=["demo-key"], model="models/gemini-1.5-flash")
        response = Mock()
        response.raise_for_status.return_value = None
        response.iter_lines.return_value = [
            'data: {"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}',
            "",
            'data: {"candidates":[{"content":{"parts":[{"text":" world"}]},"finishReason":"STOP"}]}',
            "",
        ]
        mock_request.return_value = response
        streamed = []

        result = self.client.request_text("plain prompt", profile, 0.2, stream=True, stream_callback=streamed.append)

        self.assertEqual(result, "Hello world")
        self.assertEqual(streamed, ["Hello", "Hello world"])

    @patch("app.providers.gemini_compatible.requests.request")
    def test_request_text_gemini_sends_user_role_in_contents_for_compatible_backends(self, mock_request):
        profile = ApiProfile(
            name="Gemini",
            provider="gemini",
            base_url="https://compat.example.com",
            api_keys=["demo-key"],
            model="models/gemini-1.5-flash",
        )
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "OK"}]}, "finishReason": "STOP"}
            ]
        }
        mock_request.return_value = response

        result = self.client.request_text("plain prompt", profile, 0.2)

        self.assertEqual(result, "OK")
        self.assertEqual(mock_request.call_args.kwargs["json"]["contents"][0]["role"], "user")

    @patch("app.api_client.requests.post")
    def test_translate_openai_joins_list_content(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"text": "第一行"},
                            {"text": "第二行"},
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = response

        result = self.client._translate_openai(self.profile, "demo-key", "prompt", "base64", 0.2)

        self.assertEqual(result, "第一行\n第二行")

    @patch("app.api_client.requests.post")
    def test_request_text_openai_uses_plain_text_message_content(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [
                {
                    "message": {"content": "OK"},
                }
            ]
        }
        mock_post.return_value = response

        self.client.request_text("plain prompt", self.profile, 0.2)

        self.assertEqual(mock_post.call_args.kwargs["json"]["messages"][0]["content"], "plain prompt")

    def test_translate_image_rotates_keys_between_successful_requests(self):
        profile = ApiProfile(
            name="Rotation",
            provider="openai",
            base_url="https://api.openai.com",
            api_keys=["key-1", "key-2", "key-3"],
            model="gpt-4o-mini",
            retry_count=0,
            retry_interval=0,
        )
        used_keys = []

        def fake_translate(profile_obj, api_key, prompt, image_base64, temperature, **kwargs):
            used_keys.append(api_key)
            return "ok"

        with patch.object(self.client, "_image_to_binary", return_value=b"png-data"), patch.object(self.client, "_translate_openai", side_effect=fake_translate):
            for _ in range(4):
                self.client.request_image(Mock(), profile, "Translate into 繁體中文", 0.2)

        self.assertEqual(used_keys, ["key-1", "key-2", "key-3", "key-1"])

    def test_list_models_rotates_keys_between_requests(self):
        profile = ApiProfile(
            name="Models Rotation",
            provider="openai",
            base_url="https://api.openai.com",
            api_keys=["key-1", "key-2", "key-3"],
            model="gpt-4o-mini",
        )
        used_keys = []

        with patch.object(self.client, "_request_openai_models", side_effect=lambda profile_obj, api_key, **kwargs: used_keys.append(api_key) or ["gpt-4o-mini"]):
            for _ in range(4):
                self.client.list_models(profile)

        self.assertEqual(used_keys, ["key-1", "key-2", "key-3", "key-1"])

    @patch("app.providers.gemini_compatible.requests.request")
    def test_request_gemini_models_filters_non_generate_content_models(self, mock_request):
        profile = ApiProfile(
            name="Gemini",
            provider="gemini",
            base_url="https://generativelanguage.googleapis.com",
            api_keys=["demo-key"],
            model="models/gemini-1.5-flash",
        )
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "models": [
                {"name": "models/gemini-1.5-flash", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/embedding-001", "supportedGenerationMethods": ["embedContent"]},
                {"name": "models/gemini-2.0-flash"},
            ]
        }
        mock_request.return_value = response

        self.assertEqual(self.client.list_models(profile), ["models/gemini-1.5-flash", "models/gemini-2.0-flash"])

    @patch("app.providers.gemini_compatible.requests.request")
    def test_translate_gemini_raises_block_reason_when_prompt_is_blocked(self, mock_request):
        profile = ApiProfile(
            name="Gemini",
            provider="gemini",
            base_url="https://generativelanguage.googleapis.com",
            api_keys=["demo-key"],
            model="models/gemini-1.5-flash",
        )
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"promptFeedback": {"blockReason": "SAFETY"}, "candidates": []}
        mock_request.return_value = response

        with self.assertRaisesRegex(RuntimeError, "Gemini blocked the request: SAFETY"):
            self.client._translate_gemini(profile, "demo-key", "prompt", "base64", 0.2)

    @patch("app.api_client.requests.post")
    def test_translate_openai_raises_content_filter_reason(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [
                {
                    "finish_reason": "content_filter",
                    "message": {"content": ""},
                }
            ]
        }
        mock_post.return_value = response

        with self.assertRaisesRegex(RuntimeError, "OpenAI blocked the response with content_filter"):
            self.client._translate_openai(self.profile, "demo-key", "prompt", "base64", 0.2)

    @patch("app.api_client.time.sleep")
    def test_translate_image_retry_count_one_only_retries_once_with_next_key(self, mock_sleep):
        profile = ApiProfile(
            name="Retry Test",
            provider="openai",
            base_url="https://api.openai.com",
            api_keys=["key-1", "key-2", "key-3"],
            model="gpt-4o-mini",
            retry_count=1,
            retry_interval=0,
        )

        with patch.object(self.client, "_translate_openai", side_effect=RuntimeError("boom")) as mock_translate:
            with self.assertRaisesRegex(RuntimeError, "boom"):
                self.client.request_image(Mock(), profile, "Translate into 繁體中文", 0.2)

        self.assertEqual(mock_translate.call_count, 2)
        mock_sleep.assert_not_called()

    def test_request_image_emits_user_facing_retry_event_when_another_attempt_will_run(self):
        profile = ApiProfile(
            name="Retry Notify",
            provider="openai",
            base_url="https://api.openai.com",
            api_keys=["key-1", "key-2"],
            model="gpt-4o-mini",
            retry_count=1,
            retry_interval=0,
        )
        events = []
        self.client.event_notifier = lambda event_name, payload: events.append((event_name, payload))

        with patch.object(self.client, "_translate_openai", side_effect=[RuntimeError("boom"), "OK"]):
            result = self.client.request_image(Mock(), profile, "Translate into 繁體中文", 0.2)

        self.assertEqual(result, "OK")
        self.assertEqual(
            events,
            [
                ("retrying", {"request_kind": "image", "attempt": 2, "total": 2}),
            ],
        )

    def test_translate_image_stops_retrying_when_error_is_non_retryable(self):
        profile = ApiProfile(
            name="Retry Stop",
            provider="gemini",
            base_url="https://generativelanguage.googleapis.com",
            api_keys=["key-1", "key-2", "key-3"],
            model="models/gemini-1.5-flash",
            retry_count=3,
            retry_interval=0,
        )

        with patch.object(self.client, "_image_to_binary", return_value=b"png-data"), patch.object(self.client, "_translate_gemini", side_effect=ApiClientError("Gemini finished without text (finishReason=PROHIBITED_CONTENT)", user_message="blocked", retryable=False)) as mock_translate:
            with self.assertRaisesRegex(ApiClientError, "PROHIBITED_CONTENT"):
                self.client.request_image(Mock(), profile, "Translate into 繁體中文", 0.2)

        self.assertEqual(mock_translate.call_count, 1)

    def test_list_models_stops_retrying_when_error_is_non_retryable(self):
        profile = ApiProfile(
            name="No Retry Models",
            provider="openai",
            base_url="https://api.openai.com",
            api_keys=["key-1", "key-2", "key-3"],
            model="gpt-4o-mini",
        )

        with patch.object(
            self.client,
            "_request_openai_models",
            side_effect=ApiClientError("HTTP 400: invalid model", user_message="invalid model", retryable=False),
        ) as mock_request_models:
            with self.assertRaisesRegex(ApiClientError, "HTTP 400: invalid model"):
                self.client.list_models(profile)

        self.assertEqual(mock_request_models.call_count, 1)

    @patch("app.api_client.time.sleep")
    def test_request_text_auth_failure_with_single_key_does_not_retry_same_key(self, mock_sleep):
        profile = ApiProfile(
            name="Single Key",
            provider="openai",
            base_url="https://api.openai.com",
            api_keys=["only-key"],
            model="gpt-4o-mini",
            retry_count=3,
            retry_interval=0,
        )

        with patch.object(
            self.client,
            "_request_openai_prompt",
            side_effect=ApiClientError("HTTP 401: invalid api key", user_message="bad key", retryable=True, retry_same_key=False),
        ) as mock_request:
            with self.assertRaisesRegex(ApiClientError, "HTTP 401: invalid api key"):
                self.client.request_text("prompt", profile, 0.2)

        self.assertEqual(mock_request.call_count, 1)
        mock_sleep.assert_not_called()

    def test_list_models_respects_retry_count_for_same_key_retryable_errors(self):
        profile = ApiProfile(name="Retry Models", provider="openai", base_url="https://api.openai.com", api_keys=["key-1"], model="gpt-4o-mini", retry_count=2, retry_interval=0)

        with patch.object(self.client, "_request_openai_models", side_effect=RuntimeError("temporary boom")) as mock_request_models:
            with self.assertRaisesRegex(ApiClientError, "temporary boom"):
                self.client.list_models(profile)

        self.assertEqual(mock_request_models.call_count, 3)

    def test_request_text_raises_cancelled_when_request_context_is_cancelled_before_start(self):
        request_context = RequestContext()
        request_context.cancel()

        with self.assertRaises(RequestCancelledError):
            self.client.request_text("prompt", self.profile, 0.2, request_context=request_context)

    def test_list_models_stops_retrying_when_request_is_cancelled(self):
        request_context = RequestContext()

        def cancel_on_request(*args, **kwargs):
            request_context.cancel()
            raise RequestCancelledError()

        with patch.object(self.client, "_request_openai_models", side_effect=cancel_on_request) as mock_request_models:
            with self.assertRaises(RequestCancelledError):
                self.client.list_models(self.profile, request_context=request_context)

        self.assertEqual(mock_request_models.call_count, 1)

    def test_sleep_with_cancellation_stops_mid_backoff_when_request_is_cancelled(self):
        request_context = RequestContext()
        timer = threading.Timer(0.02, request_context.cancel)
        timer.start()

        try:
            with self.assertRaises(RequestCancelledError):
                self.client._sleep_with_cancellation(0.3, request_context=request_context, poll_interval=0.01)
        finally:
            timer.cancel()

    def test_request_image_png_uses_raw_png_bytes_without_extra_processing(self):
        png_bytes = b"\x89PNG\r\n\x1a\nraw-data"

        with patch.object(self.client, "_translate_openai", return_value="ok") as mock_translate:
            result = self.client.request_image_png(png_bytes, self.profile, "Translate into 繁體中文", 0.2)

        self.assertEqual(result, "ok")
        mock_translate.assert_called_once()
        self.assertEqual(mock_translate.call_args.args[0:3], (self.profile, "demo-key", "Translate into 繁體中文"))
        self.assertEqual(mock_translate.call_args.args[4], 0.2)
        self.assertEqual(mock_translate.call_args.args[3], "iVBORw0KGgpyYXctZGF0YQ==")


if __name__ == "__main__":
    unittest.main()
