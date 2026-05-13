from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class TopBarWidget(QFrame):
    input_selected = Signal(str)
    output_selected = Signal(str)
    start_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        title = QLabel("文件盖章易")
        title.setObjectName("AppTitle")

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("选择或拖入 PDF / Word 文件")
        self.input_edit.setMinimumWidth(260)

        input_btn = QPushButton("选择输入")
        input_btn.clicked.connect(self._choose_input)

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("默认：原文件名_已盖章.pdf")
        self.output_edit.setMinimumWidth(260)

        output_btn = QPushButton("选择输出")
        output_btn.clicked.connect(self._choose_output)

        self.normal_check = QCheckBox("普通章")
        self.normal_check.setChecked(True)
        self.signature_check = QCheckBox("签字章")
        self.seam_check = QCheckBox("骑缝章")

        start_btn = QPushButton("开始盖章")
        start_btn.setObjectName("PrimaryButton")
        start_btn.clicked.connect(self.start_clicked.emit)

        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(self.input_edit, 2)
        layout.addWidget(input_btn)
        layout.addWidget(self.output_edit, 2)
        layout.addWidget(output_btn)
        layout.addWidget(self.normal_check)
        layout.addWidget(self.signature_check)
        layout.addWidget(self.seam_check)
        layout.addWidget(start_btn)

    def _choose_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择输入文件",
            "",
            "文档文件 (*.pdf *.doc *.docx);;PDF 文件 (*.pdf);;Word 文件 (*.doc *.docx)",
        )
        if path:
            self.input_edit.setText(path)
            self.input_selected.emit(path)

    def _choose_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "选择输出 PDF",
            "",
            "PDF 文件 (*.pdf)",
        )
        if path:
            self.output_edit.setText(path)
            self.output_selected.emit(path)

