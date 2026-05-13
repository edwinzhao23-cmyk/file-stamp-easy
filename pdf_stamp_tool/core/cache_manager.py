from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4


def ensure_user_data(app_root: Path) -> None:
    user_data = app_root / "user_data"
    stamps = user_data / "stamps"
    user_data.mkdir(exist_ok=True)
    stamps.mkdir(exist_ok=True)


def cache_stamp_image(app_root: Path, source_path: str | Path) -> str:
    source = Path(source_path)
    stamps_dir = app_root / "user_data" / "stamps"
    stamps_dir.mkdir(exist_ok=True)
    target = stamps_dir / f"{uuid4().hex}{source.suffix.lower()}"
    shutil.copy2(source, target)
    return str(target)
