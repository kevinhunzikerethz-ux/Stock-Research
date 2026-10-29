from src.stock_research.database.connection import get_connection


def main() -> None:
    with get_connection() as connection:
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        for table in tables:
            table_name = table["name"]

            result = connection.execute(
                f"""
                SELECT
                    COUNT(*) AS row_count,
                    MIN(Date) AS first_date,
                    MAX(Date) AS last_date
                FROM "{table_name}"
                """
            ).fetchone()

            print(
                f"{table_name}: "
                f"{result['row_count']} rows, "
                f"from {result['first_date']} "
                f"to {result['last_date']}"
            )


if __name__ == "__main__":
    main()
