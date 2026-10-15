import json
import unittest
from unittest.mock import Mock, patch

import requests

from app.api_client import ApiClient, ApiClientError
from app.models import ApiProfile


class ReasoningRequestTests(unittest.TestCase):
    def setUp(self):
        self.client = ApiClient(lambda message: None)

    def test_openai_default_omits_optional_generation_parameters(self):
        profile = ApiProfile(provider="openai", model="test-model", api_keys=["test-key"])
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": "translated"}}]}
        with patch("app.providers.openai_compatible.requests.post", return_value=response) as post:
            self.assertEqual(self.client.request_text("hello", profile, 0.2), "translated")
        payload = post.call_args.kwargs["json"]
        self.assertNotIn("reasoning_effort", payload)
        self.assertNotIn("temperature", payload)

    def test_google_openai_compatible_endpoint_keeps_its_api_prefix(self):
        profile = ApiProfile(provider="openai", base_url="https://generativelanguage.googleapis.com/v1beta/openai/", model="gemini-flash-lite-latest", api_keys=["test-key"], reasoning_effort="low")
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": "translated"}}]}
        with patch("app.providers.openai_compatible.requests.post", return_value=response) as post:
            self.client.request_text("hello", profile, 0.2)
        self.assertEqual(post.call_args.args[0], "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")
        self.assertEqual(post.call_args.kwargs["json"]["reasoning_effort"], "low")

    def test_openai_effort_applies_to_text_image_and_stream_requests(self):
        profile = ApiProfile(provider="openai", model="test-model", api_keys=["test-key"], reasoning_effort="high", use_default_temperature=False)
        for stream in (False, True):
            for image in (False, True):
                with self.subTest(stream=stream, image=image):
                    response = Mock()
                    response.json.return_value = {"choices": [{"message": {"content": "translated"}}]}
                    response.iter_lines.return_value = ['data: {"choices":[{"delta":{"content":"translated"}}]}', "", "data: [DONE]", ""]
                    with patch("app.providers.openai_compatible.requests.post", return_value=response) as post:
                        if image:
                            result = self.client.request_image_png(b"png", profile, "translate", 0.4, stream=stream)
                        else:
                            result = self.client.request_text("translate", profile, 0.4, stream=stream)
                    self.assertEqual(result, "translated")
                    payload = post.call_args.kwargs["json"]
                    self.assertEqual(payload["reasoning_effort"], "high")
                    self.assertEqual(payload["temperature"], 0.4)

    def test_gemini3_level_and_thought_filter_for_stream_and_nonstream(self):
        profile = ApiProfile(provider="gemini", model="models/gemini-flash-lite-latest", api_keys=["test-key"], reasoning_effort="low")
        for stream in (False, True):
            for image in (False, True):
                with self.subTest(stream=stream, image=image):
                    data = {"candidates": [{"content": {"parts": [{"text": "private summary", "thought": True}, {"text": "translated"}]}, "finishReason": "STOP"}]}
                    response = Mock()
                    response.json.return_value = data
                    response.iter_lines.return_value = ["data: " + json.dumps(data), ""]
                    with patch("app.providers.gemini_compatible.requests.request", return_value=response) as post:
                        if image:
                            result = self.client.request_image_png(b"png", profile, "translate", 0.2, stream=stream)
                        else:
                            result = self.client.request_text("translate", profile, 0.2, stream=stream)
                    self.assertEqual(result, "translated")
                    generation = post.call_args.kwargs["json"]["generationConfig"]
                    self.assertEqual(generation["thinkingConfig"], {"thinkingLevel": "LOW", "includeThoughts": False})
                    self.assertNotIn("temperature", generation)
                    self.assertNotIn("thinkingBudget", generation["thinkingConfig"])

    def test_gemini_default_omits_thinking_configuration(self):
        profile = ApiProfile(api_keys=["test-key"])
        response = Mock()
        response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "translated"}]}}]}
        with patch("app.providers.gemini_compatible.requests.request", return_value=response) as post:
            self.client.request_text("hello", profile, 0.2)
        self.assertNotIn("thinkingConfig", post.call_args.kwargs["json"]["generationConfig"])

    def test_rejected_reasoning_parameter_is_not_retried_without_stream(self):
        for provider, target, detail in (
            ("openai", "app.providers.openai_compatible.requests.post", "unsupported reasoning_effort"),
            ("gemini", "app.providers.gemini_compatible.requests.request", "unsupported thinkingLevel"),
        ):
            with self.subTest(provider=provider):
                profile = ApiProfile(provider=provider, base_url="https://compat.example.com", model="test-model", api_keys=["test-key"], reasoning_effort="high")
                response = Mock(status_code=400, reason="Bad Request")
                response.json.return_value = {"error": {"message": detail}}
                response.raise_for_status.side_effect = requests.HTTPError(detail)
                with patch(target, return_value=response) as post:
                    with self.assertRaises(ApiClientError):
                        self.client.request_text("translate", profile, 0.2, stream=True)
                self.assertEqual(post.call_count, 1)
