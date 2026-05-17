"""Colony counting pipeline and data models."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np
from skimage import measure

from .plate_detection import Plate, detect_or_estimate_plate
from .postprocessing import estimate_radius, filter_colonies
from .preprocessing import prepare_grayscale, resize_image
from .segmentation import clean_mask, segment_colonies, split_touching_colonies


@dataclass
class DetectionParams:
    sensitivity: int = 55
    min_area: int = 20
    max_area: int = 5000
    watershed_enabled: bool = True
    watershed_strength: int = 45
    edge_margin: int = 8
    max_processing_size: int = 1600
    adaptive_min_area: bool = True
    adaptive_min_area_percentile: int = 90


@dataclass
class Colony:
    id: int
    center_x: float
    center_y: float
    area: float
    radius_estimate: float
    circularity: float
    eccentricity: float
    solidity: float
    status: str = "auto"
    artifact_class: str = "colony"
    contour: list[tuple[int, int]] = field(default_factory=list)
    mean_hue: float = 0.0
    mean_saturation: float = 0.0
    mean_lab_b: float = 0.0


@dataclass
class DetectionResult:
    colonies: list[Colony]
    plate: Plate
    plate_mask: np.ndarray
    colony_mask: np.ndarray
    processed_gray: np.ndarray
    scale: float

    @property
    def count(self) -> int:
        return sum(1 for colony in self.colonies if colony.status != "removed")


def extract_colony_regions(labels: np.ndarray, scale: float = 1.0, source_rgb: Optional[np.ndarray] = None) -> list[Colony]:
    """Convert labeled regions into Colony records in original image coordinates."""
    colonies: list[Colony] = []
    hsv = cv2.cvtColor(source_rgb, cv2.COLOR_RGB2HSV) if source_rgb is not None else None
    lab = cv2.cvtColor(source_rgb, cv2.COLOR_RGB2LAB) if source_rgb is not None else None
    for region in measure.regionprops(labels):
        if region.area <= 0:
            continue

        perimeter = max(float(region.perimeter), 1.0)
        circularity = float(4.0 * math.pi * region.area / (perimeter * perimeter))
        center_y, center_x = region.centroid
        contour = _region_contour(region, labels)
        region_mask = labels == region.label
        mean_hue = float(np.mean(hsv[:, :, 0][region_mask])) if hsv is not None else 0.0
        mean_saturation = float(np.mean(hsv[:, :, 1][region_mask])) if hsv is not None else 0.0
        mean_lab_b = float(np.mean(lab[:, :, 2][region_mask])) if lab is not None else 0.0

        inv_scale = 1.0 / scale
        colonies.append(
            Colony(
                id=len(colonies) + 1,
                center_x=float(center_x * inv_scale),
                center_y=float(center_y * inv_scale),
                area=float(region.area * inv_scale * inv_scale),
                radius_estimate=float(estimate_radius(region.area) * inv_scale),
                circularity=float(min(circularity, 1.5)),
                eccentricity=float(region.eccentricity),
                solidity=float(region.solidity),
                contour=[(int(x * inv_scale), int(y * inv_scale)) for x, y in contour],
                mean_hue=mean_hue,
                mean_saturation=mean_saturation,
                mean_lab_b=mean_lab_b,
            )
        )
    return colonies


def count_colonies(image: np.ndarray, params: Optional[DetectionParams] = None) -> DetectionResult:
    """Run the full classical CV colony-counting pipeline."""
    if params is None:
        params = DetectionParams()
    if image is None or image.size == 0:
        raise ValueError("A non-empty RGB image is required")

    working, scale = resize_image(image, params.max_processing_size)
    plate, plate_mask = detect_or_estimate_plate(working)
    gray = prepare_grayscale(working, plate_mask)
    raw_mask = segment_colonies(gray, plate_mask, params.sensitivity, working)
    cleaned = clean_mask(raw_mask, params.min_area * scale * scale)

    if params.watershed_enabled:
        labels = split_touching_colonies(cleaned, params.watershed_strength)
    else:
        labels = measure.label(cleaned > 0).astype(np.int32)

    colonies = extract_colony_regions(labels, scale, working)
    original_plate = Plate(
        center_x=plate.center_x / scale,
        center_y=plate.center_y / scale,
        radius=plate.radius / scale,
        detected=plate.detected,
    )
    effective_min_area = _adaptive_min_area(colonies, params)
    filtered = filter_colonies(
        colonies,
        original_plate,
        min_area=effective_min_area,
        max_area=params.max_area,
        edge_margin=params.edge_margin,
    )
    _renumber(filtered)

    return DetectionResult(
        colonies=filtered,
        plate=original_plate,
        plate_mask=plate_mask,
        colony_mask=cleaned,
        processed_gray=gray,
        scale=scale,
    )


def _renumber(colonies: list[Colony]) -> None:
    for idx, colony in enumerate(colonies, start=1):
        colony.id = idx


def _adaptive_min_area(colonies: list[Colony], params: DetectionParams) -> float:
    """Raise tiny-object filtering automatically when many label-like dots exist."""
    if not params.adaptive_min_area or params.min_area > 150 or len(colonies) < 20:
        return float(params.min_area)

    areas = sorted(c.area for c in colonies if c.area > 0)
    if not areas:
        return float(params.min_area)

    percentile = int(np.clip(params.adaptive_min_area_percentile, 50, 95))
    percentile_area = areas[int((len(areas) - 1) * percentile / 100.0)]
    floor_area = 120.0

    return max(float(params.min_area), floor_area, float(percentile_area))


def _region_contour(region, labels: np.ndarray) -> list[tuple[int, int]]:
    min_row, min_col, max_row, max_col = region.bbox
    region_mask = (labels[min_row:max_row, min_col:max_col] == region.label).astype(np.uint8) * 255
    contours, _ = cv2.findContours(region_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []
    contour = max(contours, key=cv2.contourArea).reshape(-1, 2)
    return [(int(x + min_col), int(y + min_row)) for x, y in contour]
