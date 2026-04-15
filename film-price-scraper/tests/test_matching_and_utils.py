from scraper.matching import _normalize_text, match_product
from scraper.utils import detect_bundle, detect_exposures, extract_price_and_currency


def test_title_normalization() -> None:
    assert _normalize_text(" Kodak Portra 400!!! ") == "kodak portra 400"


def test_product_matching_exact_and_alias() -> None:
    catalog = [
        {"canonical_name": "Kodak Portra 400", "aliases": "portra400,kodak portra,portra"},
        {"canonical_name": "Fuji C200", "aliases": "c200,fuji c200"},
    ]

    canonical_name, score = match_product("Kodak Portra 400 35mm 36exp", catalog)
    assert canonical_name == "Kodak Portra 400"
    assert score >= 0.9

    alias_name, alias_score = match_product("FujiFilm C200 Color Negative Film", catalog)
    assert alias_name == "Fuji C200"
    assert alias_score >= 0.7


def test_bundle_detection() -> None:
    assert detect_bundle("Kodak Gold 200 3-pack")
    assert detect_bundle("Ilford HP5 pack of 5")
    assert not detect_bundle("Kodak Gold 200 single roll")


def test_exposure_detection() -> None:
    assert detect_exposures("Kodak Gold 200 36exp") == 36
    assert detect_exposures("Fuji C200 24 exposures") == 24
    assert detect_exposures("Portra 400 35mm") == 36


def test_price_parsing_decimal_and_currency() -> None:
    price, currency = extract_price_and_currency("€12,99", "EUR")
    assert price == 12.99
    assert currency == "EUR"

    price2, currency2 = extract_price_and_currency("CZK 1.234,50", "EUR")
    assert price2 == 1234.50
    assert currency2 == "CZK"
