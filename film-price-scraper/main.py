from __future__ import annotations

import argparse
import csv
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import config
from scraper.detect import detect_platform
from scraper.exporters import export_csv, export_json
from scraper.normalize import normalize_results
from scraper.run_summary import build_run_summary_record, infer_status, iso_now

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="35mm film price scraper (local MVP)")
    parser.add_argument("--merchant-url", type=str, help="Single merchant URL to scrape")
    parser.add_argument("--merchant-file", type=str, default="data/merchants.csv", help="CSV of merchants")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of merchants")
    parser.add_argument("--headless", type=str, default=None, help="Playwright headless mode true/false")
    parser.add_argument("--output-dir", type=str, default=config.OUTPUT_DIR, help="Output directory")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def parse_headless(value: str | None) -> bool:
    if value is None:
        return config.HEADLESS
    return value.strip().lower() not in {"0", "false", "no", "off"}


def load_merchants(merchant_file: str, merchant_url: str | None) -> list[dict[str, Any]]:
    if merchant_url:
        return [
            {
                "merchant_name": "ad_hoc_merchant",
                "country": "unknown",
                "base_url": merchant_url,
                "category_url": merchant_url,
                "notes": "",
            }
        ]

    path = Path(merchant_file)
    merchants: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            merchants.append(row)
    return merchants


def get_scraper(scraper_name: str, headless: bool):
    if scraper_name == "shopify":
        from scraper.shopify import ShopifyScraper

        return ShopifyScraper()
    if scraper_name == "simple_html":
        from scraper.simple_html import SimpleHtmlScraper

        return SimpleHtmlScraper()
    from scraper.playwright_scraper import PlaywrightScraper

    return PlaywrightScraper(headless=headless)


def ensure_output_dir(path: str) -> Path:
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out


def export_all(raw_products: list[Any], normalized_products: list[Any], output_dir: Path) -> None:
    export_csv(raw_products, str(output_dir / "raw_scrape.csv"))
    export_json(raw_products, str(output_dir / "raw_scrape.json"))
    export_csv(normalized_products, str(output_dir / "normalized_prices.csv"))
    export_json(normalized_products, str(output_dir / "normalized_prices.json"))


def _compact_error_message(exc: Exception) -> str:
    message = str(exc).strip()
    return message[:300]


def main() -> None:
    args = parse_args()
    setup_logging(args.debug)

    headless = parse_headless(args.headless)
    output_dir = ensure_output_dir(args.output_dir)
    merchants = load_merchants(args.merchant_file, args.merchant_url)
    if args.limit is not None:
        merchants = merchants[: args.limit]

    logger.info("Loaded %d merchants", len(merchants))

    raw_products: list[Any] = []
    run_summary: list[dict[str, Any]] = []
    merchant_success = 0
    merchant_failed = 0

    for merchant in merchants:
        name = merchant.get("merchant_name", "unknown")
        base_url = str(merchant.get("base_url", ""))
        target_url = merchant.get("category_url") or merchant.get("base_url")
        category_url = str(target_url or "")
        started_at = iso_now()
        logger.info("Merchant start: %s (%s)", name, target_url)

        try:
            detection = detect_platform(str(target_url))
            chosen_scraper = str(detection["chosen_scraper"])
            logger.info(
                "Detection for %s: platform=%s confidence=%.2f scraper=%s",
                name,
                detection["platform"],
                float(detection["confidence"]),
                chosen_scraper,
            )
            scraper = get_scraper(chosen_scraper, headless)
            products = scraper.scrape(merchant)
            raw_products.extend(products)
            merchant_success += 1
            finished_at = iso_now()
            run_summary.append(
                build_run_summary_record(
                    merchant_name=name,
                    base_url=base_url,
                    category_url=category_url,
                    detected_platform=str(detection.get("platform", "unknown")),
                    detection_confidence=float(detection.get("confidence", 0.0)),
                    scraper_used=chosen_scraper,
                    raw_product_count=len(products),
                    normalized_product_count=0,
                    started_at=started_at,
                    finished_at=finished_at,
                )
            )
            logger.info("Merchant raw products: %s count=%d", name, len(products))
        except Exception as exc:
            merchant_failed += 1
            finished_at = iso_now()
            error_message = _compact_error_message(exc)
            logger.exception("Merchant failed: %s error=%s", name, error_message)
            run_summary.append(
                build_run_summary_record(
                    merchant_name=name,
                    base_url=base_url,
                    category_url=category_url,
                    detected_platform="unknown",
                    detection_confidence=0.0,
                    scraper_used="none",
                    raw_product_count=0,
                    normalized_product_count=0,
                    started_at=started_at,
                    finished_at=finished_at,
                    error_message=error_message,
                )
            )
            continue

    catalog_path = str(Path("data") / "product_catalog.csv")
    normalized_products = normalize_results(raw_products, catalog_path)
    normalized_count_by_merchant = Counter(item.merchant_name for item in normalized_products)

    for record in run_summary:
        merchant_name = str(record.get("merchant_name", ""))
        record["normalized_product_count"] = normalized_count_by_merchant.get(merchant_name, 0)
        record["status"] = infer_status(
            int(record.get("raw_product_count", 0)),
            int(record.get("normalized_product_count", 0)),
            str(record.get("error_message", "")) or None,
        )
        logger.info(
            "Merchant normalized products: %s count=%d status=%s",
            merchant_name,
            int(record["normalized_product_count"]),
            str(record.get("status", "")),
        )

    export_all(raw_products, normalized_products, output_dir)
    export_json(run_summary, str(output_dir / "run_summary.json"))

    logger.info("Run complete")
    logger.info("Merchants succeeded: %d", merchant_success)
    logger.info("Merchants failed: %d", merchant_failed)
    logger.info("Raw products: %d", len(raw_products))
    logger.info("Normalized records: %d", len(normalized_products))
    logger.info("Run summary records: %d", len(run_summary))
    logger.info("Outputs written to: %s", output_dir)


if __name__ == "__main__":
    main()
