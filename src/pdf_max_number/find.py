from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from pdf_max_number.extract import extract_pages
from pdf_max_number.numbers import NumberToken, find_numbers
from pdf_max_number.scale import SCALE_NAME, detect_document_scale, scaled_exponent


@dataclass(frozen=True)
class NumberHit:
    value: Decimal
    original: str
    page: int
    snippet: str
    scale: str

    def as_dict(self) -> dict[str, str | int]:
        return {
            "value": _format_decimal(self.value),
            "original": self.original,
            "page": self.page,
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


def analyze_text(pages: list[tuple[int, str]]) -> FindResult:
    full = "\n".join(text for _, text in pages)
    document_exp = detect_document_scale(full)

    tokens: list[NumberToken] = []
    for page, text in pages:
        tokens.extend(find_numbers(text, page=page))
    tokens = _positive_tokens(tokens)
    if not tokens:
        return FindResult(raw=None, scaled=None)

    raw_best = max(tokens, key=lambda t: t.raw_value)
    raw_label = (
        f"suffix:{SCALE_NAME.get(raw_best.suffix_exp, raw_best.suffix_exp)}"
        if raw_best.suffix_exp
        else "none"
    )
    raw_hit = NumberHit(
        value=raw_best.raw_value,
        original=raw_best.original,
        page=raw_best.page,
        snippet=raw_best.context,
        scale=raw_label,
    )

    def adjusted(token: NumberToken) -> Decimal:
        exp, _ = scaled_exponent(token, document_exp)
        if token.suffix_exp:
            return token.raw_value
        if token.scientific:
            return token.magnitude
        return token.magnitude * (Decimal(10) ** exp)

    scaled_best = max(tokens, key=adjusted)
    exp, label = scaled_exponent(scaled_best, document_exp)
    scaled_hit = NumberHit(
        value=adjusted(scaled_best),
        original=scaled_best.original,
        page=scaled_best.page,
        snippet=scaled_best.context,
        scale=label,
    )
    return FindResult(raw=raw_hit, scaled=scaled_hit)


def find_largest(path: str | Path) -> FindResult:
    page_texts, empty = extract_pages(path)
    result = analyze_text([(p.page, p.text) for p in page_texts])
    return FindResult(raw=result.raw, scaled=result.scaled, empty_pages=tuple(empty))
