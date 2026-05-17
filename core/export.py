"""Export helpers for annotated images and CSV reports."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import cv2
import numpy as np
import pandas as pd

from models.result import AnalysisResult


def draw_annotations(image: np.ndarray, colonies: list, plate=None) -> np.ndarray:
    """Return an RGB image with plate and colony overlays drawn on top."""
    annotated = image.copy()

    if plate is not None:
        color = (80, 180, 255) if plate.detected else (160, 160, 160)
        cv2.circle(
            annotated,
            (int(round(plate.center_x)), int(round(plate.center_y))),
            int(round(plate.radius)),
            color,
            2,
        )

    for colony in colonies:
        if colony.status == "removed":
            color = (255, 90, 90)
        elif colony.status in {"manual_added", "annotation"}:
            color = (80, 220, 120)
        else:
            color = (255, 220, 40)
        center = (int(round(colony.center_x)), int(round(colony.center_y)))
        radius = max(4, int(round(colony.radius_estimate)))
        cv2.circle(annotated, center, radius, color, 2)
        cv2.putText(
            annotated,
            str(colony.id),
            (center[0] + radius + 2, center[1]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            color,
            1,
            cv2.LINE_AA,
        )
    return annotated


def save_annotated_image(
    image: np.ndarray,
    colonies: list,
    plate,
    output_dir: Union[str, Path] = "outputs/annotated",
    stem: str = "colonyvision_result",
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    annotated = draw_annotations(image, colonies, plate)
    file_path = output_path / f"{stem}_annotated.png"
    bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
    if not cv2.imwrite(str(file_path), bgr):
        raise OSError(f"Could not write annotated image to {file_path}")
    return file_path


def save_csv_report(
    colonies: list,
    output_dir: Union[str, Path] = "outputs/reports",
    stem: str = "colonyvision_result",
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "colony_id": colony.id,
            "center_x": round(colony.center_x, 2),
            "center_y": round(colony.center_y, 2),
            "area": round(colony.area, 2),
            "radius_estimate": round(colony.radius_estimate, 2),
            "circularity": round(colony.circularity, 4),
            "eccentricity": round(colony.eccentricity, 4),
            "solidity": round(colony.solidity, 4),
            "detection_status": colony.status,
            "artifact_class": colony.artifact_class,
        }
        for colony in colonies
    ]
    file_path = output_path / f"{stem}_report.csv"
    pd.DataFrame(rows).to_csv(file_path, index=False)
    return file_path


def save_analysis_csv_report(
    result: AnalysisResult,
    colonies: list,
    output_dir: Union[str, Path] = "outputs/reports",
    stem: str = "colonyvision_result",
) -> Path:
    """Save a dashboard report with sample-level and colony-level rows."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{stem}_analysis_report.csv"
    sample = result.sample
    sample_row = {
        "record_type": "sample",
        "sample_id": sample.sample_id,
        "media_type": sample.media_type,
        "dilution_factor": sample.dilution_factor,
        "plated_volume_ml": sample.plated_volume_ml,
        "ai_count": result.ai_count,
        "final_count": "" if result.final_count is None else result.final_count,
        "cfu_ml": result.cfu_ml,
        "confidence_score": result.confidence_score,
        "artifact_count": result.artifact_count,
        "status": result.status,
        "image_path": sample.image_path,
        "annotated_image_path": result.annotated_image_path or "",
        "created_at": result.created_at,
        "colony_id": "",
        "x": "",
        "y": "",
        "radius": "",
        "area": "",
        "circularity": "",
        "colony_status": "",
    }
    rows = [sample_row]
    for colony in colonies:
        rows.append(
            {
                "record_type": "colony",
                "sample_id": sample.sample_id,
                "media_type": "",
                "dilution_factor": "",
                "plated_volume_ml": "",
                "ai_count": "",
                "final_count": "",
                "cfu_ml": "",
                "confidence_score": "",
                "artifact_count": "",
                "status": result.status,
                "image_path": "",
                "annotated_image_path": "",
                "created_at": result.created_at,
                "colony_id": getattr(colony, "id", getattr(colony, "colony_id", "")),
                "x": round(getattr(colony, "center_x", getattr(colony, "x", 0.0)), 2),
                "y": round(getattr(colony, "center_y", getattr(colony, "y", 0.0)), 2),
                "radius": round(getattr(colony, "radius_estimate", getattr(colony, "radius", 0.0)), 2),
                "area": round(getattr(colony, "area", 0.0), 2),
                "circularity": round(getattr(colony, "circularity", 0.0), 4),
                "colony_status": getattr(colony, "status", "valid"),
            }
        )
    pd.DataFrame(rows).to_csv(file_path, index=False)
    return file_path
