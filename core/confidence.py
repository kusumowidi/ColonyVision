"""Heuristic confidence scoring for ColonyVision AI.

This is a quality heuristic, not a trained model probability.
"""

from __future__ import annotations


def calculate_heuristic_confidence(
    plate_detected: bool,
    blur_score: float,
    artifact_count: int,
    total_detections: int,
    merged_count: int = 0,
    edge_count: int = 0,
    manual_corrections: int = 0,
) -> float:
    score = 100.0
    if not plate_detected:
        score -= 15.0

    # Variance of Laplacian: lower values are blurrier. The penalty saturates
    # below about 50, which is where microscope/phone images tend to be shaky.
    blur_penalty = max(0.0, min(20.0, (80.0 - blur_score) / 4.0))
    score -= blur_penalty

    if total_detections > 0:
        artifact_ratio = artifact_count / total_detections
        merged_ratio = merged_count / total_detections
        edge_ratio = edge_count / total_detections
        score -= min(20.0, artifact_ratio * 40.0)
        score -= min(15.0, merged_ratio * 30.0)
        score -= min(10.0, edge_ratio * 25.0)

    score -= min(15.0, manual_corrections * 2.0)
    return round(max(0.0, min(100.0, score)), 1)
