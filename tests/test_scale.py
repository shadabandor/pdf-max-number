from pdf_max_number.numbers import find_numbers
from pdf_max_number.scale import scaled_exponent


def test_suffix_is_applied():
    token = find_numbers("5bn")[0]
    exp, label = scaled_exponent(token)
    assert exp == 9
    assert label.startswith("suffix")


def test_local_thousands_override():
    text = "All values are listed in millions. Exception table (in thousands): 12.5"
    token = find_numbers(text)[-1]
    exp, label = scaled_exponent(token)
    assert exp == 3
    assert label.startswith("local")


def test_page_text_caption_applies_when_outside_snippet():
    page = "( Dollars in Thousands)\n" + ("padding " * 400) + "\n259,899.7"
    token = find_numbers(page)[-1]
    assert "thousand" not in token.context.lower()
    exp, label = scaled_exponent(token, page_text=page)
    assert exp == 3
    assert label == "local:thousands"


def test_no_page_phrase_means_no_scale():
    token = find_numbers("Unlabeled total 5000")[0]
    exp, label = scaled_exponent(token, page_text="Unlabeled total 5000")
    assert exp == 0
    assert label == "none"


def test_years_are_not_scaled():
    token = find_numbers("Values are listed in millions. Year 2024.")[-1]
    exp, label = scaled_exponent(token)
    assert exp == 0
    assert label == "year"


def test_absolute_dollar_amount_not_scaled():
    token = find_numbers("costing $6,000,000)")[0]
    exp, label = scaled_exponent(token)
    assert exp == 0
    assert label == "absolute"
