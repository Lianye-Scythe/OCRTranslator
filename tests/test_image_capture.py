import io
import unittest
from unittest.mock import patch

from PIL import Image
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication

from app.services.image_capture import (
    CapturePlan,
    DesktopSnapshot,
    DesktopSnapshotSegment,
    ScreenCaptureService,
    _windows_native_capture_segments_for_bbox,
)


class _FakeScreen:
    def __init__(self, geometry: QRect, device_pixel_ratio: float):
        self._geometry = QRect(geometry)
        self._device_pixel_ratio = float(device_pixel_ratio)

    def geometry(self) -> QRect:
        return QRect(self._geometry)

    def devicePixelRatio(self) -> float:
        return self._device_pixel_ratio


class ImageCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_windows_native_capture_segments_scale_single_screen_bbox_by_device_pixel_ratio(self):
        screen = _FakeScreen(QRect(0, 0, 2560, 1440), 1.5)

        segments = _windows_native_capture_segments_for_bbox((100, 200, 300, 400), [screen])

        self.assertEqual(segments, [(150, 300, 450, 600)])

    def test_windows_native_capture_segments_handle_left_screen_with_negative_x_origin(self):
        screens = [
            _FakeScreen(QRect(-1600, 0, 1280, 1024), 1.25),
            _FakeScreen(QRect(0, 0, 1920, 1080), 1.0),
        ]

        segments = _windows_native_capture_segments_for_bbox((-500, 0, 100, 100), screens)

        self.assertEqual(
            segments,
            [
                (-225, 0, 0, 125),
                (0, 0, 100, 100),
            ],
        )

    def test_windows_native_capture_segments_split_vertical_stack(self):
        screens = [
            _FakeScreen(QRect(0, -1080, 1920, 1080), 1.0),
            _FakeScreen(QRect(0, 0, 1920, 1080), 1.0),
        ]

        segments = _windows_native_capture_segments_for_bbox((100, -100, 300, 100), screens)

        self.assertEqual(
            segments,
            [
                (100, -100, 300, 0),
                (100, 0, 300, 100),
            ],
        )

    def test_windows_native_capture_segments_split_mixed_dpi_selection_per_screen(self):
        screens = [
            _FakeScreen(QRect(0, 0, 1920, 1080), 1.0),
            _FakeScreen(QRect(1920, 0, 2560, 1440), 1.5),
        ]

        segments = _windows_native_capture_segments_for_bbox((1800, 0, 2100, 100), screens)

        self.assertEqual(
            segments,
            [
                (1800, 0, 1920, 100),
                (1920, 0, 2190, 150),
            ],
        )

    def test_windows_native_capture_segments_span_three_mixed_dpi_screens(self):
        screens = [
            _FakeScreen(QRect(-1600, 0, 1280, 1024), 1.25),
            _FakeScreen(QRect(0, 0, 1920, 1080), 1.0),
            _FakeScreen(QRect(1920, 0, 2560, 1440), 1.5),
        ]

        segments = _windows_native_capture_segments_for_bbox((-500, 0, 2100, 100), screens)

        self.assertEqual(
            segments,
            [
                (-225, 0, 0, 125),
                (0, 0, 1920, 100),
                (1920, 0, 2190, 150),
            ],
        )

    def test_build_capture_plan_precomputes_windows_native_segments_on_ui_thread(self):
        screens = [_FakeScreen(QRect(0, 0, 2560, 1440), 1.5)]

        with patch("app.services.image_capture.sys.platform", "win32"), patch(
            "app.services.image_capture.QGuiApplication.screens", return_value=screens
        ):
            plan = ScreenCaptureService.build_capture_plan((100, 200, 300, 400))

        self.assertEqual(
            plan,
            CapturePlan(
                source_bbox=(100, 200, 300, 400),
                native_segments=((150, 300, 450, 600),),
            ),
        )

    def test_log_capture_plan_records_screen_geometry_dpr_and_native_segments(self):
        logs = []
        service = ScreenCaptureService(logs.append)
        screens = [
            _FakeScreen(QRect(-1600, 0, 1280, 1024), 1.25),
            _FakeScreen(QRect(0, 0, 1920, 1080), 1.0),
        ]
        plan = CapturePlan(source_bbox=(-500, 0, 100, 100), native_segments=((-225, 0, 0, 125), (0, 0, 100, 100)))

        with patch("app.services.image_capture.sys.platform", "win32"), patch(
            "app.services.image_capture.QGuiApplication.screens", return_value=screens
        ):
            service.log_capture_plan((-500, 0, 100, 100), plan)

        self.assertEqual(logs, ["Capture plan | qt_bbox=(-500,0,100,100) | source_bbox=(-500,0,100,100) | screens=0:-1600,0,1280x1024@dpr=1.25; 1:0,0,1920x1080@dpr=1.00 | native_segments=(-225,0,0,125), (0,0,100,100)"])

    def test_capture_bbox_png_bytes_from_snapshot_crops_without_live_grab(self):
        snapshot = DesktopSnapshot(
            virtual_rect=(-1600, 0, 3520, 1080),
            segments=(
                DesktopSnapshotSegment((-1600, 0, 1280, 1024), (-1600, 0, 0, 1280), 1.25, Image.new("RGB", (1600, 1280), (255, 0, 0))),
                DesktopSnapshotSegment((0, 0, 1920, 1080), (0, 0, 1920, 1080), 1.0, Image.new("RGB", (1920, 1080), (0, 0, 255))),
            ),
        )
        plan = CapturePlan(source_bbox=(-500, 0, 100, 100), native_segments=((-225, 0, 0, 125), (0, 0, 100, 100)))

        with patch("app.services.image_capture.ImageGrab.grab") as mock_grab:
            png_bytes = ScreenCaptureService.capture_bbox_png_bytes_from_snapshot(
                snapshot,
                (-500, 0, 100, 100),
                capture_plan=plan,
            )

        mock_grab.assert_not_called()
        image = Image.open(io.BytesIO(png_bytes))
        image.load()
        self.assertEqual(image.size, (325, 125))
        self.assertEqual(image.getpixel((10, 10)), (255, 0, 0))
        self.assertEqual(image.getpixel((250, 10)), (0, 0, 255))

    def test_build_snapshot_background_pixmap_matches_virtual_rect_size(self):
        snapshot = DesktopSnapshot((0, 0, 1920, 1080), (DesktopSnapshotSegment((0, 0, 1920, 1080), (0, 0, 1920, 1080), 1.0, Image.new("RGB", (1920, 1080), (12, 34, 56))),))
        pixmap = ScreenCaptureService.build_snapshot_background_pixmap(snapshot)
        self.assertEqual((pixmap.width(), pixmap.height()), (1920, 1080))

    def test_capture_bbox_png_bytes_threadsafe_composites_native_segments_without_resampling(self):
        plan = CapturePlan(
            source_bbox=(1800, 0, 2100, 100),
            native_segments=((1800, 0, 1920, 100), (1920, 0, 2190, 150)),
        )

        def fake_grab(*, bbox, all_screens):
            self.assertTrue(all_screens)
            color = (255, 0, 0) if bbox[0] < 1920 else (0, 0, 255)
            return Image.new("RGB", (bbox[2] - bbox[0], bbox[3] - bbox[1]), color)

        with patch("app.services.image_capture.sys.platform", "win32"), patch(
            "app.services.image_capture.ImageGrab.grab", side_effect=fake_grab
        ):
            png_bytes = ScreenCaptureService.capture_bbox_png_bytes_threadsafe(
                (1800, 0, 2100, 100),
                capture_plan=plan,
            )

        image = Image.open(io.BytesIO(png_bytes))
        image.load()

        self.assertEqual(image.size, (390, 150))
        self.assertEqual(image.getpixel((10, 10)), (255, 0, 0))
        self.assertEqual(image.getpixel((130, 10)), (0, 0, 255))
        self.assertEqual(image.getpixel((10, 120)), (0, 0, 0))

    def test_capture_bbox_png_bytes_threadsafe_falls_back_to_direct_grab_outside_windows(self):
        grabbed = Image.new("RGB", (20, 30), (12, 34, 56))

        with patch("app.services.image_capture.sys.platform", "linux"), patch(
            "app.services.image_capture.ImageGrab.grab", return_value=grabbed
        ) as mock_grab:
            png_bytes = ScreenCaptureService.capture_bbox_png_bytes_threadsafe((10, 20, 30, 50))

        mock_grab.assert_called_once_with(bbox=(10, 20, 30, 50), all_screens=True)
        image = Image.open(io.BytesIO(png_bytes))
        image.load()
        self.assertEqual(image.size, (20, 30))
        self.assertEqual(image.getpixel((0, 0)), (12, 34, 56))


if __name__ == "__main__":
    unittest.main()
