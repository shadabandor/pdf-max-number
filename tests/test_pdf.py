from decimal import Decimal
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from pdf_max_number import find_largest
from pdf_max_number.cli import main


def _write_pdf(path: Path, lines: list[str], document_page: int | None = None) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    y = 720
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
    if document_page is not None:
        c.drawString(36, 36, str(document_page))
    c.save()


def test_generated_pdf(tmp_path: Path):
    pdf = tmp_path / "sample.pdf"
    _write_pdf(
        pdf,
        [
            "Annual report. Values are listed in millions.",
            "Revenue 3.15 compared with year 2024.",
        ],
    )
    result = find_largest(pdf)
    assert result.raw is not None
    assert result.raw.value == Decimal("2024")
    assert result.raw.document_page is None
    assert result.scaled.value == Decimal("3150000")


def test_cli_human(tmp_path: Path, capsys):
    pdf = tmp_path / "cli.pdf"
    _write_pdf(pdf, ["All figures in millions", "Item 4.2"], document_page=3)
    code = main([str(pdf)])
    assert code == 0
    out = capsys.readouterr().out
    assert "Raw: 4.2 (pdf page 1, document page 3)" in out
    assert "Adjusted: 4200000 (pdf page 1, document page 3)" in out


def test_cli_human_without_document_page(tmp_path: Path, capsys):
    pdf = tmp_path / "cli.pdf"
    _write_pdf(pdf, ["All figures in millions", "Item 4.2"])
    code = main([str(pdf)])
    assert code == 0
    out = capsys.readouterr().out
    assert "Raw: 4.2 (pdf page 1)" in out
    assert "document page" not in out


def test_document_page_comes_from_hit_page(tmp_path: Path):
    pdf = tmp_path / "multi.pdf"
    c = canvas.Canvas(str(pdf), pagesize=letter)
    c.drawString(72, 720, "Revenue 500")
    c.drawString(36, 36, "2")
    c.showPage()
    c.drawString(72, 720, "Also disclosed 9.0 million")
    c.drawString(36, 36, "3")
    c.save()
    result = find_largest(pdf)
    assert result.raw is not None
    assert result.raw.value == Decimal("500")
    assert result.raw.page == 1
    assert result.raw.document_page == 2
    assert result.scaled.value == Decimal("9000000")
    assert result.scaled.page == 2
    assert result.scaled.document_page == 3
