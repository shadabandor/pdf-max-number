from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from pdf_max_number.extract import PageText, extract_pages
from pdf_max_number.numbers import NumberToken, find_numbers
from pdf_max_number.scale import scaled_exponent


@dataclass(frozen=True)
class NumberHit:
    value: Decimal
    original: str
    page: int
    snippet: str
    scale: str
    document_page: int | None = None

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "value": _format_decimal(self.value),
            "original": self.original,
            "page": self.page,
            "document_page": self.document_page,
            "snippet": self.snippet.strip(),
            "scale": self.scale,
        }


@dataclass(frozen=True)
class FindResult:
    raw: NumberHit | None
    scaled: NumberHit | None
    empty_pages: tuple[int, ...] = ()


def _format_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral_value():
        return str(int(normalized))
    return format(normalized, "f")


def _positive_tokens(tokens: list[NumberToken]) -> list[NumberToken]:
    return [t for t in tokens if not t.negative]


def _normalize_pages(pages: list[PageText] | list[tuple[int, str]]) -> list[PageText]:
    normalized: list[PageText] = []
    for item in pages:
        if isinstance(item, PageText):
            normalized.append(item)
        else:
            page, text = item
            normalized.append(PageText(page=page, text=text))
    return normalized


def analyze_text(pages: list[PageText] | list[tuple[int, str]]) -> FindResult:
    page_texts = _normalize_pages(pages)
    doc_by_pdf = {item.page: item.document_page for item in page_texts}
    page_text_by_page = {item.page: item.text for item in page_texts}

    tokens: list[NumberToken] = []
    for item in page_texts:
        tokens.extend(find_numbers(item.text, page=item.page))
    tokens = _positive_tokens(tokens)
    if not tokens:
        return FindResult(raw=None, scaled=None)

    raw_candidates = [t for t in tokens if not t.scientific]
    raw_hit = None
    if raw_candidates:
        raw_best = max(raw_candidates, key=lambda t: t.raw_value)
        raw_hit = NumberHit(
            value=raw_best.raw_value,
            original=raw_best.original,
            page=raw_best.page,
            snippet=raw_best.context,
            scale="none",
            document_page=doc_by_pdf.get(raw_best.page),
        )

    def adjusted(token: NumberToken) -> Decimal:
        exp, _ = scaled_exponent(
            token, page_text=page_text_by_page.get(token.page)
        )
        if token.suffix_exp:
            return token.magnitude * (Decimal(10) ** token.suffix_exp)
        if token.scientific:
            return token.magnitude
        return token.magnitude * (Decimal(10) ** exp)

    scaled_best = max(tokens, key=adjusted)
    exp, label = scaled_exponent(
        scaled_best, page_text=page_text_by_page.get(scaled_best.page)
    )
    scaled_hit = NumberHit(
        value=adjusted(scaled_best),
        original=scaled_best.original,
        page=scaled_best.page,
        snippet=scaled_best.context,
        scale=label,
        document_page=doc_by_pdf.get(scaled_best.page),
    )
    return FindResult(raw=raw_hit, scaled=scaled_hit)


def find_largest(path: str | Path) -> FindResult:
    page_texts, empty = extract_pages(path)
    result = analyze_text(page_texts)
    return FindResult(raw=result.raw, scaled=result.scaled, empty_pages=tuple(empty))
