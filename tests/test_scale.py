from pdf_max_number.numbers import find_numbers
from pdf_max_number.scale import detect_document_scale, scaled_exponent


def test_document_in_millions():
    text = "All figures are listed in millions of dollars unless noted."
    assert detect_document_scale(text) == 6


def test_document_thousands_marker():
    assert detect_document_scale("Amounts ($000)") == 3


def test_most_frequent_wins():
    text = "in millions " * 3 + " in thousands"
    assert detect_document_scale(text) == 6


def test_tie_uses_last_occurrence():
    text = "in millions then later in billions"
    assert detect_document_scale(text) == 9


def test_suffix_beats_document_scale():
    token = find_numbers("5bn")[0]
    exp, label = scaled_exponent(token, document_exp=6)
    assert exp == 9
    assert label.startswith("suffix")


def test_local_thousands_override():
    text = "All values are listed in millions. Exception table (in thousands): 12.5"
    token = find_numbers(text)[-1]
    exp, label = scaled_exponent(token, document_exp=6)
    assert exp == 3
    assert label.startswith("local")


def test_years_are_not_scaled():
    token = find_numbers("Values are listed in millions. Year 2024.")[-1]
    exp, label = scaled_exponent(token, document_exp=6)
    assert exp == 0
    assert label == "year"
