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
    assert result.raw.value == Decimal("2.0")
    assert result.scaled.value == Decimal("2000000")


def test_raw_ignores_natural_language_scale():
    result = analyze_text([(1, "259899.7 and 9.6 billion")])
    assert result.raw.value == Decimal("259899.7")
    assert result.raw.original == "259899.7"
    assert result.scaled.value == Decimal("9600000000")
    assert "billion" in result.scaled.original


def test_scientific_excluded_from_raw():
    result = analyze_text([(1, "approx 1.2e6 units and 99 widgets")])
    assert result.raw.value == Decimal("99")
    assert result.scaled.value == Decimal("1200000")


def test_scientific_only_has_no_raw():
    result = analyze_text([(1, "approx 1.2e6 units")])
    assert result.raw is None
    assert result.scaled.value == Decimal("1200000")


def test_page_caption_applies_beyond_snippet():
    """Table captions at the top of a page still scale figures far down the page."""
    filler = "Narrative text. " * 80
    thousands_page = f"( Dollars in Thousands) CSAG capital budget.\n{filler}\nTotal 259,899.7"
    millions_page = "All other exhibits are in millions. Headline 1.0."
    result = analyze_text([(1, millions_page), (2, thousands_page)])
    assert result.scaled.value == Decimal("259899700.0")
    assert result.scaled.original == "259,899.7"
    assert result.scaled.scale.startswith("local:thousands")
    assert result.scaled.page == 2


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


def test_full_dollar_amount_not_multiplied_by_page_scale():
    text = (
        "Dollars in millions. Revenue 20.0. "
        "Projects costing between $250,000 and $6,000,000."
    )
    result = analyze_text([(1, text)])
    assert result.raw.value == Decimal("6000000")
    assert result.scaled.value == Decimal("20000000")
    assert result.scaled.original == "20.0"


def test_other_page_scale_is_ignored():
    result = analyze_text(
        [
            (1, "This exhibit is in millions."),
            (2, "Unlabeled table total 5000"),
        ]
    )
    assert result.scaled.value == Decimal("5000")
    assert result.scaled.scale == "none"
