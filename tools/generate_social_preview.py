from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_PATH = ROOT / "docs/images/screenshots/main-window-light.png"
ICON_PATH = ROOT / "app/assets/icons/app-icon-256.png"
OUTPUT_PATH = ROOT / "docs/images/social-preview.png"

CANVAS_SIZE = (1280, 640)
SAFE_MARGIN = 32
BACKGROUND = (239, 243, 249)
TEXT_PRIMARY = (21, 25, 30)
TEXT_SECONDARY = (66, 77, 87)
SCREENSHOT_BOX = (480, 32, 1248, 608)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")
    for directory in (Path("C:/Windows/Fonts"), Path("/mnt/c/Windows/Fonts")):
        for name in names:
            candidate = directory / name
            if candidate.is_file():
                return ImageFont.truetype(str(candidate), size=size)
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default(size=size)


def draw_text(draw: ImageDraw.ImageDraw, position: tuple[int, int], text: str, size: int,
              fill: tuple[int, int, int], *, bold: bool = False) -> None:
    font = load_font(size, bold=bold)
    bounds = draw.textbbox(position, text, font=font)
    if bounds[2] > CANVAS_SIZE[0] - SAFE_MARGIN or bounds[3] > CANVAS_SIZE[1] - SAFE_MARGIN:
        raise ValueError(f"Text exceeds the social-preview safe area: {text}")
    draw.text(position, text, font=font, fill=fill)


def render_preview() -> Image.Image:
    canvas = Image.new("RGB", CANVAS_SIZE, BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    with Image.open(ICON_PATH) as icon:
        icon = icon.convert("RGBA").resize((76, 76), Image.Resampling.LANCZOS)
        canvas.paste(icon, (SAFE_MARGIN, 104), icon)

    draw_text(draw, (SAFE_MARGIN, 214), "OCRTranslator", 62, TEXT_PRIMARY, bold=True)
    draw_text(draw, (SAFE_MARGIN, 309), "Portable OCR & AI", 32, TEXT_SECONDARY)
    draw_text(draw, (SAFE_MARGIN, 352), "Translation for Windows", 32, TEXT_SECONDARY)
    draw_text(draw, (SAFE_MARGIN, 458), "Screenshots / Selected Text", 24, TEXT_SECONDARY)
    draw_text(draw, (SAFE_MARGIN, 493), "Manual Input", 24, TEXT_SECONDARY)

    # Preserve the complete current main window and its aspect ratio.
    with Image.open(SCREENSHOT_PATH) as screenshot:
        left, top, right, bottom = SCREENSHOT_BOX
        fitted = ImageOps.contain(screenshot.convert("RGB"), (right - left, bottom - top), Image.Resampling.LANCZOS)
        x = left + (right - left - fitted.width) // 2
        y = top + (bottom - top - fitted.height) // 2
        canvas.paste(fitted, (x, y))
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the GitHub sharing image from real application assets.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--thumbnail", type=Path, help="Also write a 320x160 review image.")
    args = parser.parse_args()
    preview = render_preview()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    preview.save(args.output, format="PNG", optimize=True)
    if args.thumbnail:
        args.thumbnail.parent.mkdir(parents=True, exist_ok=True)
        preview.resize((320, 160), Image.Resampling.LANCZOS).save(args.thumbnail, format="PNG", optimize=True)
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
