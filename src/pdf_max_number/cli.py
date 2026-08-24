from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pdf_max_number.find import FindResult, find_largest


def _print_human(result: FindResult) -> None:
    if result.empty_pages:
        pages = ", ".join(str(p) for p in result.empty_pages)
        print(f"warning: no extractable text on page(s) {pages}", file=sys.stderr)
    if result.raw is None:
        print("No numbers found.")
        return
    print(f"Raw: {result.raw.as_dict()['value']}")
    print(f"Adjusted: {result.scaled.as_dict()['value']}")


def _print_json(result: FindResult) -> None:
    payload = {
        "raw": result.raw.as_dict() if result.raw else None,
        "adjusted": result.scaled.as_dict() if result.scaled else None,
        "empty_pages": list(result.empty_pages),
    }
    print(json.dumps(payload, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Find the largest raw and scale-adjusted numbers in a PDF."
    )
    parser.add_argument("pdf", type=Path, help="Path to a PDF file")
    parser.add_argument("--json", action="store_true", help="Print JSON with evidence")
    args = parser.parse_args(argv)

    if not args.pdf.is_file():
        print(f"error: file not found: {args.pdf}", file=sys.stderr)
        return 1

    result = find_largest(args.pdf)
    if args.json:
        _print_json(result)
    else:
        _print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
