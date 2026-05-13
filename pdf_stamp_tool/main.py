from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from core.cache_manager import ensure_user_data
from core.config_manager import ConfigManager


def main() -> int:
    if getattr(sys, "frozen", False):
        app_root = Path(sys.executable).resolve().parent
    else:
        app_root = Path(__file__).resolve().parent
    ensure_user_data(app_root)

    app = QApplication(sys.argv)
    app.setApplicationName("文件盖章易")
    app.setOrganizationName("FileStampEasy")

    config = ConfigManager(app_root)
    window = MainWindow(app_root=app_root, config_manager=config)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
