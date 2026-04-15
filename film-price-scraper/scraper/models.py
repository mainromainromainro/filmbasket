from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ScrapedProduct(BaseModel):
    merchant_name: str
    source_url: str
    product_title_raw: str
    price: float | None
    currency: str
    in_stock: bool
    variant: str | None
    exposures: int | None
    is_bundle: bool
    format: str
    platform_detected: str
    scrape_method: str
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class NormalizedProductRecord(BaseModel):
    merchant_name: str
    canonical_name: str | None
    matched: bool
    match_score: float
    product_title_raw: str
    price: float | None
    currency: str
    in_stock: bool
    source_url: str
    scraped_at: datetime
