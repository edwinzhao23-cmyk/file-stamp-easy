from __future__ import annotations

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QWidget,
)
from PySide6.QtCore import Qt

from .common import Card


class StampProcessPanel(Card):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        title = QLabel("印章处理")
        title.setObjectName("CardTitle")

        self.target_combo = QComboBox()
        self.target_combo.addItems(["普通公章", "法人签字章", "骑缝章"])

        self.remove_bg_check = QCheckBox("去白底")
        self.remove_bg_check.setChecked(True)

        self.rembg_check = QCheckBox("优先使用 rembg AI 抠图")

        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 255)
        self.threshold_spin.setValue(245)

        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0.1, 1.0)
        self.opacity_spin.setSingleStep(0.01)
        self.opacity_spin.setValue(0.92)

        self.mottled_slider = QSlider(Qt.Orientation.Horizontal)
        self.mottled_slider.setRange(0, 100)
        self.mottled_slider.setValue(3)

        self.edge_slider = QSlider(Qt.Orientation.Horizontal)
        self.edge_slider.setRange(0, 100)
        self.edge_slider.setValue(12)

        self.sharpen_slider = QSlider(Qt.Orientation.Horizontal)
        self.sharpen_slider.setRange(0, 100)
        self.sharpen_slider.setValue(35)

        self.preview_label = QLabel("处理后印章预览区")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(96)
        self.preview_label.setStyleSheet(
            "background:#F8FAFC;border:1px dashed #CBD5E1;border-radius:6px;color:#6B7280;"
        )

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)
        form.addRow("作用对象", self.target_combo)
        form.addRow("白底阈值", self.threshold_spin)
        form.addRow("透明度", self.opacity_spin)
        form.addRow("斑驳强度", self.mottled_slider)
        form.addRow("边缘柔化", self.edge_slider)
        form.addRow("锐化强度", self.sharpen_slider)

        self.layout.addWidget(title)
        self.layout.addWidget(self.remove_bg_check)
        self.layout.addWidget(self.rembg_check)
        self.layout.addLayout(form)
        self.layout.addWidget(self.preview_label)

    def set_preview_pixmap(self, pixmap: QPixmap | None, message: str = "") -> None:
        if pixmap is None:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText(message or "处理后印章预览区")
            return

        scaled = pixmap.scaled(
            220,
            120,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setText("")
        self.preview_label.setPixmap(scaled)
