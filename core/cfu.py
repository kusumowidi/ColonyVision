"""CFU/ml calculations for plate-count workflows."""

from __future__ import annotations

import math


def calculate_cfu_ml(count: int, dilution_factor: float, plated_volume_ml: float) -> float:
    if plated_volume_ml <= 0:
        raise ValueError("plated_volume_ml must be greater than zero")
    return float(count) * float(dilution_factor) / float(plated_volume_ml)


def format_scientific(value: float) -> str:
    if value == 0:
        return "0"
    exponent = int(math.floor(math.log10(abs(value))))
    mantissa = value / (10**exponent)
    return f"{mantissa:.2f} x 10^{exponent}"
