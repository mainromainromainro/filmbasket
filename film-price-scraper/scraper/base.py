from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import requests
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

from config import BACKOFF_FACTOR, MAX_RETRIES, REQUEST_TIMEOUT
from scraper.models import ScrapedProduct

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    @abstractmethod
    def scrape(self, merchant: dict[str, Any]) -> list[ScrapedProduct]:
        raise NotImplementedError

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_fixed(BACKOFF_FACTOR), reraise=True)
    def _make_request(self, url: str) -> requests.Response:
        logger.debug("Requesting URL: %s", url)
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response

    def _safe_request(self, url: str) -> requests.Response:
        try:
            return self._make_request(url)
        except RetryError as exc:
            message = f"Failed after retries for URL: {url}"
            logger.error(message)
            raise RuntimeError(message) from exc
        except requests.RequestException as exc:
            message = f"HTTP request failed for URL: {url}"
            logger.error(message)
            raise RuntimeError(message) from exc

    def _log_result(self, count: int, merchant: dict[str, Any]) -> None:
        logger.info(
            "Merchant '%s' scraped product count: %d",
            merchant.get("merchant_name", "unknown"),
            count,
        )
