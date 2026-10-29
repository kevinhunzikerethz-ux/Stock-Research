
"""Download and cache SEC Company Facts for a company."""

import gzip
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from stock_research.data_sources.sec.company_metadata import get_or_resolve_cik
from stock_research.data_sources.sec.sec_company_lookup import SEC_USER_AGENT


PROJECT_ROOT = Path(__file__).resolve().parents[4]
SEC_RAW_DIR = PROJECT_ROOT / "data" / "sec_raw"
SEC_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json"


class SECCompanyFactsError(Exception):
    """Raised when SEC Company Facts cannot be retrieved."""


def get_company_facts_file(ticker: str) -> Path:
    """Return the cached Company Facts file, downloading it if missing."""
    normalized_ticker = ticker.strip().upper()

    if not normalized_ticker:
        raise ValueError("Ticker must not be empty.")

    cik = get_or_resolve_cik(normalized_ticker)
    output_file = SEC_RAW_DIR / f"{normalized_ticker.lower()}_companyfacts.json"

    # Reuse the existing file if it already belongs to this company.
    if output_file.exists():
        try:
            with output_file.open("r", encoding="utf-8") as file:
                cached_data = json.load(file)

            if str(cached_data.get("cik", "")).zfill(10) == cik:
                return output_file
        except (OSError, ValueError):
            pass

    url = SEC_FACTS_URL.format(cik)

    request = Request(
        url,
        headers={
            "User-Agent": SEC_USER_AGENT,
            "Accept-Encoding": "gzip",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            raw_data = response.read()

        if raw_data.startswith(b"\x1f\x8b"):
            raw_data = gzip.decompress(raw_data)

        data = json.loads(raw_data.decode("utf-8"))

        if str(data.get("cik", "")).zfill(10) != cik:
            raise ValueError(
                f"The SEC response CIK does not match {normalized_ticker}."
            )

    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        EOFError,
        ValueError,
        UnicodeDecodeError,
    ) as exc:
        raise SECCompanyFactsError(
            f"Could not retrieve Company Facts for {normalized_ticker}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    SEC_RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    return output_file
