from __future__ import annotations

import pytest

from core.cfu import calculate_cfu_ml, format_scientific


def test_calculate_cfu_ml():
    assert calculate_cfu_ml(148, 1000, 1.0) == 148000.0
    assert calculate_cfu_ml(84, 100, 0.1) == 84000.0


def test_calculate_cfu_ml_rejects_zero_volume():
    with pytest.raises(ValueError):
        calculate_cfu_ml(10, 1000, 0)


def test_format_scientific():
    assert format_scientific(148000) == "1.48 x 10^5"
    assert format_scientific(0) == "0"
