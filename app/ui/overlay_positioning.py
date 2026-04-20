from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QGuiApplication


def overlay_vertical_safe_margins(config) -> tuple[int, int]:
    margin = int(getattr(config, "margin", 18) or 18)
    default_top_margin = max(42, margin * 2)
    default_bottom_margin = max(16, margin + 6)
    top_margin = int(getattr(config, "overlay_auto_expand_top_margin", default_top_margin) or 0)
    bottom_margin = int(getattr(config, "overlay_auto_expand_bottom_margin", default_bottom_margin) or default_bottom_margin)
    top_margin = max(0, min(200, top_margin))
    bottom_margin = max(8, min(200, bottom_margin))
    return top_margin, bottom_margin


def get_screen_rect_for_point(point: QPoint) -> QRect:
    screen = QGuiApplication.screenAt(point) or QGuiApplication.primaryScreen()
    return screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)


def get_target_screen_rect(bbox) -> QRect:
    left, top, right, bottom = bbox
    center = QPoint(int((left + right) / 2), int((top + bottom) / 2))
    return get_screen_rect_for_point(center)


def clamp_rect_to_visible_screen(rect: QRect) -> QRect:
    if rect.width() <= 0 or rect.height() <= 0:
        return QRect(rect)
    screen_rect = get_screen_rect_for_point(rect.center())
    width = min(rect.width(), screen_rect.width())
    height = min(rect.height(), screen_rect.height())
    x = max(screen_rect.left(), min(rect.x(), screen_rect.right() - width + 1))
    y = max(screen_rect.top(), min(rect.y(), screen_rect.bottom() - height + 1))
    return QRect(int(x), int(y), int(width), int(height))


def clamp_overlay_size_to_screen(config, translation_overlay, screen_rect: QRect, text: str, width: int, height: int, *, render_markdown: bool = True) -> tuple[int, int]:
    margin = config.margin
    top_margin, bottom_margin = overlay_vertical_safe_margins(config)
    width = min(width, max(240, screen_rect.width() - margin * 2))
    available_height = max(220, screen_rect.height() - top_margin - bottom_margin)
    desired_height = translation_overlay.measure_content_height(text, width, render_markdown=render_markdown)
    height = max(height, desired_height)
    height = min(height, available_height)
    return int(width), int(height)


def preferred_overlay_width_for_bbox(config, bbox) -> int:
    left, _top, right, _bottom = bbox
    screen_rect = get_target_screen_rect(bbox)
    margin = config.margin
    screen_left = screen_rect.left()
    screen_right = screen_rect.right()
    left_space = max(240, left - screen_left - margin * 2)
    right_space = max(240, screen_right - right - margin * 2)
    return int(left_space if ((left + right) / 2) >= screen_rect.center().x() else right_space)


def fit_overlay_size(config, translation_overlay, bbox, text: str, width: int, height: int, *, render_markdown: bool = True) -> tuple[int, int]:
    left, top, right, bottom = bbox
    screen_rect = get_target_screen_rect(bbox)
    margin = config.margin
    screen_left = screen_rect.left()
    screen_top = screen_rect.top()
    screen_right = screen_rect.right()
    screen_bottom = screen_rect.bottom()

    if config.mode == "book_lr":
        preferred_width = preferred_overlay_width_for_bbox(config, bbox)
        width = min(width, preferred_width)
    else:
        top_margin, bottom_margin = overlay_vertical_safe_margins(config)
        top_space = max(200, top - screen_top - top_margin)
        bottom_space = max(200, screen_bottom - bottom - bottom_margin)
        preferred_height = bottom_space if ((top + bottom) / 2) < screen_rect.center().y() else top_space
        height = min(height, preferred_height)

    return clamp_overlay_size_to_screen(config, translation_overlay, screen_rect, text, width, height, render_markdown=render_markdown)


def compute_overlay_position(config, bbox, width: int, height: int) -> tuple[int, int]:
    left, top, right, bottom = bbox
    screen_rect = get_target_screen_rect(bbox)
    margin = config.margin
    soft_top_margin, soft_bottom_margin = overlay_vertical_safe_margins(config)
    screen_left = screen_rect.left()
    screen_top = screen_rect.top()
    screen_right = screen_rect.right()
    screen_bottom = screen_rect.bottom()
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2

    def clamp_x(value: int) -> int:
        return max(screen_left + margin, min(value, screen_right - width - margin + 1))

    def clamp_y(value: int) -> int:
        return max(screen_top + soft_top_margin, min(value, screen_bottom - height - soft_bottom_margin + 1))

    if config.mode == "book_lr":
        prefer_left = center_x >= screen_rect.center().x()
        preferred_x = left - width - margin if prefer_left else right + margin
        alternate_x = right + margin if prefer_left else left - width - margin
        if screen_left + margin <= preferred_x <= screen_right - width - margin + 1:
            x = preferred_x
        elif screen_left + margin <= alternate_x <= screen_right - width - margin + 1:
            x = alternate_x
        else:
            x = clamp_x(preferred_x)
        y = clamp_y(top + 12)
    else:
        prefer_below = center_y < screen_rect.center().y()
        preferred_y = bottom + margin if prefer_below else top - height - margin
        alternate_y = top - height - margin if prefer_below else bottom + margin
        if screen_top + soft_top_margin <= preferred_y <= screen_bottom - height - soft_bottom_margin + 1:
            y = preferred_y
        elif screen_top + soft_top_margin <= alternate_y <= screen_bottom - height - soft_bottom_margin + 1:
            y = alternate_y
        else:
            y = clamp_y(preferred_y)
        x = clamp_x(left)
    return int(x), int(y)


def compute_overlay_position_for_point(config, anchor_point: QPoint, width: int, height: int) -> tuple[int, int]:
    screen_rect = get_screen_rect_for_point(anchor_point)
    margin = config.margin
    soft_top_margin, soft_bottom_margin = overlay_vertical_safe_margins(config)

    def clamp_x(value: int) -> int:
        return max(screen_rect.left() + margin, min(value, screen_rect.right() - width - margin + 1))

    def clamp_y(value: int) -> int:
        return max(screen_rect.top() + soft_top_margin, min(value, screen_rect.bottom() - height - soft_bottom_margin + 1))

    desired_x = anchor_point.x() - width // 2
    desired_y = anchor_point.y() + max(18, margin)
    if desired_y > screen_rect.bottom() - height - soft_bottom_margin + 1:
        desired_y = anchor_point.y() - height - max(18, margin)
    return int(clamp_x(desired_x)), int(clamp_y(desired_y))
