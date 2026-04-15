from __future__ import annotations

import json
from pathlib import Path

from scraper.shopify import ShopifyScraper
from scraper.simple_html import SimpleHtmlScraper

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_shopify_fixture_extraction() -> None:
    payload = json.loads((FIXTURE_DIR / "shopify_products.json").read_text(encoding="utf-8"))
    merchant = {
        "merchant_name": "fixture_shop",
        "base_url": "https://fixture.example",
        "category_url": "https://fixture.example/collections/film",
    }

    scraper = ShopifyScraper()
    products = scraper._build_products_from_payload(merchant, payload)

    assert len(products) == 2
    first = products[0]
    second = products[1]

    assert first.product_title_raw.lower().startswith("kodak gold 200")
    assert first.price == 28.99
    assert first.currency == "EUR"
    assert first.is_bundle is True
    assert first.exposures == 36

    assert second.product_title_raw.lower().startswith("ilford hp5+")
    assert second.in_stock is False
    assert second.exposures == 24


def test_simple_html_fixture_extraction() -> None:
    html = (FIXTURE_DIR / "category_page.html").read_text(encoding="utf-8")
    merchant = {
        "merchant_name": "fixture_html",
        "base_url": "https://example.com",
        "category_url": "https://example.com/film",
    }

    scraper = SimpleHtmlScraper()
    products = scraper._extract_products_from_html(merchant=merchant, url=merchant["category_url"], html=html)

    assert len(products) == 2

    portra = products[0]
    c200 = products[1]

    assert portra.price == 19.90
    assert portra.currency == "EUR"
    assert portra.in_stock is True
    assert portra.exposures == 36

    assert c200.price == 249.00
    assert c200.currency == "CZK"
    assert c200.in_stock is False
    assert c200.exposures == 24
