
"""Command-line interface for synchronizing stock prices."""

import argparse

from stock_research.application.price_update_service import (
    sync_daily_prices,
)


def main() -> None:
    """Synchronize prices for a ticker provided on the command line."""
    parser = argparse.ArgumentParser(
        description="Synchronize daily stock prices into SQLite."
    )
    parser.add_argument(
        "ticker",
        nargs="?",
        help="Stock ticker, for example AAPL, MSFT, or NVDA.",
    )

    args = parser.parse_args()

    # Prompt only when no ticker was supplied.
    ticker = args.ticker

    if ticker is None:
        ticker = input(
            "Enter a stock ticker (e.g. AAPL, MSFT, NVDA): "
        )

    ticker = ticker.strip().upper()

    if not ticker:
        print("No ticker entered. Nothing to do.")
        return

    try:
        sync_daily_prices(ticker)
    except Exception as exc:
        print(f"Failed to synchronize {ticker}: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
