from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.app_state import ActiveMode
from models.page_mark import PageMark
from models.stamp_config import StampType


class PreviewToolbar(QFrame):
    mode_changed = Signal(ActiveMode)
    previous_clicked = Signal()
    next_clicked = Signal()
    page_submitted = Signal(int)
    zoom_in_clicked = Signal()
    zoom_out_clicked = Signal()
    fit_width_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.prev_btn = QPushButton("上一页")
        self.page_edit = QLineEdit("1")
        self.page_edit.setFixedWidth(64)
        self.total_label = QLabel("/ -")
        self.next_btn = QPushButton("下一页")

        self.zoom_out_btn = QPushButton("缩小")
        self.zoom_label = QLabel("100%")
        self.zoom_in_btn = QPushButton("放大")
        self.fit_btn = QPushButton("适合宽度")

        self.view_btn = QPushButton("查看")
        self.normal_btn = QPushButton("放公章")
        self.signature_btn = QPushButton("放签字章")

        self.view_btn.setCheckable(True)
        self.normal_btn.setCheckable(True)
        self.signature_btn.setCheckable(True)
        self.view_btn.setChecked(True)

        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self.view_btn)
        group.addButton(self.normal_btn)
        group.addButton(self.signature_btn)

        self.view_btn.clicked.connect(lambda: self.mode_changed.emit(ActiveMode.VIEW))
        self.normal_btn.clicked.connect(lambda: self.mode_changed.emit(ActiveMode.PLACE_NORMAL))
        self.signature_btn.clicked.connect(lambda: self.mode_changed.emit(ActiveMode.PLACE_SIGNATURE))
        self.prev_btn.clicked.connect(self.previous_clicked.emit)
        self.next_btn.clicked.connect(self.next_clicked.emit)
        self.zoom_in_btn.clicked.connect(self.zoom_in_clicked.emit)
        self.zoom_out_btn.clicked.connect(self.zoom_out_clicked.emit)
        self.fit_btn.clicked.connect(self.fit_width_clicked.emit)
        self.page_edit.returnPressed.connect(self._submit_page)

        for widget in (
            self.prev_btn,
            self.page_edit,
            self.total_label,
            self.next_btn,
            self.zoom_out_btn,
            self.zoom_label,
            self.zoom_in_btn,
            self.fit_btn,
            self.view_btn,
            self.normal_btn,
            self.signature_btn,
        ):
            layout.addWidget(widget)

        layout.addStretch(1)

    def _submit_page(self) -> None:
        try:
            page_number = int(self.page_edit.text())
        except ValueError:
            return
        self.page_submitted.emit(page_number - 1)

    def set_page_info(self, page_index: int, page_count: int) -> None:
        self.page_edit.setText(str(page_index + 1 if page_count else 0))
        self.total_label.setText(f"/ {page_count if page_count else '-'}")

    def set_zoom(self, zoom: float) -> None:
        self.zoom_label.setText(f"{round(zoom * 100)}%")


