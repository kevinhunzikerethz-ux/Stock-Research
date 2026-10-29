
"""Resolve stock tickers to CIKs using the SEC's official mapping."""

from __future__ import annotations

import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CACHE_FILE = PROJECT_ROOT / "data" / "sec_raw" / "company_tickers.json"

CACHE_MAX_AGE_DAYS = 30

# Replace this placeholder with your real contact email before making
# requests to the SEC.
SEC_USER_AGENT = "StockResearchTerminal YOUR_REAL_EMAIL@example.com"


class SECCompanyLookupError(Exception):
    """Raised when a ticker cannot be resolved through the SEC."""


def _download_ticker_mapping() -> dict:
    """Download the SEC ticker mapping and save it to the local cache."""
    request = Request(
        SEC_TICKER_URL,
        headers={
            "User-Agent": SEC_USER_AGENT,
            "Accept-Encoding": "gzip",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            raw_data = response.read()

        # Decompress the response if it is gzip-compressed.
        if raw_data.startswith(b"\x1f\x8b"):
            raw_data = gzip.decompress(raw_data)

        data = json.loads(raw_data.decode("utf-8"))

        if not isinstance(data, dict) or not data:
            raise ValueError("SEC returned an empty or invalid ticker mapping.")

        # Validate the structure before replacing the existing cache.
        if not all(
            isinstance(company, dict)
            and "ticker" in company
            and "cik_str" in company
            for company in data.values()
        ):
            raise ValueError("SEC ticker mapping has an unexpected structure.")

    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        EOFError,
        ValueError,
        UnicodeDecodeError,
    ) as exc:
        raise SECCompanyLookupError(
            "Could not download the SEC ticker-to-CIK mapping: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise SECCompanyLookupError(
            f"Downloaded the SEC mapping but could not save the cache: {exc}"
        ) from exc

    return data


def _load_ticker_mapping() -> dict:
    """Load the local mapping and refresh it when it is over 30 days old."""
    cached_data = None
    cache_is_valid = False

    if CACHE_FILE.exists():
        try:
            with CACHE_FILE.open("r", encoding="utf-8") as file:
                cached_data = json.load(file)

            if (
                not isinstance(cached_data, dict)
                or not cached_data
                or not all(
                    isinstance(company, dict)
                    and "ticker" in company
                    and "cik_str" in company
                    for company in cached_data.values()
                )
            ):
                raise ValueError("Cached SEC mapping has an invalid structure.")

            cache_is_valid = True

            cache_age_seconds = (
                datetime.now(timezone.utc).timestamp()
                - CACHE_FILE.stat().st_mtime
            )
            max_age_seconds = CACHE_MAX_AGE_DAYS * 24 * 60 * 60

            # A fresh cache avoids unnecessary SEC requests.
            if 0 <= cache_age_seconds < max_age_seconds:
                return cached_data

        except (OSError, ValueError):
            cached_data = None
            cache_is_valid = False

    # Download when the cache is missing, invalid, or older than 30 days.
    try:
        return _download_ticker_mapping()
    except SECCompanyLookupError:
        # If the SEC is unavailable, use an existing valid cache.
        if cache_is_valid and cached_data is not None:
            return cached_data
        raise


def resolve_cik(ticker: str) -> str:
    """Return the zero-padded SEC CIK for a stock ticker."""
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("Ticker must be a non-empty string.")

    normalized_ticker = ticker.strip().upper()
    mapping = _load_ticker_mapping()

    for company in mapping.values():
        if company["ticker"].strip().upper() == normalized_ticker:
            return str(company["cik_str"]).zfill(10)

    raise SECCompanyLookupError(
        f"Ticker {normalized_ticker} was not found in the SEC mapping."
    )
