
from stock_research.database.connection import get_connection

def inspect_eps_storage():
    with get_connection() as connection:
        for table in ("companies", "sec_filings", "financial_facts"):
            print(f"\n--- {table} ---")

            columns = connection.execute(
                f'PRAGMA table_info("{table}")'
            ).fetchall()

            print("Columns:", [column[1] for column in columns])

        company = connection.execute(
            """
            SELECT company_id, ticker, company_name, cik
            FROM companies
            WHERE ticker = ?
            """,
            ("AAPL",),
        ).fetchone()

        print("\nApple company record:", tuple(company) if company else None)


def main():
    with get_connection() as connection:
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        print("\nDATABASE TABLES")

        for table_row in tables:
            table_name = table_row[0]
            print(f"\n{'=' * 60}")
            print(f"Table: {table_name}")

            # Inspect the table's columns.
            columns = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()

            for column in columns:
                print(
                    f"  {column[1]:30} "
                    f"type={column[2]:12} "
                    f"primary_key={column[5]}"
                )

            # Count rows without changing the data.
            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]

            print(f"Rows: {count}")


if __name__ == "__main__":
    inspect_eps_storage()