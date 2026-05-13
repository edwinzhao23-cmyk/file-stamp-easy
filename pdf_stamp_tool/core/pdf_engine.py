from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz

from core.exceptions import OutputPermissionError, PdfRenderError, UserFacingError
from models.page_mark import PageMark


@dataclass
class RenderedPage:
    image: object
    page_width_pt: float
    page_height_pt: float
    zoom: float


class PdfEngine:
    def __init__(self) -> None:
        self.document: fitz.Document | None = None
        self.path: Path | None = None

    @property
    def page_count(self) -> int:
        return self.document.page_count if self.document else 0

    def open(self, path: str | Path) -> None:
        self.close()
        self.path = Path(path)
        try:
            self.document = fitz.open(str(self.path))
        except Exception as exc:
            raise UserFacingError("无法打开 PDF 文件，请检查文件是否存在或是否损坏。") from exc

    def close(self) -> None:
        if self.document is not None:
            self.document.close()
        self.document = None
        self.path = None

    def page_size(self, page_index: int) -> tuple[float, float]:
        if self.document is None:
            return 0.0, 0.0
        page = self.document.load_page(page_index)
        rect = page.rect
        return rect.width, rect.height

    def render_page(self, page_index: int, zoom: float) -> RenderedPage:
        if self.document is None:
            raise UserFacingError("请先选择 PDF 文件。")
        try:
            from PySide6.QtGui import QImage

            page = self.document.load_page(page_index)
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = QImage(
                pixmap.samples,
                pixmap.width,
                pixmap.height,
                pixmap.stride,
                QImage.Format.Format_RGB888,
            ).copy()
            return RenderedPage(
                image=image,
                page_width_pt=page.rect.width,
                page_height_pt=page.rect.height,
                zoom=zoom,
            )
        except Exception as exc:
            raise PdfRenderError() from exc

    def export_stamped_pdf(
        self,
        output_path: str | Path,
        marks: list[PageMark],
        stamp_png_by_config_id: dict[str, bytes],
    ) -> None:
        if self.document is None or self.path is None:
            raise UserFacingError("请先选择 PDF 文件。")
        if not marks:
            raise UserFacingError("没有需要输出的印章标记。")

        output = Path(output_path)
        try:
            doc = fitz.open(str(self.path))
            for page_index in range(doc.page_count):
                page_marks = [mark for mark in marks if mark.page_index == page_index]
                if not page_marks:
                    continue
                page = doc.load_page(page_index)
                for mark in page_marks:
                    png_bytes = stamp_png_by_config_id.get(mark.image_config_id)
                    if not png_bytes:
                        raise UserFacingError("印章图片处理失败，无法写入 PDF。")
                    rect = fitz.Rect(
                        mark.x_pt,
                        mark.y_pt,
                        mark.x_pt + mark.width_pt,
                        mark.y_pt + mark.height_pt,
                    )
                    page.insert_image(rect, stream=png_bytes, keep_proportion=False, overlay=True)
            doc.save(str(output), garbage=4, deflate=True)
            doc.close()
        except PermissionError as exc:
            raise OutputPermissionError() from exc
        except Exception as exc:
            raise UserFacingError(f"PDF 输出失败：{exc}") from exc
