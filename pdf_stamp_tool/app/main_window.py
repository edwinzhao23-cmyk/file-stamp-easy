from __future__ import annotations

from pathlib import Path
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.app_style import APP_QSS
from app.qt_image import pil_to_qpixmap
from app.widgets.file_panel import FilePanel
from app.widgets.log_panel import LogPanel
from app.widgets.page_mark_panel import PageMarkPanel
from app.widgets.pdf_preview import PreviewWorkspace
from app.widgets.process_panel import StampProcessPanel
from app.widgets.seam_panel import SeamPanel
from app.widgets.stamp_panel import StampPanel
from app.widgets.top_bar import TopBarWidget
from core.cache_manager import cache_stamp_image
from core.config_manager import ConfigManager
from core.exceptions import NoOutputFileError, NoStampModeSelectedError, UserFacingError
from core.pdf_engine import PdfEngine
from core.seam_stamp import build_seam_marks, split_seam_stamp_png
from core.stamp_processor import StampProcessor
from core.units import mm_to_pt
from core.word_converter import WordConverter
from models.app_state import AppState, ActiveMode
from models.page_mark import PageMark
from models.seam_config import SeamSide
from models.stamp_config import StampType


class MainWindow(QMainWindow):
    def __init__(self, app_root: Path, config_manager: ConfigManager) -> None:
        super().__init__()
        self.app_root = app_root
        self.config_manager = config_manager
        self.state = AppState()
        self.pdf_engine = PdfEngine()
        self.stamp_processor = StampProcessor()
        self.word_converter = WordConverter()
        self.processed_stamp_pixmaps = {}
        self.processed_stamp_pngs = {}

        self.setWindowTitle("文件盖章易")
        self.resize(1500, 950)
        self.setMinimumSize(1180, 760)
        self.setAcceptDrops(True)
        self.setStyleSheet(APP_QSS)

        self._build_ui()
        self._connect_signals()
        self._load_settings()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        self.top_bar = TopBarWidget()

        self.file_panel = FilePanel()
        self.normal_panel = StampPanel("普通公章", StampType.NORMAL)
        self.signature_panel = StampPanel("法人签字章", StampType.SIGNATURE)
        self.seam_panel = SeamPanel()
        self.process_panel = StampProcessPanel()
        self.page_mark_panel = PageMarkPanel()

        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        left_layout.addWidget(self.file_panel)
        left_layout.addWidget(self.normal_panel)
        left_layout.addWidget(self.signature_panel)
        left_layout.addWidget(self.seam_panel)
        left_layout.addWidget(self.process_panel)
        left_layout.addWidget(self.page_mark_panel)
        left_layout.addStretch(1)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(380)
        left_scroll.setMaximumWidth(460)
        left_scroll.setWidget(left_content)

        self.preview_workspace = PreviewWorkspace()

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_scroll)
        main_splitter.addWidget(self.preview_workspace)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([410, 1040])

        self.log_panel = LogPanel()

        root.addWidget(self.top_bar)
        root.addWidget(main_splitter, 1)
        root.addWidget(self.log_panel)

        self.setCentralWidget(central)

    def _connect_signals(self) -> None:
        self.top_bar.input_selected.connect(self._set_input_file)
        self.top_bar.output_selected.connect(self._set_output_file)
        self.top_bar.start_clicked.connect(self._start_placeholder_export)
        self.normal_panel.image_selected.connect(self._set_stamp_image)
        self.signature_panel.image_selected.connect(self._set_stamp_image)
        self.seam_panel.image_selected.connect(lambda path: self._set_stamp_image(path, StampType.SEAM))
        self.normal_panel.config_changed.connect(self._sync_stamp_config_from_ui)
        self.signature_panel.config_changed.connect(self._sync_stamp_config_from_ui)
        self.process_panel.target_combo.currentIndexChanged.connect(self._refresh_stamp_preview)
        self.process_panel.remove_bg_check.toggled.connect(self._sync_process_config_from_ui)
        self.process_panel.rembg_check.toggled.connect(self._sync_process_config_from_ui)
        self.process_panel.threshold_spin.valueChanged.connect(self._sync_process_config_from_ui)
        self.process_panel.opacity_spin.valueChanged.connect(self._sync_process_config_from_ui)
        self.process_panel.mottled_slider.valueChanged.connect(self._sync_process_config_from_ui)
        self.process_panel.edge_slider.valueChanged.connect(self._sync_process_config_from_ui)
        self.process_panel.sharpen_slider.valueChanged.connect(self._sync_process_config_from_ui)
        self.preview_workspace.mode_changed.connect(self._set_active_mode)
        self.preview_workspace.previous_clicked.connect(self._previous_page)
        self.preview_workspace.next_clicked.connect(self._next_page)
        self.preview_workspace.page_submitted.connect(self._go_to_page)
        self.preview_workspace.zoom_in_clicked.connect(self._zoom_in)
        self.preview_workspace.zoom_out_clicked.connect(self._zoom_out)
        self.preview_workspace.fit_width_clicked.connect(self._fit_width)
        self.preview_workspace.page_clicked.connect(self._handle_page_click)
        self.preview_workspace.mark_selected.connect(self._select_mark)
        self.preview_workspace.mark_moved.connect(self._move_mark)
        self.preview_workspace.delete_requested.connect(self._delete_selected_mark)

    def _set_input_file(self, path: str) -> None:
        self.state.file.input_path = path
        suffix = Path(path).suffix.lower()
        self.state.file.input_type = "word" if suffix in {".doc", ".docx"} else "pdf"
        self.file_panel.set_input_path(path)
        self.log_panel.add_log(f"已选择输入文件：{path}")
        self._set_default_output_path(path)
        if self.state.file.input_type == "pdf":
            self._open_pdf(path)
        else:
            self._convert_word_and_open(path)

    def _set_output_file(self, path: str) -> None:
        self.state.file.output_path = path
        self.file_panel.set_output_path(path)
        self.log_panel.add_log(f"已选择输出文件：{path}")
        self._save_settings()

    def _set_stamp_image(self, path: str, stamp_type: StampType) -> None:
        try:
            cached_path = cache_stamp_image(self.app_root, path)
        except OSError:
            cached_path = path

        if stamp_type == StampType.NORMAL:
            self.state.normal_stamp.image_path = path
            self.state.normal_stamp.cached_path = cached_path
            label = "普通公章"
            self.process_panel.target_combo.setCurrentIndex(0)
        elif stamp_type == StampType.SIGNATURE:
            self.state.signature_stamp.image_path = path
            self.state.signature_stamp.cached_path = cached_path
            label = "法人签字章"
            self.process_panel.target_combo.setCurrentIndex(1)
        else:
            self.state.seam_stamp.image_config.image_path = path
            self.state.seam_stamp.image_config.cached_path = cached_path
            label = "骑缝章"
            self.process_panel.target_combo.setCurrentIndex(2)
        self.log_panel.add_log(f"已选择{label}图片：{path}")
        self._refresh_stamp_preview()
        self._save_settings()

    def _sync_stamp_config_from_ui(self, stamp_type: StampType) -> None:
        if stamp_type == StampType.NORMAL:
            self.state.normal_stamp.width_mm = self.normal_panel.width_spin.value()
            self.state.normal_stamp.height_mm = self.normal_panel.height_spin.value()
        elif stamp_type == StampType.SIGNATURE:
            self.state.signature_stamp.width_mm = self.signature_panel.width_spin.value()
            self.state.signature_stamp.height_mm = self.signature_panel.height_spin.value()
        self._refresh_marks()

    def _sync_process_config_from_ui(self) -> None:
        config = self._current_process_config()
        config.remove_white_bg = self.process_panel.remove_bg_check.isChecked()
        config.use_rembg = self.process_panel.rembg_check.isChecked()
        config.white_threshold = self.process_panel.threshold_spin.value()
        config.opacity = self.process_panel.opacity_spin.value()
        config.mottled_strength = self.process_panel.mottled_slider.value() / 100.0
        config.edge_soften = self.process_panel.edge_slider.value() / 100.0
        config.sharpen_strength = self.process_panel.sharpen_slider.value() / 100.0
        self._refresh_stamp_preview()

    def _current_process_config(self):
        index = self.process_panel.target_combo.currentIndex()
        if index == 0:
            return self.state.normal_stamp
        if index == 1:
            return self.state.signature_stamp
        return self.state.seam_stamp.image_config

    def _refresh_stamp_preview(self) -> None:
        config = self._current_process_config()
        if not config.source_path:
            self.process_panel.set_preview_pixmap(None, "请先选择印章图片")
            return
        try:
            processed = self.stamp_processor.process(config)
            pixmap = pil_to_qpixmap(processed.image)
            self.processed_stamp_pixmaps[config.id] = pixmap
            self.processed_stamp_pngs[config.id] = processed.png_bytes
            self.process_panel.set_preview_pixmap(pixmap)
            if processed.warning:
                self.log_panel.add_log(processed.warning)
            self._refresh_marks()
        except UserFacingError as exc:
            self.process_panel.set_preview_pixmap(None, str(exc))
            self.log_panel.add_log(f"错误：{exc}")

    def _set_active_mode(self, mode: ActiveMode) -> None:
        self.state.preview.active_mode = mode
        mode_text = {
            ActiveMode.VIEW: "查看",
            ActiveMode.PLACE_NORMAL: "放置普通公章",
            ActiveMode.PLACE_SIGNATURE: "放置法人签字章",
        }[mode]
        self.log_panel.add_log(f"当前模式：{mode_text}")

    def _start_placeholder_export(self) -> None:
        try:
            self._export_pdf()
        except UserFacingError as exc:
            self.log_panel.add_log(f"错误：{exc}")

    def _export_pdf(self) -> None:
        typed_output = self.top_bar.output_edit.text().strip()
        if typed_output:
            self.state.file.output_path = typed_output
            self.file_panel.set_output_path(typed_output)

        if self.pdf_engine.page_count == 0:
            raise UserFacingError("请先选择 PDF 文件。")
        if not self.state.file.output_path:
            raise NoOutputFileError()

        enabled_types = set()
        if self.top_bar.normal_check.isChecked():
            enabled_types.add(StampType.NORMAL)
        if self.top_bar.signature_check.isChecked():
            enabled_types.add(StampType.SIGNATURE)
        seam_enabled = self.top_bar.seam_check.isChecked() or self.seam_panel.enabled_check.isChecked()

        if not enabled_types and not seam_enabled:
            raise NoStampModeSelectedError()

        marks = [mark for mark in self.state.page_marks if mark.stamp_type in enabled_types]
        self.log_panel.progress.setValue(10)
        self.log_panel.add_log("开始生成处理后的印章图片。")
        stamp_pngs = self._build_stamp_pngs_for_marks(marks)

        if seam_enabled:
            seam_marks, seam_pngs = self._build_seam_export_data()
            marks.extend(seam_marks)
            stamp_pngs.update(seam_pngs)

        if not marks:
            raise UserFacingError("没有可输出的印章标记，请先在页面上放置印章或启用骑缝章。")

        self.log_panel.progress.setValue(35)

        self.log_panel.add_log("开始写入 PDF。")
        self.pdf_engine.export_stamped_pdf(
            self.state.file.output_path,
            marks,
            stamp_pngs,
        )
        self.log_panel.progress.setValue(100)
        self.log_panel.add_log(f"盖章完成：{self.state.file.output_path}")
        self._save_settings()
        self._show_output_done_dialog()

    def _show_output_done_dialog(self) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("盖章完成")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText("PDF 盖章完成。")
        box.setInformativeText(self.state.file.output_path)
        open_folder = box.addButton("打开输出文件夹", QMessageBox.ButtonRole.ActionRole)
        box.addButton("继续盖章", QMessageBox.ButtonRole.AcceptRole)
        box.exec()
        if box.clickedButton() == open_folder:
            folder = str(Path(self.state.file.output_path).parent)
            os.startfile(folder)

    def _build_stamp_pngs_for_marks(self, marks: list[PageMark]) -> dict[str, bytes]:
        config_ids = {mark.image_config_id for mark in marks}
        configs = {
            self.state.normal_stamp.id: self.state.normal_stamp,
            self.state.signature_stamp.id: self.state.signature_stamp,
        }
        stamp_pngs: dict[str, bytes] = {}
        for config_id in config_ids:
            config = configs.get(config_id)
            if config is None:
                continue
            processed = self.stamp_processor.process(config)
            pixmap = pil_to_qpixmap(processed.image)
            self.processed_stamp_pixmaps[config_id] = pixmap
            self.processed_stamp_pngs[config_id] = processed.png_bytes
            stamp_pngs[config_id] = processed.png_bytes
            if processed.warning:
                self.log_panel.add_log(processed.warning)
        return stamp_pngs

    def _build_seam_export_data(self) -> tuple[list[PageMark], dict[str, bytes]]:
        self._sync_seam_config_from_ui()
        config = self.state.seam_stamp
        if not config.image_config.source_path:
            raise UserFacingError("请先选择骑缝章图片。")

        page_sizes = {
            page_index: self.pdf_engine.page_size(page_index)
            for page_index in range(self.pdf_engine.page_count)
        }
        base_processed = self.stamp_processor.process(config.image_config)
        preview_marks = build_seam_marks(
            config=config,
            page_count=self.pdf_engine.page_count,
            page_sizes=page_sizes,
            image_config_id=config.image_config.id,
        )
        slices = split_seam_stamp_png(base_processed.png_bytes, len(preview_marks))
        pngs = {
            f"{config.image_config.id}:{index}": slices[str(index)]
            for index in range(len(preview_marks))
        }
        self.log_panel.add_log(f"已生成骑缝章切片：{len(preview_marks)} 页。")
        return preview_marks, pngs

    def _sync_seam_config_from_ui(self) -> None:
        config = self.state.seam_stamp
        config.enabled = self.seam_panel.enabled_check.isChecked()
        config.page_range_text = self.seam_panel.page_range_edit.text()
        config.side = SeamSide.RIGHT if self.seam_panel.side_combo.currentText() == "右侧" else SeamSide.LEFT
        config.total_width_mm = self.seam_panel.total_width_spin.value()
        config.total_height_mm = self.seam_panel.total_height_spin.value()
        config.edge_offset_mm = self.seam_panel.edge_offset_spin.value()
        config.along_offset_mm = self.seam_panel.along_offset_spin.value()

    def _set_default_output_path(self, input_path: str) -> None:
        path = Path(input_path)
        output = str(path.with_name(f"{path.stem}_已盖章.pdf"))
        self.state.file.output_path = output
        self.top_bar.output_edit.setText(output)
        self.file_panel.set_output_path(output)
        self._save_settings()

    def _open_pdf(self, path: str) -> None:
        try:
            self.pdf_engine.open(path)
            self.state.file.working_pdf_path = path
            self.state.file.page_count = self.pdf_engine.page_count
            self.state.preview.current_page_index = 0
            self.state.preview.zoom_factor = 1.0
            self.file_panel.page_label.setText(f"页数：{self.pdf_engine.page_count}")
            self.log_panel.add_log(f"PDF 已打开，共 {self.pdf_engine.page_count} 页。")
            self._render_current_page()
        except UserFacingError as exc:
            self.log_panel.add_log(f"错误：{exc}")

    def _convert_word_and_open(self, path: str) -> None:
        try:
            self.log_panel.progress.setValue(5)
            self.log_panel.add_log("开始本地转换 Word 为 PDF。")
            output_dir = self.app_root / "user_data"
            pdf_path = self.word_converter.convert_to_pdf(path, output_dir)
            self.log_panel.progress.setValue(25)
            self.log_panel.add_log(f"Word 转 PDF 完成：{pdf_path}")
            self._open_pdf(str(pdf_path))
        except UserFacingError as exc:
            self.log_panel.add_log(f"错误：{exc}")

    def _render_current_page(self) -> None:
        if self.pdf_engine.page_count == 0:
            return
        page_index = self.state.preview.current_page_index
        zoom = self.state.preview.zoom_factor
        try:
            rendered = self.pdf_engine.render_page(page_index, zoom)
            self.preview_workspace.set_page_image(
                rendered.image,
                rendered.page_width_pt,
                rendered.page_height_pt,
                rendered.zoom,
            )
            self.preview_workspace.set_page_info(page_index, self.pdf_engine.page_count)
            self._refresh_marks()
        except UserFacingError as exc:
            self.log_panel.add_log(f"错误：{exc}")

    def _refresh_marks(self) -> None:
        page_index = self.state.preview.current_page_index
        marks = self.state.marks_for_page(page_index)
        selected_id = self.state.preview.selected_mark_id
        self.preview_workspace.set_marks(marks, selected_id, self.processed_stamp_pixmaps)
        normal_count = sum(1 for mark in marks if mark.stamp_type == StampType.NORMAL)
        signature_count = sum(1 for mark in marks if mark.stamp_type == StampType.SIGNATURE)
        self.preview_workspace.set_status(
            f"当前页：第 {page_index + 1} / {self.state.file.page_count} 页    "
            f"普通章：{normal_count} 个    签字章：{signature_count} 个    "
            f"缩放：{round(self.state.preview.zoom_factor * 100)}%"
        )
        self.page_mark_panel.summary_label.setText(
            f"当前页：普通章 {normal_count} 个，签字章 {signature_count} 个"
        )
        self._refresh_mark_list(marks)

    def _refresh_mark_list(self, marks: list[PageMark]) -> None:
        self.page_mark_panel.mark_list.clear()
        if not marks:
            self.page_mark_panel.mark_list.addItem("暂无页面标记")
            return
        for index, mark in enumerate(marks, start=1):
            label = "普通公章" if mark.stamp_type == StampType.NORMAL else "法人签字章"
            self.page_mark_panel.mark_list.addItem(
                f"{label} #{index}  x={mark.x_pt:.1f}pt  y={mark.y_pt:.1f}pt"
            )

    def _previous_page(self) -> None:
        self._go_to_page(self.state.preview.current_page_index - 1)

    def _next_page(self) -> None:
        self._go_to_page(self.state.preview.current_page_index + 1)

    def _go_to_page(self, page_index: int) -> None:
        if not 0 <= page_index < self.state.file.page_count:
            return
        self.state.preview.current_page_index = page_index
        self.state.preview.selected_mark_id = ""
        self._render_current_page()

    def _zoom_in(self) -> None:
        self.state.preview.zoom_factor = min(4.0, self.state.preview.zoom_factor + 0.1)
        self._render_current_page()

    def _zoom_out(self) -> None:
        self.state.preview.zoom_factor = max(0.2, self.state.preview.zoom_factor - 0.1)
        self._render_current_page()

    def _fit_width(self) -> None:
        if self.pdf_engine.page_count == 0:
            return
        page_width, _ = self.pdf_engine.page_size(self.state.preview.current_page_index)
        available_width = max(480, self.preview_workspace.width() - 96)
        self.state.preview.zoom_factor = max(0.2, min(4.0, available_width / page_width))
        self._render_current_page()

    def _handle_page_click(self, x_pt: float, y_pt: float) -> None:
        mode = self.state.preview.active_mode
        if mode == ActiveMode.VIEW:
            self.state.preview.selected_mark_id = ""
            self._refresh_marks()
            return

        stamp_type = StampType.NORMAL if mode == ActiveMode.PLACE_NORMAL else StampType.SIGNATURE
        config = self.state.normal_stamp if stamp_type == StampType.NORMAL else self.state.signature_stamp
        width_pt = mm_to_pt(config.width_mm)
        height_pt = mm_to_pt(config.height_mm)
        mark = PageMark(
            stamp_type=stamp_type,
            page_index=self.state.preview.current_page_index,
            x_pt=max(0.0, x_pt - width_pt / 2),
            y_pt=max(0.0, y_pt - height_pt / 2),
            width_pt=width_pt,
            height_pt=height_pt,
            image_config_id=config.id,
        )
        self.state.page_marks.append(mark)
        self.state.preview.selected_mark_id = mark.id
        self.log_panel.add_log(
            f"已在第 {mark.page_index + 1} 页放置"
            f"{'普通公章' if stamp_type == StampType.NORMAL else '法人签字章'}。"
        )
        self._refresh_marks()

    def _select_mark(self, mark_id: str) -> None:
        self.state.preview.selected_mark_id = mark_id
        for mark in self.state.page_marks:
            mark.selected = mark.id == mark_id
        self._refresh_marks()

    def _move_mark(self, mark_id: str, x_pt: float, y_pt: float) -> None:
        mark = self._find_mark(mark_id)
        if mark is None:
            return
        page_width, page_height = self.pdf_engine.page_size(mark.page_index)
        mark.x_pt = min(max(0.0, x_pt), max(0.0, page_width - mark.width_pt))
        mark.y_pt = min(max(0.0, y_pt), max(0.0, page_height - mark.height_pt))
        self._refresh_marks()

    def _delete_selected_mark(self) -> None:
        mark_id = self.state.preview.selected_mark_id
        if not mark_id:
            return
        before = len(self.state.page_marks)
        self.state.page_marks = [mark for mark in self.state.page_marks if mark.id != mark_id]
        if len(self.state.page_marks) != before:
            self.log_panel.add_log("已删除选中的页面标记。")
        self.state.preview.selected_mark_id = ""
        self._refresh_marks()

    def _load_settings(self) -> None:
        data = self.config_manager.load()
        normal = data.get("normal_stamp", {})
        signature = data.get("signature_stamp", {})
        seam = data.get("seam_stamp", {})

        self._apply_stamp_settings(self.state.normal_stamp, self.normal_panel, normal)
        self._apply_stamp_settings(self.state.signature_stamp, self.signature_panel, signature)

        seam_image = seam.get("image_path", "")
        if seam_image:
            self.state.seam_stamp.image_config.image_path = seam_image
            self.state.seam_stamp.image_config.cached_path = seam.get("cached_path", seam_image)
            self.seam_panel.image_label.setText(seam_image)
        self.seam_panel.page_range_edit.setText(seam.get("page_range_text", "全部"))
        self.seam_panel.total_width_spin.setValue(float(seam.get("total_width_mm", 120.0)))
        self.seam_panel.total_height_spin.setValue(float(seam.get("total_height_mm", 40.0)))
        self.seam_panel.edge_offset_spin.setValue(float(seam.get("edge_offset_mm", 0.0)))
        self.seam_panel.along_offset_spin.setValue(float(seam.get("along_offset_mm", 80.0)))

        recent_input = data.get("last_input_path", "")
        recent_output = data.get("last_output_path", "")
        if recent_input:
            self.top_bar.input_edit.setText(recent_input)
            self.file_panel.set_input_path(recent_input)
        if recent_output:
            self.top_bar.output_edit.setText(recent_output)
            self.state.file.output_path = recent_output
            self.file_panel.set_output_path(recent_output)

    def _apply_stamp_settings(self, config, panel, data: dict) -> None:
        image_path = data.get("image_path", "")
        if image_path:
            config.image_path = image_path
            config.cached_path = data.get("cached_path", image_path)
            panel.image_label.setText(image_path)
        config.width_mm = float(data.get("width_mm", config.width_mm))
        config.height_mm = float(data.get("height_mm", config.height_mm))
        config.remove_white_bg = bool(data.get("remove_white_bg", config.remove_white_bg))
        config.white_threshold = int(data.get("white_threshold", config.white_threshold))
        config.use_rembg = bool(data.get("use_rembg", config.use_rembg))
        config.opacity = float(data.get("opacity", config.opacity))
        config.mottled_strength = float(data.get("mottled_strength", config.mottled_strength))
        config.edge_soften = float(data.get("edge_soften", config.edge_soften))
        config.sharpen_strength = float(data.get("sharpen_strength", config.sharpen_strength))
        panel.width_spin.setValue(config.width_mm)
        panel.height_spin.setValue(config.height_mm)

    def _save_settings(self) -> None:
        data = {
            "last_input_path": self.state.file.input_path,
            "last_output_path": self.state.file.output_path,
            "normal_stamp": self._stamp_config_to_dict(self.state.normal_stamp),
            "signature_stamp": self._stamp_config_to_dict(self.state.signature_stamp),
            "seam_stamp": {
                **self._stamp_config_to_dict(self.state.seam_stamp.image_config),
                "page_range_text": self.seam_panel.page_range_edit.text(),
                "total_width_mm": self.seam_panel.total_width_spin.value(),
                "total_height_mm": self.seam_panel.total_height_spin.value(),
                "edge_offset_mm": self.seam_panel.edge_offset_spin.value(),
                "along_offset_mm": self.seam_panel.along_offset_spin.value(),
            },
        }
        self.config_manager.save(data)

    def _stamp_config_to_dict(self, config) -> dict:
        return {
            "image_path": config.image_path,
            "cached_path": config.cached_path,
            "width_mm": config.width_mm,
            "height_mm": config.height_mm,
            "remove_white_bg": config.remove_white_bg,
            "white_threshold": config.white_threshold,
            "use_rembg": config.use_rembg,
            "opacity": config.opacity,
            "mottled_strength": config.mottled_strength,
            "edge_soften": config.edge_soften,
            "sharpen_strength": config.sharpen_strength,
        }

    def _find_mark(self, mark_id: str) -> PageMark | None:
        for mark in self.state.page_marks:
            if mark.id == mark_id:
                return mark
        return None

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return

        path = urls[0].toLocalFile()
        suffix = Path(path).suffix.lower()
        if suffix in {".pdf", ".doc", ".docx"}:
            self.top_bar.input_edit.setText(path)
            self._set_input_file(path)
        elif suffix in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
            self.normal_panel.image_label.setText(path)
            self._set_stamp_image(path, StampType.NORMAL)
        else:
            self.log_panel.add_log(f"暂不支持拖入的文件类型：{suffix}")
