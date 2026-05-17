"""Interactive image viewer with colony overlays."""

from __future__ import annotations

import math
from typing import Optional, Tuple

import numpy as np
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import QWidget


class ImageViewer(QWidget):
    leftClicked = Signal(float, float)
    rightClicked = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(720, 500)
        self.setMouseTracking(True)
        self.setStyleSheet("background: #F8FCFC; border: 1px solid #DDECEF; border-radius: 8px;")
        self._image: Optional[np.ndarray] = None
        self._pixmap: Optional[QPixmap] = None
        self._colonies = []
        self._plate = None
        self._draw_rect = None
        self._edit_enabled = False
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0

    def set_image(self, image: Optional[np.ndarray]) -> None:
        self._image = image
        self._pixmap = _rgb_array_to_pixmap(image) if image is not None else None
        self._colonies = []
        self._plate = None
        self.reset_view()
        self.update()

    def set_overlays(self, colonies: list, plate=None) -> None:
        self._colonies = colonies or []
        self._plate = plate
        self.update()

    def set_edit_enabled(self, enabled: bool) -> None:
        self._edit_enabled = enabled
        self.setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)

    def reset_view(self) -> None:
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self.update()

    def paintEvent(self, event):  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#F8FCFC"))

        if self._pixmap is None:
            painter.setPen(QColor("#6B8793"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Open a Petri dish image to begin")
            return

        target_width, target_height = self._scaled_size()
        scaled = self._pixmap.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.width() - scaled.width()) / 2 + self._pan_x
        y = (self.height() - scaled.height()) / 2 + self._pan_y
        self._draw_rect = (x, y, scaled.width(), scaled.height())
        painter.drawPixmap(int(x), int(y), scaled)

        scale_x = scaled.width() / self._pixmap.width()
        scale_y = scaled.height() / self._pixmap.height()
        self._draw_plate(painter, x, y, scale_x, scale_y)
        self._draw_colonies(painter, x, y, scale_x, scale_y)

    def mousePressEvent(self, event: QMouseEvent):  # noqa: N802 - Qt override
        coords = self._widget_to_image(event.position())
        if coords is None:
            return
        image_x, image_y = coords
        if event.button() == Qt.LeftButton:
            self.leftClicked.emit(image_x, image_y)
        elif event.button() == Qt.RightButton:
            self.rightClicked.emit(image_x, image_y)

    def wheelEvent(self, event: QWheelEvent):  # noqa: N802 - Qt override
        if self._pixmap is None or not (event.modifiers() & Qt.ControlModifier):
            event.ignore()
            return

        old_coords = self._widget_to_image(event.position())
        direction = event.angleDelta().y()
        if direction == 0:
            event.accept()
            return

        factor = 1.15 if direction > 0 else 1.0 / 1.15
        self._zoom = max(0.25, min(8.0, self._zoom * factor))

        if old_coords is not None:
            self._pan_to_keep_image_point_under_cursor(old_coords, event.position())
        self._clamp_pan()
        self.update()
        event.accept()

    def _draw_plate(self, painter: QPainter, x: float, y: float, sx: float, sy: float) -> None:
        if self._plate is None:
            return
        color = QColor("#38bdf8") if self._plate.detected else QColor("#9ca3af")
        painter.setPen(QPen(color, 2))
        cx = x + self._plate.center_x * sx
        cy = y + self._plate.center_y * sy
        radius = self._plate.radius * sx
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

    def _draw_colonies(self, painter: QPainter, x: float, y: float, sx: float, sy: float) -> None:
        for colony in self._colonies:
            status = getattr(colony, "status", "valid")
            if status == "removed":
                color = QColor("#ef4444")
            elif status == "artifact":
                color = QColor("#f59e0b")
            elif status == "merged":
                color = QColor("#3b82f6")
            elif status in {"manual_added", "annotation"}:
                color = QColor("#22c55e")
            else:
                color = QColor("#009c9a")
            painter.setPen(QPen(color, 2))
            image_x = getattr(colony, "center_x", getattr(colony, "x", 0.0))
            image_y = getattr(colony, "center_y", getattr(colony, "y", 0.0))
            image_radius = getattr(colony, "radius_estimate", getattr(colony, "radius", 5.0))
            colony_id = getattr(colony, "id", getattr(colony, "colony_id", ""))
            cx = x + image_x * sx
            cy = y + image_y * sy
            radius = max(5.0, image_radius * sx)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)
            if status == "removed":
                painter.drawLine(QPointF(cx - radius, cy - radius), QPointF(cx + radius, cy + radius))
                painter.drawLine(QPointF(cx - radius, cy + radius), QPointF(cx + radius, cy - radius))
            painter.drawText(int(cx + radius + 3), int(cy), str(colony_id))

    def _widget_to_image(self, point: QPointF) -> Optional[Tuple[float, float]]:
        if self._pixmap is None or self._draw_rect is None:
            return None
        x, y, width, height = self._draw_rect
        if not (x <= point.x() <= x + width and y <= point.y() <= y + height):
            return None
        image_x = (point.x() - x) * self._pixmap.width() / width
        image_y = (point.y() - y) * self._pixmap.height() / height
        if not (math.isfinite(image_x) and math.isfinite(image_y)):
            return None
        return image_x, image_y

    def _scaled_size(self) -> Tuple[int, int]:
        if self._pixmap is None:
            return (0, 0)
        fit_scale = min(self.width() / self._pixmap.width(), self.height() / self._pixmap.height())
        scale = max(0.01, fit_scale * self._zoom)
        return (max(1, int(self._pixmap.width() * scale)), max(1, int(self._pixmap.height() * scale)))

    def _pan_to_keep_image_point_under_cursor(self, image_coords: Tuple[float, float], cursor: QPointF) -> None:
        if self._pixmap is None:
            return
        target_width, target_height = self._scaled_size()
        scale_x = target_width / self._pixmap.width()
        scale_y = target_height / self._pixmap.height()
        base_x = (self.width() - target_width) / 2
        base_y = (self.height() - target_height) / 2
        self._pan_x = cursor.x() - base_x - image_coords[0] * scale_x
        self._pan_y = cursor.y() - base_y - image_coords[1] * scale_y

    def _clamp_pan(self) -> None:
        if self._pixmap is None:
            return
        target_width, target_height = self._scaled_size()
        if target_width <= self.width():
            self._pan_x = 0.0
        else:
            limit_x = (target_width - self.width()) / 2
            self._pan_x = max(-limit_x, min(limit_x, self._pan_x))

        if target_height <= self.height():
            self._pan_y = 0.0
        else:
            limit_y = (target_height - self.height()) / 2
            self._pan_y = max(-limit_y, min(limit_y, self._pan_y))


def _rgb_array_to_pixmap(image: np.ndarray) -> QPixmap:
    contiguous = np.ascontiguousarray(image)
    height, width, channels = contiguous.shape
    qimage = QImage(contiguous.data, width, height, channels * width, QImage.Format_RGB888)
    return QPixmap.fromImage(qimage.copy())
