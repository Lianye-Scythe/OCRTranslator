import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops, ImageDraw

from tools import generate_social_preview as preview


class SocialPreviewTests(unittest.TestCase):
    def test_render_has_safe_margins_and_complete_main_window(self):
        image = preview.render_preview()
        self.assertEqual(image.size, (1280, 640))
        self.assertEqual(image.mode, "RGB")
        background = Image.new("RGB", image.size, preview.BACKGROUND)
        bounds = ImageChops.difference(image, background).getbbox()
        self.assertGreaterEqual(bounds[0], preview.SAFE_MARGIN)
        self.assertGreaterEqual(bounds[1], preview.SAFE_MARGIN)
        self.assertLessEqual(bounds[2], image.width - preview.SAFE_MARGIN)
        self.assertLessEqual(bounds[3], image.height - preview.SAFE_MARGIN)
        self.assertEqual(preview.SCREENSHOT_PATH.name, "main-window-light.png")
        self.assertIsNotNone(ImageChops.difference(
            image.crop(preview.SCREENSHOT_BOX), background.crop(preview.SCREENSHOT_BOX),
        ).getbbox())

    def test_text_overflow_fails_instead_of_silently_clipping(self):
        image = Image.new("RGB", preview.CANVAS_SIZE)
        with self.assertRaises(ValueError):
            preview.draw_text(ImageDraw.Draw(image), (32, 32), "OCRTranslator" * 20, 82, (0, 0, 0))

    def test_cli_writes_full_size_and_review_thumbnail(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "full" / "social.png"
            thumbnail = Path(directory) / "review" / "small.png"
            with patch("sys.argv", ["preview", "--output", str(output), "--thumbnail", str(thumbnail)]):
                preview.main()
            for file, size in ((output, (1280, 640)), (thumbnail, (320, 160))):
                with Image.open(file) as image:
                    self.assertEqual(image.size, size)
                self.assertLess(file.stat().st_size, 1_000_000)


if __name__ == "__main__":
    unittest.main()
