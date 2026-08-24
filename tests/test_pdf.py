from decimal import Decimal
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from pdf_max_number import find_largest
from pdf_max_number.cli import main


def _write_pdf(path: Path, lines: list[str]) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    y = 720
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
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
    assert result.scaled.value == Decimal("3150000")


def test_cli_human(tmp_path: Path, capsys):
    pdf = tmp_path / "cli.pdf"
    _write_pdf(pdf, ["All figures in millions", "Item 4.2"])
    code = main([str(pdf)])
    assert code == 0
    out = capsys.readouterr().out
    assert "Raw: 4.2" in out
    assert "Adjusted: 4200000" in out
