from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_PATH = ROOT / "docs/images/screenshots/overlay-light-manga.png"
ICON_PATH = ROOT / "app/assets/icons/app-icon-256.png"
OUTPUT_PATH = ROOT / "docs/images/social-preview.png"

CANVAS_SIZE = (1280, 640)
SAFE_MARGIN = 32
BACKGROUND = (250, 251, 252)
TEXT_PRIMARY = (21, 25, 30)
TEXT_SECONDARY = (66, 77, 87)
ACCENT = (16, 116, 105)


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
        icon = icon.convert("RGBA").resize((52, 52), Image.Resampling.LANCZOS)
        canvas.paste(icon, (SAFE_MARGIN, 49), icon)

    draw_text(draw, (104, 24), "OCRTranslator", 82, TEXT_PRIMARY, bold=True)
    draw_text(draw, (SAFE_MARGIN, 128), "Portable OCR & AI Translation for Windows", 38, TEXT_SECONDARY)
    draw.line((SAFE_MARGIN, 184, CANVAS_SIZE[0] - SAFE_MARGIN - 1, 184), fill=(210, 219, 223), width=2)

    draw_text(draw, (SAFE_MARGIN, 193), "Japanese source", 24, TEXT_SECONDARY, bold=True)
    draw_text(draw, (456, 193), "Chinese translation", 24, ACCENT, bold=True)

    # Crop a real reading example, retaining the result window's native toolbar.
    with Image.open(SCREENSHOT_PATH) as screenshot:
        source = screenshot.crop((600, 0, 1130, 325)).convert("RGB")
        translation = screenshot.crop((18, 16, 583, 242)).convert("RGB")
        height = round(792 * translation.height / translation.width)
        source = ImageOps.fit(source, (400, height), method=Image.Resampling.LANCZOS)
        translation = translation.resize((792, height), Image.Resampling.LANCZOS)
        canvas.paste(source, (SAFE_MARGIN, 232))
        canvas.paste(translation, (456, 232))

    draw_text(draw, (SAFE_MARGIN, 564), "Screenshots  /  Selected Text  /  Manual Input", 30, TEXT_PRIMARY)
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
