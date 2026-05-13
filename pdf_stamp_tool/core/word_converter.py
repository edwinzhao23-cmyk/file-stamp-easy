from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from core.exceptions import WordConvertError


class WordConverter:
    def convert_to_pdf(self, input_path: str | Path, output_dir: str | Path) -> Path:
        source = Path(input_path)
        target_dir = Path(output_dir)
        target_dir.mkdir(exist_ok=True)
        target = target_dir / f"{source.stem}.pdf"

        for converter in (self._convert_with_word_com, self._convert_with_wps_com):
            try:
                if converter(source, target):
                    return target
            except Exception:
                continue

        try:
            if self._convert_with_libreoffice(source, target_dir):
                libreoffice_target = target_dir / f"{source.stem}.pdf"
                if libreoffice_target.exists():
                    return libreoffice_target
        except Exception:
            pass

        raise WordConvertError(
            "Word 转 PDF 失败：未检测到可用的 Microsoft Word、WPS 或 LibreOffice。请手动另存为 PDF 后再导入。"
        )

    def _convert_with_word_com(self, source: Path, target: Path) -> bool:
        try:
            import win32com.client  # type: ignore
        except Exception:
            return False

        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        doc = None
        try:
            doc = word.Documents.Open(str(source))
            doc.ExportAsFixedFormat(str(target), 17)
            return target.exists()
        finally:
            if doc is not None:
                doc.Close(False)
            word.Quit()

    def _convert_with_wps_com(self, source: Path, target: Path) -> bool:
        try:
            import win32com.client  # type: ignore
        except Exception:
            return False

        for prog_id in ("Kwps.Application", "Wps.Application"):
            app = None
            doc = None
            try:
                app = win32com.client.DispatchEx(prog_id)
                app.Visible = False
                doc = app.Documents.Open(str(source))
                doc.ExportAsFixedFormat(str(target), 17)
                return target.exists()
            except Exception:
                continue
            finally:
                if doc is not None:
                    doc.Close(False)
                if app is not None:
                    app.Quit()
        return False

    def _convert_with_libreoffice(self, source: Path, target_dir: Path) -> bool:
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            return False
        result = subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(target_dir),
                str(source),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0

