from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QWidget,
)

from .common import Card


class SeamPanel(Card):
    image_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        title = QLabel("骑缝章")
        title.setObjectName("CardTitle")

        self.enabled_check = QCheckBox("启用骑缝章")
        self.image_label = QLabel("未选择图片")
        self.image_label.setObjectName("MutedText")
        choose_btn = QPushButton("选择骑缝章图片")
        choose_btn.clicked.connect(self._choose_image)

        self.page_range_edit = QLineEdit("全部")
        self.page_range_edit.setPlaceholderText("全部、1-5、2,4-8")

        self.side_combo = QComboBox()
        self.side_combo.addItems(["右侧", "左侧"])

        self.total_width_spin = QDoubleSpinBox()
        self.total_width_spin.setRange(1, 500)
        self.total_width_spin.setSuffix(" mm")
        self.total_width_spin.setValue(120)

        self.total_height_spin = QDoubleSpinBox()
        self.total_height_spin.setRange(1, 300)
        self.total_height_spin.setSuffix(" mm")
        self.total_height_spin.setValue(40)

        self.edge_offset_spin = QDoubleSpinBox()
        self.edge_offset_spin.setRange(0, 100)
        self.edge_offset_spin.setSuffix(" mm")

        self.along_offset_spin = QDoubleSpinBox()
        self.along_offset_spin.setRange(0, 500)
        self.along_offset_spin.setSuffix(" mm")
        self.along_offset_spin.setValue(80)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)
        form.addRow("页码", self.page_range_edit)
        form.addRow("盖章侧边", self.side_combo)
        form.addRow("总宽", self.total_width_spin)
        form.addRow("总高", self.total_height_spin)
        form.addRow("离边距离", self.edge_offset_spin)
        form.addRow("沿边偏移", self.along_offset_spin)

        self.layout.addWidget(title)
        self.layout.addWidget(self.enabled_check)
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(choose_btn)
        self.layout.addLayout(form)

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择骑缝章图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if path:
            self.image_label.setText(path)
            self.image_selected.emit(path)
