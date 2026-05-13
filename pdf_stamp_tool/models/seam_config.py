from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .stamp_config import StampImageConfig, StampType


class SeamSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass
class SeamStampConfig:
    enabled: bool = False
    image_config: StampImageConfig = field(
        default_factory=lambda: StampImageConfig(
            stamp_type=StampType.SEAM,
            width_mm=120.0,
            height_mm=40.0,
        )
    )
    page_range_text: str = "全部"
    total_width_mm: float = 120.0
    total_height_mm: float = 40.0
    side: SeamSide = SeamSide.RIGHT
    edge_offset_mm: float = 0.0
    along_offset_mm: float = 80.0
