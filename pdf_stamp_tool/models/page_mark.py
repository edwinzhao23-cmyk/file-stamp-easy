from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from .stamp_config import StampType


@dataclass
class PageMark:
    id: str = field(default_factory=lambda: uuid4().hex)
    stamp_type: StampType = StampType.NORMAL
    page_index: int = 0
    x_pt: float = 0.0
    y_pt: float = 0.0
    width_pt: float = 0.0
    height_pt: float = 0.0
    rotation_deg: float = 0.0
    image_config_id: str = ""
    selected: bool = False

    def contains(self, x_pt: float, y_pt: float) -> bool:
        return (
            self.x_pt <= x_pt <= self.x_pt + self.width_pt
            and self.y_pt <= y_pt <= self.y_pt + self.height_pt
        )
