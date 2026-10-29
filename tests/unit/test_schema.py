
"""Unit tests for database schema creation."""

import sqlite3

from src.stock_research.database.schema import initialize_database


def test_initialize_database_creates_expected_tables():
    """Verify that all initial schema tables are created."""
    connection = sqlite3.connect(":memory:")

    try:
        initialize_database(connection)

        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        expected_tables = {
            "schema_migrations",
            "companies",
            "daily_prices",
            "sec_filings",
            "financial_facts",
            "data_updates",
        }

        assert expected_tables.issubset(tables)
    finally:
        connection.close()


def test_initialize_database_preserves_existing_data():
    """Verify that existing tables and records are preserved."""
    connection = sqlite3.connect(":memory:")

    try:
        connection.execute(
            """
            CREATE TABLE prices_aapl (
                Date TEXT PRIMARY KEY,
                Close REAL
            )
            """
        )
        connection.execute(
            "INSERT INTO prices_aapl VALUES (?, ?)",
            ("2025-01-02", 100.0),
        )
        connection.commit()

        initialize_database(connection)

        row = connection.execute(
            "SELECT Date, Close FROM prices_aapl"
        ).fetchone()

        assert row == ("2025-01-02", 100.0)
    finally:
        connection.close()


def test_initialize_database_is_idempotent():
    """Verify that running initialization twice is safe."""
    connection = sqlite3.connect(":memory:")

    try:
        initialize_database(connection)
        initialize_database(connection)

        migrations = connection.execute(
            "SELECT version FROM schema_migrations"
        ).fetchall()

        assert migrations == [(1,)]
    finally:
        connection.close()


def test_initialize_database_rolls_back_on_failure():
    """Verify that failed initialization leaves no partial schema."""
    import sqlite3

    import pytest

    from src.stock_research.database.schema import (
        SCHEMA_STATEMENTS,
        initialize_database,
    )

    connection = sqlite3.connect(":memory:")

    try:
        # Force a failure after the first schema statement.
        original_statements = SCHEMA_STATEMENTS

        try:
            import src.stock_research.database.schema as schema

            schema.SCHEMA_STATEMENTS = (
                original_statements[0],
                "THIS IS NOT VALID SQL",
            )

            with pytest.raises(sqlite3.OperationalError):
                initialize_database(connection)
        finally:
            schema.SCHEMA_STATEMENTS = original_statements

        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        assert "schema_migrations" not in tables
    finally:
        connection.close()

