from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from config import DEFAULT_CURRENCY, HEADLESS
from scraper.base import BaseScraper
from scraper.models import ScrapedProduct
from scraper.simple_html import CARD_SELECTORS, LINK_SELECTORS, PRICE_SELECTORS, TITLE_SELECTORS
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


class PlaywrightScraper(BaseScraper):
    def __init__(self, headless: bool | None = None) -> None:
        self.headless = HEADLESS if headless is None else headless

    def scrape(self, merchant: dict[str, Any]) -> list[ScrapedProduct]:
        url = merchant.get("category_url") or merchant["base_url"]
        html = self._fetch_dynamic_html(url)
        soup = BeautifulSoup(html, "lxml")

        cards = []
        for selector in CARD_SELECTORS:
            cards = soup.select(selector)
            if cards:
                break

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
                    platform_detected="playwright",
                    scrape_method="playwright_fallback",
                    scraped_at=datetime.utcnow(),
                )
            )

        self._log_result(len(results), merchant)
        return results

    def _fetch_dynamic_html(self, url: str) -> str:
        logger.info("Playwright fallback loading: %s", url)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
        return html

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
