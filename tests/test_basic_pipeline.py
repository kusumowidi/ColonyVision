from __future__ import annotations

import numpy as np
import cv2
import pandas as pd

from core.colony_counter import Colony, DetectionParams, count_colonies
from core.export import save_csv_report


def synthetic_plate_image() -> np.ndarray:
    image = np.full((420, 420, 3), 235, dtype=np.uint8)
    cv2.circle(image, (210, 210), 180, (220, 220, 210), -1)
    cv2.circle(image, (210, 210), 181, (120, 120, 120), 3)
    for center, radius in [((150, 160), 10), ((210, 180), 8), ((260, 250), 13), ((170, 280), 7)]:
        cv2.circle(image, center, radius, (70, 70, 70), -1)
    return image


def synthetic_plate_with_label() -> np.ndarray:
    image = np.full((520, 520, 3), 224, dtype=np.uint8)
    cv2.circle(image, (260, 260), 230, (220, 222, 190), -1)
    cv2.circle(image, (260, 260), 232, (95, 95, 95), 3)

    for center in [(150, 180), (190, 210), (315, 240), (360, 320), (220, 360)]:
        cv2.circle(image, center, 12, (155, 135, 42), -1)

    for row in range(140, 380, 22):
        for col in range(250, 315, 14):
            cv2.circle(image, (col, row), 4, (45, 75, 85), -1)
    return image


def test_core_pipeline_detects_synthetic_colonies():
    result = count_colonies(
        synthetic_plate_image(),
        DetectionParams(sensitivity=65, min_area=30, max_area=1500, watershed_enabled=True),
    )
    assert result.count >= 3
    assert result.plate.radius > 100
    assert all(colony.area > 0 for colony in result.colonies)


def test_core_pipeline_rejects_blue_label_dots():
    result = count_colonies(
        synthetic_plate_with_label(),
        DetectionParams(sensitivity=65, min_area=30, max_area=1500, watershed_enabled=True),
    )
    label_like = [
        colony
        for colony in result.colonies
        if 240 <= colony.center_x <= 325 and 120 <= colony.center_y <= 400
    ]
    assert result.count >= 4
    assert len(label_like) <= 2


def test_csv_export_writes_required_columns(tmp_path):
    colonies = [
        Colony(
            id=1,
            center_x=10,
            center_y=20,
            area=100,
            radius_estimate=5.64,
            circularity=0.9,
            eccentricity=0.1,
            solidity=0.95,
            status="manual_added",
        )
    ]
    path = save_csv_report(colonies, output_dir=tmp_path, stem="test")
    data = pd.read_csv(path)
    assert list(data.columns) == [
        "colony_id",
        "center_x",
        "center_y",
        "area",
        "radius_estimate",
        "circularity",
        "eccentricity",
        "solidity",
        "detection_status",
        "artifact_class",
    ]
    assert data.loc[0, "detection_status"] == "manual_added"
