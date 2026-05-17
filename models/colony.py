"""Dashboard-level colony model."""

from __future__ import annotations

from dataclasses import dataclass

VALID_STATUSES = {"valid", "artifact", "merged", "manual_added", "removed"}


@dataclass
class Colony:
    colony_id: int
    x: float
    y: float
    radius: float
    area: float
    circularity: float
    status: str = "valid"

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Unsupported colony status: {self.status}")
