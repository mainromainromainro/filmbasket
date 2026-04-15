from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from config import DEFAULT_CURRENCY
from scraper.base import BaseScraper
from scraper.models import ScrapedProduct
from scraper.utils import (
    detect_bundle,
    detect_exposures,
    detect_format,
    extract_price_and_currency,
    infer_stock,
    is_likely_film_product,
    safe_join_url,
)

logger = logging.getLogger(__name__)

CARD_SELECTORS = [
    "[data-product-id]",
    ".product",
    ".product-card",
    ".product-item",
    ".grid-product",
    ".woocommerce ul.products li.product",
]
TITLE_SELECTORS = ["h2", "h3", ".product-title", ".card-title", "a[title]"]
PRICE_SELECTORS = [".price", "[data-price]", ".product-price", ".woocommerce-Price-amount"]
LINK_SELECTORS = ["a[href]"]


class SimpleHtmlScraper(BaseScraper):
    def scrape(self, merchant: dict[str, Any]) -> list[ScrapedProduct]:
        url = merchant.get("category_url") or merchant["base_url"]
        response = self._safe_request(url)
        results = self._extract_products_from_html(merchant=merchant, url=str(url), html=response.text)
        self._log_result(len(results), merchant)
        return results

    def _extract_products_from_html(self, merchant: dict[str, Any], url: str, html: str) -> list[ScrapedProduct]:
        soup = BeautifulSoup(html, "lxml")
        cards = self._find_product_cards(soup)

        results: list[ScrapedProduct] = []
        for card in cards:
            title = self._extract_text(card, TITLE_SELECTORS)
            if not title or not is_likely_film_product(title):
                continue

            price_text = self._extract_text(card, PRICE_SELECTORS)
            price, currency = extract_price_and_currency(price_text, DEFAULT_CURRENCY)
            href = self._extract_href(card, LINK_SELECTORS)
            source_url = safe_join_url(url, href) if href else url
            in_stock = infer_stock(card.get_text(" ", strip=True))

            results.append(
                ScrapedProduct(
                    merchant_name=merchant["merchant_name"],
                    source_url=source_url,
                    product_title_raw=title,
                    price=price,
                    currency=currency,
                    in_stock=in_stock,
                    variant=None,
                    exposures=detect_exposures(title),
                    is_bundle=detect_bundle(title),
                    format=detect_format(title),
                    platform_detected="html",
                    scrape_method="simple_html",
                    scraped_at=datetime.utcnow(),
                )
            )

        return results

    def _find_product_cards(self, soup: BeautifulSoup) -> list[Any]:
        for selector in CARD_SELECTORS:
            cards = soup.select(selector)
            if cards:
                logger.debug("Found %d cards with selector %s", len(cards), selector)
                return cards
        return []

    @staticmethod
    def _extract_text(node: Any, selectors: list[str]) -> str:
        for selector in selectors:
            element = node.select_one(selector)
            if element:
                if element.get("title"):
                    return str(element.get("title")).strip()
                return element.get_text(" ", strip=True)
        return ""

    @staticmethod
    def _extract_href(node: Any, selectors: list[str]) -> str | None:
        for selector in selectors:
            element = node.select_one(selector)
            if element and element.get("href"):
                return str(element.get("href")).strip()
        return None
