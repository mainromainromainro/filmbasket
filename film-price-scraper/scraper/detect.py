from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _looks_like_shopify_headers(headers: requests.structures.CaseInsensitiveDict[str]) -> bool:
    return any(key.lower().startswith("x-shopify-") for key in headers.keys())


def _looks_like_shopify_html(html: str) -> bool:
    html_lower = html.lower()
    return "shopify.theme" in html_lower or "cdn.shopify.com" in html_lower


def _has_simple_price_signal(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    selectors = [".price", "[data-price]", ".product-price", ".woocommerce-Price-amount"]
    return any(soup.select_one(selector) for selector in selectors)


def _shopify_products_json_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    return urljoin(base, "/products.json?limit=1")


def detect_platform(url: str) -> dict[str, str | float]:
    logger.info("Detecting platform for %s", url)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Detection request failed for %s, using playwright fallback: %s", url, exc)
        return {"platform": "unknown", "confidence": 0.2, "chosen_scraper": "playwright"}

    html = response.text

    if _looks_like_shopify_headers(response.headers):
        return {"platform": "shopify", "confidence": 0.95, "chosen_scraper": "shopify"}

    if _looks_like_shopify_html(html):
        return {"platform": "shopify", "confidence": 0.9, "chosen_scraper": "shopify"}

    products_json_url = _shopify_products_json_url(url)
    logger.debug("Detection trying Shopify products endpoint: %s", products_json_url)
    try:
        products_response = requests.get(products_json_url, timeout=10)
        if products_response.ok:
            payload = products_response.json()
            if isinstance(payload, dict) and "products" in payload:
                return {"platform": "shopify", "confidence": 0.85, "chosen_scraper": "shopify"}
        logger.debug("products.json endpoint did not confirm Shopify for %s", url)
    except (requests.RequestException, ValueError):
        logger.debug("products.json check failed for %s", url)

    if _has_simple_price_signal(html):
        return {"platform": "html", "confidence": 0.7, "chosen_scraper": "simple_html"}

    return {"platform": "unknown", "confidence": 0.4, "chosen_scraper": "playwright"}
