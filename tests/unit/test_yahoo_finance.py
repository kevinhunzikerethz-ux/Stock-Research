
"""Unit tests for the Yahoo Finance data source."""

from unittest.mock import patch

import pandas as pd
import pytest

from src.stock_research.data_sources.market_data.yahoo_finance import (
    YahooFinanceError,
    fetch_daily_prices,
)


def sample_prices() -> pd.DataFrame:
    """Create sample data without making a network request."""
    return pd.DataFrame(
        {
            "Open": [100.0, 102.0],
            "Close": [101.0, 103.0],
            "Adj Close": [99.0, 101.0],
            "Volume": [1000, 1200],
        },
        index=pd.to_datetime(
            ["2025-01-02", "2025-01-03"]
        ),
    )


@patch(
    "src.stock_research.data_sources.market_data.yahoo_finance.yf.Ticker"
)
def test_fetch_returns_only_required_columns(mock_ticker):
    mock_ticker.return_value.history.return_value = sample_prices()

    result = fetch_daily_prices("aapl")

    assert list(result.columns) == ["Close", "Adj Close"]
    assert result.index.name == "Date"
    assert len(result) == 2
    mock_ticker.assert_called_once_with("AAPL")


@patch(
    "src.stock_research.data_sources.market_data.yahoo_finance.yf.Ticker"
)
def test_fetch_uses_full_unadjusted_history(mock_ticker):
    mock_ticker.return_value.history.return_value = sample_prices()

    fetch_daily_prices("AAPL")

    mock_ticker.return_value.history.assert_called_once_with(
        period="max",
        interval="1d",
        auto_adjust=False,
        actions=False,
    )


def test_empty_ticker_is_rejected():
    with pytest.raises(ValueError, match="Ticker must not be empty"):
        fetch_daily_prices("  ")


@patch(
    "src.stock_research.data_sources.market_data.yahoo_finance.yf.Ticker"
)
def test_empty_response_raises_error(mock_ticker):
    mock_ticker.return_value.history.return_value = pd.DataFrame()

    with pytest.raises(YahooFinanceError, match="No price data"):
        fetch_daily_prices("AAPL")


@patch(
    "src.stock_research.data_sources.market_data.yahoo_finance.yf.Ticker"
)
def test_missing_required_column_raises_error(mock_ticker):
    mock_ticker.return_value.history.return_value = pd.DataFrame(
        {"Close": [100.0]}
    )

    with pytest.raises(YahooFinanceError, match="Missing required columns"):
        fetch_daily_prices("AAPL")


@patch(
    "src.stock_research.data_sources.market_data.yahoo_finance.yf.Ticker"
)
def test_missing_price_values_raise_error(mock_ticker):
    mock_ticker.return_value.history.return_value = pd.DataFrame(
        {
            "Close": [100.0, None],
            "Adj Close": [99.0, 98.0],
        }
    )

    with pytest.raises(YahooFinanceError, match="Missing closing-price"):
        fetch_daily_prices("AAPL")


@patch(
    "src.stock_research.data_sources.market_data.yahoo_finance.yf.Ticker"
)
def test_download_exception_is_wrapped(mock_ticker):
    mock_ticker.return_value.history.side_effect = RuntimeError(
        "Network unavailable"
    )

    with pytest.raises(YahooFinanceError, match="Failed to download"):
        fetch_daily_prices("AAPL")
