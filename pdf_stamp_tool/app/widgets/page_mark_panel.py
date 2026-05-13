from __future__ import annotations

from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QHBoxLayout, QWidget

from .common import Card


class PageMarkPanel(Card):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        title = QLabel("页面标记管理")
        title.setObjectName("CardTitle")

        self.summary_label = QLabel("当前页：普通章 0 个，签字章 0 个")
        self.summary_label.setObjectName("MutedText")

        self.mark_list = QListWidget()
        self.mark_list.setMinimumHeight(120)
        self.mark_list.addItem("暂无页面标记")

        actions = QHBoxLayout()
        locate_btn = QPushButton("定位")
        delete_btn = QPushButton("删除选中")
        delete_btn.setObjectName("DangerButton")
        actions.addWidget(locate_btn)
        actions.addWidget(delete_btn)

        self.layout.addWidget(title)
        self.layout.addWidget(self.summary_label)
        self.layout.addWidget(self.mark_list)
        self.layout.addLayout(actions)

