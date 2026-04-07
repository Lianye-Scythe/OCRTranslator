import io
import math
import sys
from dataclasses import dataclass

from PIL import Image, ImageGrab
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QPixmap


@dataclass(frozen=True)
class CapturePlan:
    source_bbox: tuple[int, int, int, int]
    native_segments: tuple[tuple[int, int, int, int], ...] = ()


@dataclass(frozen=True)
class DesktopSnapshotSegment:
    screen_geometry: tuple[int, int, int, int]
    native_bbox: tuple[int, int, int, int]
    device_pixel_ratio: float
    image: Image.Image


@dataclass(frozen=True)
class DesktopSnapshot:
    virtual_rect: tuple[int, int, int, int]
    segments: tuple[DesktopSnapshotSegment, ...]


def _normalize_bbox(bbox) -> tuple[int, int, int, int]:
    left, top, right, bottom = (int(value) for value in bbox)
    if right < left:
        left, right = right, left
    if bottom < top:
        top, bottom = bottom, top
    return left, top, right, bottom


def _bbox_to_qrect(bbox) -> QRect:
    left, top, right, bottom = _normalize_bbox(bbox)
    return QRect(left, top, max(0, right - left), max(0, bottom - top))


def _qrect_to_tuple(rect: QRect) -> tuple[int, int, int, int]:
    return rect.x(), rect.y(), rect.width(), rect.height()


def _tuple_to_qrect(rect_tuple: tuple[int, int, int, int]) -> QRect:
    x, y, width, height = rect_tuple
    return QRect(int(x), int(y), int(width), int(height))


def _virtual_rect_for_screens(screens) -> QRect:
    if not screens:
        return QRect(0, 0, 1920, 1080)
    rect = QRect(screens[0].geometry())
    for screen in screens[1:]:
        rect = rect.united(screen.geometry())
    return rect


def _qt_rect_to_native_bbox(rect: QRect, *, screen_geometry: QRect, device_pixel_ratio: float) -> tuple[int, int, int, int]:
    scale = max(float(device_pixel_ratio or 1.0), 1.0)
    qt_left = rect.x()
    qt_top = rect.y()
    qt_right = rect.x() + rect.width()
    qt_bottom = rect.y() + rect.height()
    screen_left = screen_geometry.x()
    screen_top = screen_geometry.y()
    native_left = screen_left + math.floor((qt_left - screen_left) * scale)
    native_top = screen_top + math.floor((qt_top - screen_top) * scale)
    native_right = screen_left + math.ceil((qt_right - screen_left) * scale)
    native_bottom = screen_top + math.ceil((qt_bottom - screen_top) * scale)
    return native_left, native_top, native_right, native_bottom


def _windows_native_capture_segments_for_bbox(bbox, screens) -> list[tuple[int, int, int, int]]:
    selection_rect = _bbox_to_qrect(bbox)
    if selection_rect.isEmpty():
        return []
    segments: list[tuple[int, int, int, int]] = []
    for screen in screens or []:
        geometry = QRect(screen.geometry())
        if geometry.isEmpty():
            continue
        intersection = selection_rect.intersected(geometry)
        if intersection.isEmpty():
            continue
        native_bbox = _qt_rect_to_native_bbox(
            intersection,
            screen_geometry=geometry,
            device_pixel_ratio=screen.devicePixelRatio(),
        )
        if native_bbox[0] >= native_bbox[2] or native_bbox[1] >= native_bbox[3]:
            continue
        segments.append(native_bbox)
    segments.sort(key=lambda item: (item[1], item[0], item[3], item[2]))
    return segments


def _format_bbox(bbox) -> str:
    left, top, right, bottom = _normalize_bbox(bbox)
    return f"({left},{top},{right},{bottom})"


def _format_screen_debug_entry(index: int, screen) -> str:
    geometry = QRect(screen.geometry())
    return (
        f"{index}:{geometry.x()},{geometry.y()},{geometry.width()}x{geometry.height()}"
        f"@dpr={screen.devicePixelRatio():.2f}"
    )


