from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_PATH = ROOT / "docs/images/screenshots/main-window-light.png"
ICON_PATH = ROOT / "app/assets/icons/app-icon-256.png"
OUTPUT_PATH = ROOT / "docs/images/social-preview.png"

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 640

BACKGROUND_TOP = (246, 248, 252)
BACKGROUND_BOTTOM = (236, 242, 252)
ACCENT_PRIMARY = (37, 99, 235)
ACCENT_SECONDARY = (79, 70, 229)
TEXT_PRIMARY = (15, 23, 42)
TEXT_SECONDARY = (71, 85, 105)
TEXT_TERTIARY = (51, 65, 85)
PANEL_FILL = (255, 255, 255, 188)
PANEL_BORDER = (148, 163, 184, 54)
SCREENSHOT_BORDER = (255, 255, 255, 230)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates = []
    if bold:
        font_candidates.extend(
            [
                "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/calibrib.ttf",
            ]
        )
    else:
        font_candidates.extend(
            [
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
            ]
        )

    for candidate in font_candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)

    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def vertical_gradient(width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line((0, y, width, y), fill=color)
    return image


def add_blurred_blob(base: Image.Image, bbox: tuple[int, int, int, int], color: tuple[int, int, int, int], blur_radius: int) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse(bbox, fill=color)
    overlay = overlay.filter(ImageFilter.GaussianBlur(blur_radius))
    base.alpha_composite(overlay)


def rounded_image(image: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.size[0], image.size[1]), radius=radius, fill=255)
    rounded = image.copy()
    rounded.putalpha(mask)
    return rounded


def fit_within(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    fitted = image.copy()
    fitted.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return fitted


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int, min_size: int, bold: bool = False) -> ImageFont.ImageFont:
    for size in range(start_size, min_size - 1, -2):
        font = load_font(size, bold=bold)
        width, _ = text_size(draw, text, font)
        if width <= max_width:
            return font
    return load_font(min_size, bold=bold)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        width, _ = text_size(draw, candidate, font)
        if width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_wrapped_text(draw: ImageDraw.ImageDraw, position: tuple[int, int], text: str, font: ImageFont.ImageFont, fill: tuple[int, int, int], max_width: int, line_spacing: int) -> int:
    x, y = position
    lines = wrap_text(draw, text, font, max_width)
    _, line_height = text_size(draw, "Ag", font)
    draw.multiline_text((x, y), "\n".join(lines), font=font, fill=fill, spacing=line_spacing)
    return len(lines) * line_height + max(len(lines) - 1, 0) * line_spacing


def draw_shadow(base: Image.Image, bbox: tuple[int, int, int, int], radius: int, blur_radius: int, color: tuple[int, int, int, int]) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(bbox, radius=radius, fill=color)
    overlay = overlay.filter(ImageFilter.GaussianBlur(blur_radius))
    base.alpha_composite(overlay)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    background = vertical_gradient(CANVAS_WIDTH, CANVAS_HEIGHT, BACKGROUND_TOP, BACKGROUND_BOTTOM).convert("RGBA")
    add_blurred_blob(background, (-60, -20, 420, 400), (*ACCENT_SECONDARY, 48), 55)
    add_blurred_blob(background, (860, -80, 1360, 360), (*ACCENT_PRIMARY, 40), 65)
    add_blurred_blob(background, (700, 360, 1240, 760), (*ACCENT_SECONDARY, 24), 72)

    screenshot = Image.open(SCREENSHOT_PATH).convert("RGBA")
    icon = Image.open(ICON_PATH).convert("RGBA")

    screenshot = screenshot.crop((0, 34, screenshot.size[0], screenshot.size[1]))

    panel_box = (54, 56, 456, 584)
    draw_shadow(background, (panel_box[0] + 4, panel_box[1] + 12, panel_box[2] + 4, panel_box[3] + 12), 30, 20, (15, 23, 42, 24))
    panel_overlay = Image.new("RGBA", background.size, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel_overlay)
    panel_draw.rounded_rectangle(panel_box, radius=30, fill=PANEL_FILL, outline=PANEL_BORDER, width=1)
    background.alpha_composite(panel_overlay)

    draw = ImageDraw.Draw(background)
    text_max_width = panel_box[2] - panel_box[0] - 72

    title_font = fit_font(draw, "OCRTranslator", text_max_width, start_size=54, min_size=40, bold=True)
    subtitle_font = load_font(22)
    meta_font = load_font(20)

    icon_size = 84
    icon_render = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    draw_shadow(background, (90, 92, 90 + icon_size, 92 + icon_size), 22, 14, (37, 99, 235, 30))
    background.alpha_composite(icon_render, (90, 92))

    draw.text((90, 204), "OCRTranslator", font=title_font, fill=TEXT_PRIMARY)
    subtitle_height = draw_wrapped_text(
        draw,
        (92, 286),
        "Portable Windows OCR / AI desktop tool for screenshot, selected-text, and manual-input workflows.",
        subtitle_font,
        TEXT_SECONDARY,
        max_width=text_max_width,
        line_spacing=8,
    )

    meta_y = 286 + subtitle_height + 38
    draw_wrapped_text(
        draw,
        (92, meta_y),
        "Screen capture  •  Selected text  •  Manual input",
        meta_font,
        TEXT_SECONDARY,
        max_width=text_max_width,
        line_spacing=8,
    )
    draw.text((92, panel_box[3] - 52), "Windows  •  PySide6  •  OCR  •  AI", font=meta_font, fill=TEXT_TERTIARY)

    frame_box = (470, 58, 1232, 582)
    draw_shadow(background, (frame_box[0] + 14, frame_box[1] + 22, frame_box[2] + 14, frame_box[3] + 22), 32, 24, (15, 23, 42, 38))

    frame_overlay = Image.new("RGBA", background.size, (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(frame_overlay)
    frame_draw.rounded_rectangle(frame_box, radius=30, fill=(255, 255, 255, 194), outline=(255, 255, 255, 224), width=1)
    background.alpha_composite(frame_overlay)

    content_padding = 16
    content_width = frame_box[2] - frame_box[0] - content_padding * 2
    content_height = frame_box[3] - frame_box[1] - content_padding * 2
    fitted_screenshot = fit_within(screenshot, content_width, content_height)
    fitted_screenshot = ImageOps.expand(fitted_screenshot, border=2, fill=SCREENSHOT_BORDER)
    rounded_screenshot = rounded_image(fitted_screenshot, radius=26)

    screenshot_x = frame_box[0] + (frame_box[2] - frame_box[0] - rounded_screenshot.size[0]) // 2
    screenshot_y = frame_box[1] + (frame_box[3] - frame_box[1] - rounded_screenshot.size[1]) // 2
    background.alpha_composite(rounded_screenshot, (screenshot_x, screenshot_y))

    background.convert("RGB").save(OUTPUT_PATH, format="PNG", optimize=True)
    print(f"Created {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
