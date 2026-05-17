"""Helpers for labeled colony datasets with sidecar JSON annotations."""

from __future__ import annotations

import json
import math
from pathlib import Path

import cv2
import numpy as np

from .colony_counter import Colony, DetectionResult
from .plate_detection import create_plate_mask, detect_or_estimate_plate


def has_sidecar_annotations(image_path: Path) -> bool:
    json_path = image_path.with_suffix(".json")
    if not json_path.exists():
        return False
    try:
        data = json.loads(json_path.read_text())
    except json.JSONDecodeError:
        return False
    return bool(data.get("labels"))


def load_sidecar_annotation_result(image: np.ndarray, image_path: Path) -> DetectionResult:
    """Create a DetectionResult from dataset bounding-box annotations."""
    json_path = image_path.with_suffix(".json")
    data = json.loads(json_path.read_text())
    labels = data.get("labels", [])
    plate, mask = detect_or_estimate_plate(image)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    colonies = []
    for index, label in enumerate(labels, start=1):
        width = float(label["width"])
        height = float(label["height"])
        center_x = float(label["x"]) + width / 2.0
        center_y = float(label["y"]) + height / 2.0
        area = math.pi * (width / 2.0) * (height / 2.0)
        colonies.append(
            Colony(
                id=index,
                center_x=center_x,
                center_y=center_y,
                area=area,
                radius_estimate=(width + height) / 4.0,
                circularity=1.0,
                eccentricity=0.0 if abs(width - height) < 1e-6 else min(abs(width - height) / max(width, height), 0.99),
                solidity=1.0,
                status="annotation",
                artifact_class=str(label.get("class", "colony")),
            )
        )

    return DetectionResult(
        colonies=colonies,
        plate=plate,
        plate_mask=mask if mask is not None else create_plate_mask(image.shape, plate),
        colony_mask=np.zeros(gray.shape, dtype=np.uint8),
        processed_gray=gray,
        scale=1.0,
    )
