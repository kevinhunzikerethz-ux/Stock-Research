
"""Integration tests for the SQLite database."""

from src.stock_research.database.connection import (
    DATABASE_PATH,
    get_connection,
)


def test_database_file_exists():
    """Verify that the expected database file exists."""
    assert DATABASE_PATH.exists(), (
        f"Database file not found: {DATABASE_PATH}"
    )


def test_database_contains_price_tables():
    """Verify that the existing historical price tables are present."""
    with get_connection() as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

    expected_tables = {
        "prices_aapl",
        "prices_iren",
        "prices_msft",
        "prices_nvo",
    }

    missing_tables = expected_tables - tables

    assert not missing_tables, (
        f"Missing expected price tables: {sorted(missing_tables)}. "
        f"Database: {DATABASE_PATH}"
    )


def test_apple_prices_are_available():
    """Verify that Apple historical prices can be queried."""
    with get_connection() as connection:
        result = connection.execute(
            """
            SELECT COUNT(*) AS row_count
            FROM prices_aapl
            """
        ).fetchone()

    assert result["row_count"] > 0, (
        "The Apple price table contains no records."
    )
