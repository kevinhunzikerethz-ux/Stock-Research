
from stock_research.database.connection import get_connection


def verify_sec_eps():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                fiscal_year,
                fiscal_period,
                period_start,
                period_end,
                value,
                form_type,
                filed_date
            FROM financial_facts
            WHERE company_id = ?
              AND concept = ?
            ORDER BY period_end DESC, filed_date DESC
            LIMIT 20
            """,
            (1, "EarningsPerShareDiluted"),
        ).fetchall()

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM financial_facts
            WHERE company_id = ?
              AND concept = ?
            """,
            (1, "EarningsPerShareDiluted"),
        ).fetchone()[0]

        print(f"Total stored EPS observations: {count}")
        print("\nMost recent observations:")
        print(
            "FY | Period | Start      | End        | EPS  | Form | Filed"
        )

        for row in rows:
            print(
                f"{row[0]} | {row[1]} | {row[2]} | {row[3]} "
                f"| {row[4]:.2f} | {row[5]} | {row[6]}"
            )


if __name__ == "__main__":
    verify_sec_eps()
