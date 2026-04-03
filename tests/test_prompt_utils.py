import unittest

from app.prompt_utils import build_image_request_prompt, build_text_request_prompt, render_prompt_template


class PromptUtilsTests(unittest.TestCase):
    def test_render_prompt_template_replaces_known_variables_only(self):
        result = render_prompt_template("Translate to {target_language}. Keep {unknown}.", target_language="English")
        self.assertEqual(result, "Translate to English. Keep {unknown}.")

    def test_build_image_request_prompt_injects_target_language(self):
        result = build_image_request_prompt("Translate into {target_language}.", target_language="日本語")
        self.assertEqual(result, "Translate into 日本語.")

    def test_build_text_request_prompt_appends_wrapped_text_input(self):
        result = build_text_request_prompt("Summarize in {target_language}.", "Line 1\nLine 2", target_language="English")
        self.assertIn("Summarize in English.", result)
        self.assertIn("<text-input>", result)
        self.assertIn("Line 1\nLine 2", result)
        self.assertIn("</text-input>", result)
        self.assertNotIn("Please process the following text according to the instructions above.", result)


if __name__ == "__main__":
    unittest.main()
