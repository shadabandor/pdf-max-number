from decimal import Decimal

from pdf_max_number.numbers import find_numbers


def test_us_grouped_and_currency():
    tokens = find_numbers("Revenue was $1,234.56 last year.")
    assert [t.raw_value for t in tokens] == [Decimal("1234.56")]


def test_suffix_million():
    tokens = find_numbers("Market cap 3.15M")
    assert tokens[0].raw_value == Decimal("3150000")
    assert tokens[0].suffix_exp == 6


def test_suffix_bn_word():
    tokens = find_numbers("Liability of 5bn")
    assert tokens[0].raw_value == Decimal("5000000000")


def test_scientific():
    tokens = find_numbers("approx 1.2e6 units")
    assert tokens[0].raw_value == Decimal("1200000")
    assert tokens[0].scientific


def test_skips_slash_dates():
    tokens = find_numbers("Filed on 12/31/2024 with 10 widgets")
    assert [t.raw_value for t in tokens] == [Decimal("10")]


def test_iso_dates_skipped():
    tokens = find_numbers("Range 2024-01-01 to 99")
    assert [t.raw_value for t in tokens] == [Decimal("99")]


def test_accounting_negative():
    tokens = find_numbers("Loss of (1,234)")
    assert tokens[0].negative
    assert tokens[0].raw_value == Decimal("-1234")


def test_eu_decimal_comma():
    tokens = find_numbers("Total 1.234,56 euros")
    assert tokens[0].raw_value == Decimal("1234.56")


def test_percent_kept_as_figure():
    tokens = find_numbers("Margin 99.9%")
    assert tokens[0].raw_value == Decimal("99.9")


def test_grouped_decimal_is_not_billions():
    tokens = find_numbers("10,207.404")
    assert tokens[0].raw_value == Decimal("10207.404")
    assert tokens[0].suffix_exp == 0


def test_section_header_b_is_not_billion_suffix():
    tokens = find_numbers("Total 10,207.404\nB. Working Capital Fund")
    assert tokens[0].raw_value == Decimal("10207.404")
    assert tokens[0].suffix_exp == 0


def test_separated_letter_b_is_not_billion_suffix():
    tokens = find_numbers("10,207.404 B")
    assert tokens[0].raw_value == Decimal("10207.404")
    assert tokens[0].suffix_exp == 0


def test_word_billion_suffix_still_counts():
    tokens = find_numbers("Market 10,207.404 billion")
    assert tokens[0].raw_value == Decimal("10207404000000.000")
    assert tokens[0].suffix_exp == 9