class PdfPageCanvas(QWidget):
    page_clicked = Signal(float, float)
    mark_selected = Signal(str)
    mark_moved = Signal(str, float, float)
    delete_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.pixmap: QPixmap | None = None
        self.zoom = 1.0
        self.page_width_pt = 0.0
        self.page_height_pt = 0.0
        self.marks: list[PageMark] = []
        self.stamp_pixmaps = {}
        self.selected_mark_id = ""
        self.drag_mark_id = ""
        self.drag_offset_pt = (0.0, 0.0)

    def set_page_image(self, image: QImage, page_width_pt: float, page_height_pt: float, zoom: float) -> None:
        self.pixmap = QPixmap.fromImage(image)
        self.page_width_pt = page_width_pt
        self.page_height_pt = page_height_pt
        self.zoom = zoom
        self.setFixedSize(self.pixmap.size())
        self.update()

    def set_marks(self, marks: list[PageMark], selected_mark_id: str = "", stamp_pixmaps=None) -> None:
        self.marks = marks
        self.selected_mark_id = selected_mark_id
        if stamp_pixmaps is not None:
            self.stamp_pixmaps = stamp_pixmaps
        self.update()

    def clear_page(self) -> None:
        self.pixmap = None
        self.page_width_pt = 0.0
        self.page_height_pt = 0.0
        self.marks = []
        self.selected_mark_id = ""
        self.setMinimumSize(640, 760)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

        if self.pixmap is None:
            painter.setPen(QColor("#6B7280"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "拖入或选择 PDF / Word 文件后，这里显示页面预览")
            return

        painter.drawPixmap(0, 0, self.pixmap)
        for mark in self.marks:
            self._draw_mark(painter, mark)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.pixmap is None or event.button() != Qt.MouseButton.LeftButton:
            return

        x_pt, y_pt = self._event_to_pt(event)
        hit = self._hit_test(x_pt, y_pt)
        if hit is not None:
            self.selected_mark_id = hit.id
            self.drag_mark_id = hit.id
            self.drag_offset_pt = (x_pt - hit.x_pt, y_pt - hit.y_pt)
            self.mark_selected.emit(hit.id)
            self.update()
            return

        self.page_clicked.emit(x_pt, y_pt)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.drag_mark_id:
            return
        x_pt, y_pt = self._event_to_pt(event)
        new_x = max(0.0, x_pt - self.drag_offset_pt[0])
        new_y = max(0.0, y_pt - self.drag_offset_pt[1])
        self.mark_moved.emit(self.drag_mark_id, new_x, new_y)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.drag_mark_id = ""

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Delete:
            self.delete_requested.emit()
            return
        super().keyPressEvent(event)

    def _event_to_pt(self, event: QMouseEvent) -> tuple[float, float]:
        return event.position().x() / self.zoom, event.position().y() / self.zoom

    def _hit_test(self, x_pt: float, y_pt: float) -> PageMark | None:
        for mark in reversed(self.marks):
            if mark.contains(x_pt, y_pt):
                return mark
        return None

    def _draw_mark(self, painter: QPainter, mark: PageMark) -> None:
        color = {
            StampType.NORMAL: QColor("#D71920"),
            StampType.SIGNATURE: QColor("#2563EB"),
            StampType.SEAM: QColor("#0D9488"),
        }[mark.stamp_type]

        rect = QRectF(
            mark.x_pt * self.zoom,
            mark.y_pt * self.zoom,
            mark.width_pt * self.zoom,
            mark.height_pt * self.zoom,
        )

        painter.setPen(QPen(color, 2 if mark.id != self.selected_mark_id else 3))
        pixmap = self.stamp_pixmaps.get(mark.image_config_id)
        if pixmap is not None and not pixmap.isNull():
            painter.drawPixmap(rect.toRect(), pixmap)
        else:
            fill = QColor(color)
            fill.setAlpha(42)
            painter.fillRect(rect, fill)
        painter.drawRect(rect)

        if pixmap is None or pixmap.isNull():
            label = "公章" if mark.stamp_type == StampType.NORMAL else "签字章"
            painter.drawText(rect.adjusted(4, 2, -4, -2), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, label)


class PdfPreviewWidget(QFrame):
    page_clicked = Signal(float, float)
    mark_selected = Signal(str)
    mark_moved = Signal(str, float, float)
    delete_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background:#E5E7EB;border:1px solid #D1D5DB;border-radius:8px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        self.canvas = PdfPageCanvas()
        self.canvas.page_clicked.connect(self.page_clicked.emit)
        self.canvas.mark_selected.connect(self.mark_selected.emit)
        self.canvas.mark_moved.connect(self.mark_moved.emit)
        self.canvas.delete_requested.connect(self.delete_requested.emit)
        layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_page_image(self, image: QImage, page_width_pt: float, page_height_pt: float, zoom: float) -> None:
        self.canvas.set_page_image(image, page_width_pt, page_height_pt, zoom)

    def set_marks(self, marks: list[PageMark], selected_mark_id: str = "", stamp_pixmaps=None) -> None:
        self.canvas.set_marks(marks, selected_mark_id, stamp_pixmaps)


class PreviewWorkspace(QWidget):
    mode_changed = Signal(ActiveMode)
    previous_clicked = Signal()
    next_clicked = Signal()
    page_submitted = Signal(int)
    zoom_in_clicked = Signal()
    zoom_out_clicked = Signal()
    fit_width_clicked = Signal()
    page_clicked = Signal(float, float)
    mark_selected = Signal(str)
    mark_moved = Signal(str, float, float)
    delete_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.toolbar = PreviewToolbar()
        self.toolbar.mode_changed.connect(self.mode_changed.emit)
        self.toolbar.previous_clicked.connect(self.previous_clicked.emit)
        self.toolbar.next_clicked.connect(self.next_clicked.emit)
        self.toolbar.page_submitted.connect(self.page_submitted.emit)
        self.toolbar.zoom_in_clicked.connect(self.zoom_in_clicked.emit)
        self.toolbar.zoom_out_clicked.connect(self.zoom_out_clicked.emit)
        self.toolbar.fit_width_clicked.connect(self.fit_width_clicked.emit)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview = PdfPreviewWidget()
        self.preview.page_clicked.connect(self.page_clicked.emit)
        self.preview.mark_selected.connect(self.mark_selected.emit)
        self.preview.mark_moved.connect(self.mark_moved.emit)
        self.preview.delete_requested.connect(self.delete_requested.emit)
        scroll.setWidget(self.preview)

        self.status_label = QLabel("当前页：-    普通章：0 个    签字章：0 个    坐标：-")
        self.status_label.setObjectName("MutedText")

        layout.addWidget(self.toolbar)
        layout.addWidget(scroll, 1)
        layout.addWidget(self.status_label)

    def set_page_image(self, image: QImage, page_width_pt: float, page_height_pt: float, zoom: float) -> None:
        self.preview.set_page_image(image, page_width_pt, page_height_pt, zoom)
        self.toolbar.set_zoom(zoom)

    def set_page_info(self, page_index: int, page_count: int) -> None:
        self.toolbar.set_page_info(page_index, page_count)

    def set_marks(self, marks: list[PageMark], selected_mark_id: str = "", stamp_pixmaps=None) -> None:
        self.preview.set_marks(marks, selected_mark_id, stamp_pixmaps)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)
