from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from models.stamp_config import StampType

from .common import Card


class StampPanel(Card):
    image_selected = Signal(str, StampType)
    config_changed = Signal(StampType)
    apply_all_requested = Signal(StampType)
    clear_current_requested = Signal(StampType)
    clear_all_requested = Signal(StampType)

    def __init__(self, title_text: str, stamp_type: StampType, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.stamp_type = stamp_type

        title = QLabel(title_text)
        title.setObjectName("CardTitle")

        self.image_label = QLabel("未选择图片")
        self.image_label.setObjectName("MutedText")

        choose_btn = QPushButton("选择图片")
        choose_btn.clicked.connect(self._choose_image)

        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(1, 300)
        self.width_spin.setSuffix(" mm")
        self.width_spin.setValue(40 if stamp_type == StampType.NORMAL else 35)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(1, 300)
        self.height_spin.setSuffix(" mm")
        self.height_spin.setValue(40 if stamp_type == StampType.NORMAL else 15)

        self.page_range_edit = QLineEdit("全部")
        self.page_range_edit.setPlaceholderText("全部、1,3,5、2-6")
        self.width_spin.valueChanged.connect(lambda: self.config_changed.emit(self.stamp_type))
        self.height_spin.valueChanged.connect(lambda: self.config_changed.emit(self.stamp_type))
        self.page_range_edit.textChanged.connect(lambda: self.config_changed.emit(self.stamp_type))

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)
        form.addRow("宽度", self.width_spin)
        form.addRow("高度", self.height_spin)
        form.addRow("页码", self.page_range_edit)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        apply_btn = QPushButton("应用到全部页")
        clear_current_btn = QPushButton("清空当前页")
        clear_all_btn = QPushButton("清空全部")
        clear_all_btn.setObjectName("DangerButton")

        apply_btn.clicked.connect(lambda: self.apply_all_requested.emit(self.stamp_type))
        clear_current_btn.clicked.connect(lambda: self.clear_current_requested.emit(self.stamp_type))
        clear_all_btn.clicked.connect(lambda: self.clear_all_requested.emit(self.stamp_type))

        actions.addWidget(apply_btn)
        actions.addWidget(clear_current_btn)
        actions.addWidget(clear_all_btn)

        self.layout.addWidget(title)
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(choose_btn)
        self.layout.addLayout(form)
        self.layout.addLayout(actions)

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择印章图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if path:
            self.image_label.setText(path)
            self.image_selected.emit(path, self.stamp_type)
