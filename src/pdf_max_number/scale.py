from __future__ import annotations

import re
from collections import defaultdict

from pdf_max_number.numbers import NumberToken

SCALE_NAME = {3: "thousands", 6: "millions", 9: "billions", 12: "trillions"}

_SCALE_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (
        re.compile(
            r"""
            (?:
                \bin\s+thousands\b
              | \bin\s+thousand\b
              | \(\s*['’]?000\s*\)
              | \$000\b
              | ['’]000\b
            )
            """,
            re.IGNORECASE | re.VERBOSE,
        ),
        3,
    ),
    (
        re.compile(
            r"""
            (?:
                \bin\s+millions\b
              | \bin\s+million\b
              | \$\s*millions?\b
              | figures?\s+in\s+\$\s*m\b
              | (?:amounts?|values?|figures?|results?)\s+(?:are|were|is)\s+(?:listed\s+)?in\s+millions
            )
            """,
            re.IGNORECASE | re.VERBOSE,
        ),
        6,
    ),
    (
        re.compile(
            r"""
            (?:
                \bin\s+billions\b
              | \bin\s+billion\b
              | \$\s*billions?\b
              | figures?\s+in\s+\$\s*b\b
            )
            """,
            re.IGNORECASE | re.VERBOSE,
        ),
        9,
    ),
    (
        re.compile(
            r"""
            (?:
                \bin\s+trillions\b
              | \bin\s+trillion\b
              | \$\s*trillions?\b
            )
            """,
            re.IGNORECASE | re.VERBOSE,
        ),
        12,
    ),
]


def detect_document_scale(text: str) -> int:
    """Return the document-wide scale exponent, or 0 if none.

    Most frequent phrase family wins; ties go to the family whose last hit is latest.
    """
    counts: dict[int, int] = defaultdict(int)
    last_pos: dict[int, int] = {}
    for pattern, exp in _SCALE_PATTERNS:
        for match in pattern.finditer(text):
            counts[exp] += 1
            last_pos[exp] = match.start()
    if not counts:
        return 0
    return max(counts, key=lambda exp: (counts[exp], last_pos[exp]))


def detect_local_scale(token: NumberToken) -> int | None:
    """Scale exponent from the nearest phrase in the token's context window."""
    window = token.context
    token_from = token.start - token.context_start
    token_to = token.end - token.context_start
    best: tuple[int, int] | None = None  # (distance, exp)
    for pattern, exp in _SCALE_PATTERNS:
        for match in pattern.finditer(window):
            if match.end() <= token_from:
                dist = token_from - match.end()
            elif match.start() >= token_to:
                dist = match.start() - token_to
            else:
                dist = 0
            if best is None or dist < best[0]:
                best = (dist, exp)
    return None if best is None else best[1]


def looks_like_year(token: NumberToken) -> bool:
    """Four-digit calendar years should not take document/local scale."""
    if token.suffix_exp or token.scientific:
        return False
    if any(mark in token.original for mark in "$£€,."):
        return False
    if token.magnitude != token.magnitude.to_integral_value():
        return False
    n = int(token.magnitude)
    return 1800 <= n <= 2100


def looks_like_page_label(token: NumberToken) -> bool:
    prefix = token.context[: token.start - token.context_start]
    return bool(re.search(r"\bpage\s+$", prefix, re.IGNORECASE))


def scaled_exponent(token: NumberToken, document_exp: int) -> tuple[int, str]:
    """Multiplier exponent actually applied for the adjusted value, plus a label."""
    if token.suffix_exp:
        return token.suffix_exp, f"suffix:{SCALE_NAME.get(token.suffix_exp, token.suffix_exp)}"
    if token.scientific:
        return 0, "scientific"
    if looks_like_year(token):
        return 0, "year"
    if looks_like_page_label(token):
        return 0, "page"
    local = detect_local_scale(token)
    if local is not None:
        return local, f"local:{SCALE_NAME[local]}"
    if document_exp:
        return document_exp, f"document:{SCALE_NAME[document_exp]}"
    return 0, "none"
