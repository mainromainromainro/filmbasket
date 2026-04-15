# Film Price Scraper (V1 MVP)

Local Python scraper for collecting 35mm film prices from e-commerce stores, then normalizing results against a canonical film catalog.

## What this tool does
- Reads merchants from CSV (or a single URL via CLI).
- Detects platform and prioritizes scraper path:
  1. Shopify (`/products.json`)
  2. Simple HTML selectors
  3. Playwright fallback
- Extracts raw product title, price, stock, currency, URL, and metadata.
- Matches scraped titles to a canonical 35mm product catalog conservatively.
- Exports raw and normalized results as CSV + JSON.

## Install
```bash
pip install -r requirements.txt
playwright install
```

## Run
From inside `film-price-scraper/`:

```bash
python main.py --merchant-file data/merchants.csv
python main.py --merchant-file data/merchants.csv --limit 2 --debug
python main.py --merchant-url https://kamerastore.com/products/35mm-films/ --headless true
```

## Output files
Written to `output/` by default (override with `--output-dir`):
- `raw_scrape.csv`
- `raw_scrape.json`
- `normalized_prices.csv`
- `normalized_prices.json`
- `run_summary.json` (one diagnostic record per merchant run, including status/error)

## Run tests
```bash
pytest
pytest tests/test_offline_fixtures.py
```

## Commands used for Phase validation
```bash
pip install -r requirements.txt
playwright install
python main.py --help
python main.py --merchant-url https://kamerastore.com/products/35mm-films/ --output-dir output/smoke_single
python main.py --merchant-file data/merchants.csv --limit 2 --output-dir output/smoke_batch
python main.py --merchant-file /tmp/merchants_broken.csv --limit 3 --output-dir output/smoke_failure
pytest
```

## Live vs offline verification
- **Live**: CLI runs against merchant URLs (depends on network + installed dependencies).
- **Offline**: fixture tests in `tests/test_offline_fixtures.py` validate extraction behavior without network calls.

## Add a new merchant
1. Add a row to `data/merchants.csv` with:
   - `merchant_name`
   - `country`
   - `base_url`
   - `category_url`
   - `notes`
2. Run scraper again using `--merchant-file data/merchants.csv`.

## Known V1 limitations
- Heuristic platform detection can misclassify edge cases.
- HTML selectors are generic and may miss site-specific cards.
- Playwright fallback is basic and not anti-bot aware.
- Product matching is conservative; some valid products may remain unmatched.
- No currency conversion in V1 (raw observed currency is preserved).
- Storefront structure changes can still break generic selectors.
