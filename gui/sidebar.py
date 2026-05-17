"""Dashboard sidebar."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from gui.logo_mark import LogoMark


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 22, 18, 22)
        self._layout.setSpacing(7)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        brand_row.addWidget(LogoMark(42))
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand = QLabel("ColonyVision")
        brand.setObjectName("SidebarBrand")
        subtitle = QLabel("AI Lab Console")
        subtitle.setObjectName("SidebarSubtitle")
        brand_text.addWidget(brand)
        brand_text.addWidget(subtitle)
        brand_row.addLayout(brand_text)
        self._layout.addLayout(brand_row)
        self._layout.addSpacing(24)

        for item in ["Dashboard", "Samples", "Analysis", "Results", "History", "Reports", "Settings", "Help"]:
            button = QPushButton(item)
            button.setObjectName("SidebarButton")
            button.setProperty("active", item == "Dashboard")
            self._layout.addWidget(button)

        self._layout.addStretch(1)
        lab = QLabel("MicroLab 01\nAnalyst workspace")
        lab.setObjectName("SidebarFooter")
        self._layout.addWidget(lab)
        self.apply_zoom(1.0)

    def apply_zoom(self, zoom: float) -> None:
        self.setFixedWidth(round(236 * zoom))
        self._layout.setContentsMargins(round(18 * zoom), round(22 * zoom), round(18 * zoom), round(22 * zoom))
        self._layout.setSpacing(round(7 * zoom))
