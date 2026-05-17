"""Colony segmentation utilities."""

from __future__ import annotations

import cv2
import numpy as np
from typing import Optional
from skimage import feature, filters, measure, segmentation


def segment_colonies(
    gray: np.ndarray,
    plate_mask: np.ndarray,
    sensitivity: int = 55,
    rgb_image: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Segment candidate colonies using thresholding plus optional color cues."""
    sensitivity = int(np.clip(sensitivity, 0, 100))
    masked_values = gray[plate_mask > 0]
    if masked_values.size == 0:
        return np.zeros_like(gray, dtype=np.uint8)

    otsu = filters.threshold_otsu(masked_values)
    offset = int((sensitivity - 50) * 0.9)

    # Most bright-field colony photos show colonies darker than agar. Combining
    # global and adaptive inverse thresholds makes the MVP tolerant of uneven light.
    dark_mask = (gray < np.clip(otsu + offset, 0, 255)).astype(np.uint8) * 255
    adaptive = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        51,
        max(2, 14 - sensitivity // 9),
    )
    combined = cv2.bitwise_or(dark_mask, adaptive)
    if rgb_image is not None:
        combined = _apply_colony_color_prior(combined, rgb_image, plate_mask, sensitivity)
    return cv2.bitwise_and(combined, combined, mask=plate_mask.astype(np.uint8))


def _apply_colony_color_prior(
    candidate_mask: np.ndarray,
    rgb_image: np.ndarray,
    plate_mask: np.ndarray,
    sensitivity: int,
) -> np.ndarray:
    """Suppress cool ink/label marks while preserving warm colony candidates.

    AGAR-like datasets often include blue-gray printed labels inside the dish.
    Those labels are dark enough to pass grayscale thresholding, but their LAB b
    and HSV hue differ strongly from yellow/brown bacterial colonies.
    """
    hsv = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
    hue = hsv[:, :, 0]
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    lab_b = lab[:, :, 2]

    plate_pixels = plate_mask > 0
    if not np.any(plate_pixels):
        return candidate_mask

    median_b = float(np.median(lab_b[plate_pixels]))
    sensitivity_offset = (sensitivity - 50) * 0.04

    warm_colony = (
        (lab_b > median_b + max(2.0, 5.0 - sensitivity_offset))
        & (saturation > max(8, 24 - sensitivity // 5))
        & (value > 35)
    )
    cool_ink = (
        (candidate_mask > 0)
        & (saturation > 12)
        & (lab_b < median_b - 2.0)
        & (((hue >= 75) & (hue <= 135)) | (value < 95))
    )

    combined = ((candidate_mask > 0) & ~cool_ink) | warm_colony
    return (combined.astype(np.uint8) * 255)


def clean_mask(mask: np.ndarray, min_object_size: int = 12) -> np.ndarray:
    """Remove speckle noise and close small gaps in candidate colonies."""
    binary = mask > 0
    binary = morphology_cleanup(binary, min_object_size)
    return (binary.astype(np.uint8) * 255)


def morphology_cleanup(binary: np.ndarray, min_object_size: int) -> np.ndarray:
    from skimage import morphology

    binary = morphology.remove_small_objects(binary, min_size=max(2, int(min_object_size)))
    binary = morphology.binary_opening(binary, morphology.disk(1))
    binary = morphology.binary_closing(binary, morphology.disk(2))
    binary = morphology.remove_small_holes(binary, area_threshold=max(8, int(min_object_size * 1.5)))
    return binary


def split_touching_colonies(mask: np.ndarray, watershed_strength: int = 45) -> np.ndarray:
    """Split merged colony blobs with distance transform and watershed."""
    binary = mask > 0
    if not np.any(binary):
        return np.zeros_like(mask, dtype=np.int32)

    distance = cv2.distanceTransform(binary.astype(np.uint8), cv2.DIST_L2, 5)
    min_distance = max(3, int(12 - np.clip(watershed_strength, 0, 100) / 12))
    coords = feature.peak_local_max(
        distance,
        min_distance=min_distance,
        labels=binary,
        exclude_border=False,
    )
    markers = np.zeros(distance.shape, dtype=np.int32)
    for idx, (row, col) in enumerate(coords, start=1):
        markers[row, col] = idx
    markers = measure.label(markers > 0)

    if markers.max() == 0:
        return measure.label(binary).astype(np.int32)

    labels = segmentation.watershed(-distance, markers, mask=binary)
    return labels.astype(np.int32)
