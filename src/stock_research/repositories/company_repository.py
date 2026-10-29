
"""Repository for storing and retrieving company records."""

import sqlite3


def add_company(
    connection: sqlite3.Connection,
    ticker: str,
    company_name: str | None = None,
    cik: str | None = None,
    exchange: str | None = None,
    currency: str | None = None,
    sector: str | None = None,
) -> int:
    """Insert a company and return its database ID.

    The ticker is normalized to uppercase. Duplicate tickers raise
    sqlite3.IntegrityError rather than silently overwriting data.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker must not be empty.")

    cursor = connection.execute(
        """
        INSERT INTO companies (
            ticker,
            company_name,
            cik,
            exchange,
            currency,
            sector
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            ticker,
            company_name,
            cik,
            exchange,
            currency,
            sector,
        ),
    )

    return cursor.lastrowid


def get_company_by_ticker(
    connection: sqlite3.Connection,
    ticker: str,
) -> sqlite3.Row | None:
    """Retrieve a company by ticker, or return None if it is not found."""
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker must not be empty.")

    return connection.execute(
        """
        SELECT *
        FROM companies
        WHERE ticker = ?
        """,
        (ticker,),
    ).fetchone()


def list_companies(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    """Return all companies ordered alphabetically by ticker."""
    return connection.execute(
        """
        SELECT *
        FROM companies
        ORDER BY ticker
        """
    ).fetchall()
