
"""Unit tests for SQLite connection and transaction handling."""

import sqlite3
from contextlib import contextmanager

import pytest

from src.stock_research.database.connection import get_connection


@contextmanager
def temporary_database():
    """Create an isolated in-memory database for testing."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        with connection:
            yield connection
    finally:
        connection.close()


def test_connection_commits_successful_changes():
    """Verify successful transactions are committed."""
    connection = sqlite3.connect(":memory:")

    try:
        with connection:
            connection.execute(
                "CREATE TABLE example (value INTEGER)"
            )
            connection.execute(
                "INSERT INTO example VALUES (42)"
            )

        result = connection.execute(
            "SELECT value FROM example"
        ).fetchone()

        assert result[0] == 42
    finally:
        connection.close()


def test_connection_rolls_back_failed_transaction():
    """Verify a failed transaction rolls back its changes."""
    connection = sqlite3.connect(":memory:")

    try:
        connection.execute(
            "CREATE TABLE example (value INTEGER)"
        )
        connection.commit()

        with pytest.raises(RuntimeError):
            with connection:
                connection.execute(
                    "INSERT INTO example VALUES (42)"
                )
                raise RuntimeError("Simulated failure")

        result = connection.execute(
            "SELECT COUNT(*) FROM example"
        ).fetchone()

        assert result[0] == 0
    finally:
        connection.close()


def test_existing_database_connection_still_works():
    """Verify the project connection can query the existing database."""
    with get_connection() as connection:
        result = connection.execute(
            "SELECT 1 AS value"
        ).fetchone()

    assert result["value"] == 1

def test_foreign_keys_are_enabled():
    """Verify that application connections enforce foreign keys."""
    with get_connection() as connection:
        result = connection.execute("PRAGMA foreign_keys").fetchone()

    assert result[0] == 1