from decimal import Decimal

from pdf_max_number.find import analyze_text


def test_millions_guidance_beats_year():
    text = (
        "Values are listed in millions. Revenue was 3.15. "
        "The report year is 2024."
    )
    result = analyze_text([(1, text)])
    assert result.raw.value == Decimal("2024")
    assert result.scaled.value == Decimal("3150000")


def test_suffix_not_double_counted():
    text = "Figures in millions. Also disclosed 2.0M separately."
    result = analyze_text([(1, text)])
    assert result.raw.value == Decimal("2000000")
    assert result.scaled.value == Decimal("2000000")


def test_local_override_changes_max():
    text = (
        "All amounts are in millions. Headline figure 1.0. "
        "Footnote table in thousands: 2500"
    )
    result = analyze_text([(1, text)])
    # 1.0 million = 1_000_000; 2500 thousand = 2_500_000
    assert result.scaled.value == Decimal("2500000")


def test_negatives_ignored_for_max():
    result = analyze_text([(1, "Gain 10 and loss (9999)")])
    assert result.raw.value == Decimal("10")
    assert result.scaled.value == Decimal("10")


def test_no_numbers():
    result = analyze_text([(1, "Hello world")])
    assert result.raw is None
    assert result.scaled is None


def test_section_b_does_not_turn_grouped_figure_into_billions():
    text = (
        "Dollars in millions.\n"
        "Total budgetary resources 10,207.404\n"
        "B. Working Capital Fund"
    )
    result = analyze_text([(1, text)])
    assert result.raw.value == Decimal("10207.404")
    assert result.scaled.value == Decimal("10207404000.000")
    assert result.raw.original == "10,207.404"
