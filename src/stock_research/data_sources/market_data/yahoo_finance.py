
"""Download and validate daily stock prices from Yahoo Finance."""

from __future__ import annotations

import pandas as pd
import yfinance as yf


PRICE_COLUMNS = ["Close", "Adj Close"]


class YahooFinanceError(Exception):
    """Raised when Yahoo Finance data cannot be retrieved or validated."""


def fetch_daily_prices(
    ticker: str,
    start_date: str | None = None,
) -> pd.DataFrame:
    """Fetch historical daily prices for a ticker.

    If start_date is omitted, fetch the full available history.
    Otherwise, fetch prices from start_date onward.

    Returns a DataFrame indexed by trading date with:
    Close and Adj Close.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker must not be empty.")

    try:
        stock = yf.Ticker(ticker)

        if start_date is None:
            prices = stock.history(
                period="max",
                interval="1d",
                auto_adjust=False,
                actions=False,
            )
        else:
            prices = stock.history(
                start=start_date,
                interval="1d",
                auto_adjust=False,
                actions=False,
            )

    except Exception as exc:
        raise YahooFinanceError(
            f"Failed to download prices for {ticker}."
        ) from exc

    if prices is None or prices.empty:
        raise YahooFinanceError(
            f"No price data returned for {ticker}."
        )

    missing_columns = [
        column for column in PRICE_COLUMNS
        if column not in prices.columns
    ]

    if missing_columns:
        raise YahooFinanceError(
            f"Missing required columns for {ticker}: "
            f"{missing_columns}"
        )

    prices = prices[PRICE_COLUMNS].copy()
    prices.index.name = "Date"

    if prices.isna().any().any():
        raise YahooFinanceError(
            f"Missing closing-price values returned for {ticker}."
        )

    if (prices <= 0).any().any():
        raise YahooFinanceError(
            f"Non-positive closing prices returned for {ticker}."
        )

    return prices
