
"""SQLite connection management for the Stock Research Terminal."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATABASE_PATH = PROJECT_ROOT / "data" / "stock_research.db"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Provide a managed SQLite connection with transaction handling.

    Successful operations are committed. If an exception occurs,
    uncommitted changes are rolled back. The connection is always closed.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        with connection:
            yield connection
    finally:
        connection.close()
