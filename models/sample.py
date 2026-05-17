"""Sample metadata model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Sample:
    sample_id: str
    media_type: str
    dilution_factor: float
    plated_volume_ml: float
    image_path: str
    created_at: str


def create_default_sample(image_path: str = "") -> Sample:
    now = datetime.now()
    return Sample(
        sample_id=now.strftime("SMP-%Y%m%d-%H%M%S"),
        media_type="Tryptic Soy Agar (TSA)",
        dilution_factor=1000.0,
        plated_volume_ml=1.0,
        image_path=image_path,
        created_at=now.isoformat(timespec="seconds"),
    )
