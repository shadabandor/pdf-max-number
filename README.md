# pdf-max-number

Find the largest number in a PDF, both as written (**raw**) and after applying natural scale language (**adjusted**). Raw uses the numeral only (`9.6 billion` is `9.6`). Adjusted applies suffixes and phrases like “in millions” (`9.6 billion` is `9,600,000,000`; `3.15` in millions is `3,150,000`).

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pdf-max-number path/to/file.pdf
pdf-max-number path/to/file.pdf --json
```

Human output is two lines: 
`Raw: VALUE, PDF page index, printed document page number (if exists)`
`Adjusted: VALUE, PDF page index, printed document page number (if exists)`

`--json` also includes the original span, nearby snippet, and which scale was used.

## Methodology

1. Extract page text and table cells with pdfplumber.
2. Parse numeric tokens (commas, decimals, `$`, scientific notation, suffixes like `3.15M` / `5bn`). Dates are skipped.
3. For each token, the adjusted value is: suffix if present (never doubled), else the nearest scale phrase **on that page** (so a top-of-page “Dollars in Thousands” still applies to table cells), else the raw magnitude. Other pages’ scale language is ignored.
4. Report the max raw value (the written numeral only; suffixes, scientific notation, and “in millions” do not count) and the max adjusted value (suffixes, scientific notation, and page-local phrases).

## Assumptions and limitations

- Text PDFs only. Scanned/image pages are skipped.
- Number formats are US-centric; European `1.234,56` is supported when that pattern is unambiguous.
- Scale wording must match known phrases. Unusual phrasing will not be scaled.
- Years (e.g. `2024`) count as raw numbers but are not multiplied by “in millions”-style guidance.
- Scientific notation (e.g. `1.2e6`) is omitted from the raw max; it still counts toward the adjusted max.
- Suffixes (`M`, `bn`) apply only to the adjusted value and are not combined with page scale.
- Document-wide “in millions” language is ignored unless it appears on the same page as the number.
- Page numbers in headers/footers may still appear as candidates; they rarely win against scaled financials.
- Printed document page numbers are taken from a bottom-left footer numeral when present; otherwise only the PDF page index is shown.
- Accounting negatives in parentheses are ignored when computing a maximum.
