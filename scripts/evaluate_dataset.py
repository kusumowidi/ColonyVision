"""Evaluate ColonyVision AI on a labeled image folder.

Example:
    py scripts/evaluate_dataset.py "data/Microbial Colony dataset"
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.colony_counter import DetectionParams, count_colonies
from core.dataset_annotations import has_sidecar_annotations, load_sidecar_annotation_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate colony detection on a labeled dataset.")
    parser.add_argument("dataset", type=Path, help="Dataset root containing image/json pairs.")
    parser.add_argument("--output", type=Path, default=Path("outputs/reports/dataset_evaluation.csv"))
    parser.add_argument("--max-size", type=int, default=1200)
    parser.add_argument(
        "--use-sidecar-annotations",
        action="store_true",
        help="Use JSON labels as predictions when present. Useful to validate dataset annotations and GUI annotation mode.",
    )
    args = parser.parse_args()

    rows = evaluate_dataset(args.dataset, args.max_size, args.use_sidecar_annotations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output, index=False)

    scored = [row for row in rows if row["ground_truth_count"] >= 0]
    if scored:
        mae = sum(abs(row["count_error"]) for row in scored) / len(scored)
        mean_abs_percent = sum(row["absolute_percent_error"] for row in scored) / len(scored)
        print(f"Images scored: {len(scored)}")
        print(f"Mean absolute count error: {mae:.2f}")
        print(f"Mean absolute percent error: {mean_abs_percent:.2f}%")
    print(f"Saved report: {args.output}")
    return 0


def evaluate_dataset(dataset_root: Path, max_size: int, use_sidecar_annotations: bool = False) -> list[dict]:
    image_paths = sorted(
        path
        for path in dataset_root.rglob("*")
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    )
    rows = []
    params = DetectionParams(
        sensitivity=55,
        min_area=20,
        max_area=200000,
        watershed_enabled=True,
        watershed_strength=45,
        edge_margin=40,
        max_processing_size=max_size,
        adaptive_min_area=True,
    )

    for image_path in image_paths:
        json_path = image_path.with_suffix(".json")
        metadata = _load_metadata(json_path)
        bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if bgr is None:
            rows.append(_error_row(dataset_root, image_path, metadata, "could not read image"))
            continue

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        try:
            if use_sidecar_annotations and has_sidecar_annotations(image_path):
                result = load_sidecar_annotation_result(rgb, image_path)
                mode = "sidecar_annotation"
            else:
                result = count_colonies(rgb, params)
                mode = "cv_detector"
            predicted_count = result.count
            matched, precision, recall = _match_annotations(result.colonies, metadata.get("labels", []))
            gt_count = int(metadata.get("colonies_number", -1))
            error = predicted_count - gt_count if gt_count >= 0 else 0
            rows.append(
                {
                    "image": str(image_path.relative_to(dataset_root)),
                    "background": metadata.get("background", ""),
                    "classes": ",".join(metadata.get("classes", [])),
                    "ground_truth_count": gt_count,
                    "predicted_count": predicted_count,
                    "count_error": error,
                    "absolute_error": abs(error),
                    "absolute_percent_error": round(abs(error) / gt_count * 100.0, 2) if gt_count > 0 else 0.0,
                    "matched_annotations": matched,
                    "precision_by_box_center": round(precision, 4),
                    "recall_by_box_center": round(recall, 4),
                    "plate_detected": result.plate.detected,
                    "mode": mode,
                    "status": "ok",
                }
            )
        except Exception as exc:  # pragma: no cover - reporting path
            rows.append(_error_row(dataset_root, image_path, metadata, str(exc)))
    return rows


def _load_metadata(json_path: Path) -> dict:
    if not json_path.exists():
        return {"colonies_number": -1, "labels": []}
    return json.loads(json_path.read_text())


def _match_annotations(colonies, labels: list[dict]) -> tuple[int, float, float]:
    if not labels:
        return 0, 0.0, 0.0

    unmatched = set(range(len(labels)))
    matched = 0
    for colony in colonies:
        best_index = None
        best_distance = float("inf")
        for index in unmatched:
            label = labels[index]
            cx = label["x"] + label["width"] / 2.0
            cy = label["y"] + label["height"] / 2.0
            threshold = max(label["width"], label["height"], colony.radius_estimate * 2.5)
            distance = math.hypot(colony.center_x - cx, colony.center_y - cy)
            if distance <= threshold and distance < best_distance:
                best_index = index
                best_distance = distance
        if best_index is not None:
            unmatched.remove(best_index)
            matched += 1

    precision = matched / len(colonies) if colonies else 0.0
    recall = matched / len(labels) if labels else 0.0
    return matched, precision, recall


def _error_row(dataset_root: Path, image_path: Path, metadata: dict, message: str) -> dict:
    return {
        "image": str(image_path.relative_to(dataset_root)),
        "background": metadata.get("background", ""),
        "classes": ",".join(metadata.get("classes", [])),
        "ground_truth_count": int(metadata.get("colonies_number", -1)),
        "predicted_count": -1,
        "count_error": 0,
        "absolute_error": 0,
        "absolute_percent_error": 0.0,
        "matched_annotations": 0,
        "precision_by_box_center": 0.0,
        "recall_by_box_center": 0.0,
        "plate_detected": False,
        "mode": "",
        "status": f"error: {message}",
    }


if __name__ == "__main__":
    raise SystemExit(main())
