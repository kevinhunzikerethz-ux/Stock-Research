
"""Build and display annual split-adjusted diluted EPS for a ticker."""

import sys
from datetime import date

import yfinance as yf

from stock_research.analytics.split_adjustment import (
    adjust_eps_for_stock_splits,
)
from stock_research.database.connection import get_connection


def build_annual_eps(ticker: str = "AAPL") -> None:
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("Ticker must not be empty.")

    ticker = ticker.strip().upper()

    # Retrieve stock-split events for this company.
    split_series = yf.Ticker(ticker).splits
    split_events = [
        (split_date.date(), float(ratio))
        for split_date, ratio in split_series.items()
    ]

    # Read annual diluted EPS observations from SQLite.
    with get_connection() as connection:
        company = connection.execute(
            "SELECT company_id FROM companies WHERE ticker = ?",
            (ticker,),
        ).fetchone()

        if company is None:
            raise ValueError(
                f"Company not found in database: {ticker}"
            )

        company_id = company[0]

        rows = connection.execute(
            """
            SELECT
                CAST(strftime('%Y', f.period_end) AS INTEGER) AS fiscal_year,
                f.period_start,
                f.period_end,
                f.value,
                f.filed_date
            FROM financial_facts AS f
            WHERE f.company_id = ?
              AND f.concept = ?
              AND f.form_type = '10-K'
              AND f.fiscal_period = 'FY'
              AND f.period_start IS NOT NULL
              AND f.period_end IS NOT NULL
              AND (
                    julianday(f.period_end)
                    - julianday(f.period_start)
                  ) BETWEEN 350 AND 380
              AND NOT EXISTS (
                  SELECT 1
                  FROM financial_facts AS earlier
                  WHERE earlier.company_id = f.company_id
                    AND earlier.concept = f.concept
                    AND earlier.form_type = '10-K'
                    AND earlier.period_start = f.period_start
                    AND earlier.period_end = f.period_end
                    AND earlier.filed_date < f.filed_date
              )
            ORDER BY f.period_end
            """,
            (company_id, "EarningsPerShareDiluted"),
        ).fetchall()

    print(f"Ticker: {ticker}")
    print(f"Annual periods selected: {len(rows)}")
    print(
        "\nFY | Period end | Reported EPS | "
        "Split-adjusted EPS | Filing date"
    )

    for fiscal_year, start, end, value, filed in rows:
        adjusted_eps = adjust_eps_for_stock_splits(
            reported_eps=float(value),
            period_end=date.fromisoformat(end),
            split_events=split_events,
        )

        print(
            f"{fiscal_year} | {end} | "
            f"{float(value):.2f} | "
            f"{adjusted_eps:.2f} | {filed}"
        )


if __name__ == "__main__":
    if len(sys.argv) > 2:
        raise SystemExit(
            "Usage: python scripts/build_annual_eps.py [TICKER]"
        )

    selected_ticker = sys.argv[1] if len(sys.argv) == 2 else "AAPL"
    build_annual_eps(selected_ticker)
