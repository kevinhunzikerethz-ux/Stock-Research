
"""Application service for synchronizing daily stock prices."""

from datetime import date, timedelta

from stock_research.database.connection import get_connection
from stock_research.data_sources.market_data.yahoo_finance import (
    fetch_daily_prices,
)
from stock_research.repositories.company_repository import (
    add_company,
    get_company_by_ticker,
)
from stock_research.repositories.daily_price_repository import (
    get_latest_price_date,
    save_daily_prices,
)


DEFAULT_OVERLAP_DAYS = 7


def sync_daily_prices(
    ticker: str,
    company_name: str | None = None,
    overlap_days: int = DEFAULT_OVERLAP_DAYS,
) -> int:
    """Synchronize a company's daily prices with SQLite.

    New companies receive their full available price history.
    Initialized companies receive a recent overlapping update.

    Returns the number of price records inserted or updated.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker must not be empty.")

    if overlap_days < 0:
        raise ValueError("overlap_days must not be negative.")

    # Step 1: Register the company if necessary and inspect its status.
    with get_connection() as connection:
        company = get_company_by_ticker(connection, ticker)

        if company is None:
            add_company(
                connection,
                ticker=ticker,
                company_name=company_name,
            )
            print(f"Registered {ticker}.")

        connection.execute(
            """
            INSERT OR IGNORE INTO price_history_status (company_id)
            SELECT company_id
            FROM companies
            WHERE ticker = ?
            """,
            (ticker,),
        )

        status = connection.execute(
            """
            SELECT is_initialized
            FROM price_history_status
            WHERE company_id = (
                SELECT company_id
                FROM companies
                WHERE ticker = ?
            )
            """,
            (ticker,),
        ).fetchone()

        latest_date = get_latest_price_date(connection, ticker)

        is_initialized = bool(status["is_initialized"])

    # Step 2: Download data outside the database connection.
    if is_initialized and latest_date is not None:
        start_date = (
            date.fromisoformat(latest_date)
            - timedelta(days=overlap_days)
        ).isoformat()

        print(
            f"Updating {ticker} from {start_date} "
            f"(latest stored date: {latest_date})."
        )

        prices = fetch_daily_prices(
            ticker,
            start_date=start_date,
        )
    else:
        print(f"Downloading full available price history for {ticker}.")

        prices = fetch_daily_prices(ticker)

    # Step 3: Save prices and update the status in one transaction.
    with get_connection() as connection:
        records_processed = save_daily_prices(
            connection,
            ticker,
            prices,
        )

        connection.execute(
            """
            UPDATE price_history_status
            SET
                is_initialized = 1,
                last_successful_update = CURRENT_TIMESTAMP
            WHERE company_id = (
                SELECT company_id
                FROM companies
                WHERE ticker = ?
            )
            """,
            (ticker,),
        )

    print(
        f"Successfully synchronized {ticker}: "
        f"{records_processed} price records inserted or updated."
    )

    return records_processed
