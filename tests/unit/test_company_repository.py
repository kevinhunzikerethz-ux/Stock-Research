
"""Unit tests for the company repository."""

import sqlite3

import pytest

from src.stock_research.database.schema import initialize_database
from src.stock_research.repositories.company_repository import (
    add_company,
    get_company_by_ticker,
    list_companies,
)


@pytest.fixture
def connection():
    """Provide an isolated database with the application schema."""
    database = sqlite3.connect(":memory:")
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")

    initialize_database(database)

    yield database

    database.close()


def test_add_company_stores_company(connection):
    company_id = add_company(
        connection,
        ticker="aapl",
        company_name="Apple Inc.",
        cik="0000320193",
        exchange="NASDAQ",
        currency="USD",
        sector="Technology",
    )

    company = get_company_by_ticker(connection, "AAPL")

    assert company is not None
    assert company["company_id"] == company_id
    assert company["ticker"] == "AAPL"
    assert company["company_name"] == "Apple Inc."
    assert company["cik"] == "0000320193"
    assert company["exchange"] == "NASDAQ"
    assert company["currency"] == "USD"
    assert company["sector"] == "Technology"


def test_ticker_lookup_is_case_insensitive(connection):
    add_company(connection, "MSFT", company_name="Microsoft")

    company = get_company_by_ticker(connection, "msft")

    assert company is not None
    assert company["ticker"] == "MSFT"


def test_lookup_returns_none_for_unknown_ticker(connection):
    assert get_company_by_ticker(connection, "UNKNOWN") is None


def test_duplicate_ticker_is_rejected(connection):
    add_company(connection, "AAPL")

    with pytest.raises(sqlite3.IntegrityError):
        add_company(connection, "aapl")


def test_empty_ticker_is_rejected(connection):
    with pytest.raises(ValueError):
        add_company(connection, "   ")


def test_list_companies_returns_alphabetical_order(connection):
    add_company(connection, "MSFT")
    add_company(connection, "AAPL")
    add_company(connection, "IREN")

    companies = list_companies(connection)

    assert [company["ticker"] for company in companies] == [
        "AAPL",
        "IREN",
        "MSFT",
    ]


def test_company_persists_within_database_connection(connection):
    add_company(connection, "NVO", company_name="Novo Nordisk")

    connection.commit()

    company = get_company_by_ticker(connection, "NVO")

    assert company is not None
    assert company["company_name"] == "Novo Nordisk"
