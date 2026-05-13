from __future__ import annotations

from core.exceptions import PageRangeFormatError


def parse_page_range(text: str, page_count: int) -> list[int]:
    value = text.strip()
    if not value or value == "全部":
        return list(range(page_count))

    pages: set[int] = set()
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        raise PageRangeFormatError()

    for part in parts:
        if "-" in part:
            start_text, end_text = [item.strip() for item in part.split("-", 1)]
            if not start_text.isdigit() or not end_text.isdigit():
                raise PageRangeFormatError()
            start, end = int(start_text), int(end_text)
            if start <= 0 or end <= 0 or start > end:
                raise PageRangeFormatError()
            pages.update(range(start - 1, end))
        else:
            if not part.isdigit():
                raise PageRangeFormatError()
            page = int(part)
            if page <= 0:
                raise PageRangeFormatError()
            pages.add(page - 1)

    if not pages or min(pages) < 0 or max(pages) >= page_count:
        raise PageRangeFormatError()

    return sorted(pages)

