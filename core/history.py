"""Local CSV-backed analysis history."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from models.result import AnalysisResult

HISTORY_COLUMNS = [
    "sample_id",
    "media_type",
    "dilution_factor",
    "plated_volume_ml",
    "ai_count",
    "final_count",
    "cfu_ml",
    "confidence_score",
    "artifact_count",
    "status",
    "image_path",
    "annotated_image_path",
    "created_at",
]


def ensure_history_file(path: str | Path) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        pd.DataFrame(columns=HISTORY_COLUMNS).to_csv(file_path, index=False)


def load_history(path: str | Path) -> list[dict]:
    file_path = Path(path)
    ensure_history_file(file_path)
    return pd.read_csv(file_path).fillna("").to_dict(orient="records")


def append_result_to_history(path: str | Path, result: AnalysisResult) -> None:
    file_path = Path(path)
    ensure_history_file(file_path)
    existing = pd.read_csv(file_path)
    row = _result_to_row(result)
    if existing.empty:
        updated = pd.DataFrame([row], columns=HISTORY_COLUMNS)
    else:
        updated = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
    updated.to_csv(file_path, index=False)


def latest_history(path: str | Path, limit: int = 8) -> list[dict]:
    rows = load_history(path)
    return list(reversed(rows))[:limit]


def _result_to_row(result: AnalysisResult) -> dict:
    sample = result.sample
    return {
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
    }
