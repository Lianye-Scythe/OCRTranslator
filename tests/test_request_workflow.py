import unittest
from types import SimpleNamespace

from app.services.request_workflow import RequestWorkflowController


class RequestWorkflowControllerTests(unittest.TestCase):
    def test_profile_request_signature_can_include_model(self):
        profile = SimpleNamespace(
            name="Demo",
            provider="openai",
            base_url="https://api.openai.com",
            api_keys=["key-1"],
            model="gpt-4o-mini",
        )

        signature_without_model = RequestWorkflowController.profile_request_signature(profile)
        signature_with_model = RequestWorkflowController.profile_request_signature(profile, include_model=True)

        self.assertNotEqual(signature_without_model, signature_with_model)
        self.assertEqual(signature_with_model[-1], "gpt-4o-mini")


if __name__ == "__main__":
    unittest.main()
