from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .page_mark import PageMark
from .seam_config import SeamStampConfig
from .stamp_config import StampImageConfig, StampType


class ActiveMode(str, Enum):
    VIEW = "view"
    PLACE_NORMAL = "place_normal"
    PLACE_SIGNATURE = "place_signature"


class WorkStatus(str, Enum):
    IDLE = "idle"
    LOADING_FILE = "loading_file"
    CONVERTING_WORD = "converting_word"
    RENDERING_PAGE = "rendering_page"
    EXPORTING = "exporting"
    DONE = "done"
    ERROR = "error"


@dataclass
class FileState:
    input_path: str = ""
    input_type: str = ""
    working_pdf_path: str = ""
    output_path: str = ""
    page_count: int = 0


@dataclass
class PreviewState:
    current_page_index: int = 0
    zoom_factor: float = 1.0
    zoom_mode: str = "fit_width"
    active_mode: ActiveMode = ActiveMode.VIEW
    selected_mark_id: str = ""


@dataclass
class UiState:
    is_busy: bool = False
    progress: int = 0
    current_message: str = "就绪"
    last_error: str = ""


@dataclass
class AppState:
    file: FileState = field(default_factory=FileState)
    preview: PreviewState = field(default_factory=PreviewState)
    ui: UiState = field(default_factory=UiState)
    normal_stamp: StampImageConfig = field(
        default_factory=lambda: StampImageConfig(stamp_type=StampType.NORMAL)
    )
    signature_stamp: StampImageConfig = field(
        default_factory=lambda: StampImageConfig(
            stamp_type=StampType.SIGNATURE,
            width_mm=35.0,
            height_mm=15.0,
        )
    )
    seam_stamp: SeamStampConfig = field(default_factory=SeamStampConfig)
    page_marks: list[PageMark] = field(default_factory=list)
    recent_files: list[str] = field(default_factory=list)
    recent_stamps: list[str] = field(default_factory=list)

    def marks_for_page(self, page_index: int) -> list[PageMark]:
        return [mark for mark in self.page_marks if mark.page_index == page_index]
