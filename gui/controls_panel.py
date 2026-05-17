"""Controls panel for detection settings and export actions."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ControlsPanel(QWidget):
    openImageRequested = Signal()
    runDetectionRequested = Signal()
    resetRequested = Signal()
    exportImageRequested = Signal()
    exportCsvRequested = Signal()
    parametersChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(310)
        self._build_ui()
        self._connect_signals()

    def parameters(self) -> dict:
        return {
            "sensitivity": self.sensitivity.value(),
            "min_area": self.min_area.value(),
            "max_area": self.max_area.value(),
            "watershed_enabled": self.watershed_enabled.isChecked(),
            "watershed_strength": self.watershed_strength.value(),
        }

    def set_count(self, count: int) -> None:
        self.count_label.setText(str(count))

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("ColonyVision AI")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Classical CV colony counting")
        subtitle.setObjectName("SubtitleLabel")

        self.open_button = QPushButton("Open Image")
        self.run_button = QPushButton("Run Detection")
        self.reset_button = QPushButton("Reset Detection")

        detection_group = QGroupBox("Detection Controls")
        form = QFormLayout(detection_group)
        self.sensitivity = _slider(0, 100, 55)
        self.min_area = _spinbox(1, 200000, 20)
        self.max_area = _spinbox(1, 500000, 5000)
        self.watershed_enabled = QCheckBox("Enable splitting")
        self.watershed_enabled.setChecked(True)
        self.watershed_strength = _slider(0, 100, 45)
        form.addRow("Sensitivity", self.sensitivity)
        form.addRow("Min size", self.min_area)
        form.addRow("Max size", self.max_area)
        form.addRow("Watershed", self.watershed_enabled)
        form.addRow("Split strength", self.watershed_strength)

        count_group = QFrame()
        count_group.setObjectName("CountCard")
        count_layout = QVBoxLayout(count_group)
        count_caption = QLabel("Final Count")
        count_caption.setObjectName("CaptionLabel")
        self.count_label = QLabel("0")
        self.count_label.setObjectName("CountLabel")
        count_layout.addWidget(count_caption)
        count_layout.addWidget(self.count_label)

        self.export_image_button = QPushButton("Export Annotated Image")
        self.export_csv_button = QPushButton("Export CSV Report")
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("StatusLabel")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(self.open_button)
        layout.addWidget(self.run_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(detection_group)
        layout.addWidget(count_group)
        layout.addWidget(self.export_image_button)
        layout.addWidget(self.export_csv_button)
        layout.addStretch(1)
        layout.addWidget(self.status_label)

        self.setStyleSheet(
            """
            QWidget { background: #f8fafc; color: #111827; font-size: 13px; }
            QPushButton {
                background: #1f2937; color: white; border: none; border-radius: 6px;
                padding: 10px 12px; font-weight: 600;
            }
            QPushButton:hover { background: #374151; }
            QPushButton:disabled { background: #cbd5e1; color: #64748b; }
            QGroupBox {
                border: 1px solid #d9e2ec; border-radius: 8px; margin-top: 12px;
                padding: 12px 8px 8px 8px; font-weight: 700;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            #TitleLabel { font-size: 22px; font-weight: 800; }
            #SubtitleLabel { color: #64748b; }
            #CountCard { background: white; border: 1px solid #d9e2ec; border-radius: 8px; }
            #CaptionLabel { color: #64748b; font-weight: 700; }
            #CountLabel { font-size: 42px; font-weight: 800; color: #0f766e; }
            #StatusLabel { color: #475569; }
            """
        )

    def _connect_signals(self) -> None:
        self.open_button.clicked.connect(self.openImageRequested)
        self.run_button.clicked.connect(self.runDetectionRequested)
        self.reset_button.clicked.connect(self.resetRequested)
        self.export_image_button.clicked.connect(self.exportImageRequested)
        self.export_csv_button.clicked.connect(self.exportCsvRequested)
        for widget in [self.sensitivity, self.min_area, self.max_area, self.watershed_strength]:
            widget.valueChanged.connect(self.parametersChanged)
        self.watershed_enabled.stateChanged.connect(self.parametersChanged)


def _slider(minimum: int, maximum: int, value: int) -> QSlider:
    slider = QSlider(Qt.Horizontal)
    slider.setRange(minimum, maximum)
    slider.setValue(value)
    return slider


def _spinbox(minimum: int, maximum: int, value: int) -> QSpinBox:
    spinbox = QSpinBox()
    spinbox.setRange(minimum, maximum)
    spinbox.setValue(value)
    return spinbox
