import unittest
from unittest.mock import Mock, patch

import requests

from app.services.update_checker import UpdateCheckService, compare_versions, normalize_version_text, version_tuple


class _FakeResponse:
    def __init__(self, *, status_code=200, payload=None, url="https://github.com/example/release"):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.url = url

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class UpdateCheckerTests(unittest.TestCase):
    def test_version_helpers_normalize_and_compare_semver_tags(self):
        self.assertEqual(normalize_version_text("v1.2.3"), "1.2.3")
        self.assertEqual(version_tuple("1.2.3"), (1, 2, 3))
        self.assertGreater(compare_versions("v1.2.4", "1.2.3"), 0)
        self.assertEqual(compare_versions("1.2", "1.2.0"), 0)

    @patch("app.services.update_checker.requests.get")
    def test_check_latest_release_returns_update_available_when_tag_is_newer(self, mock_get):
        mock_get.return_value = _FakeResponse(
            payload={
                "tag_name": "v1.2.0",
                "html_url": "https://github.com/Lianye-Scythe/OCRTranslator/releases/tag/v1.2.0",
            }
        )
        service = UpdateCheckService()

        result = service.check_latest_release(current_version="1.0.0")

        self.assertEqual(result.kind, "available")
        self.assertEqual(result.latest_version, "1.2.0")
        self.assertTrue(result.has_update)

    @patch("app.services.update_checker.requests.get")
    def test_check_latest_release_returns_up_to_date_when_version_matches(self, mock_get):
        mock_get.return_value = _FakeResponse(
            payload={
                "tag_name": "v1.0.0",
                "html_url": "https://github.com/Lianye-Scythe/OCRTranslator/releases/tag/v1.0.0",
            }
        )
        service = UpdateCheckService()

        result = service.check_latest_release(current_version="1.0.0")

        self.assertEqual(result.kind, "up_to_date")
        self.assertTrue(result.is_up_to_date)

    @patch("app.services.update_checker.requests.get")
    def test_check_latest_release_returns_error_on_request_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("network down")
        service = UpdateCheckService()

        result = service.check_latest_release(current_version="1.0.0")

        self.assertEqual(result.kind, "error")
        self.assertTrue(result.is_error)
        self.assertIn("network down", result.error)

    @patch("app.services.update_checker.requests.get")
    def test_check_latest_release_returns_error_when_github_status_is_not_ok(self, mock_get):
        mock_get.return_value = _FakeResponse(status_code=404, payload={"message": "Not Found"})
        service = UpdateCheckService()

        result = service.check_latest_release(current_version="1.0.0")

        self.assertEqual(result.kind, "error")
        self.assertIn("Not Found", result.error)


if __name__ == "__main__":
    unittest.main()
