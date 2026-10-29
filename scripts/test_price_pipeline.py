
"""Manually test the Yahoo Finance-to-SQLite price pipeline."""

from stock_research.data_sources.market_data.yahoo_finance import (
    fetch_daily_prices,
)
from stock_research.database.connection import get_connection
from stock_research.repositories.daily_price_repository import (
    get_daily_prices,
    get_latest_price_date,
    save_daily_prices,
)


def main() -> None:
    """Fetch a small recent sample, save it, and read it back."""
    ticker = input("Enter a registered ticker (e.g. AAPL): ").strip().upper()

    if not ticker:
        print("Please enter a ticker.")
        return

    print(f"Downloading prices for {ticker}...")

    try:
        prices = fetch_daily_prices(ticker)
    except Exception as exc:
        print(f"Download failed: {exc}")
        return

    # Keep the integration test small: only the latest five observations.
    sample = prices.tail(5)

    try:
        with get_connection() as connection:
            saved_count = save_daily_prices(connection, ticker, sample)
            connection.commit()

            stored_prices = get_daily_prices(
                connection,
                ticker,
                start_date=sample.index.min().date().isoformat(),
                end_date=sample.index.max().date().isoformat(),
            )
            latest_date = get_latest_price_date(connection, ticker)

    except Exception as exc:
        print(f"Database operation failed: {exc}")
        return

    print("\nPipeline test completed.")
    print(f"Ticker: {ticker}")
    print(f"Rows submitted: {len(sample)}")
    print(f"Rows inserted or updated: {saved_count}")
    print(f"Rows retrieved in selected date range: {len(stored_prices)}")
    print(f"Latest stored date: {latest_date}")

    if len(stored_prices) != len(sample):
        raise RuntimeError("Verification failed: saved row count mismatch.")

    print("Verification passed.")


if __name__ == "__main__":
    main()
