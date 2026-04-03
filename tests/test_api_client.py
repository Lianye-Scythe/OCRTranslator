import unittest
from unittest.mock import Mock, patch

import requests

from app.api_client import ApiClient, ApiClientError
from app.models import ApiProfile


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

        with self.assertRaisesRegex(RuntimeError, "HTTP 401: invalid api key"):
            self.client._ensure_success(response)

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
    def test_translate_gemini_raises_block_reason_when_prompt_is_blocked(self, mock_post):
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
        mock_post.return_value = response

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
                self.client.translate_image(Mock(), profile, "繁體中文", 0.2)

        self.assertEqual(mock_translate.call_count, 2)
        mock_sleep.assert_not_called()

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

        with patch.object(self.client, "_image_to_base64", return_value="base64"), patch.object(self.client, "_translate_gemini", side_effect=ApiClientError("Gemini finished without text (finishReason=PROHIBITED_CONTENT)", user_message="blocked", retryable=False)) as mock_translate:
            with self.assertRaisesRegex(ApiClientError, "PROHIBITED_CONTENT"):
                self.client.translate_image(Mock(), profile, "繁體中文", 0.2)

        self.assertEqual(mock_translate.call_count, 1)


if __name__ == "__main__":
    unittest.main()
