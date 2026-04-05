import io

from PIL import Image, ImageGrab
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


class ScreenCaptureService:
    def __init__(self, log_func=None):
        self.log = log_func or (lambda message: None)

    @staticmethod
    def image_to_png_bytes(image: Image.Image) -> bytes:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def capture_bbox_png_bytes_threadsafe(bbox) -> bytes:
        left, top, right, bottom = bbox
        return ScreenCaptureService.image_to_png_bytes(
            ImageGrab.grab(
                bbox=(left, top, right, bottom),
                all_screens=True,
            )
        )

    @staticmethod
    def build_preview_pixmap_from_bytes(png_bytes: bytes, *, max_size: tuple[int, int] = (1280, 720)) -> QPixmap:
        pixmap = QPixmap()
        pixmap.loadFromData(png_bytes, "PNG")
        return ScreenCaptureService.build_preview_pixmap_from_pixmap(pixmap, max_size=max_size)

    @staticmethod
    def build_preview_pixmap_from_pixmap(source_pixmap: QPixmap, *, max_size: tuple[int, int] = (1280, 720)) -> QPixmap:
        if source_pixmap.isNull():
            return source_pixmap
        max_width, max_height = max_size
        if source_pixmap.width() <= max_width and source_pixmap.height() <= max_height:
            return source_pixmap
        return source_pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    @staticmethod
    def scale_preview_pixmap(preview_pixmap: QPixmap, viewport_size):
        if viewport_size.width() < 40 or viewport_size.height() < 40:
            return preview_pixmap
        return preview_pixmap.scaled(viewport_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
