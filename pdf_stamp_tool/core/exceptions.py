from __future__ import annotations


class UserFacingError(Exception):
    message = "操作失败。"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)


class PdfFileOccupiedError(UserFacingError):
    message = "PDF 文件可能正在被其他程序占用，请关闭后重试。"


class OutputPermissionError(UserFacingError):
    message = "输出文件没有写入权限，请选择其他位置。"


class WordConvertError(UserFacingError):
    message = "Word 转 PDF 失败，请确认已安装 Word、WPS 或 LibreOffice。"


class InvalidStampImageError(UserFacingError):
    message = "印章图片格式错误，请选择 PNG、JPG、BMP 或 TIFF 图片。"


class PdfRenderError(UserFacingError):
    message = "PDF 页面渲染失败，请检查文件是否损坏。"


class PageRangeFormatError(UserFacingError):
    message = "页码范围格式不正确，请输入类似：全部、1,3,5 或 2-6。"


class NoOutputFileError(UserFacingError):
    message = "请先选择输出文件。"


class NoStampModeSelectedError(UserFacingError):
    message = "请至少选择一种盖章方式。"


class InvalidSeamPagesError(UserFacingError):
    message = "骑缝章至少需要 2 页，请检查页码范围。"

