from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pdfplumber

_FOOTER_PAGE_RE = re.compile(r"^\d{1,4}$")


@dataclass(frozen=True)
class PageText:
    page: int
    text: str
    document_page: int | None = None


def detect_document_page(page: Any) -> int | None:
    """Printed page number in the bottom-left footer, if present."""
    words = page.extract_words() or []
    if not words:
        return None
    height = float(page.height)
    width = float(page.width)
    left_limit = min(140.0, width * 0.22)
    bottom_limit = height - min(48.0, height * 0.10)
    candidates: list[tuple[float, float, int]] = []
    for word in words:
        if float(word["x0"]) > left_limit:
            continue
        if float(word["top"]) < bottom_limit:
            continue
        text = str(word["text"]).strip()
        if not _FOOTER_PAGE_RE.fullmatch(text):
            continue
        number = int(text)
        if 1800 <= number <= 2100:
            continue
        candidates.append((float(word["top"]), float(word["x0"]), number))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2]


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
            pages.append(
                PageText(
                    page=i,
                    text=combined,
                    document_page=detect_document_page(page),
                )
            )
    return pages, empty
