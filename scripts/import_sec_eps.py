
"""Import reported diluted EPS observations from SEC Company Facts."""

import json
import sys

from stock_research.data_sources.sec.sec_company_facts import (
    get_company_facts_file,
)
from stock_research.database.connection import get_connection


CONCEPT = "EarningsPerShareDiluted"
UNIT = "USD/shares"


def main(ticker: str = "AAPL") -> None:
    """Import diluted EPS observations for the requested ticker."""
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("Ticker must be a non-empty string.")

    ticker = ticker.strip().upper()

    # Resolve the CIK and retrieve the cached or newly downloaded SEC facts.
    input_file = get_company_facts_file(ticker)

    with input_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    # Verify that the local file belongs to the requested company.
    cik = str(data.get("cik", "")).zfill(10)

    if not cik.strip("0"):
        raise ValueError(
            f"The SEC Company Facts file for {ticker} has no valid CIK."
        )

    facts = data.get("facts", {}).get("us-gaap", {})
    concept_data = facts.get(CONCEPT)

    if concept_data is None:
        raise ValueError(
            f"{CONCEPT} was not found in the US-GAAP facts for {ticker}."
        )

    observations = concept_data.get("units", {}).get(UNIT, [])

    if not observations:
        raise ValueError(
            f"No observations found for {CONCEPT} with unit {UNIT} "
            f"for {ticker}."
        )

    with get_connection() as connection:
        company = connection.execute(
            "SELECT company_id, cik FROM companies WHERE ticker = ?",
            (ticker,),
        ).fetchone()

        if company is None:
            raise ValueError(
                f"Company {ticker} does not exist in the companies table."
            )

        company_id, database_cik = company

        # Check that the facts file matches the company in the database.
        if database_cik and str(database_cik).zfill(10) != cik:
            raise ValueError(
                f"CIK mismatch for {ticker}: database has "
                f"{str(database_cik).zfill(10)}, but the facts file has {cik}."
            )

        # Insert filing records first to satisfy the foreign-key constraint.
        filings = {}

        for item in observations:
            accession = item.get("accn")

            if not accession:
                continue

            filings[accession] = {
                "form_type": item.get("form"),
                "filing_date": item.get("filed"),
                "report_date": item.get("end"),
            }

        for accession, filing in filings.items():
            connection.execute(
                """
                INSERT OR IGNORE INTO sec_filings (
                    accession_number,
                    company_id,
                    form_type,
                    filing_date,
                    report_date,
                    primary_document
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    accession,
                    company_id,
                    filing["form_type"] or "UNKNOWN",
                    filing["filing_date"],
                    filing["report_date"],
                    None,
                ),
            )

        inserted = 0
        skipped = 0

        for item in observations:
            accession = item.get("accn")
            period_end = item.get("end")

            # Keep only observations tied to an SEC filing.
            if not accession or not period_end:
                skipped += 1
                continue

            cursor = connection.execute(
                """
                INSERT INTO financial_facts (
                    company_id,
                    concept,
                    period_start,
                    period_end,
                    fiscal_year,
                    fiscal_period,
                    value,
                    unit,
                    form_type,
                    filed_date,
                    accession_number,
                    source
                )
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM financial_facts
                    WHERE company_id = ?
                      AND concept = ?
                      AND period_start IS ?
                      AND period_end = ?
                      AND fiscal_year IS ?
                      AND fiscal_period IS ?
                      AND value = ?
                      AND unit = ?
                      AND accession_number = ?
                )
                """,
                (
                    company_id,
                    CONCEPT,
                    item.get("start"),
                    period_end,
                    item.get("fy"),
                    item.get("fp"),
                    item["val"],
                    UNIT,
                    item.get("form"),
                    item.get("filed"),
                    accession,
                    "SEC Company Facts",
                    company_id,
                    CONCEPT,
                    item.get("start"),
                    period_end,
                    item.get("fy"),
                    item.get("fp"),
                    item["val"],
                    UNIT,
                    accession,
                ),
            )

            if cursor.rowcount:
                inserted += 1
            else:
                skipped += 1

        connection.commit()

    print(f"Company: {ticker} (company_id={company_id})")
    print(f"CIK: {cik}")
    print(f"Input file: {input_file.name}")
    print(f"SEC observations found: {len(observations)}")
    print(f"Inserted: {inserted}")
    print(f"Skipped (missing metadata or already present): {skipped}")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        raise SystemExit(
            "Usage: python scripts/import_sec_eps.py [TICKER]"
        )

    selected_ticker = sys.argv[1] if len(sys.argv) == 2 else "AAPL"
    main(selected_ticker)
