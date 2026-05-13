from __future__ import annotations

from io import BytesIO

from PIL import Image

from core.exceptions import InvalidSeamPagesError
from core.page_range import parse_page_range
from core.units import mm_to_pt
from models.page_mark import PageMark
from models.seam_config import SeamSide, SeamStampConfig
from models.stamp_config import StampType


def build_seam_marks(
    config: SeamStampConfig,
    page_count: int,
    page_sizes: dict[int, tuple[float, float]],
    image_config_id: str,
) -> list[PageMark]:
    pages = parse_page_range(config.page_range_text, page_count)
    if len(pages) < 2:
        raise InvalidSeamPagesError()

    total_width_pt = mm_to_pt(config.total_width_mm)
    total_height_pt = mm_to_pt(config.total_height_mm)
    slice_width_pt = total_width_pt / len(pages)
    edge_offset_pt = mm_to_pt(config.edge_offset_mm)
    along_offset_pt = mm_to_pt(config.along_offset_mm)

    marks: list[PageMark] = []
    for index, page_index in enumerate(pages):
        page_width, page_height = page_sizes[page_index]
        if config.side == SeamSide.LEFT:
            x_pt = edge_offset_pt
        else:
            x_pt = page_width - edge_offset_pt - slice_width_pt
        y_pt = min(max(0.0, along_offset_pt), max(0.0, page_height - total_height_pt))
        marks.append(
            PageMark(
                stamp_type=StampType.SEAM,
                page_index=page_index,
                x_pt=x_pt,
                y_pt=y_pt,
                width_pt=slice_width_pt,
                height_pt=total_height_pt,
                image_config_id=f"{image_config_id}:{index}",
            )
        )
    return marks


def split_seam_stamp_png(png_bytes: bytes, slice_count: int) -> dict[str, bytes]:
    if slice_count < 2:
        raise InvalidSeamPagesError()

    image = Image.open(BytesIO(png_bytes)).convert("RGBA")
    width, height = image.size
    result: dict[str, bytes] = {}
    for index in range(slice_count):
        left = round(index * width / slice_count)
        right = round((index + 1) * width / slice_count)
        slice_image = image.crop((left, 0, right, height))
        buffer = BytesIO()
        slice_image.save(buffer, format="PNG")
        result[str(index)] = buffer.getvalue()
    return result

