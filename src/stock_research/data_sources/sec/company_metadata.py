
"""Resolve and persist company metadata needed by SEC data sources."""

from stock_research.data_sources.sec.sec_company_lookup import resolve_cik
from stock_research.database.connection import get_connection


def get_or_resolve_cik(ticker: str) -> str:
    """Return a company's CIK, resolving and saving it when necessary."""
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("Ticker must be a non-empty string.")

    normalized_ticker = ticker.strip().upper()

    with get_connection() as connection:
        company = connection.execute(
            """
            SELECT company_id, cik
            FROM companies
            WHERE ticker = ?
            """,
            (normalized_ticker,),
        ).fetchone()

        if company is None:
            raise ValueError(
                f"Company {normalized_ticker} does not exist in the database."
            )

        company_id, existing_cik = company

        # Reuse the CIK already stored in the database.
        if existing_cik:
            return str(existing_cik).zfill(10)

        # Resolve the missing CIK through the SEC mapping.
        cik = resolve_cik(normalized_ticker)

        # Persist the resolved CIK for future use.
        connection.execute(
            """
            UPDATE companies
            SET cik = ?, updated_at = CURRENT_TIMESTAMP
            WHERE company_id = ?
            """,
            (cik, company_id),
        )

        return cik
