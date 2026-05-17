from __future__ import annotations

from core.history import append_result_to_history, load_history
from models.result import AnalysisResult
from models.sample import Sample


def test_history_append_and_load(tmp_path):
    sample = Sample(
        sample_id="SMP-TEST",
        media_type="Tryptic Soy Agar (TSA)",
        dilution_factor=1000,
        plated_volume_ml=1.0,
        image_path="plate.jpg",
        created_at="2026-05-17T10:00:00",
    )
    result = AnalysisResult(
        sample=sample,
        colonies=[],
        ai_count=10,
        final_count=9,
        cfu_ml=9000,
        confidence_score=91.5,
        artifact_count=1,
        status="Approved",
        annotated_image_path="annotated.png",
        created_at="2026-05-17T10:05:00",
    )
    path = tmp_path / "history.csv"

    append_result_to_history(path, result)
    rows = load_history(path)

    assert len(rows) == 1
    assert rows[0]["sample_id"] == "SMP-TEST"
    assert rows[0]["final_count"] == 9
