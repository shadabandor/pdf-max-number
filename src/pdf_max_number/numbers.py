from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

DATE_RE = re.compile(
    r"""
    \b(?:
        \d{1,2}[/-]\d{1,2}[/-]\d{2,4}
      | \d{4}[/-]\d{1,2}[/-]\d{1,2}
    )\b
    """,
    re.VERBOSE,
)

# Longer suffix names first so "million" wins over "m".
SUFFIX_EXP: dict[str, int] = {
    "thousands": 3,
    "thousand": 3,
    "millions": 6,
    "million": 6,
    "billions": 9,
    "billion": 9,
    "trillions": 12,
    "trillion": 12,
    "bn": 9,
    "mm": 6,
    "tn": 12,
    "k": 3,
    "m": 6,
}

# Word suffixes may sit on the same line ("5 billion"). Compact tokens
# ("3.15M", "5bn") must touch the number so a following heading is not a suffix.
_WORD_SUFFIX = (
    "thousands|thousand|millions|million|billions|billion|"
    "trillions|trillion|bn|mm|tn"
)
# Do not treat a lone "B"/"T" as billions/trillions: "Volume 11B" is a label.
_GLUED_SUFFIX = "bn|mm|tn|k|m"

NUMBER_RE = re.compile(
    rf"""
    (?<![A-Za-z])
    (?P<neg>-)?
    (?P<open>\()?
    (?P<currency>[$£€])?
    (?P<body>
          \d{{1,3}}(?:,\d{{3}})+(?:\.\d+)?   # 1,234.56
        | \d{{1,3}}(?:\.\d{{3}})+,\d+         # 1.234,56
        | \d+\.\d+                            # 3.15
        | \d+                                 # 315
    )
    (?:[eE](?P<exp>[+-]?\d+)(?![A-Za-z]))?
    (?:
          [ \t]+(?P<suffix>{_WORD_SUFFIX})\b
        | (?P<glued_suffix>{_GLUED_SUFFIX})\b
    )?
    (?P<close>\))?
    (?P<pct>%)?
    """,
    re.VERBOSE | re.IGNORECASE,
)


@dataclass(frozen=True)
class NumberToken:
    magnitude: Decimal
    suffix_exp: int
    scientific: bool
    original: str
    start: int
    end: int
    page: int
    context: str
    context_start: int
    negative: bool

    @property
    def raw_value(self) -> Decimal:
        """Written numeral only. Suffixes like 'billion' are not applied."""
        return -self.magnitude if self.negative else self.magnitude


def _mask_dates(text: str) -> str:
    return DATE_RE.sub(lambda m: " " * (m.end() - m.start()), text)


def _parse_body(body: str) -> Decimal | None:
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d+", body):
        normalized = body.replace(".", "").replace(",", ".")
    else:
        normalized = body.replace(",", "")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def find_numbers(text: str, page: int = 1, context_radius: int = 200) -> list[NumberToken]:
    masked = _mask_dates(text)
    tokens: list[NumberToken] = []
    for match in NUMBER_RE.finditer(masked):
        body = match.group("body")
        magnitude = _parse_body(body)
        if magnitude is None:
            continue

        scientific = match.group("exp") is not None
        if scientific:
            magnitude = magnitude * (Decimal(10) ** int(match.group("exp")))

        suffix_raw = match.group("suffix") or match.group("glued_suffix")
        suffix_exp = SUFFIX_EXP.get(suffix_raw.lower(), 0) if suffix_raw else 0

        opened = match.group("open") is not None
        closed = match.group("close") is not None
        negative = match.group("neg") is not None or (opened and closed)
        if opened != closed and match.group("open"):
            # Unbalanced paren — treat as grouping, not a negative.
            negative = match.group("neg") is not None

        start, end = match.start(), match.end()
        ctx_start = max(0, start - context_radius)
        ctx_end = min(len(text), end + context_radius)
        tokens.append(
            NumberToken(
                magnitude=magnitude,
                suffix_exp=suffix_exp,
                scientific=scientific,
                original=text[start:end],
                start=start,
                end=end,
                page=page,
                context=text[ctx_start:ctx_end],
                context_start=ctx_start,
                negative=negative,
            )
        )
    return tokens
