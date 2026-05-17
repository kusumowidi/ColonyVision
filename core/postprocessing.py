"""Postprocessing and artifact filtering for colony candidates."""

from __future__ import annotations

import math
from typing import Iterable

from .plate_detection import Plate


def estimate_radius(area: float) -> float:
    return math.sqrt(max(area, 0.0) / math.pi)


def filter_colonies(
    colonies: Iterable,
    plate: Plate,
    min_area: float,
    max_area: float,
    min_circularity: float = 0.25,
    max_eccentricity: float = 0.97,
    min_solidity: float = 0.55,
    edge_margin: float = 8.0,
) -> list:
    """Filter colonies using geometric quality metrics."""
    colony_list = list(colonies)
    lab_b_values = [c.mean_lab_b for c in colony_list if getattr(c, "mean_lab_b", 0.0) > 0]
    median_candidate_b = sorted(lab_b_values)[len(lab_b_values) // 2] if lab_b_values else 0.0
    filtered = []
    for colony in colony_list:
        if colony.area < min_area or colony.area > max_area:
            continue
        if colony.circularity < min_circularity:
            continue
        if colony.eccentricity > max_eccentricity:
            continue
        if colony.solidity < min_solidity:
            continue

        dx = colony.center_x - plate.center_x
        dy = colony.center_y - plate.center_y
        distance_from_center = math.hypot(dx, dy)
        if distance_from_center > plate.radius - edge_margin:
            continue
        if is_likely_label_or_ink(colony, median_candidate_b):
            continue

        colony.artifact_class = classify_possible_artifact(colony)
        filtered.append(colony)
    return filtered


def is_likely_label_or_ink(colony, median_candidate_b: float) -> bool:
    """Reject cool blue/gray printed labels that mimic small round colonies."""
    hue = getattr(colony, "mean_hue", 0.0)
    saturation = getattr(colony, "mean_saturation", 0.0)
    lab_b = getattr(colony, "mean_lab_b", 0.0)
    if lab_b <= 0:
        return False

    cool_hue = 75.0 <= hue <= 135.0
    much_cooler_than_colonies = median_candidate_b > 0 and lab_b < median_candidate_b - 4.0
    if saturation > 12.0 and cool_hue and much_cooler_than_colonies:
        return True
    if saturation > 20.0 and lab_b < 124.0 and colony.area < 500.0:
        return True
    return False


def classify_possible_artifact(colony) -> str:
    if colony.circularity < 0.4:
        return "irregular"
    if colony.solidity < 0.75:
        return "porous_or_edge"
    return "colony"
