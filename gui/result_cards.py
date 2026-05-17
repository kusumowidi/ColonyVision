"""Reusable dashboard metric cards."""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class MetricCard(QFrame):
    def __init__(self, title: str, value: str = "-", helper: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(112)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(5)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("MetricTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        self.helper_label = QLabel(helper)
        self.helper_label.setObjectName("MetricHelper")
        self.helper_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.helper_label)

    def set_value(self, value: str, helper: Optional[str] = None) -> None:
        self.value_label.setText(value)
        if helper is not None:
            self.helper_label.setText(helper)
