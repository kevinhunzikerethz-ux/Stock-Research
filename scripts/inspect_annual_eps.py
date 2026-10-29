
from stock_research.database.connection import get_connection


def inspect_annual_eps():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                fiscal_year,
                fiscal_period,
                period_start,
                period_end,
                value,
                filed_date,
                accession_number
            FROM financial_facts
            WHERE company_id = ?
              AND concept = ?
              AND form_type = '10-K'
              AND period_start IS NOT NULL
              AND period_end IS NOT NULL
              AND (
                    julianday(period_end) - julianday(period_start)
                  ) BETWEEN 350 AND 380
            ORDER BY period_end DESC, filed_date DESC
            LIMIT 30
            """,
            (1, "EarningsPerShareDiluted"),
        ).fetchall()

        print(f"Full-year observations found: {len(rows)}")
        print("FY | FP | Start | End | EPS | Filed | Accession")

        for row in rows:
            print(" | ".join(str(value) for value in row))


if __name__ == "__main__":
    inspect_annual_eps()
