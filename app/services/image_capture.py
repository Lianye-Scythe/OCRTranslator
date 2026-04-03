import io

from PIL import Image, ImageGrab
from PySide6.QtCore import QBuffer, QByteArray, QRect, Qt
from PySide6.QtGui import QGuiApplication, QPixmap


class ScreenCaptureService:
    def __init__(self, log_func=None):
        self.log = log_func or (lambda message: None)

    @staticmethod
    def pixmap_to_image(pixmap: QPixmap) -> Image.Image:
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.WriteOnly)
        pixmap.save(buffer, "PNG")
        buffer.close()
        return Image.open(io.BytesIO(byte_array.data())).convert("RGB")

    def capture_bbox_image(self, bbox) -> Image.Image:
        left, top, right, bottom = bbox
        width = max(1, right - left)
        height = max(1, bottom - top)
        capture_rect = QRect(left, top, width, height)
        screen = QGuiApplication.screenAt(capture_rect.center()) or QGuiApplication.primaryScreen()
        if screen and screen.geometry().contains(capture_rect.topLeft()) and screen.geometry().contains(capture_rect.bottomRight()):
            local_rect = capture_rect.translated(-screen.geometry().topLeft())
            pixmap = screen.grabWindow(0, local_rect.x(), local_rect.y(), local_rect.width(), local_rect.height())
            if not pixmap.isNull():
                return self.pixmap_to_image(pixmap)
        self.log("Qt capture crossed screen bounds or returned empty data, falling back to Pillow all-screen capture")
        return ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True).convert("RGB")

    @staticmethod
    def build_preview_pixmap(image: Image.Image, *, max_size: tuple[int, int] = (1280, 720)) -> QPixmap:
        preview = image.copy()
        preview.thumbnail(max_size)
        data = io.BytesIO()
        preview.save(data, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(data.getvalue(), "PNG")
        return pixmap

    @staticmethod
    def scale_preview_pixmap(preview_pixmap: QPixmap, viewport_size):
        if viewport_size.width() < 40 or viewport_size.height() < 40:
            return preview_pixmap
        return preview_pixmap.scaled(viewport_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
