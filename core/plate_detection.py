"""Petri dish detection and mask creation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union

import cv2
import numpy as np


@dataclass
class Plate:
    center_x: float
    center_y: float
    radius: float
    detected: bool = True


def detect_plate_circle(image: np.ndarray) -> Optional[Plate]:
    """Detect the dominant circular Petri dish with Hough Circle Transform."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (9, 9), 2)
    height, width = gray.shape
    min_dim = min(width, height)

    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_dim * 0.5,
        param1=90,
        param2=28,
        minRadius=int(min_dim * 0.25),
        maxRadius=int(min_dim * 0.52),
    )
    if circles is None:
        return None

    candidates = np.round(circles[0, :]).astype(int)
    image_center = np.array([width / 2.0, height / 2.0])
    best = max(
        candidates,
        key=lambda c: c[2] - 0.002 * np.linalg.norm(np.array([c[0], c[1]]) - image_center),
    )
    return Plate(float(best[0]), float(best[1]), float(best[2]), True)


def fallback_plate(image: np.ndarray) -> Plate:
    """Use a conservative centered circle when plate detection is uncertain."""
    height, width = image.shape[:2]
    radius = min(width, height) * 0.48
    return Plate(width / 2.0, height / 2.0, radius, False)


def create_plate_mask(image_shape: Union[Tuple[int, int], Tuple[int, int, int]], plate: Plate) -> np.ndarray:
    """Create an 8-bit mask for the detected or estimated dish area."""
    height, width = image_shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.circle(
        mask,
        (int(round(plate.center_x)), int(round(plate.center_y))),
        int(round(plate.radius)),
        255,
        thickness=-1,
    )
    return mask


def detect_or_estimate_plate(image: np.ndarray) -> tuple[Plate, np.ndarray]:
    plate = detect_plate_circle(image)
    if plate is None:
        plate = fallback_plate(image)
    return plate, create_plate_mask(image.shape, plate)
