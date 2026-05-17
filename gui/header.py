"""Top dashboard header."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from gui.logo_mark import LogoMark


class Header(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Header")
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(28, 20, 28, 14)
        self._layout.setSpacing(14)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("ColonyVision AI")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Minimal lab dashboard for plate-count review")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        profile = QLabel("System ready\nAK  Analyst")
        profile.setObjectName("ProfileLabel")
        profile.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._layout.addWidget(LogoMark(40))
        self._layout.addLayout(title_box)
        self._layout.addStretch(1)
        self._layout.addWidget(profile)

    def apply_zoom(self, zoom: float) -> None:
        self._layout.setContentsMargins(round(28 * zoom), round(20 * zoom), round(28 * zoom), round(14 * zoom))
        self._layout.setSpacing(round(14 * zoom))
