import json
from pathlib import Path
import unittest

from app.config_store import _migrate_legacy_config
from app.default_prompts import (
    DEFAULT_TRANSLATION_IMAGE_PROMPT,
    DEFAULT_TRANSLATION_TEXT_PROMPT,
    PREVIOUS_TRANSLATION_IMAGE_PROMPT,
    PREVIOUS_TRANSLATION_TEXT_PROMPT,
)
from app.prompt_utils import build_image_request_prompt, build_text_request_prompt


class DefaultPromptTests(unittest.TestCase):
    def test_example_and_new_config_use_current_translation_prompts(self):
        example = json.loads((Path(__file__).resolve().parents[1] / "config.example.json").read_text(encoding="utf-8"))
        for config in ({}, example):
            preset = next(p for p in _migrate_legacy_config(config).prompt_presets if p.builtin_id == "translate")
            self.assertEqual(preset.image_prompt, DEFAULT_TRANSLATION_IMAGE_PROMPT)
            self.assertEqual(preset.text_prompt, DEFAULT_TRANSLATION_TEXT_PROMPT)
        preset = next(p for p in example["prompt_presets"] if p["builtin_id"] == "translate")
        self.assertEqual(preset["image_prompt"], DEFAULT_TRANSLATION_IMAGE_PROMPT)
        self.assertEqual(preset["text_prompt"], DEFAULT_TRANSLATION_TEXT_PROMPT)

    def test_unchanged_previous_defaults_upgrade_on_load(self):
        payload = {"prompt_presets": [{
            "name": "Renamed", "builtin_id": "translate",
            "image_prompt": PREVIOUS_TRANSLATION_IMAGE_PROMPT.replace("\n", "\r\n"),
            "text_prompt": PREVIOUS_TRANSLATION_TEXT_PROMPT,
        }]}
        preset = _migrate_legacy_config(payload).prompt_presets[0]
        self.assertEqual(preset.name, "Renamed")
        self.assertEqual(preset.image_prompt, DEFAULT_TRANSLATION_IMAGE_PROMPT)
        self.assertEqual(preset.text_prompt, DEFAULT_TRANSLATION_TEXT_PROMPT)

    def test_customized_fields_and_custom_presets_are_not_overwritten(self):
        payload = {"prompt_presets": [
            {"builtin_id": "translate", "image_prompt": "Custom image", "text_prompt": PREVIOUS_TRANSLATION_TEXT_PROMPT},
            {"builtin_id": "", "name": "Custom", "image_prompt": PREVIOUS_TRANSLATION_IMAGE_PROMPT, "text_prompt": "Custom text"},
        ]}
        presets = _migrate_legacy_config(payload).prompt_presets
        self.assertEqual(presets[0].image_prompt, "Custom image")
        self.assertEqual(presets[0].text_prompt, DEFAULT_TRANSLATION_TEXT_PROMPT)
        self.assertEqual(presets[1].image_prompt, PREVIOUS_TRANSLATION_IMAGE_PROMPT)
        self.assertEqual(presets[1].text_prompt, "Custom text")

    def test_target_language_substitution_keeps_the_requested_directives(self):
        image = build_image_request_prompt(DEFAULT_TRANSLATION_IMAGE_PROMPT, target_language="English")
        text = build_text_request_prompt(DEFAULT_TRANSLATION_TEXT_PROMPT, target_language="English")
        self.assertIn('TRANSLATE it into "English"', image)
        self.assertIn('into **"English"**', text)
        self.assertNotIn("{target_language}", image + text)
        self.assertIn("one bubble/block per line", image)
        self.assertIn("punctuation layout exactly as provided", text)
