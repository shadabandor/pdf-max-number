# pdf-max-number

Find the largest number in a PDF, both as written (**raw**) and after applying document scale language (**adjusted**). Example: if the file says figures are in millions, `3.15` is treated as `3,150,000`.

Self-contained: local PDF parsing only, no network or external APIs.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pdf-max-number path/to/file.pdf
pdf-max-number path/to/file.pdf --json
```

Human output is two lines: `Raw:` and `Adjusted:`. `--json` adds the original span, page, nearby snippet, and which scale was used.

## Methodology

1. Extract page text and table cells with pdfplumber.
2. Parse numeric tokens (commas, decimals, `$`, scientific notation, suffixes like `3.15M` / `5bn`). Dates are skipped.
3. Scan the full text for document-wide scale phrases (`in millions`, `$ millions`, `'000`, …). The most frequent family wins; ties use the last occurrence.
4. For each token, the adjusted value is: suffix if present (never doubled), else a nearby local scale phrase, else the document scale, else the raw magnitude.
5. Report the max raw value (suffixes count, document scale does not) and the max adjusted value.

## Assumptions and limitations

- Text PDFs only. Scanned/image pages are skipped (no OCR).
- Number formats are US-centric; European `1.234,56` is supported when that pattern is unambiguous.
- Scale wording must match known phrases. Unusual phrasing will not be scaled.
- Years (e.g. `2024`) count as raw numbers but are not multiplied by “in millions”-style guidance.
- Suffixes (`M`, `bn`) override document scale so values are not multiplied twice.
- Page numbers in headers/footers may still appear as candidates; they rarely win against scaled financials.
- Accounting negatives in parentheses are ignored when computing a maximum.
