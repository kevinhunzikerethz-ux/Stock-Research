
"""Database schema and initialization for the Stock Research Terminal."""

import sqlite3


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        description TEXT NOT NULL,
        applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS companies (
        company_id INTEGER PRIMARY KEY,
        ticker TEXT NOT NULL UNIQUE COLLATE NOCASE,
        company_name TEXT,
        cik TEXT,
        exchange TEXT,
        currency TEXT,
        sector TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_prices (
        company_id INTEGER NOT NULL,
        price_date TEXT NOT NULL,
        close REAL NOT NULL CHECK (close > 0),
        adj_close REAL NOT NULL CHECK (adj_close > 0),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (company_id, price_date),
        FOREIGN KEY (company_id)
            REFERENCES companies(company_id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS annual_eps (
        company_id INTEGER NOT NULL,
        fiscal_year INTEGER NOT NULL,
        period_start TEXT NOT NULL,
        period_end TEXT NOT NULL,
        reported_eps REAL NOT NULL,
        split_adjusted_eps REAL NOT NULL,
        filed_date TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (company_id, fiscal_year),
        FOREIGN KEY (company_id)
            REFERENCES companies(company_id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_annual_eps_period
    ON annual_eps(company_id, period_end)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_daily_prices_date
    ON daily_prices(price_date)
    """,
    """
    CREATE TABLE IF NOT EXISTS sec_filings (
        accession_number TEXT PRIMARY KEY,
        company_id INTEGER NOT NULL,
        form_type TEXT NOT NULL,
        filing_date TEXT,
        report_date TEXT,
        filing_url TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id)
            REFERENCES companies(company_id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sec_filings_company_date
    ON sec_filings(company_id, filing_date)
    """,
    """
    CREATE TABLE IF NOT EXISTS financial_facts (
        fact_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL,
        accession_number TEXT,
        concept TEXT NOT NULL,
        period_start TEXT,
        period_end TEXT NOT NULL,
        fiscal_year INTEGER,
        fiscal_period TEXT,
        value REAL NOT NULL,
        unit TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id)
            REFERENCES companies(company_id)
            ON DELETE CASCADE,
        FOREIGN KEY (accession_number)
            REFERENCES sec_filings(accession_number)
            ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_financial_facts_company_period
    ON financial_facts(company_id, concept, period_end)
    """,
    """
    CREATE TABLE IF NOT EXISTS data_updates (
        update_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL,
        data_source TEXT NOT NULL,
        update_type TEXT NOT NULL,
        started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT,
        status TEXT NOT NULL DEFAULT 'running',
        records_processed INTEGER NOT NULL DEFAULT 0,
        error_message TEXT,
        FOREIGN KEY (company_id)
            REFERENCES companies(company_id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_data_updates_company
    ON data_updates(company_id, started_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS price_history_status (
        company_id INTEGER PRIMARY KEY,
        is_initialized INTEGER NOT NULL DEFAULT 0
            CHECK (is_initialized IN (0, 1)),
        last_successful_update TEXT,
        FOREIGN KEY (company_id)
            REFERENCES companies(company_id)
            ON DELETE CASCADE
    )
    """,
)


def initialize_database(connection: sqlite3.Connection) -> None:
    """Create missing tables and indexes in a single transaction.

    Existing tables and records are preserved. If initialization fails,
    all changes made by this initialization attempt are rolled back.
    """
    connection.execute("BEGIN IMMEDIATE")

    try:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)

        connection.execute(
            """
            INSERT OR IGNORE INTO schema_migrations (
                version,
                description
            )
            VALUES (?, ?)
            """,
            (1, "Create initial normalized research schema"),
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise
