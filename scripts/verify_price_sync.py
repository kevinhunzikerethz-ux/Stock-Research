
"""Verify synchronized daily prices in the SQLite database."""

from stock_research.database.connection import get_connection


def main() -> None:
    with get_connection() as connection:
        companies = connection.execute(
            """
            SELECT
                c.ticker,
                COUNT(p.price_date) AS price_count,
                MIN(p.price_date) AS first_date,
                MAX(p.price_date) AS latest_date,
                s.is_initialized,
                s.last_successful_update
            FROM companies AS c
            LEFT JOIN daily_prices AS p
                ON p.company_id = c.company_id
            LEFT JOIN price_history_status AS s
                ON s.company_id = c.company_id
            GROUP BY
                c.company_id,
                c.ticker,
                s.is_initialized,
                s.last_successful_update
            ORDER BY c.ticker
            """
        ).fetchall()

    print("Price synchronization status\n")

    for company in companies:
        print(
            f"{company['ticker']}: "
            f"{company['price_count']} prices | "
            f"{company['first_date']} to {company['latest_date']} | "
            f"initialized={company['is_initialized']} | "
            f"last update={company['last_successful_update']}"
        )


if __name__ == "__main__":
    main()
