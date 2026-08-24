from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pdfplumber


@dataclass(frozen=True)
class PageText:
    page: int
    text: str


def extract_pages(path: str | Path) -> tuple[list[PageText], list[int]]:
    """Extract text (and table cell text) per page.

    Returns pages and a list of page numbers that had no extractable text.
    """
    pages: list[PageText] = []
    empty: list[int] = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            parts: list[str] = []
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
            for table in page.extract_tables() or []:
                for row in table:
                    line = " ".join((cell or "").strip() for cell in row)
                    if line.strip():
                        parts.append(line)
            combined = "\n".join(parts)
            if not combined.strip():
                empty.append(i)
            pages.append(PageText(page=i, text=combined))
    return pages, empty
