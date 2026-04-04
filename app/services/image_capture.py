from dataclasses import dataclass
import io

from PIL import Image, ImageGrab
from PySide6.QtCore import QBuffer, QByteArray, QRect, Qt
from PySide6.QtGui import QGuiApplication, QPixmap


@dataclass(slots=True)
class CaptureResult:
    png_bytes: bytes
    preview_pixmap: QPixmap | None = None


class ScreenCaptureService:
    def __init__(self, log_func=None):
        self.log = log_func or (lambda message: None)

    @staticmethod
    def pixmap_to_png_bytes(pixmap: QPixmap) -> bytes:
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.WriteOnly)
        pixmap.save(buffer, "PNG")
        buffer.close()
        return bytes(byte_array.data())

    @staticmethod
    def image_to_png_bytes(image: Image.Image) -> bytes:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def capture_bbox_image(self, bbox) -> CaptureResult:
        left, top, right, bottom = bbox
        width = max(1, right - left)
        height = max(1, bottom - top)
        capture_rect = QRect(left, top, width, height)
        screen = QGuiApplication.screenAt(capture_rect.center()) or QGuiApplication.primaryScreen()
        if screen and screen.geometry().contains(capture_rect.topLeft()) and screen.geometry().contains(capture_rect.bottomRight()):
            local_rect = capture_rect.translated(-screen.geometry().topLeft())
            pixmap = screen.grabWindow(0, local_rect.x(), local_rect.y(), local_rect.width(), local_rect.height())
            if not pixmap.isNull():
                return CaptureResult(
                    png_bytes=self.pixmap_to_png_bytes(pixmap),
                    preview_pixmap=self.build_preview_pixmap_from_pixmap(pixmap),
                )
        self.log("Qt capture crossed screen bounds or returned empty data, falling back to Pillow all-screen capture")
        image = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
        png_bytes = self.image_to_png_bytes(image)
        return CaptureResult(
            png_bytes=png_bytes,
            preview_pixmap=self.build_preview_pixmap_from_bytes(png_bytes),
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
    def build_preview_pixmap(image: Image.Image, *, max_size: tuple[int, int] = (1280, 720)) -> QPixmap:
        return ScreenCaptureService.build_preview_pixmap_from_bytes(ScreenCaptureService.image_to_png_bytes(image), max_size=max_size)

    @staticmethod
    def scale_preview_pixmap(preview_pixmap: QPixmap, viewport_size):
        if viewport_size.width() < 40 or viewport_size.height() < 40:
            return preview_pixmap
        return preview_pixmap.scaled(viewport_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
