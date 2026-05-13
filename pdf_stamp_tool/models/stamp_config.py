from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4


class StampType(str, Enum):
    NORMAL = "normal"
    SIGNATURE = "signature"
    SEAM = "seam"


@dataclass
class StampImageConfig:
    id: str = field(default_factory=lambda: uuid4().hex)
    stamp_type: StampType = StampType.NORMAL
    image_path: str = ""
    cached_path: str = ""
    width_mm: float = 40.0
    height_mm: float = 40.0
    remove_white_bg: bool = True
    white_threshold: int = 245
    use_rembg: bool = False
    auto_trim: bool = True
    ink_color: str = "#D71920"
    opacity: float = 0.92
    mottled_strength: float = 0.03
    edge_soften: float = 0.12
    sharpen_strength: float = 0.35

    @property
    def source_path(self) -> Path | None:
        path = self.cached_path or self.image_path
        return Path(path) if path else None
