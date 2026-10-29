
"""Repository for storing and retrieving daily stock prices."""

import sqlite3

import pandas as pd


def save_daily_prices(
    connection: sqlite3.Connection,
    ticker: str,
    prices: pd.DataFrame,
) -> int:
    """Insert or update daily prices for a registered company.

    The DataFrame must have a date index and Close / Adj Close columns.
    Returns the number of rows inserted or updated.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker must not be empty.")

    required_columns = {"Close", "Adj Close"}
    missing_columns = required_columns - set(prices.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required price columns: {sorted(missing_columns)}"
        )

    if prices.empty:
        return 0

    if prices.index.hasnans:
        raise ValueError("Price data contains missing dates.")

    if prices[list(required_columns)].isna().any().any():
        raise ValueError("Price data contains missing values.")

    if (prices[["Close", "Adj Close"]] <= 0).any().any():
        raise ValueError("Prices must be greater than zero.")

    company = connection.execute(
        "SELECT company_id FROM companies WHERE ticker = ?",
        (ticker,),
    ).fetchone()

    if company is None:
        raise ValueError(
            f"Company {ticker} is not registered in the database."
        )

    records = []

    for date, row in prices.iterrows():
        price_date = pd.Timestamp(date).date().isoformat()

        records.append(
            (
                company["company_id"],
                price_date,
                float(row["Close"]),
                float(row["Adj Close"]),
            )
        )

    cursor = connection.executemany(
        """
        INSERT INTO daily_prices (
            company_id,
            price_date,
            close,
            adj_close
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT (company_id, price_date)
        DO UPDATE SET
            close = excluded.close,
            adj_close = excluded.adj_close
        """,
        records,
    )

    return cursor.rowcount


def get_daily_prices(
    connection: sqlite3.Connection,
    ticker: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[sqlite3.Row]:
    """Retrieve daily prices in ascending date order.

    Optional dates use the YYYY-MM-DD format and are inclusive.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker must not be empty.")

    query = """
        SELECT
            p.price_date,
            p.close,
            p.adj_close
        FROM daily_prices AS p
        JOIN companies AS c
            ON c.company_id = p.company_id
        WHERE c.ticker = ?
    """
    parameters: list[str] = [ticker]

    if start_date is not None:
        query += " AND p.price_date >= ?"
        parameters.append(start_date)

    if end_date is not None:
        query += " AND p.price_date <= ?"
        parameters.append(end_date)

    query += " ORDER BY p.price_date"

    return connection.execute(query, parameters).fetchall()


def get_latest_price_date(
    connection: sqlite3.Connection,
    ticker: str,
) -> str | None:
    """Return the latest stored trading date, or None if no prices exist."""
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker must not be empty.")

    result = connection.execute(
        """
        SELECT MAX(p.price_date) AS latest_date
        FROM daily_prices AS p
        JOIN companies AS c
            ON c.company_id = p.company_id
        WHERE c.ticker = ?
        """,
        (ticker,),
    ).fetchone()

    return result["latest_date"]
