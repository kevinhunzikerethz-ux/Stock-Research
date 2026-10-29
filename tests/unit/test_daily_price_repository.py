
"""Unit tests for the daily-price repository."""

import sqlite3

import pandas as pd
import pytest

from src.stock_research.database.schema import initialize_database
from src.stock_research.repositories.company_repository import add_company
from src.stock_research.repositories.daily_price_repository import (
    get_daily_prices,
    get_latest_price_date,
    save_daily_prices,
)


@pytest.fixture
def connection():
    """Provide an isolated database with one registered company."""
    database = sqlite3.connect(":memory:")
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")

    initialize_database(database)
    add_company(database, "AAPL", company_name="Apple Inc.")
    database.commit()

    yield database

    database.close()


@pytest.fixture
def sample_prices():
    """Provide three sample daily prices."""
    return pd.DataFrame(
        {
            "Close": [100.0, 105.0, 110.0],
            "Adj Close": [99.0, 104.0, 109.0],
        },
        index=pd.to_datetime(
            ["2025-01-02", "2025-01-03", "2025-01-06"]
        ),
    )


def test_save_daily_prices_inserts_records(connection, sample_prices):
    count = save_daily_prices(connection, "AAPL", sample_prices)

    assert count == 3

    prices = get_daily_prices(connection, "AAPL")
    assert len(prices) == 3
    assert prices[0]["price_date"] == "2025-01-02"
    assert prices[0]["close"] == 100.0
    assert prices[0]["adj_close"] == 99.0


def test_saving_existing_dates_updates_instead_of_duplicating(
    connection, sample_prices
):
    save_daily_prices(connection, "AAPL", sample_prices)

    revised = pd.DataFrame(
        {"Close": [120.0], "Adj Close": [119.0]},
        index=pd.to_datetime(["2025-01-03"]),
    )

    save_daily_prices(connection, "AAPL", revised)

    prices = get_daily_prices(connection, "AAPL")

    assert len(prices) == 3
    assert prices[1]["close"] == 120.0
    assert prices[1]["adj_close"] == 119.0


def test_get_daily_prices_filters_inclusive_date_range(
    connection, sample_prices
):
    save_daily_prices(connection, "AAPL", sample_prices)

    prices = get_daily_prices(
        connection,
        "AAPL",
        start_date="2025-01-03",
        end_date="2025-01-03",
    )

    assert len(prices) == 1
    assert prices[0]["price_date"] == "2025-01-03"


def test_get_latest_price_date(connection, sample_prices):
    assert get_latest_price_date(connection, "AAPL") is None

    save_daily_prices(connection, "AAPL", sample_prices)

    assert get_latest_price_date(connection, "AAPL") == "2025-01-06"


def test_unknown_company_is_rejected(connection, sample_prices):
    with pytest.raises(ValueError, match="not registered"):
        save_daily_prices(connection, "UNKNOWN", sample_prices)


def test_missing_price_column_is_rejected(connection):
    invalid_prices = pd.DataFrame(
        {"Close": [100.0]},
        index=pd.to_datetime(["2025-01-02"]),
    )

    with pytest.raises(ValueError, match="Missing required price columns"):
        save_daily_prices(connection, "AAPL", invalid_prices)


def test_missing_price_value_is_rejected(connection):
    invalid_prices = pd.DataFrame(
        {"Close": [100.0], "Adj Close": [float("nan")]},
        index=pd.to_datetime(["2025-01-02"]),
    )

    with pytest.raises(ValueError, match="missing values"):
        save_daily_prices(connection, "AAPL", invalid_prices)


def test_empty_dataframe_returns_zero(connection):
    empty_prices = pd.DataFrame(
        columns=["Close", "Adj Close"],
        index=pd.DatetimeIndex([]),
    )

    assert save_daily_prices(connection, "AAPL", empty_prices) == 0
