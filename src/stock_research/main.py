
"""Application entry point for the Stock Research Terminal."""

from stock_research.database.connection import get_connection
from stock_research.database.schema import initialize_database
from stock_research.repositories.company_repository import (
    add_company,
    get_company_by_ticker,
    list_companies,
)


INITIAL_COMPANIES = [
    {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "cik": "0000320193",
    },
    {
        "ticker": "IREN",
        "company_name": "IREN Limited",
    },
    {
        "ticker": "MSFT",
        "company_name": "Microsoft Corporation",
        "cik": "0000789019",
    },
    {
        "ticker": "NVO",
        "company_name": "Novo Nordisk",
        "cik": "0000353278",
    },
]


def main() -> None:
    """Initialize the database and register known companies."""

    with get_connection() as connection:
        # Create any missing tables and indexes.
        # Existing tables and records are preserved.
        initialize_database(connection)

        # Register the initial companies if they do not exist.
        for company_data in INITIAL_COMPANIES:
            ticker = company_data["ticker"]

            existing_company = get_company_by_ticker(
                connection,
                ticker,
            )

            if existing_company is None:
                add_company(connection, **company_data)
                print(f"Added {ticker}.")
            else:
                print(f"{ticker} already exists; skipped.")

        # Display the companies stored in the database.
        companies = list_companies(connection)

    print(f"\nCompanies stored: {len(companies)}")

    for company in companies:
        print(
            f"  {company['ticker']}: "
            f"{company['company_name'] or 'Name not set'}"
        )


if __name__ == "__main__":
    main()
