"""Main dashboard workflow page."""

from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core import Colony as CoreColony
from core import DetectionParams, DetectionResult, count_colonies
from core.cfu import calculate_cfu_ml, format_scientific
from core.confidence import calculate_heuristic_confidence
from core.dataset_annotations import has_sidecar_annotations, load_sidecar_annotation_result
from core.export import save_analysis_csv_report, save_annotated_image
from core.history import append_result_to_history, latest_history
from gui.history_table import HistoryTable
from gui.image_viewer import ImageViewer
from gui.result_cards import MetricCard
from models.colony import Colony as ReportColony
from models.result import AnalysisResult
from models.sample import Sample, create_default_sample

HISTORY_PATH = Path("outputs/history/results_history.csv")


class DetectionWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, image: np.ndarray, params: DetectionParams):
        super().__init__()
        self.image = image
        self.params = params

    def run(self) -> None:
        try:
            self.finished.emit(count_colonies(self.image, self.params))
        except Exception as exc:  # pragma: no cover - GUI worker path
            self.failed.emit(str(exc))


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image: Optional[np.ndarray] = None
        self.image_path: Optional[Path] = None
        self.result: Optional[DetectionResult] = None
        self.sample: Sample = create_default_sample()
        self.ai_count = 0
        self.final_count: Optional[int] = None
        self.status = "No Sample Loaded"
        self.edit_mode = False
        self.annotated_image_path: Optional[Path] = None
        self._thread: Optional[QThread] = None
        self._worker: Optional[DetectionWorker] = None

        self._build_ui()
        self._connect_signals()
        self.refresh_history()
        self._refresh_metrics()

    def _build_ui(self) -> None:
        self._page_layout = QVBoxLayout(self)
        self._page_layout.setContentsMargins(30, 12, 30, 30)
        self._page_layout.setSpacing(14)

        top_grid = QGridLayout()
        top_grid.setColumnStretch(0, 3)
        top_grid.setColumnStretch(1, 1)

        viewer_card = QFrame()
        viewer_card.setObjectName("Card")
        viewer_layout = QVBoxLayout(viewer_card)
        viewer_layout.setContentsMargins(18, 16, 18, 16)
        viewer_layout.setSpacing(12)
        viewer_header = QHBoxLayout()
        title = QLabel("Plate Analysis")
        title.setObjectName("SectionTitle")
        self.viewer_status = QLabel("Upload an image to begin")
        self.viewer_status.setObjectName("MutedLabel")
        viewer_header.addWidget(title)
        viewer_header.addStretch(1)
        viewer_header.addWidget(self.viewer_status)
        self.viewer = ImageViewer()
        legend = QLabel("Ctrl+scroll to zoom. Valid: teal  |  Artifact: amber  |  Merged: blue  |  Manual: green  |  Removed: red")
        legend.setObjectName("MutedLabel")
        viewer_layout.addLayout(viewer_header)
        viewer_layout.addWidget(self.viewer, 1)
        viewer_layout.addWidget(legend)

        right_panel = QVBoxLayout()
        self.ai_count_card = MetricCard("AI Colony Count", "0")
        self.confidence_card = MetricCard("Heuristic Confidence", "-", "Quality heuristic, not model probability")
        self.cfu_card = MetricCard("CFU/ml Result", "-")
        self.artifact_card = MetricCard("Artifact Flags", "0")
        self.status_card = MetricCard("Status", self.status)
        for card in [
            self.ai_count_card,
            self.confidence_card,
            self.cfu_card,
            self.artifact_card,
            self.status_card,
        ]:
            right_panel.addWidget(card)

        self.edit_button = QPushButton("Edit Count")
        self.edit_button.setObjectName("SecondaryButton")
        self.approve_button = QPushButton("Approve Result")
        self.approve_button.setObjectName("PrimaryButton")
        right_panel.addWidget(self.edit_button)
        right_panel.addWidget(self.approve_button)
        right_panel.addStretch(1)

        top_grid.addWidget(viewer_card, 0, 0)
        top_grid.addLayout(right_panel, 0, 1)

        metadata_card = self._build_metadata_card()
        history_card = QFrame()
        history_card.setObjectName("Card")
        history_layout = QVBoxLayout(history_card)
        history_layout.setContentsMargins(18, 16, 18, 16)
        history_layout.setSpacing(10)
        history_title = QLabel("Recent Results")
        history_title.setObjectName("SectionTitle")
        self.history_table = HistoryTable()
        history_layout.addWidget(history_title)
        history_layout.addWidget(self.history_table)

        self._page_layout.addWidget(self._build_workflow_strip())
        self._page_layout.addWidget(metadata_card)
        self._page_layout.addLayout(top_grid, 1)
        self._page_layout.addWidget(history_card)

    def apply_zoom(self, zoom: float) -> None:
        self._page_layout.setContentsMargins(round(30 * zoom), round(12 * zoom), round(30 * zoom), round(30 * zoom))
        self._page_layout.setSpacing(round(14 * zoom))

    def _build_workflow_strip(self) -> QFrame:
        card = QFrame()
        card.setObjectName("WorkflowCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        title = QLabel("Workflow")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        layout.addStretch(1)
        self.workflow_steps = []
        for text in ["Sample", "Image", "Analysis", "Review", "Approved"]:
            step = QLabel(text)
            step.setObjectName("StepPill")
            step.setProperty("active", False)
            self.workflow_steps.append(step)
            layout.addWidget(step)
        return card

    def _build_metadata_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("MetaCard")
        layout = QGridLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(8)

        self.sample_id_input = QLineEdit(self.sample.sample_id)
        self.media_type_input = QLineEdit(self.sample.media_type)
        self.dilution_input = QDoubleSpinBox()
        self.dilution_input.setRange(0.0001, 1_000_000_000)
        self.dilution_input.setDecimals(4)
        self.dilution_input.setValue(self.sample.dilution_factor)
        self.volume_input = QDoubleSpinBox()
        self.volume_input.setRange(0.0001, 10_000)
        self.volume_input.setDecimals(4)
        self.volume_input.setValue(self.sample.plated_volume_ml)

        self.min_area_input = QSpinBox()
        self.min_area_input.setRange(1, 500000)
        self.min_area_input.setValue(20)
        self.max_area_input = QSpinBox()
        self.max_area_input.setRange(1, 1000000)
        self.max_area_input.setValue(200000)

        self.upload_button = QPushButton("Upload Image")
        self.upload_button.setObjectName("PrimaryButton")
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setObjectName("PrimaryButton")
        self.reset_button = QPushButton("Reset View")
        self.reset_button.setObjectName("SecondaryButton")
        self.export_image_button = QPushButton("Export Image")
        self.export_image_button.setObjectName("SecondaryButton")
        self.export_report_button = QPushButton("Export Report")
        self.export_report_button.setObjectName("SecondaryButton")

        setup_title = QLabel("Sample Setup")
        setup_title.setObjectName("SectionTitle")
        setup_hint = QLabel("Enter sample metadata and tune basic detection limits before analysis.")
        setup_hint.setObjectName("MutedLabel")
        layout.addWidget(setup_title, 0, 0)
        layout.addWidget(setup_hint, 0, 1, 1, 2)

        fields = [
            ("Sample ID", self.sample_id_input),
            ("Media Type", self.media_type_input),
            ("Dilution Factor", self.dilution_input),
            ("Plated Volume (ml)", self.volume_input),
            ("Min Colony Size", self.min_area_input),
            ("Max Colony Size", self.max_area_input),
        ]
        for idx, (label, widget) in enumerate(fields):
            label_widget = QLabel(label)
            label_widget.setObjectName("FieldLabel")
            row = idx // 3 * 2 + 1
            layout.addWidget(label_widget, row, idx % 3)
            layout.addWidget(widget, row + 1, idx % 3)

        actions = QHBoxLayout()
        for button in [
            self.upload_button,
            self.run_button,
            self.reset_button,
            self.export_image_button,
            self.export_report_button,
        ]:
            actions.addWidget(button)
        layout.addLayout(actions, 5, 0, 1, 3)
        return card

    def _connect_signals(self) -> None:
        self.upload_button.clicked.connect(self.open_image)
        self.run_button.clicked.connect(self.run_analysis)
        self.reset_button.clicked.connect(self.reset_view)
        self.edit_button.clicked.connect(self.toggle_edit_mode)
        self.approve_button.clicked.connect(self.approve_result)
        self.export_image_button.clicked.connect(self.export_annotated)
        self.export_report_button.clicked.connect(self.export_report)
        self.viewer.leftClicked.connect(self.add_manual_colony)
        self.viewer.rightClicked.connect(self.remove_nearest_colony)
        for widget in [self.dilution_input, self.volume_input]:
            widget.valueChanged.connect(self._refresh_metrics)

    def open_image(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Petri Dish Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if not file_name:
            return
        bgr = cv2.imread(file_name, cv2.IMREAD_COLOR)
        if bgr is None:
            QMessageBox.warning(self, "Image Error", "Could not open the selected image.")
            return

        self.image = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        self.image_path = Path(file_name)
        self.sample = create_default_sample(str(self.image_path))
        self.sample_id_input.setText(self.sample.sample_id)
        self.media_type_input.setText(self.sample.media_type)
        self.result = None
        self.ai_count = 0
        self.final_count = None
        self.status = "Ready for Analysis"
        self.viewer.set_image(self.image)
        self.viewer_status.setText(self.image_path.name)
        self._refresh_metrics()

    def run_analysis(self) -> None:
        if self.image is None:
            QMessageBox.information(self, "No Image", "Upload an image before running analysis.")
            return
        if self._thread is not None:
            return
        self._read_sample_metadata()

        if self.image_path is not None and has_sidecar_annotations(self.image_path):
            self.result = load_sidecar_annotation_result(self.image, self.image_path)
            self._after_analysis("Loaded dataset sidecar annotations")
            return

        params = DetectionParams(
            sensitivity=55,
            min_area=self.min_area_input.value(),
            max_area=self.max_area_input.value(),
            watershed_enabled=True,
            watershed_strength=45,
            edge_margin=40,
            max_processing_size=1200,
            adaptive_min_area=True,
        )
        if params.min_area >= params.max_area:
            QMessageBox.warning(self, "Invalid Settings", "Minimum colony size must be less than maximum size.")
            return

        self.status = "Analysis Running"
        self._refresh_metrics()
        self.run_button.setEnabled(False)
        self._thread = QThread()
        self._worker = DetectionWorker(self.image, params)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_detection_finished)
        self._worker.failed.connect(self._on_detection_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    def reset_view(self) -> None:
        self.result = None
        self.ai_count = 0
        self.final_count = None
        self.status = "Ready for Analysis" if self.image is not None else "No Sample Loaded"
        self.edit_mode = False
        self.viewer.set_edit_enabled(False)
        self.viewer.reset_view()
        self.viewer.set_overlays([], None)
        self._refresh_metrics()

    def toggle_edit_mode(self) -> None:
        if self.result is None:
            QMessageBox.information(self, "No Result", "Run analysis before editing the count.")
            return
        self.edit_mode = not self.edit_mode
        self.viewer.set_edit_enabled(self.edit_mode)
        self.edit_button.setText("Finish Editing" if self.edit_mode else "Edit Count")
        if self.edit_mode:
            self.status = "Editing"
        elif self.status == "Editing":
            self.status = "Edited"
        self._refresh_metrics()

    def add_manual_colony(self, x: float, y: float) -> None:
        if not self.edit_mode or self.result is None:
            return
        radius = max(6.0, math.sqrt(self.min_area_input.value() / math.pi))
        self.result.colonies.append(
            CoreColony(
                id=len(self.result.colonies) + 1,
                center_x=x,
                center_y=y,
                area=math.pi * radius * radius,
                radius_estimate=radius,
                circularity=1.0,
                eccentricity=0.0,
                solidity=1.0,
                status="manual_added",
            )
        )
        self.status = "Edited"
        self._refresh_overlays_and_metrics()

    def remove_nearest_colony(self, x: float, y: float) -> None:
        if not self.edit_mode or self.result is None or not self.result.colonies:
            return
        active = [c for c in self.result.colonies if c.status != "removed"]
        if not active:
            return
        nearest = min(active, key=lambda c: math.hypot(c.center_x - x, c.center_y - y))
        distance = math.hypot(nearest.center_x - x, nearest.center_y - y)
        if distance <= max(18.0, nearest.radius_estimate * 2.0):
            nearest.status = "removed"
            self.status = "Edited"
            self._refresh_overlays_and_metrics()

    def approve_result(self) -> None:
        if self.result is None:
            QMessageBox.information(self, "No Result", "Run analysis before approving a result.")
            return
        self._read_sample_metadata()
        try:
            cfu_value = self._current_cfu()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid CFU Input", str(exc))
            return

        annotated_path = self._save_annotated_if_possible()
        analysis = self._build_analysis_result("Approved", cfu_value, annotated_path)
        append_result_to_history(HISTORY_PATH, analysis)
        self.annotated_image_path = annotated_path
        self.status = "Approved"
        self.refresh_history()
        self._refresh_metrics()

    def export_annotated(self) -> None:
        if self.result is None:
            QMessageBox.information(self, "No Result", "Run analysis before exporting.")
            return
        path = self._save_annotated_if_possible()
        self.annotated_image_path = path
        self.viewer_status.setText(f"Annotated image saved: {path}")

    def export_report(self) -> None:
        if self.result is None:
            QMessageBox.information(self, "No Result", "Run analysis before exporting.")
            return
        self._read_sample_metadata()
        try:
            cfu_value = self._current_cfu()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid CFU Input", str(exc))
            return
        analysis = self._build_analysis_result(self.status, cfu_value, self.annotated_image_path)
        path = save_analysis_csv_report(analysis, self.result.colonies, stem=self.sample.sample_id)
        self.viewer_status.setText(f"CSV report saved: {path}")

    def refresh_history(self) -> None:
        self.history_table.set_rows(latest_history(HISTORY_PATH))

    def _on_detection_finished(self, result: DetectionResult) -> None:
        self.result = result
        self._after_analysis("Analysis complete")

    def _on_detection_failed(self, message: str) -> None:
        QMessageBox.warning(self, "Detection Error", message)
        self.status = "Analysis Failed"
        self._refresh_metrics()

    def _cleanup_worker(self) -> None:
        self.run_button.setEnabled(True)
        self._worker = None
        self._thread = None

    def _after_analysis(self, message: str) -> None:
        if self.result is None:
            return
        self._classify_colony_statuses()
        self.ai_count = self._valid_count(include_manual=False)
        self.final_count = None
        self.status = "Pending Analyst Review"
        self.viewer_status.setText(message)
        self._refresh_overlays_and_metrics()

    def _classify_colony_statuses(self) -> None:
        if self.result is None:
            return
        active = [c for c in self.result.colonies if c.status != "removed"]
        areas = sorted(c.area for c in active)
        large_threshold = areas[int(len(areas) * 0.92)] if areas else float("inf")
        for colony in active:
            if colony.status in {"manual_added", "removed"}:
                continue
            if colony.status == "annotation":
                colony.status = "valid"
            elif colony.area >= large_threshold and len(areas) > 10:
                colony.status = "merged"
            elif colony.artifact_class != "colony" or colony.circularity < 0.35:
                colony.status = "artifact"
            else:
                colony.status = "valid"

    def _refresh_overlays_and_metrics(self) -> None:
        if self.result is None:
            return
        self.viewer.set_overlays(self.result.colonies, self.result.plate)
        if self.status in {"Edited", "Editing"}:
            self.final_count = self._valid_count(include_manual=True)
        self._refresh_metrics()

    def _refresh_metrics(self) -> None:
        count_for_cfu = self.final_count if self.final_count is not None else self.ai_count
        try:
            cfu_value = calculate_cfu_ml(count_for_cfu, self.dilution_input.value(), self.volume_input.value())
            cfu_text = format_scientific(cfu_value)
        except Exception:
            cfu_text = "Invalid volume"

        artifact_count = self._artifact_count()
        confidence = self._confidence_score()
        self.ai_count_card.set_value(str(self.ai_count))
        self.confidence_card.set_value(f"{confidence:.1f}%" if self.result is not None else "-")
        self.cfu_card.set_value(cfu_text)
        self.artifact_card.set_value(str(artifact_count))
        final_helper = f"Final count: {self.final_count}" if self.final_count is not None else "Final count pending review"
        self.status_card.set_value(self.status, final_helper)
        self._refresh_workflow()

    def _refresh_workflow(self) -> None:
        if not hasattr(self, "workflow_steps"):
            return
        active_index = 0
        if self.image is not None:
            active_index = 1
        if self.status == "Analysis Running":
            active_index = 2
        elif self.result is not None:
            active_index = 3
        if self.status == "Approved":
            active_index = 4

        for index, step in enumerate(self.workflow_steps):
            step.setProperty("active", index <= active_index)
            step.style().unpolish(step)
            step.style().polish(step)
            step.update()

    def _read_sample_metadata(self) -> None:
        image_path = str(self.image_path) if self.image_path else ""
        self.sample = Sample(
            sample_id=self.sample_id_input.text().strip() or create_default_sample().sample_id,
            media_type=self.media_type_input.text().strip() or "Tryptic Soy Agar (TSA)",
            dilution_factor=float(self.dilution_input.value()),
            plated_volume_ml=float(self.volume_input.value()),
            image_path=image_path,
            created_at=self.sample.created_at,
        )

    def _valid_count(self, include_manual: bool) -> int:
        if self.result is None:
            return 0
        valid_statuses = {"valid", "merged", "annotation"}
        if include_manual:
            valid_statuses.add("manual_added")
        return sum(1 for colony in self.result.colonies if colony.status in valid_statuses)

    def _artifact_count(self) -> int:
        if self.result is None:
            return 0
        return sum(1 for colony in self.result.colonies if colony.status in {"artifact", "merged"})

    def _confidence_score(self) -> float:
        if self.result is None or self.image is None:
            return 0.0
        gray = cv2.cvtColor(self.image, cv2.COLOR_RGB2GRAY)
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        total = len([c for c in self.result.colonies if c.status != "removed"])
        manual = len([c for c in self.result.colonies if c.status in {"manual_added", "removed"}])
        edge_count = self._edge_count()
        return calculate_heuristic_confidence(
            plate_detected=self.result.plate.detected,
            blur_score=blur_score,
            artifact_count=sum(1 for c in self.result.colonies if c.status == "artifact"),
            total_detections=total,
            merged_count=sum(1 for c in self.result.colonies if c.status == "merged"),
            edge_count=edge_count,
            manual_corrections=manual,
        )

    def _edge_count(self) -> int:
        if self.result is None:
            return 0
        plate = self.result.plate
        count = 0
        for colony in self.result.colonies:
            distance = math.hypot(colony.center_x - plate.center_x, colony.center_y - plate.center_y)
            if distance > plate.radius - 40:
                count += 1
        return count

    def _current_cfu(self) -> float:
        count = self.final_count if self.final_count is not None else self.ai_count
        return calculate_cfu_ml(count, self.dilution_input.value(), self.volume_input.value())

    def _save_annotated_if_possible(self) -> Optional[Path]:
        if self.image is None or self.result is None:
            return None
        return save_annotated_image(self.image, self.result.colonies, self.result.plate, stem=self.sample.sample_id)

    def _build_analysis_result(self, status: str, cfu_value: float, annotated_path: Optional[Path]) -> AnalysisResult:
        colonies = [
            ReportColony(
                colony_id=colony.id,
                x=colony.center_x,
                y=colony.center_y,
                radius=colony.radius_estimate,
                area=colony.area,
                circularity=colony.circularity,
                status=colony.status if colony.status != "annotation" else "valid",
            )
            for colony in (self.result.colonies if self.result else [])
        ]
        return AnalysisResult(
            sample=self.sample,
            colonies=colonies,
            ai_count=self.ai_count,
            final_count=self.final_count,
            cfu_ml=cfu_value,
            confidence_score=self._confidence_score(),
            artifact_count=self._artifact_count(),
            status=status,
            annotated_image_path=str(annotated_path) if annotated_path else None,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
