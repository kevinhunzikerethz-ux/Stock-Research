
"""Tests for the daily price-update service."""

from unittest.mock import patch

import pandas as pd

from stock_research.application.price_update_service import (
    sync_daily_prices,
)


def make_prices() -> pd.DataFrame:
    """Create a small valid price DataFrame for testing."""
    return pd.DataFrame(
        {
            "Close": [100.0, 101.0],
            "Adj Close": [99.0, 100.0],
        },
        index=pd.to_datetime(
            ["2026-10-27", "2026-10-28"]
        ),
    )


@patch(
    "stock_research.application.price_update_service.fetch_daily_prices"
)
def test_new_ticker_downloads_full_history(
    mock_fetch,
    tmp_path,
    monkeypatch,
):
    """A new ticker should request its full price history."""
    from stock_research.database import connection as db_connection

    database_path = tmp_path / "test.db"
    monkeypatch.setattr(
        db_connection,
        "DATABASE_PATH",
        database_path,
    )

    from stock_research.database.schema import initialize_database
    from stock_research.database.connection import get_connection

    with get_connection() as connection:
        initialize_database(connection)

    mock_fetch.return_value = make_prices()

    sync_daily_prices("TEST")

    mock_fetch.assert_called_once_with("TEST")

    with get_connection() as connection:
        status = connection.execute(
            """
            SELECT is_initialized
            FROM price_history_status
            WHERE company_id = (
                SELECT company_id FROM companies WHERE ticker = ?
            )
            """,
            ("TEST",),
        ).fetchone()

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM daily_prices
            WHERE company_id = (
                SELECT company_id FROM companies WHERE ticker = ?
            )
            """,
            ("TEST",),
        ).fetchone()[0]

    assert status["is_initialized"] == 1
    assert count == 2


@patch(
    "stock_research.application.price_update_service.fetch_daily_prices"
)
def test_initialized_ticker_uses_incremental_update(
    mock_fetch,
    tmp_path,
    monkeypatch,
):
    """An initialized ticker should request only a recent date range."""
    from stock_research.database import connection as db_connection

    database_path = tmp_path / "test.db"
    monkeypatch.setattr(
        db_connection,
        "DATABASE_PATH",
        database_path,
    )

    from stock_research.database.schema import initialize_database
    from stock_research.database.connection import get_connection
    from stock_research.repositories.company_repository import add_company
    from stock_research.repositories.daily_price_repository import (
        save_daily_prices,
    )

    with get_connection() as connection:
        initialize_database(connection)
        add_company(connection, ticker="TEST")

        save_daily_prices(connection, "TEST", make_prices())

        company_id = connection.execute(
            "SELECT company_id FROM companies WHERE ticker = ?",
            ("TEST",),
        ).fetchone()["company_id"]

        connection.execute(
            """
            INSERT INTO price_history_status (
                company_id,
                is_initialized
            )
            VALUES (?, 1)
            """,
            (company_id,),
        )

    mock_fetch.return_value = make_prices()

    sync_daily_prices("TEST", overlap_days=7)

    mock_fetch.assert_called_once_with(
        "TEST",
        start_date="2026-10-21",
    )
