import json
from datetime import datetime

from scraper.exporters import export_json
from scraper.models import ScrapedProduct
from scraper.run_summary import build_run_summary_record, infer_status


def test_export_json_serializes_datetime(tmp_path) -> None:
    record = ScrapedProduct(
        merchant_name="test",
        source_url="https://example.com/p/1",
        product_title_raw="Kodak Gold 200",
        price=12.5,
        currency="EUR",
        in_stock=True,
        variant=None,
        exposures=36,
        is_bundle=False,
        format="35mm",
        platform_detected="html",
        scrape_method="simple_html",
        scraped_at=datetime(2026, 1, 1, 0, 0, 0),
    )
    out_file = tmp_path / "records.json"
    export_json([record], str(out_file))

    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload[0]["scraped_at"].startswith("2026-01-01T00:00:00")


def test_run_summary_record_generation() -> None:
    summary = build_run_summary_record(
        merchant_name="merchant",
        base_url="https://example.com",
        category_url="https://example.com/film",
        detected_platform="shopify",
        detection_confidence=0.91,
        scraper_used="shopify",
        raw_product_count=5,
        normalized_product_count=4,
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:00:05Z",
    )

    assert summary["merchant_name"] == "merchant"
    assert summary["status"] == "success"
    assert infer_status(0, 0, "") == "partial"
    assert infer_status(0, 0, "network error") == "failed"
