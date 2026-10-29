
"""Check whether the price history status table exists."""

from stock_research.database.connection import get_connection


def main() -> None:
    with get_connection() as connection:
        result = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = ?
              AND name = ?
            """,
            ("table", "price_history_status"),
        ).fetchone()

    if result:
        print("OK: price_history_status exists.")
    else:
        print("ERROR: price_history_status does not exist.")


if __name__ == "__main__":
    main()
