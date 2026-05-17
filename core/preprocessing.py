"""Image preprocessing utilities for colony detection."""

from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np


def resize_image(image: np.ndarray, max_size: int = 1600) -> Tuple[np.ndarray, float]:
    """Resize image to a practical processing size while preserving aspect ratio."""
    height, width = image.shape[:2]
    largest = max(height, width)
    if largest <= max_size:
        return image.copy(), 1.0

    scale = max_size / float(largest)
    resized = cv2.resize(
        image,
        (int(width * scale), int(height * scale)),
        interpolation=cv2.INTER_AREA,
    )
    return resized, scale


def denoise_image(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Reduce small sensor noise and agar texture."""
    if kernel_size % 2 == 0:
        kernel_size += 1
    return cv2.medianBlur(image, kernel_size)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Enhance local contrast using LAB luminance CLAHE."""
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l_channel)
    enhanced_lab = cv2.merge((enhanced_l, a_channel, b_channel))
    return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)


def normalize_lighting(gray: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
    """Flatten slow illumination gradients with background estimation.

    Colonies are usually smaller than the dish-scale lighting variation, so a large
    blur gives a useful background model that can be subtracted from the image.
    """
    if gray.ndim != 2:
        raise ValueError("normalize_lighting expects a grayscale image")

    background = cv2.GaussianBlur(gray, (0, 0), sigmaX=35, sigmaY=35)
    normalized = cv2.addWeighted(gray, 1.45, background, -0.45, 0)
    normalized = cv2.normalize(normalized, None, 0, 255, cv2.NORM_MINMAX)
    normalized = normalized.astype(np.uint8)

    if mask is not None:
        normalized = cv2.bitwise_and(normalized, normalized, mask=mask.astype(np.uint8))
    return normalized


def prepare_grayscale(image: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
    """Create a contrast-enhanced grayscale image for segmentation."""
    denoised = denoise_image(image)
    enhanced = enhance_contrast(denoised)
    gray = cv2.cvtColor(enhanced, cv2.COLOR_RGB2GRAY)
    return normalize_lighting(gray, mask)