def _build_screens_debug_entries(screens) -> list[str]:
    return [_format_screen_debug_entry(index, screen) for index, screen in enumerate(screens or [])]


def _pil_image_to_qimage(image: Image.Image) -> QImage:
    rgba = image.convert("RGBA")
    buffer = rgba.tobytes("raw", "RGBA")
    return QImage(buffer, rgba.width, rgba.height, QImage.Format_RGBA8888).copy()


class ScreenCaptureService:
    def __init__(self, log_func=None):
        self.log = log_func or (lambda message: None)

    @staticmethod
    def image_to_png_bytes(image: Image.Image) -> bytes:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def build_capture_plan(bbox) -> CapturePlan:
        source_bbox = _normalize_bbox(bbox)
        if not sys.platform.startswith("win"):
            return CapturePlan(source_bbox=source_bbox)
        native_segments = tuple(_windows_native_capture_segments_for_bbox(source_bbox, QGuiApplication.screens()))
        return CapturePlan(source_bbox=source_bbox, native_segments=native_segments)

    def log_capture_plan(self, bbox, capture_plan: CapturePlan) -> None:
        source_bbox_text = _format_bbox(capture_plan.source_bbox)
        if sys.platform.startswith("win"):
            screens = QGuiApplication.screens()
            screens_text = "; ".join(_build_screens_debug_entries(screens)) or "none"
            native_segments_text = ", ".join(_format_bbox(segment) for segment in capture_plan.native_segments) or "direct-fallback"
            self.log(
                "Capture plan | "
                f"qt_bbox={_format_bbox(bbox)} | "
                f"source_bbox={source_bbox_text} | "
                f"screens={screens_text} | "
                f"native_segments={native_segments_text}"
            )
            return
        self.log(
            f"Capture plan | source_bbox={source_bbox_text} | platform={sys.platform} | native_segments=direct"
        )

    @staticmethod
    def capture_desktop_snapshot() -> DesktopSnapshot:
        screens = QGuiApplication.screens()
        virtual_rect = _virtual_rect_for_screens(screens)
        if sys.platform.startswith("win"):
            segments = []
            for screen in screens or []:
                geometry = QRect(screen.geometry())
                if geometry.isEmpty():
                    continue
                native_bbox = _qt_rect_to_native_bbox(
                    geometry,
                    screen_geometry=geometry,
                    device_pixel_ratio=screen.devicePixelRatio(),
                )
                segments.append(
                    DesktopSnapshotSegment(
                        screen_geometry=_qrect_to_tuple(geometry),
                        native_bbox=native_bbox,
                        device_pixel_ratio=float(screen.devicePixelRatio()),
                        image=ScreenCaptureService._grab_image(native_bbox),
                    )
                )
            return DesktopSnapshot(virtual_rect=_qrect_to_tuple(virtual_rect), segments=tuple(segments))
        full_bbox = (virtual_rect.left(), virtual_rect.top(), virtual_rect.right() + 1, virtual_rect.bottom() + 1)
        return DesktopSnapshot(
            virtual_rect=_qrect_to_tuple(virtual_rect),
            segments=(
                DesktopSnapshotSegment(
                    screen_geometry=_qrect_to_tuple(virtual_rect),
                    native_bbox=_normalize_bbox(full_bbox),
                    device_pixel_ratio=1.0,
                    image=ScreenCaptureService._grab_image(full_bbox),
                ),
            ),
        )

    @staticmethod
    def _grab_image(bbox) -> Image.Image:
        left, top, right, bottom = _normalize_bbox(bbox)
        return ImageGrab.grab(
            bbox=(left, top, right, bottom),
            all_screens=True,
        )

    @staticmethod
    def _compose_captured_parts(captured_parts: list[tuple[tuple[int, int, int, int], Image.Image]]) -> Image.Image:
        if len(captured_parts) == 1:
            return captured_parts[0][1]
        min_left = min(segment[0] for segment, _image in captured_parts)
        min_top = min(segment[1] for segment, _image in captured_parts)
        max_right = max(segment[2] for segment, _image in captured_parts)
        max_bottom = max(segment[3] for segment, _image in captured_parts)
        composite = Image.new(captured_parts[0][1].mode, (max_right - min_left, max_bottom - min_top))
        for segment, image in captured_parts:
            composite.paste(image, (segment[0] - min_left, segment[1] - min_top))
        return composite

    @staticmethod
    def _capture_native_segments(native_segments: tuple[tuple[int, int, int, int], ...]) -> Image.Image:
        captured_parts = [(segment, ScreenCaptureService._grab_image(segment)) for segment in native_segments]
        return ScreenCaptureService._compose_captured_parts(captured_parts)

    @staticmethod
    def build_snapshot_background_pixmap(snapshot: DesktopSnapshot) -> QPixmap:
        virtual_rect = _tuple_to_qrect(snapshot.virtual_rect)
        if virtual_rect.isEmpty() or not snapshot.segments:
            return QPixmap()
        background = QImage(virtual_rect.size(), QImage.Format_RGBA8888)
        background.fill(Qt.black)
        painter = QPainter(background)
        for segment in snapshot.segments:
            screen_rect = _tuple_to_qrect(segment.screen_geometry)
            target_rect = QRect(screen_rect.topLeft() - virtual_rect.topLeft(), screen_rect.size())
            painter.drawImage(target_rect, _pil_image_to_qimage(segment.image))
        painter.end()
        return QPixmap.fromImage(background)

    @staticmethod
    def capture_bbox_image_from_snapshot(snapshot: DesktopSnapshot, bbox, *, capture_plan: CapturePlan | None = None) -> Image.Image:
        plan = capture_plan or ScreenCaptureService.build_capture_plan(bbox)
        selection_rect = _bbox_to_qrect(plan.source_bbox)
        captured_parts: list[tuple[tuple[int, int, int, int], Image.Image]] = []
        for segment in snapshot.segments:
            screen_geometry = _tuple_to_qrect(segment.screen_geometry)
            intersection = selection_rect.intersected(screen_geometry)
            if intersection.isEmpty():
                continue
            native_bbox = _qt_rect_to_native_bbox(
                intersection,
                screen_geometry=screen_geometry,
                device_pixel_ratio=segment.device_pixel_ratio,
            )
            crop_box = (
                native_bbox[0] - segment.native_bbox[0],
                native_bbox[1] - segment.native_bbox[1],
                native_bbox[2] - segment.native_bbox[0],
                native_bbox[3] - segment.native_bbox[1],
            )
            captured_parts.append((native_bbox, segment.image.crop(crop_box)))
        if captured_parts:
            return ScreenCaptureService._compose_captured_parts(captured_parts)
        if snapshot.segments:
            fallback_segment = snapshot.segments[0]
            return fallback_segment.image.crop((0, 0, 0, 0))
        return Image.new("RGBA", (0, 0))

    @staticmethod
    def capture_bbox_png_bytes_from_snapshot(snapshot: DesktopSnapshot, bbox, *, capture_plan: CapturePlan | None = None) -> bytes:
        return ScreenCaptureService.image_to_png_bytes(ScreenCaptureService.capture_bbox_image_from_snapshot(snapshot, bbox, capture_plan=capture_plan))

    @staticmethod
    def capture_bbox_image_threadsafe(bbox, *, capture_plan: CapturePlan | None = None) -> Image.Image:
        plan = capture_plan or ScreenCaptureService.build_capture_plan(bbox)
        if sys.platform.startswith("win") and plan.native_segments:
            return ScreenCaptureService._capture_native_segments(plan.native_segments)
        return ScreenCaptureService._grab_image(plan.source_bbox)

    @staticmethod
    def capture_bbox_png_bytes_threadsafe(bbox, *, capture_plan: CapturePlan | None = None) -> bytes:
        return ScreenCaptureService.image_to_png_bytes(
            ScreenCaptureService.capture_bbox_image_threadsafe(bbox, capture_plan=capture_plan)
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
