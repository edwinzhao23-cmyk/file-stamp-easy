from __future__ import annotations

PT_PER_MM = 72.0 / 25.4


def mm_to_pt(value_mm: float) -> float:
    return value_mm * PT_PER_MM


def pt_to_mm(value_pt: float) -> float:
    return value_pt / PT_PER_MM

