
"""Manually download historical stock prices and export them to CSV."""

from pathlib import Path

from src.stock_research.data_sources.market_data.yahoo_finance import (
    fetch_daily_prices,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Download and export historical prices for a selected ticker."""
    ticker = input("Enter a stock ticker (e.g. AAPL): ").strip().upper()

    if not ticker:
        print("Error: Please enter a ticker symbol.")
        return

    try:
        prices = fetch_daily_prices(ticker)
    except ValueError as exc:
        print(f"Invalid input: {exc}")
        return
    except Exception as exc:
        print(f"Failed to retrieve prices: {exc}")
        return

    output_path = PROJECT_ROOT / "data" / f"{ticker}_historical_prices.csv"

    # Include the trading date as the first CSV column.
    prices.to_csv(output_path, index=True, index_label="Date")

    # Verify the downloaded data before reporting success.
    expected_columns = ["Close", "Adj Close"]

    assert list(prices.columns) == expected_columns, (
        f"Unexpected columns: {list(prices.columns)}"
    )
    assert not prices.empty, "No price data was downloaded."
    assert prices.index.name == "Date", "Date index is missing."
    assert prices.notna().all().all(), "Missing price values detected."

    print("\nDownload successful.")
    print(f"Ticker: {ticker}")
    print(f"Rows downloaded: {len(prices):,}")
    print(
        f"Date range: {prices.index.min().date()} "
        f"to {prices.index.max().date()}"
    )
    print(f"CSV saved to: {output_path}")
    print("Verification passed: Date, Close, and Adj Close are present.")


if __name__ == "__main__":
    main()
