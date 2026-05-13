from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QListWidget, QProgressBar, QVBoxLayout, QWidget


class LogPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LogPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QLabel("日志与处理状态")
        title.setObjectName("CardTitle")

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.log_list = QListWidget()
        self.log_list.setMaximumHeight(120)
        self.log_list.addItem("就绪：请选择 PDF 或 Word 文件开始。")

        layout.addWidget(title)
        layout.addWidget(self.progress)
        layout.addWidget(self.log_list)

    def add_log(self, text: str) -> None:
        self.log_list.addItem(text)
        self.log_list.scrollToBottom()

