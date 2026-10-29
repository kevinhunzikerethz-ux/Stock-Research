"""Repository for storing and retrieving annual split-adjusted EPS records."""

import math
import sqlite3


def save_annual_eps(
    connection: sqlite3.Connection,
    ticker: str,
    records: list[dict],
) -> int:
    """Insert or update annual EPS records for a company.

    Each record must contain:
        fiscal_year
        period_start
        period_end
        reported_eps
        split_adjusted_eps
        filed_date

    Returns the number of records inserted or updated.
    Unchanged records are not counted.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker must not be empty.")

    company = connection.execute(
        "SELECT company_id FROM companies WHERE ticker = ?",
        (ticker,),
    ).fetchone()

    if company is None:
        raise ValueError(f"Company not found in database: {ticker}")

    company_id = company["company_id"]
    records_processed = 0

    for record in records:
        required_fields = (
            "fiscal_year",
            "period_start",
            "period_end",
            "reported_eps",
            "split_adjusted_eps",
            "filed_date",
        )

        for field in required_fields:
            if field not in record:
                raise ValueError(f"Missing required EPS field: {field}")

        for field in ("reported_eps", "split_adjusted_eps"):
            value = record[field]
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{field} must be a finite number.")

        cursor = connection.execute(
            """
            INSERT INTO annual_eps (
                company_id,
                fiscal_year,
                period_start,
                period_end,
                reported_eps,
                split_adjusted_eps,
                filed_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_id, fiscal_year)
            DO UPDATE SET
                period_start = excluded.period_start,
                period_end = excluded.period_end,
                reported_eps = excluded.reported_eps,
                split_adjusted_eps = excluded.split_adjusted_eps,
                filed_date = excluded.filed_date,
                updated_at = CURRENT_TIMESTAMP
            WHERE
                annual_eps.period_start IS NOT excluded.period_start
                OR annual_eps.period_end IS NOT excluded.period_end
                OR annual_eps.reported_eps IS NOT excluded.reported_eps
                OR annual_eps.split_adjusted_eps IS NOT excluded.split_adjusted_eps
                OR annual_eps.filed_date IS NOT excluded.filed_date
            """,
            (
                company_id,
                record["fiscal_year"],
                record["period_start"],
                record["period_end"],
                record["reported_eps"],
                record["split_adjusted_eps"],
                record["filed_date"],
            ),
        )
        records_processed += cursor.rowcount

    return records_processed


def get_annual_eps(
    connection: sqlite3.Connection,
    ticker: str,
) -> list[sqlite3.Row]:
    """Retrieve annual EPS records in chronological order."""
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker must not be empty.")

    return connection.execute(
        """
        SELECT
            e.fiscal_year,
            e.period_start,
            e.period_end,
            e.reported_eps,
            e.split_adjusted_eps,
            e.filed_date,
            e.updated_at
        FROM annual_eps AS e
        JOIN companies AS c ON c.company_id = e.company_id
        WHERE c.ticker = ?
        ORDER BY e.period_end
        """,
        (ticker,),
    ).fetchall()
