from __future__ import annotations

from datetime import datetime


def iso_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def infer_status(raw_product_count: int, normalized_product_count: int, error_message: str | None) -> str:
    if error_message:
        return "failed"
    if raw_product_count > 0 and normalized_product_count > 0:
        return "success"
    return "partial"


def build_run_summary_record(
    *,
    merchant_name: str,
    base_url: str,
    category_url: str,
    detected_platform: str,
    detection_confidence: float,
    scraper_used: str,
    raw_product_count: int,
    normalized_product_count: int,
    started_at: str,
    finished_at: str,
    error_message: str = "",
) -> dict[str, str | float | int]:
    return {
        "merchant_name": merchant_name,
        "base_url": base_url,
        "category_url": category_url,
        "detected_platform": detected_platform,
        "detection_confidence": round(float(detection_confidence), 3),
        "scraper_used": scraper_used,
        "raw_product_count": raw_product_count,
        "normalized_product_count": normalized_product_count,
        "status": infer_status(raw_product_count, normalized_product_count, error_message or None),
        "error_message": error_message,
        "started_at": started_at,
        "finished_at": finished_at,
    }
