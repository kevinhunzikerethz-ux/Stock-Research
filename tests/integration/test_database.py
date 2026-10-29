
import sqlite3
from pathlib import Path

database_path = Path(__file__).parent / "stock_research.db"

with sqlite3.connect(database_path) as connection:
    tables = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """).fetchall()

    print("Available tables:")
    for (table_name,) in tables:
        print(f"  {table_name}")

    print("\nLatest Apple prices:")
    rows = connection.execute("""
        SELECT Date, Close, Volume
        FROM prices_aapl
        ORDER BY Date DESC
        LIMIT 5
    """).fetchall()

    for row in rows:
        print(row)
