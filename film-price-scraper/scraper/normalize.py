from __future__ import annotations

import csv
from pathlib import Path

from config import MIN_MATCH_SCORE
from scraper.matching import match_product
from scraper.models import NormalizedProductRecord, ScrapedProduct


def _load_catalog(catalog_path: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with Path(catalog_path).open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows


def normalize_results(scraped: list[ScrapedProduct], catalog_path: str) -> list[NormalizedProductRecord]:
    catalog = _load_catalog(catalog_path)
    normalized: list[NormalizedProductRecord] = []

    for item in scraped:
        canonical_name, score = match_product(item.product_title_raw, catalog)
        matched = canonical_name is not None and score >= MIN_MATCH_SCORE

        normalized.append(
            NormalizedProductRecord(
                merchant_name=item.merchant_name,
                canonical_name=canonical_name if matched else None,
                matched=matched,
                match_score=score if matched else 0.0,
                product_title_raw=item.product_title_raw,
                price=item.price,
                currency=item.currency,
                in_stock=item.in_stock,
                source_url=item.source_url,
                scraped_at=item.scraped_at,
            )
        )

    return normalized
