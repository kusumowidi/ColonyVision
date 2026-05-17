"""Analysis result model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from models.colony import Colony
from models.sample import Sample


@dataclass
class AnalysisResult:
    sample: Sample
    colonies: List[Colony]
    ai_count: int
    final_count: Optional[int]
    cfu_ml: float
    confidence_score: float
    artifact_count: int
    status: str
    annotated_image_path: Optional[str]
    created_at: str
