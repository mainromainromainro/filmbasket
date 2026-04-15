from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus

from config import DEFAULT_CURRENCY
from scraper.base import BaseScraper
from scraper.models import ScrapedProduct
from scraper.utils import (
    detect_bundle,
    detect_exposures,
    detect_format,
    extract_price_and_currency,
    is_likely_film_product,
    safe_join_url,
)

logger = logging.getLogger(__name__)


class ShopifyScraper(BaseScraper):
    def scrape(self, merchant: dict[str, Any]) -> list[ScrapedProduct]:
        base_url = merchant["base_url"].rstrip("/")
        all_products: list[ScrapedProduct] = []

        page = 1
        while True:
            products_url = f"{base_url}/products.json?limit=250&page={page}"
            response = self._safe_request(products_url)
            payload = response.json()
            products = payload.get("products", []) if isinstance(payload, dict) else []
            if not products:
                break
            all_products.extend(self._build_products_from_payload(merchant, payload))

            page += 1

        self._log_result(len(all_products), merchant)
        return all_products

    def _build_products_from_payload(self, merchant: dict[str, Any], payload: dict[str, Any]) -> list[ScrapedProduct]:
        base_url = merchant["base_url"].rstrip("/")
        merchant_name = merchant["merchant_name"]
        built: list[ScrapedProduct] = []
        products = payload.get("products", []) if isinstance(payload, dict) else []

        for product in products:
            title = str(product.get("title", "")).strip()
            if not is_likely_film_product(title):
                continue

            handle = str(product.get("handle", "")).strip()
            product_url = safe_join_url(base_url, f"/products/{quote_plus(handle)}") if handle else base_url
            variants = product.get("variants", [])
            if not variants:
                built.append(
                    ScrapedProduct(
                        merchant_name=merchant_name,
                        source_url=product_url,
                        product_title_raw=title,
                        price=None,
                        currency=DEFAULT_CURRENCY,
                        in_stock=bool(product.get("available", True)),
                        variant=None,
                        exposures=detect_exposures(title),
                        is_bundle=detect_bundle(title),
                        format=detect_format(title),
                        platform_detected="shopify",
                        scrape_method="shopify_products_json",
                        scraped_at=datetime.utcnow(),
                    )
                )
                continue

            for variant in variants:
                variant_title = str(variant.get("title") or "").strip() or None
                combined_title = f"{title} {variant_title}".strip() if variant_title else title
                price_val, currency = extract_price_and_currency(str(variant.get("price", "")), DEFAULT_CURRENCY)
                built.append(
                    ScrapedProduct(
                        merchant_name=merchant_name,
                        source_url=product_url,
                        product_title_raw=combined_title,
                        price=price_val,
                        currency=currency,
                        in_stock=bool(variant.get("available", product.get("available", True))),
                        variant=variant_title,
                        exposures=detect_exposures(combined_title),
                        is_bundle=detect_bundle(combined_title),
                        format=detect_format(combined_title),
                        platform_detected="shopify",
                        scrape_method="shopify_products_json",
                        scraped_at=datetime.utcnow(),
                    )
                )
        return built
