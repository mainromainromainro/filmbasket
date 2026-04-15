from __future__ import annotations

import re
from urllib.parse import urljoin

FILM_KEYWORDS = [
    "portra",
    "superia",
    "c200",
    "ultramax",
    "gold 200",
    "colorplus",
    "cinestill",
    "hp5",
    "fp4",
    "kentmere",
    "tri-x",
    "trix",
    "tmax",
    "fomapan",
    "35mm",
]

BUNDLE_PATTERNS = [
    re.compile(r"\b3\s*[-x]?\s*pack\b", re.IGNORECASE),
    re.compile(r"\bx\s*3\b", re.IGNORECASE),
    re.compile(r"\bpack\s*of\s*3\b", re.IGNORECASE),
    re.compile(r"\b3er\b", re.IGNORECASE),
    re.compile(r"\b5\s*[-x]?\s*pack\b", re.IGNORECASE),
    re.compile(r"\bx\s*5\b", re.IGNORECASE),
    re.compile(r"\bpack\s*of\s*5\b", re.IGNORECASE),
]

CURRENCY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"€|eur", re.IGNORECASE), "EUR"),
    (re.compile(r"\$|usd", re.IGNORECASE), "USD"),
    (re.compile(r"czk|kč", re.IGNORECASE), "CZK"),
    (re.compile(r"£|gbp", re.IGNORECASE), "GBP"),
]

OUT_OF_STOCK_MARKERS = [
    "out of stock",
    "sold out",
    "agotado",
    "épuisé",
    "nicht verfügbar",
    "unavailable",
]


def is_likely_film_product(title: str) -> bool:
    lowered = title.lower()
    return any(keyword in lowered for keyword in FILM_KEYWORDS)


def detect_exposures(title: str) -> int | None:
    lowered = title.lower()
    if re.search(r"\b36\b|\b36exp\b|\b36 exposures\b", lowered):
        return 36
    if re.search(r"\b24\b|\b24exp\b|\b24 exposures\b", lowered):
        return 24
    if "35mm" in lowered:
        return 36
    return None


def detect_bundle(title: str) -> bool:
    return any(pattern.search(title) for pattern in BUNDLE_PATTERNS)


def detect_format(title: str) -> str:
    lowered = title.lower()
    if "120" in lowered:
        return "120"
    return "35mm"


def extract_price_and_currency(price_text: str, default_currency: str) -> tuple[float | None, str]:
    if not price_text:
        return None, default_currency

    currency = default_currency
    for pattern, code in CURRENCY_PATTERNS:
        if pattern.search(price_text):
            currency = code
            break

    normalized = price_text.replace("\xa0", " ").strip()
    normalized = re.sub(r"[^\d,.\s]", "", normalized)
    numeric_chunks = re.findall(r"\d[\d.,\s]*", normalized)
    if not numeric_chunks:
        return None, currency

    candidate = numeric_chunks[0].replace(" ", "")
    if "," in candidate and "." in candidate:
        if candidate.rfind(",") > candidate.rfind("."):
            candidate = candidate.replace(".", "").replace(",", ".")
        else:
            candidate = candidate.replace(",", "")
    elif "," in candidate:
        candidate = candidate.replace(",", ".")

    try:
        return float(candidate), currency
    except ValueError:
        return None, currency


def safe_join_url(base: str, path: str) -> str:
    return urljoin(base, path)


def infer_stock(text: str) -> bool:
    lowered = text.lower()
    return not any(marker in lowered for marker in OUT_OF_STOCK_MARKERS)
