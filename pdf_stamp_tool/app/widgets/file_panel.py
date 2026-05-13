from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget

from .common import Card


class FilePanel(Card):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        title = QLabel("文件设置")
        title.setObjectName("CardTitle")
        self.input_label = QLabel("输入文件：未选择")
        self.output_label = QLabel("输出文件：未选择")
        self.page_label = QLabel("页数：-")
        self.convert_label = QLabel("Word 转换：待处理")
        self.convert_label.setObjectName("MutedText")

        self.layout.addWidget(title)
        self.layout.addWidget(self.input_label)
        self.layout.addWidget(self.output_label)
        self.layout.addWidget(self.page_label)
        self.layout.addWidget(self.convert_label)

    def set_input_path(self, path: str) -> None:
        self.input_label.setText(f"输入文件：{path or '未选择'}")

    def set_output_path(self, path: str) -> None:
        self.output_label.setText(f"输出文件：{path or '未选择'}")

