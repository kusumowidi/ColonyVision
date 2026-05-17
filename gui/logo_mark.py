"""Small vector logo mark inspired by the ColonyVision identity."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget


class LogoMark(QWidget):
    def __init__(self, size: int = 44, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = QRectF(3, 3, self.width() - 6, self.height() - 6)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor("#073763"))
        gradient.setColorAt(1, QColor("#00A6A6"))

        painter.setPen(QPen(QBrush(gradient), 4.5, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(QColor("#F4FBFC"))
        painter.drawEllipse(rect)

        painter.setPen(QPen(QColor("#BFE8EA"), 2))
        painter.drawEllipse(rect.adjusted(5, 5, -5, -5))

        center = QPointF(self.width() / 2, self.height() / 2)
        nodes = [
            QPointF(self.width() * 0.34, self.height() * 0.34),
            QPointF(self.width() * 0.66, self.height() * 0.34),
            QPointF(self.width() * 0.32, self.height() * 0.64),
            QPointF(self.width() * 0.68, self.height() * 0.62),
            QPointF(self.width() * 0.50, self.height() * 0.76),
        ]

        painter.setPen(QPen(QColor("#00A6A6"), 3, Qt.SolidLine, Qt.RoundCap))
        for node in nodes:
            painter.drawLine(center, node)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#009C9A"))
        painter.drawEllipse(center, 5.5, 5.5)
        for index, node in enumerate(nodes):
            radius = 4.0 if index % 2 else 5.0
            painter.drawEllipse(node, radius, radius)
